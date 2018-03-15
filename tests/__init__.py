import unittest
from unittest import TestSuite
from tests.hint import HintTestCase
from tests.terminal import TerminalTestCase

test_cases = (HintTestCase,TerminalTestCase,)

def load_tests(loader, tests, pattern):
    suite = TestSuite()
    for test_class in test_cases:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite
