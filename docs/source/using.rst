Using Metapack Packages
=======================

Metapack packages come in several variants:

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

All of this data and metadata is acessible through either the Metapack programamtic interface or the CLI


Opening Packages
----------------

Finding Resources
-----------------

Iterating Data
--------------

Pandas and GeoPandas
--------------------