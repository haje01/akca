# akca

Another Kinesis Consumer Application

## Setup

### Create IAM User

Create an appropriate IAM User for Kinesis Consumer. ( refer
http://docs.aws.amazon.com/kinesis/latest/dev/learning-kinesis-module-one-iam.html )

### Python3

    sudo apt-get install python3 -y

### pip3 

    sudo apt-get install python3-pip -y

### Java

    sudo apt-get install openjdk-7-jre-headless -y

### AWS CLI

	sudo pip3 install awscli
	aws configure

Enter previous IAM User Access Key & Secret Access Key.

### akca code

Install git

    sudo apt-get install git -y

Clone akca code

    cd
    git clone https://github.com/haje01/akca.git

### Amazon Kinesis Client Library for Python

Install [Amazon Kinesis Client Library for Python](https://github.com/awslabs/amazon-kinesis-client-python)

    git clone https://github.com/haje01/amazon-kinesis-client-python.git
    cd amazon-kinesis-client-python
    python3 setup.py download_jars
    sudo python3 setup.py install

### rtail

To monitor logs you need to install rtail

    sudo apt-get install npm -y
    sudo npm install -g rtail

### Fluentd

Install Fluentd for Ubuntu 14.04(Trusty)

    curl -L https://toolbelt.treasuredata.com/sh/install-ubuntu-trusty-td-agent2.sh | sh

Make log directory beforehand.

    sudo mkdir -p /logdata
    sudo chown -R td-agent:td-agent /logdata

Copy Fluentd config file.

    sudo cp ~/akca/files/td-agent.conf /etc/td-agent/td-agent.conf

Edit `/etc/td-agent/td-agent.conf` as your need, then restart Fluentd service

    sudo /etc/init.d/td-agent restart


### Python Fluentd logger

Install forked Python Fluentd logger. This has a small change that raises exception when `sender` retry reaches `bufmax` in order to ensure Kinesis records are properly sent to Fluentd. 

    git clone https://github.com/haje01/fluent-logger-python.git
    cd fluent-logger-python
    sudo pip3 install -e .
    
### Fluent Amazon S3 Output Plugin

    sudo td-agent-gem install fluent-plugin-s3

### Config KCL App

    cd akca
    cp files/sample.properties app.properties
    vi app.properties

In `app.properties`, fill in `streamName`, `regionName` and absolute path of `kclpy_app.py` for `excutableName`.

## Run

### Dev Launch

    ./launch.sh

### Service Launch

Install Supervisord

    sudo apt-get install supervisor -y

Copy Supervisord config file.

    sudo cp ~/akca/files/supervisord.conf /etc/supervisor/conf.d/akca.conf

Edit `/etc/supervisor/conf.d/akca.conf` as your need, then start Supervisord.

    sudo service supervisor start

### Monitoring
    
You can monitor various logs (Kinesis Consumer, Supervisor and Fluent) by `rtail`. Visit:

http://[RTAIL_WEB_HOST]:[RTAIL_WEB_PORT]

### Maintenance

When you stop service for maintenance, please remember to stop supervisor before fluentd(td-agent), otherwise you might lose some of your data.

    sudo service supervisor stop

then

    sudo /etd/init.d/td-agent stop


---

Have Fun!
