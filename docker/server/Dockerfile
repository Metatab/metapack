FROM python:3.10-slim-buster
MAINTAINER Eric Busboom "eric@civicknowledge.com"

ARG CONFIG_FILE=metatab.yaml

VOLUME /opt/metatab

RUN  apt-get update && \
     apt-get install -y g++ gcc  python3-dev libxml2 libxml2-dev libxslt-dev  bash git

RUN pip install metapack-build metapack-wp publicdata_census invoke #2

RUN apt-get install -y cron anacron curl unzip

#RUN mkdir /etc/cron.weekly
ADD build_metatab.sh /etc/cron.weekly/build_metatab.sh

WORKDIR  /opt/metatab
RUN cd /tmp &&\
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install

ADD ${CONFIG_FILE} /etc/metapack.yaml


RUN git clone https://github.com/metatab-packages/template-collection.git  collection
#RUN git config pull.ff only 

