#!/bin/bash
# Script to setup development environment
# If running on a new linux insall, or one that isn't set up for python development:
# apt install upgrade
# apt install update
# apt install gcc python3-dev python3-pip
#
# Maybe also these?
# libxml2-dev libxslt1-dev zlib1g-dev

git clone https://github.com/CivicKnowledge/rowpipe.git && (cd rowpipe && python setup.py develop)
git clone https://github.com/CivicKnowledge/tableintuit.git && (cd tableintuit && python setup.py develop)
git clone https://github.com/CivicKnowledge/rowgenerators.git && (cd rowgenerators && python setup.py develop)
git clone https://github.com/CivicKnowledge/pandas-reporter.git && (cd pandas-reporter && python setup.py develop)
git clone https://github.com/CivicKnowledge/metatab.git; (cd metatab && python setup.py develop)
git clone https://github.com/CivicKnowledge/metapack.git; (cd metapack && python setup.py develop)
pip uninstall -y six;
pip install six==1.10.0
pip install fiona shapely pyproj terminaltables geopandas
