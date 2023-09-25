import unittest

from test_display import TestDisplay
from test_issues import TestIssues
from test_urls import TestUrls


def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TestIssues))
    test_suite.addTest(unittest.makeSuite(TestDisplay))
    test_suite.addTest(unittest.makeSuite(TestUrls))

    return test_suite


if __name__ == '__main__':
    mySuit = suite()
    runner = unittest.TextTestRunner()
    runner.run(mySuit)
