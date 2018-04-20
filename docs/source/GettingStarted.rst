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

Adding Row Generators
---------------------

If you've examined the :file:`metadata.csv` file in the example package, you'll have noticed that one of the ``Datafile`` terms is not a normal url: 

::

	Section: Resoruces
	Datafile: python:pylib#row_generator

This reference is for a function, written in Python, that will be called to
yield row data. The :code:`pylib` part of the URL is the module name, in this
case it is the module in the packages :file:`pylib` subdirectory, and
:code:`row_generator` is the function name.

See :doc:`GeneratingRows` for more details about row generating functions and programs. 

Building Packages
-----------------

To build data packages from a source package, use the :ref:`mp build program
<mp_build>`.

.. code-block:: bash

	$ mp build # From within the soruce package. 
	
If the current workking directory is not inside the soruce package, you can also reference it explictly, such as with our exmaple package: 

.. code-block:: bash

	$ mp build metatab.org-tutorial
	
Before the build starts, Metapack will ensure that all of the ``Datafile``
terms have associated schemas, and try to autogenerate any that do not. You can
also trigger this process manually with :command:`mp update -s`. You will want to run the schema update manually if you want to add column descriptions to the autogenerated schema, or otherwise alter the schema. 

By default, :command:`mp build` will generate a Filesystem package, which is a
directory like the source package, but with all of the referenced datasets
localized to a :file:`data` directory, and with some additional generated
files. The build packages will be located inside the source package in the
:file:`_packages` directory. Building the example package will result in the
built package at :file:`_packages/metatab.org-tutorial-1`. This package
contains:

::

	├── README.md
	├── data
	│   ├── random-names.csv
	│   ├── random_names.csv
	│   ├── renter_cost-2.csv
	│   ├── renter_cost.csv
	│   ├── renter_cost_excel07.csv
	│   ├── renter_cost_excel97.csv
	│   ├── row_generator.csv
	│   ├── simple-example-altnames.csv
	│   ├── simple-example.csv
	│   ├── unicode-latin1.csv
	│   └── unicode-utf8.csv
	├── datapackage.json
	├── docs
	├── index.html
	└── metadata.csv

The generated files include: 

- :file:`datapackage.json`. A `Frictionless Data Package <http://frictionlessdata.io/docs/data-package/>`_ version of the metadata
- :file:`index.html`. A data package overview and file list. 
- :file:`data`. A directory holding CSV versions of all of the resources.
- :file:`metadata.csv`. An updates Metatab file with references to the local data sets and the date and time the package was created. 

You can also generate other package formats, including CSV, Excel and Zip. The
Zip file format is the same as the Filesystem directory, but is zipped. The
Excel format has only the metadata and data files ( no :file:`index.html` or
other documentation ) but is a convenient single file. The CSV file just
references the file locations of the Filesystem package, and is primarily used
when the filesystem package is stored on the web.

To build all of the other file packages: 

.. code-block:: bash

	$ mp build -cez # -f is optional; the FS package is always built. 

If you change the metadata and try to bulid again, :command:`mp buld` will see
that the package already exists and will not build it. You can force it to
rebuild with the :option:`-F` option, but if you've updated the metadata or the
data, rather than made an error, you should increment the version number in the
`Root.Version` term and build again.

Referencing Metatab Files
-------------------------

Now that some packages are built, it is a good time to mention how Metapack
programs refer to packages. Nearly all of the programs take an optional
:strong:`metatabfile` argument. This argument can be:

- Empty. It will default to :file:`metadata.csv` in the current directory
- A path to a directory, which will be assumed to be a filesystem package with a :file:`metadata.csv` file inside it.
- A path to a file, which will be guessed, by the extension, to be a ZIP, Excel or CSV package. 

For instance, from the directory containing the example source package, all of
the following commands will return the fully-versioned package name,
"metatab.org-tutorial-1"

.. code-block:: bash

  $ mp info metatab.org-tutorial/
  $ mp info metatab.org-tutorial/metadata.csv 
  $ mp info metatab.org-tutorial/_packages/metatab.org-tutorial-1
  $ mp info metatab.org-tutorial/_packages/metatab.org-tutorial-1.csv 
  $ mp info metatab.org-tutorial/_packages/metatab.org-tutorial-1.xlsx 
  $ mp info metatab.org-tutorial/_packages/metatab.org-tutorial-1.zip

As we will see in the next section ( and as you saw when adding URLs to the
package ) a package URL can also have a fragment, which is a string that starts
with '#', appended to the URL. These are used to identify a resource within the
package.

Examining Packages
------------------

There are a few programs you can use to examine packages and view their
resources. The most important is :ref:`mp run program <mp_run>`. The
:command:`mp run` command will run resources, generating the tabular data in a
variety of formats. This is valuable when you are creating a new soruce
package, or when you want to view the contents of a built package.

For instance, when you are working on a source package, :command:`mp run` lets
you see the tabuar data to test configurations. With no arguments, the program will list out the resources in the package. 

