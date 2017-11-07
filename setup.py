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

setup(
    name='metapack',
    version='0.6.16',
    description='Data packaging system using Metatab',
    long_description=readme,
    packages=find_packages(),
    package_data={'metatab.jupyter': ['*.csv']},
    zip_safe=False,
    install_requires=[

        'unicodecsv',
        'pyyaml',
        'datapackage',
        'markdown',
        'boto3',
        'nbconvert',
        'docopt',
        'IPython',
        'nameparser',
        'pybtex',
        'appurl>=0.1.5',
        'rowgenerators>=0.7.0',
        'rowpipe>=0.1.5',
        'metatab>=0.6.6',
        'tableintuit>=0.0.6',
        'geoid>=1.0.4',

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
        ],
        'appurl.urls' : [
            "metapack+ = metapack.appurl:MetapackUrl",
            "metatab+ = metapack.appurl:MetapackUrl",
            ".ipynb = metapack.appurl:JupyterNotebookUrl"

        ],
        'rowgenerators': [

            "<MetapackUrl> = metapack.rowgenerator:MetapackGenerator",
            "<JupyterNotebookUrl> = metapack.rowgenerator:JupyterNotebookSource",

        ],
        'mt.subcommands': [
            'pack=metapack.cli.metapack:metapack',
            's3=metapack.cli.metas3:metas3',
            'ckan=metapack.cli.metakan:metakan',
            'notebook=metapack.cli.notebook:notebook'
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
        'geo': ['fiona','shapely','pyproj'],

    },

)
