# Handling categorical data labels and codes

import pandas as pd
from pandas import isnull
from typing import Dict, List, Tuple, Union

LABELS_SUFFIX = '_labels'  # The name of the reference to the labels, which link codes in a dataset to strings


def isnan(v):
    import math
    try:
        return math.isnan(v)
    except TypeError:
        return False


class Categorical:

    def __init__(self, resource, labels_resource=None):
        """
        @param resource:
        @type resource:
        """

        self.doc = resource.doc
        self.resource = resource

        if labels_resource is None:
            self.labels_resource = self.doc.resource(self.resource.name + LABELS_SUFFIX)
        else:
            self.labels_resource = labels_resource

        if not self.labels_resource:
            raise Exception("No labels resource for {}".format(self.resource.name + LABELS_SUFFIX))

        self.labels_df = self.labels_resource.dataframe()

        self.label_map = None

    @property
    def map(self):
        """Return a dict of codes to labels for each column in the resource"""

        if self.label_map is None:

            label_map = {}
            for gn, g in self.labels_df.groupby('column'):
                label_map[gn] = {r.code: r.category for r in g.itertuples() if not isnull(r.code)}

            self.label_map = label_map

        return self.label_map

    def col_map(self, col_name):
        """Return a dict of codes to labels for a single column"""

        return self.map[col_name]

    def add(self, col_name: str, col_map: Dict):
        """Add a column to the label map
        @param col_name: Name of the column
        @type col_name:
        @param col_map: Map of codes to labels
        @type col_map:
        """

        self.map[col_name] = col_map

    def remove(self, col_name: str):
        """Remove a column from the label map
        @param col_name: Name of the column
        @type col_name:
        """

        del self.map[col_name]


    def _convert_series(self, s: pd.Series):

        col_name = s.name
        cm = self.col_map(col_name)

        if len(cm) == 0:
            return s.copy()

        nu = s.nunique()
        if nu > len(cm):
            return s.copy()

        try:


            # This first conversion will result in a categorical where the
            # categories are the original code.
            sc = s.astype('category')

            # This second conversion will result in a categorical where the
            # categories are the labels.
            new_cats = [cm.get(int(float(ct)), ct) for ct in sc.cat.categories]

            sc = sc.cat.rename_categories(new_cats)

            return sc

        except ValueError as e:
            if 'unique' in str(e):
                import warnings
                from collections import Counter
                warnings.warn("The column '{}' has duplicate labels".format(col_name))

            else:
                raise (e)

        return s

    def to_categorical(self, dfs: Union[pd.Series, pd.DataFrame]) -> Union[pd.Series, pd.DataFrame]:


        if isinstance(dfs, pd.Series):
            return self._convert_series(dfs)
        else:
            d = {}
            for c in dfs.columns:
                if c in self.map:
                    d[c] = self._convert_series(dfs[c])
                else:
                    d[c] = dfs[c].copy()

            return pd.DataFrame(d)
