import unittest
import threading
import time
import warnings
import pwm.service as service
from gi.repository import Wnck, Gtk, GLib, Gdk
from subprocess import Popen

WINDOW_NAME = 'test-window-term-name'


class Application(threading.Thread):

	def run(self) -> None:
		service.load()
		service.start()

	def stop(self):
		service.stop()
		self.join()


application = Application()


class ServiceIntegrationTestCase(unittest.TestCase):

	def setUpClass(cls=None) -> None:
		warnings.filterwarnings("ignore", category=DeprecationWarning)
		warnings.filterwarnings("ignore", category=ResourceWarning)
		application.start()
		time.sleep(2)

	def tearDownClass(cls=None) -> None:
		application.stop()

	def test_open_close_window(self):
		service.message('edit Calculator')
		time.sleep(2)

		service.message('ls')
		time.sleep(1)
		self.assertIn('Calculator', service.messages.to_string())

		service.message('bdelete Calculator')
		time.sleep(2)

		service.message('ls')
		time.sleep(1)
		self.assertNotIn('Calculator', service.messages.to_string())

	def test_minimize(self):
		Popen(['alacritty', '--title', WINDOW_NAME])
		time.sleep(2)

		service.message('ls')
		time.sleep(1)
		self.assertIn('%a ' + WINDOW_NAME, service.messages.to_string())

		service.message('quit')
		time.sleep(1)

		service.message('ls')
		time.sleep(1)
		self.assertIn(WINDOW_NAME, service.messages.to_string())
		self.assertNotIn('%a ' + WINDOW_NAME, service.messages.to_string())

		service.message('bdelete ' + WINDOW_NAME)
		time.sleep(2)


if __name__ == '__main__':
	unittest.main()
