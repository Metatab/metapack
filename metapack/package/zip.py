from os import walk
from os.path import join
import zipfile
from metapack.util import slugify

from .core import PackageBuilder


class ZipPackageBuilder(PackageBuilder):
    """A Zip File package"""

    type_code = 'zip'
    type_suffix = '.zip'

    def __init__(self, source_ref=None, package_root=None,  callback=None, env=None):

        super().__init__(source_ref, package_root, callback, env)

        self.package_path, self.cache_path = self.make_package_path(self.package_root, self.package_name)

    @classmethod
    def make_package_path(cls, package_root, package_name):

        cache_path = package_name + cls.type_suffix

        package_path = package_root.join(cache_path)

        return package_path, cache_path

    def save(self, path=None):

        self.check_is_ready()

        root_dir = slugify(self.doc.find_first_value('Root.Name'))

        self.prt("Creating ZIP Package at '{}' from filesystem package at '{}'"
                 .format(self.package_path, self.source_dir))

        self.zf = zipfile.ZipFile(self.package_path.path, 'w', zipfile.ZIP_DEFLATED)

        for root, dirs, files in walk(self.source_dir):
            for f in files:
                source = join(root, f)
                rel = source.replace(self.source_dir,'').strip('/')
                dest = join(root_dir, rel)

                self.zf.write(source,dest)

        self.zf.close()

        return self.package_path