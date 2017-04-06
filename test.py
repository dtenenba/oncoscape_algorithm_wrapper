"""Unit Tests. Run without arguments to run all tests."""
# get test data from here:
# https://oncoscape-plsr-mongo-test-tables.s3.amazonaws.com/mongo_bkup.tar.gz

import sys
from unittest import TestCase, TestLoader, TextTestRunner, TestSuite

class WrapperTest(TestCase):
    """Tests of algorithm wrappers"""

    # def setUp(self):
    #     pass
    #
    # def tearDown(self):
    #     pass

    def test_foo(self):
        """Test that True is True"""
        self.assertEqual(True, True)

def main():
    """Define test suite"""
    tests = TestSuite([TestLoader().loadTestsFromTestCase(WrapperTest,)])
    ret = TextTestRunner(verbosity=1).run(TestSuite(tests))
    exitcode = not ret.wasSuccessful()
    # Be sure and exit with the exitcode so that
    # any continuous integration is signaled
    # with the result of the tests:
    sys.exit(exitcode)


if __name__ == '__main__':
    main()
