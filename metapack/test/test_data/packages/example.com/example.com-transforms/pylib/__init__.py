
from math import pi
from geoid.acs import Tract, AcsGeoid
from geoid.census import County, CensusGeoid
from geoid.tiger import Blockgroup, TigerGeoid
from random import randint, random
from datetime import datetime, date, time

def doubleit(v):

    return 2*v
    
    
def row_generator(resource, doc, env, *args, **kwargs):
    """ An example row generator function.

    Reference this function in a Metatab file as the value of a Datafile:

            Datafile: python:pylib#row_generator

    The function must yield rows, with the first being headers, and subsequenct rows being data.

    :param resource: The Datafile term being processed
    :param doc: The Metatab document that contains the term being processed
    :param args: Positional arguments passed to the generator
    :param kwargs: Keyword arguments passed to the generator
    :return:


    The env argument is a dict with these environmental keys:

    * CACHE_DIR
    * RESOURCE_NAME
    * RESOLVED_URL
    * WORKING_DIR
    * METATAB_DOC
    * METATAB_WORKING_DIR
    * METATAB_PACKAGE

    It also contains key/valu pairs for all of the properties of the resource.

    """

    yield 'int float prop ratio str acs_tract census_tract tiger_tract date time datetime'.split()

    for i in range(10):
        
        tract = Tract(6,72,randint(1,10))
        
        yield [
            i,
            float(i)/pi,
            random(),
            float(randint(1,1000))/float(randint(1,1000)),
            'string-'+str(i),
            tract,
            tract.convert(CensusGeoid),
            tract.convert(TigerGeoid),
            date(randint(2000,2020), randint(1,12), randint(1,27)),
            time(randint(0,23), randint(0,59), randint(0,59)),
            datetime(randint(2000,2020), randint(1,12), randint(1,27), randint(0,23), randint(0,59), randint(0,59))
            
            
        ]
        
        