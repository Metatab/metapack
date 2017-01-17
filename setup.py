#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from setuptools.command.test import test as TestCommand
from setuptools import find_packages
import uuid
import imp

from pip.req import parse_requirements

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
    readme = f.read()

ps_meta = imp.load_source('_meta', 'metapack/_meta.py')

packages = find_packages()

tests_require = install_requires = parse_requirements('requirements.txt', session=uuid.uuid1())

classifiers = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.4',
    'Topic :: Software Development :: Libraries :: Python Modules',
]


setup(
    name='metapack',
    version=ps_meta.__version__,
    description='Data format for storing structured data in spreadsheet tables',
    long_description=readme,
    packages=packages,
    include_package_data=True,

    install_requires=[
        'datapackage',
        'rowgenerators',
        'metatab'
    ],
    dependency_links=[
        'git+https://github.com/CivicKnowledge/rowgenerators.git#egg=rowgenerators',
        'git+https://github.com/CivicKnowledge/metatab-py.git#egg=metatab'
    ],

    entry_points={
        'console_scripts': [
            'metapack=metapack.cli:metapack',
        ],
    },

    author=ps_meta.__author__,
    author_email=ps_meta.__author__,
    url='https://github.com/CivicKnowledge/metapack.git',
    license='BSD',
    classifiers=classifiers,

)
