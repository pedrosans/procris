import unittest
import tests.integration
import pocoy.applications as applications
import pocoy.model as model
import gi
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, Gdk
from datetime import datetime

applications.load()


def launch_setup_apps():
	calculator = applications.info_for('Calculator')
	logs = applications.info_for('Logs')
	applications.launch_app(app_info=calculator, desktop=0, timestamp=datetime.now().microsecond)
	applications.launch_app(app_info=logs, desktop=1, timestamp=datetime.now().microsecond)


class LayoutIntegrationTestCase(unittest.TestCase):

	def setUp(self) -> None:
		self.calculator = None
		self.logs = None

		tests.integration.run_and_join(launch_setup_apps)

		screen = Wnck.Screen.get_default()

		model.windows.read_default_screen()

		for w in screen.get_windows():
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
		workspace_1 = model.monitors.primary_monitors[0].stack
		workspace_2 = model.monitors.primary_monitors[1].stack
		self.assertIn(
			self.calculator.get_xid(),
			workspace_1,
			'calc: {} should be in: {}'.format(self.calculator.get_xid(), workspace_1))
		self.assertIn(
			self.logs.get_xid(),
			workspace_2,
			'logs: {} should be in: {}'.format(self.logs.get_xid(), workspace_2))

	def test_dont_read_window_outside_its_workspace(self):
		workspace_1 = model.monitors.primary_monitors[0].stack
		workspace_2 = model.monitors.primary_monitors[1].stack
		self.assertNotIn(
			self.calculator.get_xid(),
			workspace_2,
			'calc: {} should not be in: {}'.format(self.calculator.get_xid(), workspace_2))
		self.assertNotIn(
			self.logs.get_xid(),
			workspace_1,
			'logs: {} should not be in: {}'.format(self.logs.get_xid(), workspace_1))


if __name__ == '__main__':
	unittest.main()
