import unittest
import threading
import time
import warnings

import gi
from tests.integration import run_on_main_loop_and_wait

gi.require_version('Wnck', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Wnck, GLib, Gtk
from subprocess import Popen
from pwm.model import Windows


class ServiceIntegrationTestCase(unittest.TestCase):

	def setUpClass(cls=None) -> None:
		warnings.filterwarnings("ignore", category=DeprecationWarning)
		warnings.filterwarnings("ignore", category=ResourceWarning)
		threading.Thread(target=lambda: Gtk.main()).start()
		time.sleep(2)

	def tearDownClass(cls=None) -> None:
		GLib.idle_add(Gtk.main_quit, priority=GLib.PRIORITY_HIGH)
		time.sleep(1)

	def setUp(self) -> None:
		Popen(['alacritty', '--title', WINDOW_NAME_ONE])
		Popen(['alacritty', '--title', WINDOW_NAME_TWO])
		Popen(['alacritty', '--title', WINDOW_NAME_THREE])
		time.sleep(1)
		Popen(['wmctrl', '-a', WINDOW_NAME_ONE])
		time.sleep(1)
		self.windows = Windows()
		run_on_main_loop_and_wait(self.windows.read_default_screen)

	def tearDown(self) -> None:
		Popen(['wmctrl', '-c', WINDOW_NAME_ONE])
		Popen(['wmctrl', '-c', WINDOW_NAME_TWO])
		Popen(['wmctrl', '-c', WINDOW_NAME_THREE])
		time.sleep(1)

	def test_read_active(self):
		self.assertEqual(WINDOW_NAME_ONE, self.windows.active.get_wnck_window().get_name())

	def test_minimize(self):
		first_active_xid = self.windows.active.get_wnck_window().get_xid()

		GLib.idle_add(self.windows.active.minimize, None, priority=GLib.PRIORITY_HIGH)
		time.sleep(1)

		# removes the active flag even before to read the screen a second time
		self.assertNotEqual(self.windows.active.xid, first_active_xid)

		run_on_main_loop_and_wait(self.windows.read_default_screen)
		self.assertNotEqual(WINDOW_NAME_ONE, self.windows.active.get_wnck_window().get_name())
		self.assertTrue(get_window(WINDOW_NAME_ONE, self.windows).is_minimized())

	def test_only(self):
		GLib.idle_add(self.windows.active.only, None, priority=GLib.PRIORITY_HIGH)
		time.sleep(1)

		run_on_main_loop_and_wait(self.windows.read_default_screen)
		self.assertEqual(WINDOW_NAME_ONE, self.windows.active.get_wnck_window().get_name())
		self.assertTrue(get_window(WINDOW_NAME_TWO, self.windows).is_minimized())
		self.assertTrue(get_window(WINDOW_NAME_THREE, self.windows).is_minimized())


WINDOW_NAME_ONE = 'test-terminal-name-one'
WINDOW_NAME_TWO = 'test-terminal-name-two'
WINDOW_NAME_THREE = 'test-terminal-name-three'


def get_window(name, windows) -> Wnck.Window:
	return next(filter(lambda w: w.get_name() == name, windows.buffers), None)


if __name__ == '__main__':
	unittest.main()
