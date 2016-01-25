# akca

Another Kinesis Consumer Application

## Prerequisite

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

### git

    sudo apt-get install git -y

### Amazon Kinesis Client Library for Python

Install [Amazon Kinesis Client Library for Python](https://github.com/awslabs/amazon-kinesis-client-python)

    git clone https://github.com/haje01/amazon-kinesis-client-python.git
    cd amazon-kinesis-client-python
    python3 setup.py download_jars
    sudo python3 setup.py install

## Install & Setup

    cd
    git clone https://github.com/haje01/akca.git
    cd akca
    cp akca/sample.properties app.properties
    vi app.properties

In `app.properties`, fill in `streamName`, `regionName` and absolute path of `kclpy_app.py` for `excutableName`.


## Launch

    ./launch.sh
