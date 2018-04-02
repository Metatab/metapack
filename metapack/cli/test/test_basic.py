# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Tests for CLI programs
"""


import unittest

from metapack import open_package
from metapack.cli.test.core import delete_contents

from .core import exec_cmd


class TestCli(unittest.TestCase):

    def setUp(self):
        import tempfile
        import os

        super().setUp()

        self.env_dir = os.getenv('METAPACK_TEST_DIR')

        if not self.env_dir:
            self.temp_dir = tempfile.mkdtemp()
        else:
            self.temp_dir = None
            delete_contents(self.env_dir)

        self.test_dir = self.env_dir or self.temp_dir

        os.chdir(self.test_dir)

    def tearDown(self):

        super().tearDown()

        if self.temp_dir:
            delete_contents(self.temp_dir)

    def test_basic_build(self):
        from os.path import exists, join
        from os import chdir

        out, err, exc = exec_cmd('new -o example.com -d dataset')

        self.assertIsNone(exc)

        pkg_dir = join(self.test_dir, 'example.com-dataset')

        self.assertTrue(exists(pkg_dir))

        with open_package(pkg_dir) as pkg:
            pkg.find_first('Root.Version').value = '1.1.1'
            pkg['Resources'].clean()
            pkg['Resources'].new_term('Datafile',
                                      'http://public.source.civicknowledge.com/example.com/sources/renter_cost.csv',
                                      name='renter_cost')

        chdir(pkg_dir)

        out, err, exc = exec_cmd('build -f')

        self.assertIsNotNone(exc) # Should be SystemExit

        out, err, exc = exec_cmd('pack -s')

        self.assertIsNone(exc,err)

        out, err, exc = exec_cmd('build -f -e -c -z')

        self.assertIsNone(exc)

        self.assertTrue(exists(join(pkg_dir,'_packages/example.com-dataset-1.1.1.zip')))


if __name__ == '__main__':
    unittest.main()
