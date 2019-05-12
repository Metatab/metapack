Metapack Overview
=================

A Metapackage data package is a collection of data and metadata, where the
metadata is expressed in Metatab format, usually in a CSV
file. Metapack packages come in several variants:

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

All of this data and metadata is acessible through either the Metapack
programamtic interface or the CLI commands.

The resources, references and documentation metadata makes heavy use of URLs to
refer to external resources, and the resources and references use of `custom
urls <https://row-generators.readthedocs.io/en/latest/appurls/index.html>`_ to
refer to row-oriented data.

For this overview, we'll refer to the metadata file for the `example.com-full-2017-us-1 <https://docs.google.com/spreadsheets/d/1j_rmEfDuR7h22GQvMp9s6pCKiiqW9l3xZY67IRnDiy8/edit?usp=sharing>`_ package 

Just Enough Metatab
-------------------

To fully understand this documentation, you'll want to have a basic
understanding of Metatab. The best information is in the `Specification
<https://github.com/Metatab/metatab-declarations/blob/master/specs/Metatab%20Spe
cification.md>`_, but you can get by with a short introduction.

Metatab is a tabular format for structured data, so you can put records that
have multiple properties and children into a spreadsheet. Each of the Metatab
records is a :code:`Term`. Terms have a short name and a fullt qualified name.
For instance, the term that holds title information is the :code:`Root.Title`
term, but can be shortened to :code:`Title`.

In a Metatab file, the first column always holds a term name, and the second
column holds the term value. The follwoing columns can hold properties, which
are also child terms.

Child Relationship are encoded by specifing a term that has the first part of
the fully qualified term be the same name as the parent term. For instance,
these rows:

+--------------+------------+
| Root.Table   | TableName  |
+--------------+------------+
| Table.Column | ColumnName |
+--------------+------------+
	
Will create a :code:`Root.Table` term, with a value of 'TableName' and a
:code:`Table.Column` child, with a column name of 'ColumnName'.

Rows can also have properties, values in the third column of the file or
later, which are converted to child properties. The term name for the
properties is specified in a header, which is part of the section the terms are
in. A Metatab document starts with a root section, but the section can be
explicitly set with a :code:`Section` term. Here is an example, from the
Schema section of a typical Metatab document:

+---------+------------+----------+
| Section | Schema     | DataType |
+---------+------------+----------+
| Table   | TableName  |          |
+---------+------------+----------+
| Column  | ColumnName | integer  |
+---------+------------+----------+

In the :code:`Section` row, the third column, "DataType" declares that in
this section, any value in the third column is a child of the row's term,
with a name of :code:`DataType`. Therefore, the third line of this example
results in a :code:`Table.Column` term with a value of "ColumnName" and the
:code:`Table.Column` term has a child term of type :code:`Column.DataType`
with a value of "integer"

For writing in text files, there is a "Text Lines" version of the format, which
consists of only the term and value portions of the format; all properties are
represented explicityly as children. This is the format you will see in this
documentation. For instance, the Schema section example would be expressed in
Text Lines as::

	Section: Schema
	Table: TableName
	Table.Column: ColumnName
	Column.DataType: Integer
	
In both CSV and Lines format, the parent portion of a term name can be elided if it can be inferred from the previous term, so the above example can also be written as:: 

	Section: Schema
	Table: TableName
	Table.Column: ColumnName
		.DataType: Integer
	
	
The Lines format is more compact and more readable in text files, so
occasionally documentation will use the Lines format.

Root, Documentation and Contact Metadata
----------------------------------------

The Root section is the first, unlabeled section of a Metatab document, which
contains information such as the package title, name, and identification
numbers. In the `example.com-full-2017-us-1
<https://docs.google.com/spreadsheets/d/1j_rmEfDuR7h22GQvMp9s6pCKiiqW9l3xZY67IRn
Diy8/edit?usp=sharing>`_ example file, the root section contains:

