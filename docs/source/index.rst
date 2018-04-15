
Metapack!
*********

This module provides services for creating references to data files, downloading those files,
and iterating through them as a sequence of rows. For instance, you can define a URL to a CSV file
within a ZIP archive on the web as:

    http://example.com/archive.zip#file.csv

After constructing this URL, the module provides an interface to access the CSV file as rows, downloading
the archive,  caching it, and extracting the inner CSV file.

Additionally, the module provides services for transforming data during iteration, to set default value
cast to specific types, extract components of dates, and many other transformations.

The components of this module include:

* Application Urls: exensible URLs for referencing row data
* Row Generators: Objects that yield rows that are referenced by an Application Url
* Row Transforms: Construct pipelines that transform the value of columns while rows are being iterated
* Value Types: Rich types for column values, allowing sophisticated interactions and transformations with Row Transforms.
* Row Pipes: Composable functions that alter and filter entire rows.


Example
=======

.. code-block:: python

    from rowgenerators import  parse_app_url
    from os.path import exists

    url_str = 'http://public.source.civicknowledge.com/'\
              'example.com/sources/test_data.zip#simple-example.csv'

    url = parse_app_url(url_str) # Parse a string to an Application url

    resource_url = url.get_resource() # Download the .zip file

    target_url = resource_url.get_target() # Extract `file.csv` from the .zip

    assert(target_url.path) # The path to file.csv

    generator = target_url.generator

    rows = list(generator) # Fetch all of the rows. First row is header

    # Iterate rows as dicts
    float_sum = sum(float(row['float']) for row in generator.iter_dict)

    # Iterate with RowProxy objects
    int_sum = sum(int(row.int) for row in generator.iter_rp)

    print(len(rows), float_sum, int_sum)


Install
=======

Use pip:

.. code-block:: bash

    $ pip install rowgenerators


Or, from github:

.. code-block:: bash

    $ pip install git+https://github.com/CivicKnowledge/rowgenerators.git


Contents
========

.. toctree::
    :maxdepth: 2

    Census.rst
    GeneratingRowsWithPrograms.rst
    GeneratingWithFunctions.rst
    GettingStarted.rst
    WranglingPackages.rst




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
