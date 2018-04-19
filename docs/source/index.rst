
Metatab and Metapack
====================


`Metatab <http://metatab.org>`_ is a metadata format that allows structured
metadata -- the sort of information about a dataset like title, origin, or date
of publication that you'd normally store in JSON, YAML or XML -- to be stored
and edited in tabular forms like CSV or Excel. Metatab files look exactly like
you'd expect, so they are very easy for non-technical users to read and edit,
using tools they already have. Metatab is an excellent format for creating,
storing and transmitting metadata. 

The tabular format is much easier for data creators to write and for
data consumers to read, and it allows a complete data packages to be stored in
a single Excel file.

Metapack is a data package format and packging system that uses Metatab
formatted files for both metadata and for the instructions for building data
packages. You can create a Metatab formatted file that describes the data you'd
like to package and create an Excel or Zip file data package that holds that
data. Metapack also includes programs to load data sets to AWS S3, Data.World
and CKAN, and to use these packages in Jupyter notebooks.

Because Metatab is just a file format, and Metapack is the set of programs for
building data packages, this guide primarily deals with Metapack. For more
information about metatab, visit http://metatab.org.


Install
=======

Install the Metapack package from PiPy with:

.. code-block:: bash

    $ pip install metapack

For development, you'll probably want the development package, with sub-mdules for related repos: 

.. code-block:: bash

    $ git clone --recursive https://github.com/Metatab/metapack-dev.git
    $ cd metapack-dev
    $ bin/init-develop.sh

Quick Start
===========

Generate a new Metapack package with examples: 

.. code-block:: bash

    $ mp new -o metatab.org -d tutorial -L -E -T "Quickstart Example Package" 

You now have a Metapack package in the :file:`metatab.org-tutorial` directory, with two example data resources. Build the data packages with:

.. code-block:: bash

    $ mp build metatab.org-tutorial/ -f -e -z
    
Now the :file:`metatab.org-tutorial/_packages` directory has a Zip, Excel and Filesystem package, along with links to each package's unversioned name.  

Explore the schema for one of the built packages with: 

.. code-block:: bash

    $ cd metatab.org-tutorial/_packages/
    $ mp info -s metatab.org-tutorial-1.zip#random_names

And dump a sample of the data for a resource in a table format: 

.. code-block:: bash

    $ mp run -T metatab.org-tutorial-1.zip#random_names

Also, open the Excel package (metatab.org-tutorial-1.xlsx) to see the pretty
formatting of the metadata, and the generated HTML documentation in :file:`metatab.org-tutorial-1/index.html`

That's just a quick preview of how the system works. For more details see :doc:`GettingStarted`.

Contents
========

.. toctree::
    :maxdepth: 2
    
    Home <self>
    JustEnough.rst
    GettingStarted.rst
    WranglingPackages.rst
    GeneratingRows.rst
    commands.rst
    Publishing.rst
    


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
