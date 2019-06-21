FROM n42org/tox

RUN apt-get update && \
apt-get upgrade -y && \
apt-get install -y g++  && \
apt-get clean && rm -r /var/lib/apt/lists/*

WORKDIR /code
