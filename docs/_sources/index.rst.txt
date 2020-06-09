Metapack: Data Packaging System
===============================

Metapack is a data package format and packging system that uses Metatab
formatted files for both metadata and for the instructions for building data
packages.

`Metatab <http://metatab.org>`_ is a metadata format that allows structured
metadata -- the sort of information about a dataset like title, origin, or date
of publication that you'd normally store in JSON, YAML or XML -- to be stored
and edited in tabular forms like CSV or Excel. Metatab files look exactly like
you'd expect, so they are very easy for non-technical users to read and edit,
using tools they already have. Metatab is an excellent format for creating,
storing and transmitting metadata. For more information about metatab, visit
http://metatab.org, or get :doc:`overview` to understand the format.

Using metapack, you can create a Metatab formatted file that describes the data
you'd like to package and create an Excel or Zip file data package that holds
that data. Metapack also includes programs to load data sets to AWS S3,
Data.World and CKAN, and to use these packages in Jupyter notebooks.

This python module provides CLI tools and APIs for inspecting and using data
packages, but does not provide support for building data packages. For building
data packages, see the `metapack-build
<https://github.com/Metatab/metapack-build>`_. module.



Install
=======


The most consistently reliable way to install Metapack, especially in MacOs,  is
within Conda, which will avoid having to compile the geographic libraries for
geos and gdal.

.. code-block:: bash

    conda create --name metapack python=3.6 --file https://raw.githubusercontent.com/Metatab/metapack/master/conda/conda-requirements.txt
    conda activate metapack
    pip install metapack

On Linux, you can usually install the Metapack package from PiPy with:

.. code-block:: bash

    $ pip install metapack

Other modules you may want include:

* `metapack-build <https://github.com/Metatab/metapack-build>`_ for building
  packages.
* `metapack-jupyter <https://github.com/Metatab/metapack-jupyter>`_. for
  Jupyter notebook support.
* `metapack-wp <https://github.com/Metatab/metapack-wp>`_. for publising
  packages to the web.

Install everything with

.. code-block:: bash

    $ pip install metapack metapack-build metapack-jupyter metapack-wp

For development, you'll probably want the development package, with sub-modules
for related repos:

.. code-block:: bash

    $ git clone --recursive https://github.com/Metatab/metapack-dev.git
    $ cd metapack-dev
    $ bin/init-develop.sh

Metatab and Metapack Overview
=============================

.. toctree::

    overview

Using Metapack Packages
=======================

.. toctree::
   :maxdepth: 3

   using


.. toctree::
   :maxdepth: 2

   commands

Building Metapack Packages
==========================

.. note::

	Creating Metapack packages requires the
	`metapack-build <https://github.com/Metatab/metapack-build>`_. module.

* :doc:`Getting Started Tutorial <mpbuild:build/GettingStarted>`
* :doc:`Generating Rows <mpbuild:build/GeneratingRows>`
* :doc:`Altering rows with transforms <mpbuild:build/Transforms>`


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
