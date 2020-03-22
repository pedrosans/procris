import unittest
from datetime import datetime
import tests.integration
import gi
import procris.applications as applications
from procris.layout import Layout
from procris.windows import Windows
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, Gdk

applications.load()


def launch_setup_apps():
	applications.launch_name(name='Calculator', desktop=0, timestamp=datetime.now().microsecond)
	applications.launch_name(name='Logs', desktop=1, timestamp=datetime.now().microsecond)


class LayoutIntegrationTestCase(unittest.TestCase):

	def setUp(self) -> None:
		self.windows = Windows()
		self.layout = Layout(windows=self.windows)
		self.calculator = None
		self.logs = None

		tests.integration.run_and_join(launch_setup_apps)

		self.windows.read_screen()
		self.layout.read_display()

		for w in Wnck.Screen.get_default().get_windows():
			if w.get_name() in ['Calculator', 'Logs']:
				print('Opened: {} at {}'.format(w.get_name(), w.get_workspace().get_name()))
				self.calculator = w if w.get_name() == 'Calculator' else self.calculator
				self.logs = w if w.get_name() == 'Logs' else self.logs

	def tearDown(self) -> None:
		for w in Wnck.Screen.get_default().get_windows():
			if w.get_name() in ['Calculator', 'Logs']:
				w.close(datetime.now().microsecond)
		# for w in Wnck.Screen.get_default().get_windows():
		# 	print('{} {}'.format(w.get_xid(), w.get_name()))

	def test_read_window_in_workspace(self):
		self.assertIn(
			self.calculator.get_xid(),
			self.layout.stacks[0],
			'calc: {} should be in: {}'.format(self.calculator.get_xid(), self.layout.stacks[0]))
		self.assertIn(
			self.logs.get_xid(),
			self.layout.stacks[1],
			'logs: {} should be in: {}'.format(self.logs.get_xid(), self.layout.stacks[1]))

	def test_dont_read_window_outside_its_workspace(self):
		self.assertNotIn(
			self.calculator.get_xid(),
			self.layout.stacks[1],
			'calc: {} should not be in: {}'.format(self.calculator.get_xid(), self.layout.stacks[1]))
		self.assertNotIn(
			self.logs.get_xid(),
			self.layout.stacks[0],
			'logs: {} should not be in: {}'.format(self.logs.get_xid(), self.layout.stacks[0]))


if __name__ == '__main__':
	unittest.main()
