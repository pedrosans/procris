import unittest
import threading
import time
import warnings
import gi
gi.require_version('Wnck', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Wnck, GLib, Gtk
from datetime import datetime
from subprocess import Popen
from procris.windows import Windows

warnings.filterwarnings("ignore", category=DeprecationWarning)

WINDOW_NAME = 'test-terminal-name'


def term_window() -> Wnck.Window:
	Wnck.Screen.get_default().force_update()
	for w in Wnck.Screen.get_default().get_windows():
		if w.get_name() == WINDOW_NAME:
			return w
	return None


def minimize_active():
	GLib.idle_add(minimize_active, priority=GLib.PRIORITY_HIGH)


class ServiceIntegrationTestCase(unittest.TestCase):

	def setUp(self) -> None:
		Popen(['alacritty', '--title', WINDOW_NAME])
		threading.Thread(target=lambda: Gtk.main()).start()
		time.sleep(2)

	def tearDown(self) -> None:
		term_window().close(datetime.now().microsecond)
		GLib.idle_add(Gtk.main_quit, priority=GLib.PRIORITY_HIGH)

	def test_minimize(self):
		windows = Windows()
		GLib.idle_add(windows.read_screen, priority=GLib.PRIORITY_HIGH)
		time.sleep(1)

		self.assertEqual(WINDOW_NAME, windows.active.get_wnck_window().get_name())

		windows.active.minimize(None)
		self.assertIsNone(windows.active.get_wnck_window())
		time.sleep(1)

		GLib.idle_add(windows.read_screen, priority=GLib.PRIORITY_HIGH)
		time.sleep(1)

		self.assertNotEqual(WINDOW_NAME, windows.active.get_wnck_window().get_name())
		self.assertTrue(term_window().is_minimized())


if __name__ == '__main__':
	unittest.main()
