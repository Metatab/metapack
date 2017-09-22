#!/usr/bin/env bash

cd /opt/metapack

source bin/activate

cd rowpipe && python setup.py develop && cd .. && \
cd tableintuit && python setup.py develop && cd .. && \
cd rowgenerators && python setup.py develop && cd .. && \
cd pandas-reporter && python setup.py develop && cd .. && \
cd metatab && python setup.py develop && cd .. && \
cd metapack && python setup.py develop && cd .. && \
pip uninstall -y six && \
pip install six==1.10.0

pip install fiona shapely pyproj terminaltables geopandas pandas