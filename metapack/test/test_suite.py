
import unittest

from metapack.test.test_basic import TestBasic
from metapack.test.test_packages import TestPackages
from metapack.test.test_ipy import TestIPython
from metapack.test.test_issues import TestIssues
from metapack.test.test_publish import TestPublish
from metapack.test.test_urls import TestUrls


def suite():

    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TestBasic))
    test_suite.addTest(unittest.makeSuite(TestPackages))
    test_suite.addTest(unittest.makeSuite(TestIPython))
    test_suite.addTest(unittest.makeSuite(TestIssues))
    test_suite.addTest(unittest.makeSuite(TestPublish))
    test_suite.addTest(unittest.makeSuite(TestUrls))

    return test_suite


if __name__ == '__main__':
    mySuit=suite()
    runner=unittest.TextTestRunner()
    runner.run(mySuit)