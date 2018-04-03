#!/bin/bash
# Script to setup development environment


pip uninstall -y six
pip install six==1.10.0
pip install fiona shapely pyproj terminaltables geopandas pandas numpy

git clone https://github.com/CivicKnowledge/rowpipe.git && (cd rowpipe && python setup.py develop)
git clone https://github.com/CivicKnowledge/tableintuit.git && (cd tableintuit && python setup.py develop)
git clone https://github.com/CivicKnowledge/rowgenerators.git && (cd rowgenerators && python setup.py develop)
git clone https://github.com/CivicKnowledge/pandas-reporter.git && (cd pandas-reporter && python setup.py develop)
git clone https://github.com/CivicKnowledge/metatab.git; (cd metatab && python setup.py develop)
git clone https://github.com/CivicKnowledge/metapack.git; (cd metapack && python setup.py develop)

