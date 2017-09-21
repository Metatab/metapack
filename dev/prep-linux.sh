#!/usr/bin/env bash

# If running on a new linux insall, or one that isn't set up for python development:


apt upgrade && \
apt update && \
apt install -y gcc python3-dev python3-pip libxml2-dev libxslt1-dev zlib1g-dev