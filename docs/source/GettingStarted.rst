Getting Started
===============

Install
-------

Install the Metapack package from PiPy with:

.. code-block:: bash

    $ pip install metapack

For development, you'll probably want the development package, with sub-mdules for related repos: 

.. code-block:: bash

	$ git clone --recursive https://github.com/Metatab/metapack-dev.git
	$ cd metapack-dev
	$ bin/init-develop.sh

Creating Packages with Metapack
-------------------------------

Metapack data packages consists of metadata and data, linked together in an
Excel file, Zip File, or as files in a directory. These package files are
created by the :command:`mp build` program, taking a source package as input.
A Metapack source package is very similar to a output package: the primary
difference is that a source package references datasets with URLs to remote
resources. Building a package loads those resources into the load file. More
generally, a source package decribes how to run a data processing pipeline, and
the output package has just the outputs of these data processing steps.

So, what we're going to do is create a directory-based source package, then
build the soruce package to create an Excel File, a Zip File and another
directory package.

Creating a new package
----------------------

To create a new package, use the :ref:`mp new program <mp_new>` . 

.. code-block:: bash

	$ mp new -o metatab.org -d tutorial -L -E -T "Quickstart Example Package" 
	
This command will create a directory named :file:`metatab.org-tutorial`,
which will contain a :file:`metadata.csv` file, the Metatab-formated metadata
file for the package. 
	
The :strong:`origin` and :strong:`dataset` options are required. These
options, along with :strong:`time`, :strong:`space`, :strong:`grain`,
:strong:`variant`, and :strong:`revision` are used to build the name of the
data package, which is also used in the name of the directory for the package.
The origin should usually be a second level internet domain, such as
'metatab.org'.

The :strong:`-E` option will generate example data, and the :strong:`-L` option will create a :file:`pylib` directory that hold some python code for generating rows. 

If you need to change the name of the package later, you can edit the
identifiying terms in the metadata file. After setting the ``Dataset``,
``Origin``, ``Version``, ``Time`` or ``Space`` and saving the file, , run
``metapack -u`` to update ``Name``:

.. code-block:: bash

	$ cd metatab.org-tutorial
	$ mp update -n
	Changed Name
	Name is:  metatab.org-tutorial-2018-1

Otherwise, you will usually still want to edit the file to set the `Title` and
`Description` terms.

Adding Data References
----------------------

Since this is a data package, it is important to have references to data. The
package we are creating here is a filesystem package, and will usually
reference the URLs to data on the web. Later, we will generate other packages,
such as ZIP or Excel files, and the data will be downloaded and included
directly in the package. We define the paths or URLs to data files with the
``Datafile`` term in the ``Resources`` section. 

For the ``Datafile`` term, you can add entries directly, but it is easier to
use the :command:`mp url` program to add them. :command:`mp url` program will
inspect the file for you, finding internal files in ZIP files and creating the
correct URLs for Excel files.

If you have made changes to the ``metadata.csv`` file, save it, then run:

.. code-block:: bash

    $ mp url -a  http://public.source.civicknowledge.com/example.com/sources/test_data.zip

The ``test_data.zip`` file is a test file with many types of tabular datafiles
within it. The :command:`mp url` command will download it, open it, find all of
the metadata files int it, and add URLs to the metatab. If any of the files in
the zip file are Excel format, it will also create URLs for each of the tabs.

This file is large and may take awhile. If you need a smaller file, try:
http://public.source.civicknowledge.com/example.com/sources/renter_cost.csv


Now reload the file. The Resource section should have 9 ``Datafile`` entries,
all of them with fragments. The fragments will be URL encoded, so are a bit
hard to read. %2F is a '/' and %3B is a ';'. The :command:`mp url` program will
also add a name, and try to figure out on which row the data starts and which
lines are for headers.

Note that the ``unicode-latin1`` and ``unicode-utf8`` files do not have values
for HeaderLines and Startline. This is because the row intuiting process failed
to categorize the lines, because all of them are mostly strings. In these
cases, download the file and examine it. For these two files, you can enter '0'
for ``HeaderLines`` and '1' for ``StartLine``, or leave those values empty and Metatab will use 0 and 1 

If you enter the ``Datafile`` terms manually, you should enter the URL for the
datafile, ( in the cell below "Resources" ) and the ``Name`` value. If the URL
to the resource is a zip file or an Excel file, you can use a URL fragment to
indicate the inner filename. For Excel files, the fragment is either the name
of the tab in the file, or the number of the tab. ( The first number is 0 ). If
the resource is a zip file that holds an Excel file, the fragment can have both
the internal file name and the tab number, separated by a semicolon ';' For
instance:

- http://public.source.civicknowledge.com/example.com/sources/test_data.zip#simple-example.csv
- http://example.com/renter_cost_excel07.xlsx#2
- http://example.com/test_data.zip#renter_cost_excel07.xlsx;B2

If you don't specify a tab name for an Excel file, the first will be used.

There are also URL forms for Google spreadsheet, S3 files and Socrata.

To test manually added URLs, use the ``rowgen`` program, which will download
and cache the URL resource, then try to interpret it as a CSV or Excel file.

