Generating Rows With Functions
==============================

``Datafile``s can specify URLs that will use a Python function to generate rows.

Here is an example from ``ffiec.gov-cra_disclosure_smb_purchases-2010_2015-1
``

First, the URL must have a ``python`` scheme:

..

    Datafile: python:lib#extract

The ``lib`` component references the module that holds the function to use, and the fragement (``#extract`` ) is the name of the function. The module can be anything. In this case, Metatab will automatically import the :py:module:`lib` module, from the package that holds the source Metatab file ( :file:`metadata.csv` ). To be a module, the :file:`lib` directory must have a :file:`__init__.py`  in it.

The signature for the function is  ``f(resource, doc, *args, **kwargs)``, where ``resource`` is the Metatab resoruce term for the ``Datafile`` term, and  ``doc`` is the Metapack document.
