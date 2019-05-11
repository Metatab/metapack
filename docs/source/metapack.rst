Metapack Overview
=================

A Metapackage data package is a collection of data and metadata, where the metadata is expressed in Metatab format, usually in a CSV file.[#other_formats].  Metapack packages come in several variants:

* Filesystem: files in a directory
* ZIP: A ZIPped Filesystem package
* S3: A Filesystem package in an S3 buckets
* Excel: All metadata and data in a single Excel spreadsheet
* Source: A Filesystem package with data processing instructions, to build all other package types.

Each package has data, metadata and documention.

* Root Metadata includes the title, name, identifiers, and other top level information
* Resources are data that is included in the data package, usually as a CSV file.
* References are URLs to other documents or data
* Documentation includes a README file, links to websites, and inline notes.
* Data Dictionary, a list of all tables and their columns. 

All of this data and metadata is acessible through either the Metapack programamtic interface or the CLI commands. 

The resources, references and documentation metadata makes heavy use of URLs to
refer to external resources, and the resources and references use of `custom
urls <https://row-generators.readthedocs.io/en/latest/appurls/index.html>`_ to
refer to row-oriented data.

.. rubric:: Footnotes

.. [#other_formats] Metatab can also be expressed in a line oriented format, which is easier to edit in the terminal and can be included in a Jupyter notebooks
