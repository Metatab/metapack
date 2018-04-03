#!/usr/bin/env bash

cd /opt/metapack/pip

source bin/activate

# The fs package has a requirement for six~=1.10.0 which gets screwed up, and isn't
# tested until metapack iterated over entrypoints at runtime.
pip uninstall -y six
pip install six==1.10.0

pip install appurl rowgenerators rowpipe metatab metapack

# Get the metapack package so we have the test scripts

git clone https://github.com/CivicKnowledge/metapack.git
