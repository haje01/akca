#!/usr/bin/env python3
'''
Copyright 2014-2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Amazon Software License (the "License").
You may not use this file except in compliance with the License.
A copy of the License is located at

http://aws.amazon.com/asl/

or in the "license" file accompanying this file. This file is distributed
on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
express or implied. See the License for the specific language governing
permissions and limitations under the License.
'''
from __future__ import print_function
import sys, time, json, base64
import logging

from amazon_kclpy import kcl
from fluent.sender import SEND_FAIL_SEC

# Send fail error should be raised before checkpoint
CHECKPOINT_FREQ_SEC = SEND_FAIL_SEC * 3
MAX_SEND_ERROR = 10


class StopProcessing(Exception):
    pass


class RecordProcessor(kcl.RecordProcessorBase):
    '''
    A RecordProcessor processes a shard in a stream. Its methods will be called with this pattern:

    - initialize will be called once
    - process_records will be called zero or more times
    - shutdown will be called if this MultiLangDaemon instance loses the lease to this shard
    '''
    def __init__(self):
        self.SLEEP_SECONDS = 5
        self.CHECKPOINT_RETRIES = 5

    def initialize(self, shard_id):
        '''
        Called once by a KCLProcess before any calls to process_records

        :type shard_id: str
        :param shard_id: The shard id that this processor is going to be working on.
        '''
        self.largest_seq = None
        self.send_record_errcnt = 0
        self.last_checkpoint_time = time.time()
        self.shard_id = shard_id.replace('shardId', 'sid')

        import logging 
        logging.basicConfig(
             filename='/tmp/akca-{}.log'.format(self.shard_id),
             level=logging.INFO, 
             format= '[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
             datefmt='%H:%M:%S'
        )
        self._logging = logging

        from fluent import sender, event
        sender.setup('akca.{}'.format(self.shard_id))
        self.evt = event
        self.log_critical('processor initialized for {}'.format(self.shard_id))

    def log_info(self, msg):
        self._logging.info(msg)
        self.send('log.info', msg)

    def log_error(self, msg):
        self._logging.error(msg)
        self.send('log.error', msg)

    def log_critical(self, msg):
        self._logging.critical(msg)
        self.send('log.critical', msg)

    def send(self, tag, msg):
        try:
            self.evt.Event(tag, {'msg': msg})
        except Exception as e:
            self._logging.error("Send Error: {}".format(e))

    def checkpoint(self, checkpointer, sequence_number=None):
        '''
        Checkpoints with retries on retryable exceptions.

        :type checkpointer: amazon_kclpy.kcl.Checkpointer
        :param checkpointer: A checkpointer provided to either process_records or shutdown

        :type sequence_number: str
        :param sequence_number: A sequence number to checkpoint at.
        '''
        for n in range(0, self.CHECKPOINT_RETRIES):
            try:
                checkpointer.checkpoint(sequence_number)
                self.log_info('checkpoint success: {}'.format(sequence_number))
                return
            except kcl.CheckpointError as e:
                if 'ShutdownException' == e.value:
                    '''
                    A ShutdownException indicates that this record processor should be shutdown. This is due to
                    some failover event, e.g. another MultiLangDaemon has taken the lease for this shard.
                    '''
                    self.log_error('Encountered shutdown execption, skipping checkpoint')
                    return
                elif 'ThrottlingException' == e.value:
                    '''
                    A ThrottlingException indicates that one of our dependencies is is over burdened, e.g. too many
                    dynamo writes. We will sleep temporarily to let it recover.
                    '''
                    if self.CHECKPOINT_RETRIES - 1 == n:
                        self.log_error('Failed to checkpoint after {n} attempts, giving up.\n'.format(n=n))
                        return
                    else:
                        self.log_error('Was throttled while checkpointing, will attempt again in {s} seconds'.format(s=self.SLEEP_SECONDS))
                elif 'InvalidStateException' == e.value:
                    self.log_error('MultiLangDaemon reported an invalid state while checkpointing.\n')
                else: # Some other error
                    self.log_error('Encountered an error while checkpointing, error was {e}.\n'.format(e=e))
            time.sleep(self.SLEEP_SECONDS)

    def process_record(self, data, partition_key, sequence_number):
        '''
        Called for each record that is passed to process_records.

        :type data: str
        :param data: The blob of data that was contained in the record.

        :type partition_key: str
        :param partition_key: The key associated with this recod.

        :type sequence_number: int
        :param sequence_number: The sequence number associated with this record.
        '''
        ####################################
        # Insert your processing logic here
        ####################################
        try:
            data = data.decode('utf8')
            sd = json.loads(data)
            sd['_seq'] = str(sequence_number)
            sd['_shd'] = self.shard_id
        except Exception as e:
            self.log_error("JSON Error {} at {}".format(str(e), data))
            # if data has illegal format, send it as is.
            sd = data

        try:
            self.evt.Event('data', sd)
        except Exception as e:
            return False
        return True

    def process_records(self, records, checkpointer):
        '''
        Called by a KCLProcess with a list of records to be processed and a checkpointer which accepts sequence numbers
        from the records to indicate where in the stream to checkpoint.

        :type records: list
        :param records: A list of records that are to be processed. A record looks like
            {"data":"<base64 encoded string>","partitionKey":"someKey","sequenceNumber":"1234567890"} Note that "data" is a base64
            encoded string. You can use base64.b64decode to decode the data into a string. We currently do not do this decoding for you
            so as to leave it to your discretion whether you need to decode this particular piece of data.

        :type checkpointer: amazon_kclpy.kcl.Checkpointer
        :param checkpointer: A checkpointer which accepts a sequence number or no parameters.
        '''
        try:
            self.log_info('processing {} records'.format(len(records)))
            for record in records:
                # record data is base64 encoded, so we need to decode it first
                data = base64.b64decode(record.get('data'))
                seq = record.get('sequenceNumber')
                seq = int(seq)
                key = record.get('partitionKey')
                res = self.process_record(data, key, seq)
                if not res:
                    # sleep for a while
                    self.send_record_errcnt += 1
                    time.sleep(1)
                    if self.send_record_errcnt > MAX_SEND_ERROR:
                        raise StopProcessing()
                else:
                    self.send_record_errcnt = 0

                if self.largest_seq == None or seq > self.largest_seq:
                    self.largest_seq = seq

            self.log_info('processing done')
            self.send_record_errcnt = 0
            # Checkpoints every 60 seconds
            if time.time() - self.last_checkpoint_time > CHECKPOINT_FREQ_SEC:
                self.checkpoint(checkpointer, str(self.largest_seq))
                self.last_checkpoint_time = time.time()
        except StopProcessing:
            self._logging.critical("Over Max Error ({} errors). Stop Processing...".format(self.send_record_errcnt))
            time.sleep(60*60*24)  # Hopefully Killed by being Zombie
        except Exception as e:
            sys.stderr.write("======== Processing Error ========\n")
            sys.stderr.write("Encountered an exception while processing records. Exception was {e}\n".format(e=e))
            self.log_error('Processing Error: {}'.format(e))

    def shutdown(self, checkpointer, reason):
        '''
        Called by a KCLProcess instance to indicate that this record processor should shutdown. After this is called,
        there will be no more calls to any other methods of this record processor.

        :type checkpointer: amazon_kclpy.kcl.Checkpointer
        :param checkpointer: A checkpointer which accepts a sequence number or no parameters.

        :type reason: str
        :param reason: The reason this record processor is being shutdown, either TERMINATE or ZOMBIE. If ZOMBIE,
            clients should not checkpoint because there is possibly another record processor which has acquired the lease
            for this shard. If TERMINATE then checkpointer.checkpoint() should be called to checkpoint at the end of the
            shard so that this processor will be shutdown and new processor(s) will be created to for the child(ren) of
            this shard.
        '''
        self.log_critical('shutdown for {}'.format(reason))
        try:
            if reason == 'TERMINATE':
                # Checkpointing with no parameter will checkpoint at the
                # largest sequence number reached by this processor on this
                # shard id
                self.log_critical('Was told to terminate, will attempt to checkpoint.')
                self.checkpoint(checkpointer, None)
            else: # reason == 'ZOMBIE'
                self.log_critical('Shutting down due to failover. Will not checkpoint.')
        except:
            pass

if __name__ == "__main__":
    kclprocess = kcl.KCLProcess(RecordProcessor())
    kclprocess.run()
