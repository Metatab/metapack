# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""

"""

from metatab.exc import MetatabError


class MetapackError(MetatabError):
    pass


class MetatabFileNotFound(MetatabError):
    pass


class InternalError(MetatabError):
    pass


class PackageError(MetapackError):
    pass


class ResourceError(MetapackError):
    pass


class NoResourceError(ResourceError):
    pass


class NoRowProcessor(ResourceError):
    pass
