# Copyright (c) 2019 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""Exported objects from this module are added to the document environment,
which is passed into generators. So, these functions can be used in 'python:'
scheme urls. """


def colmap(resource, doc, env, colmap, *args, **kwargs):
    """
    Run resources with column maps and combine multiple resources

    This function is referenced from a resource or reference url:

    Reference: python:#colmaps&colmap=data_group

    When run, the function will collect all of the other resources or references
    that have a ColMap arg prop of 'data_group' and iterate them after applying
    the column map.

    The function can take two additional arguments: ``prefix`` and ``suffix``,
    which name an arg property of the collected resources that will be
    prepended or appended to the yielded rows. For instance:

    Reference: data/data-1.csv
    Reference.Name: data_ref_1
    Reference.ColMap: data_group
    Reference.Year: 1999
    Reference.Month: 12

    Reference: python:#colmap&colmap=data_group&prefix=Year
    Reference.Name: collected
    Reference.Suffix: Month

    Running the ``collected`` reference will iterate over ``data_ref_1``,
    apply the column map in the file named ``colmap-data_group.csv``, alter the
    iterated header by prepending 'Year' and apppending 'Month', and alter
    the iterated data rows by prepending '1999' and appending '12'


    :param resource:
    :param doc:
    :param env:
    :param colmap:
    :param args:
    :param kwargs:
    :return:
    """

    from itertools import chain
    from rowgenerators.source import ReorderRowGenerator

    headers = None

    prefix = kwargs.get('prefix', resource.get_value('prefix', ''))
    pre_header = prefix.split(',')

    suffix = kwargs.get('suffix', resource.get_value('suffix', ''))
    post_header = suffix.split(',')

    for r in chain(doc.references(), doc.resources()):
        if r.get_value('ColMap') == colmap:

            pre_row = tuple([r.get_value(e) for e in pre_header])
            post_row = tuple([r.get_value(e) for e in post_header])

            rrg = ReorderRowGenerator(r, r.header_map)
            itr = iter(rrg)

            if not headers:
                headers = next(itr)
                yield pre_header + headers + post_header
            else:
                next(itr)

            for row in itr:
                yield pre_row + row + post_row


__all__ = [colmap]