.. code-block:: bash

	$ cd metatab.org-tutorial
	$ mp run

	Type      Name                     Url
	--------  -----------------------  ---------------------------------------------------------------------
	Resource  random_names             h.../random-names.csv
	Resource  row_generator            python:pylib#row_generator
	Resource  random-names             ...random-names.csv&encoding=ascii
	Resource  renter_cost              ...renter_cost.csv&encoding=ascii
	Resource  simple-example-altnames  ...simple-example-altnames.csv&encoding=ascii
	Resource  simple-example           ...simple-example.csv&encoding=ascii
	Resource  unicode-latin1           ...unicode-latin1.csv&encoding=latin1
	Resource  unicode-utf8             ...unicode-utf8.csv&encoding=utf8
	Resource  renter_cost_excel07      ...renter_cost_excel07.xlsx;Sheet1&encoding=ascii
	Resource  renter_cost_excel97      ...renter_cost_excel97.xls;Sheet1&encoding=ascii
	Resource  renter_cost-2            ...renter_cost.tsv&encoding=ascii

To run one of thes resources, you add it to the URL of the package as a fragment, appending a '#' and then the resorurce name. If the package is the local directory, the URL is empty, but the shell will interpret the '3' as a comment, so you'll need to escape it. So, to show the random names in the current source package: 

.. code-block:: bash

	$ mp run \#random_names
	
To show the same resource in one of the buld packages: 

.. code-block:: bash

	$ mp run _packages/metatab.org-tutorial-1.zip#random_names

Having the CSV dumped to the terminal isn't very informative for large files, so there are some options that are better suited for development. The :option:`-T` will produce a pretty table of the first 20 rows:

.. code-block:: bash

	$ mp run -T \#random_names 
	┌──────────────────┬───────────────┐
	│ name             │ size          │
	├──────────────────┼───────────────┤
	│ Gabriel Rowland  │ 54.9378140631 │
	├──────────────────┼───────────────┤
	│ Jerry Gay        │ 50.3511258436 │
	├──────────────────┼───────────────┤
	│ Tucker Good      │ 48.6469162116 │
	├──────────────────┼───────────────┤
	│ Noah Fowlers     │ 49.0099728493 │
	...

This view is useful for viewing the rows, but it will truncate columns to the width of the terminal, so if you want to review all of the columns, you can "pivot" the table, transposing rows into columns. 

.. code-block:: bash

	$ mp run -T -p \#renter_cost_excel07
	┌─────────────────────────┬──────────────────┬──────────────────┐
	│ Column Name             │ Row 1            │ Row 2            │
	├─────────────────────────┼──────────────────┼──────────────────┤
	│ id                      │ 1                │ 2                │
	├─────────────────────────┼──────────────────┼──────────────────┤
	│ gvid                    │ 0O0P01           │ 0O0P03           │
	├─────────────────────────┼──────────────────┼──────────────────┤
	│ renter_cost_gt_30       │ 1447             │ 5581             │
	├─────────────────────────┼──────────────────┼──────────────────┤
	│ renter_cost_gt_30_cv    │ 13.6176070904818 │ 6.23593207100335 │
	├─────────────────────────┼──────────────────┼──────────────────┤
	│ owner_cost_gt_30_pct    │ 42.2481751824818 │ 49.280353200883  │
	├─────────────────────────┼──────────────────┼──────────────────┤
	│ owner_cost_gt_30_pct_cv │ 8.27214070699712 │ 4.9333693053569  │
	└─────────────────────────┴──────────────────┴──────────────────┘

This view will show as many rows ( which are now columns ) as the terminal
width can handle, so you may want to restrict the width of the columns with the
:option:`-R` option.

Another useful option for analysis is the sample option :option:`-S`, which
will run the resource and collect the most common values for a single column:

.. code-block:: bash

	$ mp run \#random_names  -S name 
	Value              Count
	---------------  -------
	Gabriel Rowland        1
	Jerry Gay              1
	Tucker Good            1
	Noah Fowlers           1
	Chase Mcmillan         1
	Brody Grimes           1
	Dylan Ferguson         1
	Hashim Franco          1
	Hakeem Bond            1
	Fulton Jordan          1


Using a Package
+++++++++++++++

At this point, the package is functionally complete, and you can check that the
package is usable. First, list the resources with :

.. code-block:: bash

    $ metapack -R metadata.csv
    random-names ...random-names.csv
    renter_cost ...renter_cost.csv
    simple-example-altnames ...simple-example-altnames.csv
    simple-example ...simple-example.csv
    unicode-latin1 ...unicode-latin1.csv
    unicode-utf8 ...unicode-utf8.csv
    renter_cost_excel07 ...renter_cost_excel07.xlsx%3BSheet1
    renter_cost_excel97 ...renter_cost_excel97.xls%3BSheet1
    renter_cost-2 ...renter_cost.tsv

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
