
Generating Rows
================

Metatab Datafile terms can reference programs and IPython notebooks to generate rows. 

To reference a program, the ``Root.Datafile`` must be a URL with a ``program`` scheme and a relative path. Usually, the file is
placed in a subdirectory named 'scripts' at the same level as the ``metadata.csv`` file. It must be an executable program, and
may be any executable program.

When a data package is created, regardless of the type, a filesystem package is created first, then other types of packages are
created from the filesystem package. This means that the row-generating program is only run once per resource when multiple
packages are created, and also that the program can open the Metatab package being used to run the program to access previously
created resource files.


Generating Rows With Functions
******************************

Datafiles can specify URLs that will use a Python function to generate rows.

First, the URL must have a ``python`` scheme:

..

    Datafile: python:pylib#extract

The ``lib`` component references the module that holds the function to use, and
the fragement (``#extract`` ) is the name of the function. The module can be
anything. In this case, Metatab will automatically import the :py:mod:`lib`
module, from the package that holds the source Metatab file (
:file:`metadata.csv` ). To be a module, the :file:`lib` directory must have a
:file:`__init__.py` in it.

The signature for the function is:

.. py:function:: f(resource, doc, env, *args, **kwargs)

	Yield rows for a ``Root.Datafile``
	
	:param Term resource: The resource object for the Root.Datafile that is being built. 
	:param MetapackDoc doc: The current Metapack document. 
	:param dict env: a dictionary of environmental variables. 
	:return: Yields tuple or list rows. 

where ``resource`` is the Metatab resource term for the ``Datafile`` term, and ``doc`` is the Metapack document.

Common Patterns
---------------

One of the most common reasons to create a row generating function is to link multiple datasets together. Frequently this
involves iterating over another Metapack package, constructing maps from other datasets, and linking them together. 






Generating Rows With Programs
*****************************

Generally, it is much easier to implement a python function as a row generator than a program, but programs can also be useful. The program can receive information from Metatab through program options and environmental variables, and must print CSV
formatted lines to std out.

There are two broad sources for inputs to the program. The first is are several values that are passed into the program
regardless of the configuration of the ``Root.DataFile`` term. The second are the properties of the ``Root.DataFile`` terms.

The inputs for all programs are: 

- :envvar:`METATAB_DOC`: An env var that holds the URL for the Metatab document being processed
- :envvar:`METATAB_PACKAGE`: An env var that holds the metatab document's package URL. ( Which is usually the same as the document URL )
- :envvar:`METATAB_WORKING_DIR`: An env var that holds the path to the directory holding the metatab file. 
- :envvar:`PROPERTIES`: An env var with holds a JSON encoded dict with the three previous env values, along with the ``properties`` dict for the ``Root.DataFile`` term. 

Additionally, the program receives the ``Root.DataFile`` properties in these forms:

- Properties that have names that are all uppercased are assigned to env variables. 
- Properties that have names that begin with '-' are assigned to program options.

Since the program must output CSV formatted lines, a CSV writer can be constructed on ``sys.stdout``:

.. code-block:: python 

     import sys
     import csv
     
     w = csv.writer(sys.stdout)
     
     w.writerow(...)
     
     
If the program generates logging or warnings, they must be printed to ``sys.stderr``

.. code-block:: python 

     import sys
     
     print("ERROR!", file=sys.stderr)

It is very common for a program to open the Metatab document that is being used to run the row generator. You can use the :envvar:`METATAB_DOC` environmental variable to get a reference to the current package. 

.. code-block:: python 

    import metatab as mt
    doc = mt.open_package(environ['METATAB_DOC'])


     
     