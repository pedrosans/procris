import unittest
from datetime import datetime
from pwm.windows import Windows
import pwm.terminal as terminal

import tests.integration
terminal.load()

INTEGRATION_TEST_NAME = 'integration-test-name'


def execute_alacritty():
	terminal.execute('alacritty --title {} '.format(INTEGRATION_TEST_NAME))


class TerminalIntegrationTestCase(unittest.TestCase):

	def test_load_commands(self):
		self.assertIn('ls', terminal.NAME_MAP.keys())

	def test_load_aliases(self):
		self.assertIn('ll', terminal.ALIASES_MAP.keys())

	def test_complete_parameter(self):
		completions = terminal.query_command_parameters('tmux k')
		self.assertIn('kill-pane', completions)
		self.assertIn('kill-server', completions)
		self.assertIn('kill-session', completions)
		self.assertIn('kill-window', completions)

	def test_run_command(self):
		t = tests.integration.run(execute_alacritty)
		windows = Windows()
		windows.read_default_screen()
		opened = None
		for w in windows.visible:
			if w.get_name() == INTEGRATION_TEST_NAME:
				opened = w
		self.assertTrue(opened)
		opened.close(datetime.now().microsecond)
		t.join()


if __name__ == '__main__':
	unittest.main()

