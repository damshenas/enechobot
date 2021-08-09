# Docker for bitbuicket pipeline 
# This can be used as custom image for the pipeline
# Not in use since we use AWS managed images for pipeline
# To be deleted 

FROM node:15.11.0-buster

ENV AWS_CDK_VERSION=1.92.0
ENV AWS_CLI_VERSION=1.19.22

RUN npm install --silent -g aws-cdk@${AWS_CDK_VERSION} && cdk version
RUN apt-get -qq -y update && apt-get -qq install -y  python3 python3-pip jq bash git groff less 
RUN pip3 -q install --no-cache-dir awscli==$AWS_CLI_VERSION && aws --version

WORKDIR /root
