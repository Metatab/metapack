# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Row generating functions for use in the pylib package of data packages.
"""


# The class used to be here, and still gets referenced here

def copy_reference(resource, doc, env, *args, **kwargs):
    """A row-generating function that yields from a reference. This permits an upstream package to be
    copied and modified by this package, while being formally referenced as a dependency

    The function will generate rows from a reference that has the same name as the resource term
    """

    yield from doc.reference(resource.name)


def copy_reference_group(resource, doc, env, *args, **kwargs):
    """
    A Row generating function that copies all of the references that have the same 'Group' argument as this reference

    This version collects columns names from the set of references and outputs a combined set, matching
    input to outputs by name. Use copy_reference_group_s to skipp all of that and just match by position

    The 'RefArgs' argument is a comma seperated list of arguments from the references that will be prepended to each
    row.

    :param resource:
    :param doc:
    :param env:
    :param args:
    :param kwargs:
    :return:
    """

    all_headers = []

    # Combine all of the headers into a list of tuples by position
    for ref in doc.references():
        if ref.get_value('Group') == resource.get_value('Group'):
            for row in ref.iterrowproxy():
                all_headers.append(list(row.keys()))
                break

    # For each position, add the headers that are not already in the header set.
    # this merges the headers from all datasets, maintaining the order. mostly.

    headers = []
    for e in zip(*all_headers):
        for c in set(e):
            if c not in headers:
                headers.append(c)

    if resource.get_value('RefArgs'):
        ref_args = [e.strip() for e in resource.get_value('RefArgs').strip().split(',')]
    else:
        ref_args = []

    yield ref_args + headers

    for ref in doc.references():
        if ref.get_value('Group') == resource.get_value('Group'):
            ref_args_values = [ref.get_value(e) for e in ref_args]

            for row in ref.iterdict:
                yield ref_args_values + [row.get(c) for c in headers]


def copy_reference_group_s(resource, doc, env, *args, **kwargs):
    """
    A Row generating function that copies all of the references that have the same 'Group' argument as this reference

    Like copy_reference_group but just uses the output schema, and matches columns by position
    The 'RefArgs' argument is a comma seperated list of arguments from the references that will be prepended to each
    row.

    :param resource:
    :param doc:
    :param env:
    :param args:
    :param kwargs:
    :return:
    """

    if resource.get_value('RefArgs'):
        ref_args = [e.strip() for e in resource.get_value('RefArgs').strip().split(',')]
    else:
        ref_args = []

    header = None

    for i, ref in enumerate(doc.references()):

        if ref.get_value('Group') == resource.get_value('Group'):
            ref_args_values = [ref.get_value(e) for e in ref_args]

            for j, row in enumerate(ref):
                if j == 0:
                    if not header:
                        header = ref_args + row
                        yield header
                else:
                    yield ref_args_values + row
