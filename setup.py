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

setup_d = dict(
    name='metapack',
    version='0.7.5',
    description='Data packaging system using Metatab',
    long_description=readme,
    packages=find_packages(),
    package_data={
        '': ['*.tpl', '*.tplx', '*.csv', '*.json', '*.txt', '*.ipynb', ''],
    },

    zip_safe=False,
    install_requires=[

        'unicodecsv',
        'pyyaml',
        'datapackage',
        'markdown',
        'boto3',
        'nbconvert',
        'IPython',
        'nameparser',
        'pybtex',
        'rowgenerators>=0.7.16',
        'metatabdecl>=1.0.0',
        'metatab>=0.6.6',
        'tableintuit>=0.0.6',
        'geoid>=1.0.4',
        'terminaltables',
        'docopt'


        # 'wordpress_xmlrpc'# For `mp notebook -w`, sending notebooks to wordpress
    ],

    entry_points={
        'console_scripts': [
            'mp=metapack.cli.mp:mp',
            'metaworld=metapack.cli.metaworld:metaworld',
            'metaaws=metapack.cli.metaaws:metaaws',
            'metasql=metapack.cli.metasql:metasql'

        ],
        'nbconvert.exporters': [
            'metapack = metapack.jupyter:MetapackExporter',
            'hugo = metapack.jupyter:HugoExporter',
        ],

        'appurl.urls': [
            "metapack+ = metapack.appurl:MetapackUrl",
            "metatab+ = metapack.appurl:MetapackUrl",
            ".ipynb = metapack.appurl:JupyterNotebookUrl",
            "index: = metapack.appurl:SearchUrl"

        ],
        'rowgenerators': [

            "<MetapackUrl> = metapack.rowgenerator:MetapackGenerator",
            "<JupyterNotebookUrl> = metapack.rowgenerator:JupyterNotebookSource",

        ],
        'mt.subcommands': [
            'pack=metapack.cli.metapack:metapack',
            'build=metapack.cli.build:build',
            's3=metapack.cli.metas3:metas3',
            'index=metapack.cli.index:index_args',
            'ckan=metapack.cli.metakan:metakan',
            'notebook=metapack.cli.notebook:notebook',
            'run=metapack.cli.run:run',
            'search=metapack.cli.search:search'

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
        'geo': ['fiona', 'shapely', 'pyproj'],

    },

    test_suite='metapack.test.test_suite.suite',
    tests_require=['nose','publicdata', 'geopandas', 'fiona', 'shapely', 'pyproj'],

)

setup(
    **setup_d
)
