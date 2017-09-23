# Setup all of the key Metapack packages, from github.

FROM ubuntu:16.04

MAINTAINER Eric Busboom "eric@civicknowledge.com"

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


WORKDIR /opt/metapack

# Setup the git venv

RUN python3 -mvenv git

WORKDIR /opt/metapack/git

RUN . bin/activate && \
    bin/pip install --upgrade pip && \
    bin/pip install --ignore-installed requests && \
    bin/pip install pandas IPython nbconvert fiona shapely pyproj \
                 terminaltables tabulate geopandas pybtex boto3 pyyaml markdown unicodecsv docopt \
                 nameparser wheel datapackage fs && \
    bin/pip install tableintuit pandasreporter metatabdecl # other Civic Knowledge packages

ADD setup-git.sh /opt/metapack/git/setup.sh


# Setup the pip venv

WORKDIR /opt/metapack

RUN python3 -mvenv pip

WORKDIR /opt/metapack/pip

RUN . bin/activate && \
    bin/pip install --upgrade pip && \
    bin/pip install --ignore-installed requests && \
    bin/pip install pandas IPython nbconvert fiona shapely pyproj \
                 terminaltables tabulate geopandas pybtex boto3 pyyaml markdown unicodecsv docopt \
                 nameparser wheel datapackage fs && \
    bin/pip install tableintuit pandasreporter  metatabdecl # other Civic Knowledge packages

ADD setup-pip.sh /opt/metapack/pip/setup.sh

# Run the final install scripts

#RUN /tmp/setup-git.sh
#RUN /tmp/setup-pip.sh


VOLUME /opt/metapack
WORKDIR /opt/metapack


