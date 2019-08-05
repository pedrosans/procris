import unittest
import tests.command
import tests.terminal
import tests.hint

test_case_classes = (tests.command.CommandInputTestCase,
                     tests.terminal.TerminalTestCase,
                     tests.hint.HintTestCase)


def load_tests(loader, test_suite_array, pattern):
    suite = unittest.TestSuite()
    for test_class in test_case_classes:
        unit_tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(unit_tests)
    return suite
