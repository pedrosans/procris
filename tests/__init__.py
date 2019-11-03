import unittest
import tests.names
import tests.terminal
import tests.assistant
import tests.layout

test_case_classes = (tests.names.CommandInputTestCase,
                     tests.terminal.TerminalTestCase,
                     tests.assistant.AssistantTestCase,
                     tests.layout.LayoutTestCase
                     )


def load_tests(loader, test_suite_array, pattern):
    suite = unittest.TestSuite()
    for test_class in test_case_classes:
        unit_tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(unit_tests)
    return suite
