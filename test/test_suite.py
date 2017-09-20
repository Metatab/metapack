
import unittest
from test_basic import TestBasic
from test_packages import TestPackages


def suite():

    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TestBasic))
    test_suite.addTest(unittest.makeSuite(TestPackages))

    return test_suite


if __name__ == '__main__':
    mySuit=suite()
    runner=unittest.TextTestRunner()
    runner.run(mySuit)