
FROM ubuntu:16.04

MAINTAINER Eric Busboom "eric@civicknowledge.com"

#VOLUME /opt/metapack

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    gcc \
    git \
    language-pack-en \
    libffi-dev \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    make \
    python3 \
    python3-dev \
    python3-numpy \
    python3-pip \
    python3-scipy \
    python3-venv \
    sqlite3  \
    wget && \
    apt-get clean && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Fixes security warnings in later pip installs. The --ignore-installed bit is requred because some of the
# installed packages already exist, but pip 8 refuses to remove them because they were installed with
# distutils.
RUN pip3 install --upgrade pip && pip3 install --ignore-installed requests


WORKDIR /opt

RUN python3 -mvenv metapack

WORKDIR /opt/metapack

RUN git clone https://github.com/CivicKnowledge/rowpipe.git && \
    git clone https://github.com/CivicKnowledge/tableintuit.git && \
    git clone https://github.com/CivicKnowledge/rowgenerators.git &&  \
    git clone https://github.com/CivicKnowledge/pandas-reporter.git &&  \
    git clone https://github.com/CivicKnowledge/metatab.git &&  \
    git clone https://github.com/CivicKnowledge/metapack.git # foobar

ADD setup.sh /tmp/setup.sh

RUN /tmp/setup.sh

