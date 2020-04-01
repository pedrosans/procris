import unittest
import threading
import time
import warnings
import gi
import pwm.model
from tests.integration import run_on_main_loop_and_wait
gi.require_version('Wnck', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Wnck, GLib, Gtk, Gdk
from subprocess import Popen
from pwm.model import Windows, ActiveWindow

windows: Windows = pwm.model.windows
active_window: ActiveWindow = pwm.model.active_window


class ServiceIntegrationTestCase(unittest.TestCase):

	@staticmethod
	def setUpClass(cls=None) -> None:
		warnings.filterwarnings("ignore", category=DeprecationWarning)
		warnings.filterwarnings("ignore", category=ResourceWarning)
		threading.Thread(target=lambda: Gtk.main()).start()
		time.sleep(2)

	def setUp(self) -> None:
		Popen(['alacritty', '--title', WINDOW_NAME_ONE])
		Popen(['alacritty', '--title', WINDOW_NAME_TWO])
		Popen(['alacritty', '--title', WINDOW_NAME_THREE])
		time.sleep(1)
		Popen(['wmctrl', '-a', WINDOW_NAME_ONE]).communicate()
		time.sleep(1)
		run_on_main_loop_and_wait(windows.read_default_screen)
		time.sleep(1)

	def test_read_active(self):
		self.assertEqual(WINDOW_NAME_ONE, active_window.get_wnck_window().get_name())

	def test_minimize(self):
		first_active_xid = active_window.get_wnck_window().get_xid()

		GLib.idle_add(active_window.minimize, None, priority=GLib.PRIORITY_HIGH)
		time.sleep(1)

		# removes the active flag even before to read the screen a second time
		self.assertNotEqual(active_window.xid, first_active_xid)

		run_on_main_loop_and_wait(windows.read_default_screen)
		self.assertNotEqual(WINDOW_NAME_ONE, active_window.get_wnck_window().get_name())
		self.assertTrue(get_window(WINDOW_NAME_ONE).is_minimized())

	def test_only(self):
		GLib.idle_add(active_window.only, None, priority=GLib.PRIORITY_HIGH)
		time.sleep(1)
		Popen(['wmctrl', '-a', 'test'])
		self.assertEqual(WINDOW_NAME_ONE, active_window.get_wnck_window().get_name())
		self.assertNotIn(get_window(WINDOW_NAME_TWO).get_xid(), list(map(lambda x: x.get_xid(), windows.visible)))
		self.assertNotIn(get_window(WINDOW_NAME_THREE).get_xid(), list(map(lambda x: x.get_xid(), windows.visible)))
		# self.assertTrue(get_window(WINDOW_NAME_TWO).is_minimized())

	def tearDown(self) -> None:
		Popen(['wmctrl', '-c', WINDOW_NAME_ONE]).communicate()
		time.sleep(1)
		Popen(['wmctrl', '-c', WINDOW_NAME_TWO]).communicate()
		time.sleep(1)
		Popen(['wmctrl', '-c', WINDOW_NAME_THREE]).communicate()
		time.sleep(1)

	@staticmethod
	def tearDownClass(cls=None) -> None:
		GLib.idle_add(Gtk.main_quit, priority=GLib.PRIORITY_HIGH)
		time.sleep(1)


WINDOW_NAME_ONE = 'test-terminal-name-one'
WINDOW_NAME_TWO = 'test-terminal-name-two'
WINDOW_NAME_THREE = 'test-terminal-name-three'


def get_window(name) -> Wnck.Window:
	return next(filter(lambda w: w.get_name() == name, windows.buffers), None)


if __name__ == '__main__':
	unittest.main()
