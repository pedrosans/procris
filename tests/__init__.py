import unittest
from unittest import TestSuite
from tests.hint import HintTestCase

test_cases = (HintTestCase,)

def load_tests(loader, tests, pattern):
    suite = TestSuite()
    for test_class in test_cases:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite
