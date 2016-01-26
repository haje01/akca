# akca

AWS Kinesis Consumer Application

## Setup

### Create IAM User

Create an appropriate IAM User for Kinesis Consumer. ( refer
http://docs.aws.amazon.com/kinesis/latest/dev/learning-kinesis-module-one-iam.html )

### Python3

### pip3 

    sudo apt-get install python3-pip -y

### Java

    sudo apt-get install openjdk-7-jre-headless -y

### AWS CLI

	sudo pip3 install awscli
	aws configure

Then, enter IAM Access Key & Secret Access Key. The IAM user should have appropriate permissions to access AWS resources. 

### git & source code

    sudo apt-get install git -y

Clone akca source

    git clone https://github.com/haje01/akca.git

### Amazon Kinesis Client Library for Python

Install [Amazon Kinesis Client Library for Python](https://github.com/awslabs/amazon-kinesis-client-python)

    git clone https://github.com/haje01/amazon-kinesis-client-python.git
    cd amazon-kinesis-client-python
    python3 setup.py download_jars
    sudo python3 setup.py install

### Fluentd

Install Fluentd for Ubuntu 14.04(Trusty)

    curl -L https://toolbelt.treasuredata.com/sh/install-ubuntu-trusty-td-agent2.sh | sh

Copy Fluentd config file.

    sudo cp ~/akca/files/td-agent.conf /etc/td-agent/td-agent.conf

Edit `/etc/td-agent/td-agent.conf` as your need, then start Fluentd service

    sudo /etc/init.d/td-agent restart


### Python Fluentd logger

    sudo pip3 install fluent-logger
    
### Fluent Amazon S3 Output Plugin

    sudo td-agent-gem install fluent-plugin-s3


## Setup

    cd
    git clone https://github.com/haje01/akca.git
    cd akca
    cp akca/sample.properties app.properties
    vi app.properties

In `app.properties`, fill in `streamName`, `regionName` and absolute path of `kclpy_app.py` for `excutableName`.

Make Log Directory

    sudo mkdir -p /logdata/${SERVICE_NAME}
    sudo chown -R td-agent:td-agent /logdata

## Launch

### Dev Launch

    ./launch.sh

### Service Launch

Install Supervisord

    sudo apt-get install supervisor -y

Copy Supervisord config file.

    sudo cp ~/akca/files/supervisord.conf /etc/supervisor/conf.d/akca.conf

Edit `/etc/supervisor/conf.d/akca.conf` as your need, then start Supervisord.

    sudo service supervisor start

#### Service Monitoring
    
Check Supervisor log 

    sudo tail -f /var/log/supervisor/supervisord.log

Check akca log

    tail -f /var/log/supervisor/akca.log