+--------------+---------------------------------------------------------------------+
| Declare      | metatab-latest                                                      |
+--------------+---------------------------------------------------------------------+
| Title        | A Metatab Example Data Package                                      |
+--------------+---------------------------------------------------------------------+
| Description  | An example data package, from the Metatab tutorial at               |
+--------------+---------------------------------------------------------------------+
| Description  | https://github.com/CivicKnowledge/metatab-py/blob/master/README.rst |
+--------------+---------------------------------------------------------------------+
| Identifier   | 96cd659b-94ad-46ae-9c18-4018caa64355                                |
+--------------+---------------------------------------------------------------------+
| Name         | example.com-full-2017-us-1                                          |
+--------------+---------------------------------------------------------------------+
| Dataset      | full                                                                |
+--------------+---------------------------------------------------------------------+
| Origin       | example.com                                                         |
+--------------+---------------------------------------------------------------------+
| Time         | 2017                                                                |
+--------------+---------------------------------------------------------------------+
| Space        | US                                                                  |
+--------------+---------------------------------------------------------------------+
| Version      | 1                                                                   |
+--------------+---------------------------------------------------------------------+
| Modified     | 2017-09-20T16:00:18                                                 |
+--------------+---------------------------------------------------------------------+
| Issued       | 2017-09-20T16:43:33                                                 |
+--------------+---------------------------------------------------------------------+
| Giturl       | https://github.com/CivicKnowledge/metapack.git                      |
+--------------+---------------------------------------------------------------------+
| Distribution | http://library.metatab.org/example.com-full-2017-us-1/metadata.csv  |
+--------------+---------------------------------------------------------------------+
| Distribution | http://library.metatab.org/example.com-full-2017-us-1.zip           |
+--------------+---------------------------------------------------------------------+
| Distribution | http://library.metatab.org/example.com-full-2017-us-1.csv           |
+--------------+---------------------------------------------------------------------+


Some of the important terms in this section include: 

* Declare: specifies the terms that are valid for the document and their datatypes. 
* Title: The dataset title
* Description: A simple description, which can be split across multiple terms. 
* Identifier: An automatically generated unique string for this dataset. 
* Name: The formal name of the dataset, which is created from the Origin, Dataset, Variation, Time, Space, Grain and Version terms. 
* Distribution: Indicates where other versions of this same package are located on the Web. 

The Documentation section has links to URLS, or text files included in a ZIP
package, for imporant documentation, download pages, data dictionaries, or notes. 

The Contacts section lists the names, urls and email addresses for people opr organizations that created, wrangled or published the dataset. 


Resources and References
------------------------

The heart of the metadata is the Resorces and References section. Both sections
have the same format, with an important difference: The Resources section
declares row-oriented datafiles that are included in data packages ( ie, files
that are copied into a ZIP package ) while the References section specifies
URLs to objects that are not included in the data package, and may not be
row-oriented data.

The Resources section has ( Line Lines format ) ::

	Section: Resources|Name|schema|StartLine|HeaderLines|Description|nrows|||
	Datafile: http://public.source.civicknowledge.com/example.com/sources\
			  /test_data.zip#renter_cost.csv
	    .Name: renter_cost
	    .Startline: 5
	    .Headerlines: 3,4
	    .Description: Portion of income spent on rent, extracted from the ACS
	    .Nrows: 12000


The values for the Datafile terms are urls that reference row-oriented data on
the web. The fragment portion of the URL -- preceeded by a '#' -- describes
that file within the ZIP file to extract. The ``.Startline`` argument indicates
that the first data line of the file is on line 5, not line 1 as is typical,
and the ``.Headerlines`` argument indicates that rather than using line 0 for
the headers, the headers are on lines 3 and 4. The values in line 3 and line 4
will be concatenated column-wise.

Datafiles can also be references from other metatab packages, such as with this resource line::

	Datafile: metapack+http://library.metatab.org/\
	          example.com-simple_example-2017-us-2.csv#random-names
	    .Name: random-names-csv
	    .Schema: random-names
	    .Description: Names and a random number

The ``metapack+`` portion of the URL indicates that the URL references a
metapack package, and the fragment ``#random-names`` is a resource in the
package.

In source packages, resources can also reference programs::

	Datafile: program+file:scripts/rowgen.py
	    .Name: rowgen

The preceeding examples are actually from a source package, so when this
package is built all of the resources will be downloaded and processed into a
standard CSV files, with a corresponding change to their URLs.


The References section has the same structure to URLs, but the data for the
resources is not copied into the data package. References frequently refer to
more complex data, such as geographic shape files::

	Reference: shape+http://ds.civicknowledge.org/\
	           sangis.org/Subregional_Areas_2010.zip
	    .Name: sra
	    .Description: Sub-regional areas

The ``shape+`` protocol is defined in the `rowgenerators module
<https://github.com/Metatab/rowgenerators>`_. The full set of url patterns that
the rowgenerators module recognizes can be found from running the
:command:`rowgen-urls -l` program


Schemas: The Data Dictionary
----------------------------

The last major section of the metadata is the Schema section, which holds
information about each of the tables and each column in the table. Like a
typical Data Dictionary, this information usually ( or should, anyway )
includes a description of each column.

Continue to the next section, :doc:`using`, for basic use patterns.


.. rubric:: Footnotes

.. [#other_formats] Metatab can also be expressed in a line oriented format, which is easier to edit in the terminal and can be included in a Jupyter notebooks

