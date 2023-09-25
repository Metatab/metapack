#!/usr/bin/env bash

cd /opt/metapack/git

source bin/activate

# The fs package has a requirement for six~=1.10.0 which gets screwed up, and isn't
# tested until metapack iterated over entrypoints at runtime.
pip uninstall -y six
pip install six==1.10.0

git clone https://github.com/CivicKnowledge/appurl.git
git clone https://github.com/CivicKnowledge/rowpipe.git
git clone https://github.com/CivicKnowledge/rowgenerators.git
git clone https://github.com/CivicKnowledge/metatab.git
git clone https://github.com/CivicKnowledge/metapack.git

for i in appurl rowpipe rowgenerators metatab metapack
do
    d=/opt/metapack/git/$i
    echo ==== $d ====
    cd $d
    python setup.py develop

done