.. code-block:: bash

    $ rowgen http://public.source.civicknowledge.com/example.com/sources/test_data.zip#renter_cost_excel07.xlsx

    ------------------------  ------  ----------  ----------------  ----------------  -----------------
    Renter Costs
    This is a header comment

                                      renter                        owner
    id                        gvid    cost_gt_30  cost_gt_30_cv     cost_gt_30_pct    cost_gt_30_pct_cv
    1.0                       0O0P01  1447.0      13.6176070904818  42.2481751824818  8.27214070699712
    2.0                       0O0P03  5581.0      6.23593207100335  49.280353200883   4.9333693053569
    3.0                       0O0P05  525.0       17.6481586482953  45.2196382428941  13.2887199930555
    4.0                       0O0P07  352.0       28.0619645779719  47.4393530997305  17.3833286873892

Or just download the file and look at it. In this case, for both
`unicode-latin1` and `unicode-utf8` you can see that the headers are on line 0
and the data starts on line 1 so enter those values into the `metadata.csv`
file. Setting the ``StartLine`` and ``HeaderLines`` values is critical for
properly generating schemas.

The URLs used in the resources, and the generators that produce row data from
the data specified by the URLs are implemented in the `rowgenerators module
<https://github.com/Metatab/rowgenerators>`_ . Refer to the `rowgenerators
documentation <http://row-generators.readthedocs.io/en/latest/>`_ for more
details about the URL structure.

Building Packages
+++++++++++++++++

To build data packages from a source package, use the :ref:`mp build program
<mp_build>`.

.. code-block:: bash

	$ mp build
	
Before the build starts, Metapack will ensure that all of the ``Datafile``
terms have associated schemas, and try to autogenerate any that do not. You can
also trigger this process manually with :command:`mp update -s`.

Using a Package
+++++++++++++++

At this point, the package is functionally complete, and you can check that the
package is usable. First, list the resources with :

.. code-block:: bash

    $ metapack -R metadata.csv
    random-names http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fcsv%2Frandom-names.csv
    renter_cost http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fcsv%2Frenter_cost.csv
    simple-example-altnames http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fcsv%2Fsimple-example-altnames.csv
    simple-example http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fcsv%2Fsimple-example.csv
    unicode-latin1 http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fcsv%2Funicode-latin1.csv
    unicode-utf8 http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fcsv%2Funicode-utf8.csv
    renter_cost_excel07 http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fexcel%2Frenter_cost_excel07.xlsx%3BSheet1
    renter_cost_excel97 http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fexcel%2Frenter_cost_excel97.xls%3BSheet1
    renter_cost-2 http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Ftab%2Frenter_cost.tsv

You can dump one of the resources as a CSV by running the same command with the
resource name as a fragment to the name of the metatab file:

.. code-block:: bash

    $ metapack -R metadata.csv#simple-example

or:

.. code-block:: bash

    $ metapack -R "#simple-example"

You can also read the resources from a Python program, with an easy way to
convert a resource to a Pandas DataFrame.

.. code-block:: python 

    import metatab

    doc = metatab.open_package('.')  # Will look for 'metadata.csv'

    print(type(doc))

    for r in doc.resources():
        print(r.name, r.url)
    
    r = doc.first_resource('renter_cost')

    # Dump the row
    for row in r:
        print row


    # Or, turn it into a pandas dataframe
    # ( After installing pandas ) 
    
    df = doc.first_resource('renter_cost').dataframe()

For a more complete example, see `this Jupyter notebook example
<https://github.com/CivicKnowledge/metatab/blob/master/examples/Access%20Example
s.ipynb>`_

Making Other Package Formats
++++++++++++++++++++++++++++

The tutorial above is actually creating a data package in a directory. There are several other forms of packages that Metapack can create including Excel, ZIP and S3.


.. code-block:: bash

    $ metapack -e # Make an Excel package, example.com-example_data_package-2017-us-1.xlsx
    $ metapack -z # Make a ZIP package, example.com-example_data_package-2017-us-1.zip

The Excel package, ``example-package.xlsx`` will have the Metatab metadata from
metata.csv in the ``Meta`` tab, and will have one tab per resource from the
Resources section. The ZIP package ``example-package.zip`` will have all of the
resources in the ``data`` directory and will also include the metadata in
`Tabular Data Package
<http://specs.frictionlessdata.io/tabular-data-package/>`_ format in the
``datapackage.json`` file. You can interate over the resources in these
packages too:

.. code-block:: bash

    $ metapack -R example.com-example_data_package-2017-us-1.zip#simple-example
    $ metapack -R example.com-example_data_package-2017-us-1.xlsx#simple-example

The ``metapack -R`` also works with URLs:

.. code-block:: bash

    $ metapack -R http://devel.metatab.org/excel/example.com-example_data_package-2017-us-1.xlsx#simple-example
    $ metapack -R http://devel.metatab.org/excel/example.com-example_data_package-2017-us-1.zip#simple-example

And, you can access the packages in Python:


.. code-block:: python 

    import metatab

    doc = metatab.open_package('example-package.zip') 
    # Or
    doc = metatab.open_package('example-package.xlsx') 
    
Note that the data files in a derived package may be different that the ones in
the source directory package. The derived data files will always have a header
on the first line and data starting on the second line. The header will be
taken from the data file's schema, using the ``Table.Column`` term value as the
header name, or the ``AltName`` property, if it is defined. The names are
always "slugified" to remove characters other than '-', '_' and '.' and will
always be lowercase, with initial numbers removed.

If the ``Datafile`` term has a ``StartLine`` property, the values will be used
in generating the data in derived packages to select the first line for
yielding data rows. ( The ``HeaderLines`` property is used to build the schema,
from which the header line is generated. )
