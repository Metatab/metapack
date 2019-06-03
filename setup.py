#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from setuptools import find_packages, setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
    readme = f.read()

classifiers = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3.4',
    'Topic :: Software Development :: Libraries :: Python Modules',
]


# noinspection PyTypeChecker
setup_d = dict(
    name='metapack',
    version='0.9.5',
    description='Data packaging system using Metatab',
    long_description=readme,
    packages=find_packages(),
    # package_data= {}, package_data is only used for binary distributions! ARRRG!

    zip_safe=False,
    install_requires=[
        'metatab',
        'metatabdecl',
        'rowgenerators',
        'geoid',
        'tableintuit',
        #
        # For generating documentation
        'markdown==2.6.11',
        'nameparser',
        'pybtex',
        'jinja2',
        'terminaltables',

        #
        'boto3',
        'bs4',
        'unicodecsv',
        'pyyaml',

        #
        # Fix dependency screwups
        #'urllib3', #'urllib3<1.24,>=1.20', # To keep botocore happy.
        #'click', # 'click<7.0,>=3.3', # For jsontableschema
        #'python-dateutil', #'python-dateutil<2.7.0', # Stupid botocore
        #'openpyxl', #'openpyxl<2.5', # Required by tabulator


        #'jupyter-console<5.2.0' # 6 and later cause conflict with ipython + prompt-toolkit
        # 'wordpress_xmlrpc'# For `mp notebook -w`, sending notebooks to wordpress
    ],

    entry_points={
        'console_scripts': [
            'mp=metapack.cli.mp:mp',
        ],
        'nbconvert.exporters': [
            #'metapack = metapack.jupyter:MetapackExporter',
            #'hugo = metapack.jupyter:HugoExporter',
        ],

        'appurl.urls': [
            "metapack+ = metapack.appurl:MetapackUrl",
            "index: = metapack.appurl:SearchUrl"

        ],
        'rowgenerators': [
            "metapack+.txt =  metatab.rowgenerators:TextRowGenerator",

        ],
        'mt.subcommands': [
            'info=metapack.cli.info:info_args',
            'config=metapack.cli.config:config_args',
            'index=metapack.cli.index:index_args',
            'search=metapack.cli.search:search',
            'run=metapack.cli.run:run',
            'doc=metapack.cli.doc:doc_args',
            'open=metapack.cli.open:open_args',
        ]
    },

    include_package_data=True,
    author='Eric Busboom',
    author_email='eric@civicknowledge.com',
    url='https://github.com/Metatab/metapack.git',
    license='BSD',
    classifiers=classifiers,
    extras_require={
        'test': ['datapackage'],
        'geo': ['fiona', 'shapely', 'pyproj', 'geopandas'],
        'jupyter': ['jupyter', 'pandas', 'geopandas' ],

    },

    test_suite='metapack.test.test_suite.suite',
    tests_require=['nose','publicdata', 'geopandas', 'fiona', 'shapely', 'pyproj', 'jupyter','tox','tox-pyenv'],

)

setup(
    **setup_d
)
