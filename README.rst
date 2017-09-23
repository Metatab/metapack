Metatab
=======

Parse and manipulate structured data and metadata in a tabular format.

`Metatab <http://metatab.org>`_ is a data format that allows structured metadata -- the sort you'd normally store in JSON, YAML or XML -- to be stored and edited in tabular forms like CSV or Excel. Metatab files look exactly like you'd expect, so they are very easy for non-technical users to read and edit, using tools they already have. Metatab is an excellent format for creating, storing and transmitting metadata. For more information about metatab, visit http://metatab.org.

Metapack is a packaging system that uses Metatab to create Zip, Excel and filesystem data packages.

This repository has a Python module and executable. For a Javascript version, see the `metatab-js <https://github.com/CivicKnowledge/metatab-js>`_ repository.


Install
-------

Metapack only works with Python 3.5 or later, and you'll almost certainly want to install it into a virtual environment. To set up a virtual environment:

.. code-block:: bash

    python3 -mvenv metapack
    cd metapack
    source bin/activate

Since we're stil in development, you'll get the latest code by installing package from github, but you can also install from pip. In either case, you should create the virtualenv, and afterward, you'll have to reinstall the six package because of an odd conflict

To install the package with pip:

.. code-block:: bash

    pip install metapack

Because the fs package has an odd version requirement on `six`, you'll have to fix the version:

.. code-block:: bash

    pip uninstall -y six
    pip install six==1.10.0

To run the tests, you'll also need to install some support modules;

.. code-block:: bash

    $ pip install fiona shapely pyproj terminaltables geopandas


Then test parsing using a remote file with:

.. code-block:: bash

    $ metatab -j https://raw.githubusercontent.com/CivicKnowledge/metatab-py/master/test-data/example1.csv

Run ``metatab -h`` to get other program options.

The ``test-data`` directory has test files that also serve as examples to parse. You can either clone the repo and parse them from the files, or from the Github page for the file, click on the ``raw`` button to get raw view of the flie, then copy the URL.

Getting Started
---------------

See `Getting Started <https://github.com/CivicKnowledge/metatab-py/blob/master/docs/GettingStarted.rst>`_ for an initial tutorial, or the other guides in the 
`docs directory on Github <https://github.com/CivicKnowledge/metatab-py/tree/master/docs>`_

