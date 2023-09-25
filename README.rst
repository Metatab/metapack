.. image:: https://travis-ci.org/Metatab/metapack.svg?branch=master
    :target: https://travis-ci.org/Metatab/metapack

Metapack, Metatab Data Packaging
================================

Parse and manipulate structured data and metadata in a tabular format.

`Metatab <http://metatab.org>`_ is a data format that allows structured
metadata -- the sort you'd normally store in JSON, YAML or XML -- to be stored
and edited in tabular forms like CSV or Excel. Metatab files look exactly like
you'd expect, so they are very easy for non-technical users to read and edit,
using tools they already have. Metatab is an excellent format for creating,
storing and transmitting metadata. For more information about metatab, visit
http://metatab.org.

Metapack is a packaging system that uses Metatab to create Zip, Excel and
filesystem data packages.

This repository has a Python module and executable. For a Javascript version,
see the `metatab-js <https://github.com/CivicKnowledge/metatab-js>`_ repository.

See the `documentation for full details <http://docs.metatab.org/>`_


Install
-------

Metapack requires geographic libraries, most importantly gda, pyproj, shapely
and geopandas. These libraries can be difficult to install, often requiring
compilation. By far, the easiest way to install them properly is with Anaconda.
And, because, metapack has a lot of dependencies, you'll want to install it in
a virtual environment. Metapack only works with Python 3.5 or later:

.. code-block:: bash

    $ conda create --name metapack python=3.7
    $ conda activate metapack
    $ conda install numpy pandas gdal geos pyproj=1.9.5.1 fiona shapely geopandas
    $ pip install metapack


Verify that the install worked by running `` mp config``


Getting Started
---------------

See `Getting Started
<https://github.com/CivicKnowledge/metatab-py/blob/master/docs/GettingStarted.rst>`_ for an initial tutorial, or the other guides in the `docs directory on
Github <https://github.com/CivicKnowledge/metatab-py/tree/master/docs>`_

Development Notes
-----------------

Clearing the Cache
++++++++++++++++++

Some tests can pass despite errors if the file the test is looking for is
cached. The cache can be set with an evironmental variable and cleared before
the tests to solve this problem


.. code-block:: bash

    $ cache_dir=/tmp/some/dir
    $ rm -rf $cache_dir
    $ mkdir -p  $cache_dir
    $ APPURL_CACHE=$cache_dir python setup.py test


Development Testing with Docker
+++++++++++++++++++++++++++++++

Testing during development for other versions of Python is a bit of a pain,
since you have to install the alternate version, and Tox will run all of the
tests, not just the one you want.

One way to deal with this is to install Docker locally, then run the docker
test container on the source directory. This is done automatically from the
Makefile in appurl/tests


.. code-block:: bash

    $ cd metapack/metapack/test
    $ make build # to create the container image
    $ make shell # to run bash the container

You now have a docker container where the /code directory is the appurl source
dir. Since the Docker container is running code from your host machine, you can
edit it normally.

Now, run tox to build the tox virtual environments, then enter the specific
version you want to run tests for and activate the virtual environment.

To run one environment. for example, Python 3.4

.. code-block:: bash

    # tox -e py34

To run one test in one environment environment. for example, Python 3.4

.. code-block:: bash

    # tox -e py34 -- -s
