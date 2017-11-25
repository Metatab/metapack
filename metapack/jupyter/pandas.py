# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""Support for PANDAS dataframes"""

from pandas import DataFrame, Series



class MetatabSeries(Series):

    _metadata = [ 'metatab_resource', 'name', '_description', '_schema'] # Name is defined in the parent

    @property
    def _constructor(self):
        return MetatabSeries

    @property
    def _constructor_expanddim(self):
        return MetatabDataFrame

    @property
    def column(self):
        """Return the information about the column"""
        raise NotImplementedError()

    @property
    def description(self): # b/c the _metadata elements aren't created until assigned
        try:
            return self._description
        except AttributeError:
            return None

    @description.setter
    def description(self, v):
        self._description = v


class MetatabDataFrame(DataFrame):

    _metadata = [ 'metatab_resource','metatab_errors', '_name',  '_title']

    def __init__(self, data=None, index=None, columns=None, dtype=None, copy=False, metatab_resource=None):

        self.metatab_resource = metatab_resource
        self.metatab_errors = {}

        super(MetatabDataFrame, self).__init__(data, index, columns, dtype, copy)

    @property
    def geo(self):
        """Return a geopandas dataframe"""
        import geopandas as gpd
        from shapely.geometry.polygon import BaseGeometry
        from shapely.wkt import loads

        gdf = gpd.GeoDataFrame(self)

        first = next(gdf.iterrows())[1].geometry

        if isinstance(first, str):
            shapes = [ loads(row['geometry']) for i, row in gdf.iterrows()]

        elif not isinstance(first, BaseGeometry):
            # If we are reading a metatab package, the geometry column's type should be
            # 'geometry' which will give the geometry values class type of
            # rowpipe.valuetype.geo.ShapeValue. However, there are other
            # types of objects that have a 'shape' property.

            shapes = [row['geometry'].shape for i, row in gdf.iterrows()]

        else:
            shapes = gdf['geometry']

        gdf['geometry'] = gpd.GeoSeries(shapes)
        gdf.set_geometry('geometry')
        return gdf

    @property
    def _constructor(self):

        return MetatabDataFrame

    @property
    def _constructor_sliced(self):
        return MetatabSeries

    def _getitem_column(self, key):
        c = super(MetatabDataFrame, self)._getitem_column(key)
        c.metatab_resource = self.metatab_resource
        return c

    def copy(self, deep=True):
        df = super().copy(deep)

        for c in df.columns:
            df[c].__class__ = MetatabSeries



        return df

    @property
    def title(self):  # b/c the _metadata elements aren't created until assigned
        try:
            return self._title
        except AttributeError:
            return ''

    @title.setter
    def title(self, v):
        self._title = v

    @property
    def name(self):  # b/c the _metadata elements aren't created until assigned
        try:
            return self._name
        except AttributeError:
            return ''

    @name.setter
    def name(self, v):
        self._name = v

    @property
    def rows(self):
        """Yield rows like a partition does, with a header first, then rows. """

        yield [self.index.name] + list(self.columns)

        for t in self.itertuples():
            yield list(t)


