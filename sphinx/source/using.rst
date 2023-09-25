Using Metapack Packages
=======================

This section will use and example package, which is available online in three forms at: 

* http://library.metatab.org/example.com-full-2017-us-1.zip
* http://library.metatab.org./example.com-full-2017-us-1.xlsx
* http://library.metatab.org/example.com-full-2017-us-1.csv

Additionally, the section will refer to the filesystem package, which is just the ZIP package unpacked: 

.. code-block:: bash

	$ wget http://library.metatab.org/example.com-full-2017-us-1.zip
	$ unzip example.com-full-2017-us-1.zip 


Command Line Operations
-----------------------

.. note::
	
	See :doc:`the commands page <commands>` for detailed documentation of the
	commands in the base metapack package.

Command line programs that operate on packages take a URL to a local or remote
package, with a URL fragment to refer to a resource.

Metapack has a single CLI entrypoint, :program:`mp`, to run commands. The
entrypoint is exensible, so other python modules can install additinoal
commands. You can see the commands that are avilable, and their version
numebrs, with :program:`mp config`

.. code-block:: bash

	$ mp config 
	
	Package        Version
	-------------  ---------
	metapack       0.9.1
	metatab        0.7.16
	metatabdecl    1.6
	rowgenerators  0.8.31
	publicdata     0.3.8
	tableintuit    0.1.5

	Subcommand    Package
	------------  -------------------------------------
	config        metapack 0.9.1
	doc           metapack 0.9.1
	index         metapack 0.9.1
	info          metapack 0.9.1
	open          metapack 0.9.1
	run           metapack 0.9.1
	search        metapack 0.9.1
	build         metapack-build 0.0.2
	edit          metapack-build 0.0.2
	new           metapack-build 0.0.2
	s3            metapack-build 0.0.2
	stats         metapack-build 0.0.2
	update        metapack-build 0.0.2
	url           metapack-build 0.0.2
	wp            metapack-wp 0.0.6.post0.dev1+g4c7a6bc
	
Commands which operate on packages take a URL as the last argument. There are a
few common forms for these URLs:

.. list-table::
   :widths: 20 75
   
   * - Full url
     - http://library.metatab.org/example.com-full-2017-us-1.zip
   * - Local file
     - example.com-full-2017-us-1.zip
   * - Metatab.csv in current directory
     - . or ''
	  
Commands that operate on resources use URLs that have a fragment and the name of the resource:

.. list-table::
   :widths: 20 75
   
   * - Full url
     - http://library.metatab.org/example.com-full-2017-us-1.zip#renter_cost
   * - Local file
     - example.com-full-2017-us-1.zip#renter_cost
   * - Metatab.csv in current directory
     - .#renter_cost
	  
For instance, to list the resources in a package: 

.. code-block:: bash
    
    # Remote Package
    $ mp info http://library.metatab.org/example.com-full-2017-us-1.zip
    
    # Local filesystem package
    $ cd example.com-full-2017-us-1
    $ mp info -r

To display the resources: 


.. code-block:: bash
    
    # Remote Package
    $ mp info http://library.metatab.org/example.com-full-2017-us-1.zip#renter_cost
    
    # Local filesystem package
    $ cd example.com-full-2017-us-1
    $ mp info -r .#renter_cost

Note that in a filesystem package, the reference to the package ('.') can be
omitted when referencing the package, but is included when referencing a
resource. This is because the shell considers strings that start with '#' to be
comments. To avoid this, the '#' can also be escaped, :program:`mp info -r
\\#renter_cost`, but this form is not commonly used.

Opening Packages
++++++++++++++++

Opening packages with the CLI primarily means opening the CSV files included in
the package, which you can do from direct reference. Just open the metadata
file and read the resource URLs. However, you can also use the :program:`mp
run` program to dump the data in a variety of formats. The URL requires a
resource fragment, but if you don't include it, :program:`mp run` will show the
resources.

.. code-block:: bash

    $ mp run example.com-full-2017-us-1.zip 
    Select a resource to run:
    Type       Ref                       Url
    ---------  ------------------------  --------------------------------------
    Resource   #renter_cost              data/renter_cost.csv
    Resource   #simple-example-altnames  data/simple-example-altnames.csv
    Resource   #simple-example           data/simple-example.csv
    ...
    
    $ mp run example.com-full-2017-us-1.zip#renter_cost
    id,col2,renter_cost_gt_30,renter_cost_gt_30_cv, ...
    1,,1447,13.6176070905,42.2481751825,8.272140707
    2,,5581,6.235932071,49.2803532009,4.9333693054
    3,,525,17.6481586483,45.2196382429,13.2887199931

If you just want to list all of the resources and references, use :program:`mp info -r`.


Using Packages In Python
------------------------

Using packages in Python involves opening the package, and then acessing a resource. 

.. code-block:: python 

    import metapack as mp
    
    # Open the package. 
    pkg = mp.open_package('http://library.metatab.org/example.com-full-2017-us-1.csv')   
    print(pkg) # display documentation
    
    # Get a handle on a resource
    r = pkg.resource('renter_cost')  

    # Get a dataframe for the resource
    df = r.dataframe()


