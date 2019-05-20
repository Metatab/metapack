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


Install
-------

Metapack only works with Python 3.5 or later, and you'll almost certainly want
to install it into a virtual environment. To set up a virtual environment:

.. code-block:: bash

    python3 -mvenv metapack
    cd metapack
    source bin/activate

Since we're stil in development, you'll get the latest code by installing
package from github, but you can also install from pip. In either case, you
should create the virtualenv, and afterward, you'll have to reinstall the six
package because of an odd conflict

To install the package with pip:

.. code-block:: bash

    pip install metapack

Because the fs package has an odd version requirement on `six`, you'll have to
fix the version:

.. code-block:: bash

    pip uninstall -y six
    pip install six==1.10.0

To run the tests, you'll also need to install some support modules;

.. code-block:: bash

    $ pip install fiona shapely pyproj terminaltables geopandas


Then test parsing using a remote file with the ``metatab`` program, from the
``metatab`` module:

.. code-block:: bash

    $ metatab -j https://raw.githubusercontent.com/CivicKnowledge/metatab-py/master/test-data/example1.csv

Run ``metatab -h`` to get other program options.

The ``test-data`` directory has test files that also serve as examples to
parse. You can either clone the repo and parse them from the files, or from the
Github page for the file, click on the ``raw`` button to get raw view of the
flie, then copy the URL.

The main program for metapack is `mt`, which has a number of ( extensible) sub
commands. See the commands with: ``mt -h``.

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


