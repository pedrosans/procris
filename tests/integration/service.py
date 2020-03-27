import unittest
import threading
import time
import warnings
import pwm.service as service
from subprocess import Popen


class ServiceIntegrationTestCase(unittest.TestCase):

	@staticmethod
	def setUpClass(cls=None) -> None:
		warnings.filterwarnings("ignore", category=DeprecationWarning)
		warnings.filterwarnings("ignore", category=ResourceWarning)
		application.start()
		time.sleep(2)

	def test_open_close_window(self):
		run('edit Calculator', wait=2)
		run('ls')
		self.assertIn('Calculator', service.messages.to_string())
		run('bdelete Calculator', wait=2)
		run('ls')
		self.assertNotIn('Calculator', service.messages.to_string())

	def test_minimize_command(self):
		Popen(['alacritty', '--title', WINDOW_NAME])
		time.sleep(1)
		Popen(['wmctrl', '-a', WINDOW_NAME])
		time.sleep(1)

		run('ls')
		self.assertIn('%a ' + WINDOW_NAME, service.messages.to_string())
		run('quit')
		run('ls')
		self.assertIn(WINDOW_NAME, service.messages.to_string())
		self.assertNotIn('%a ' + WINDOW_NAME, service.messages.to_string())

		run('bdelete ' + WINDOW_NAME, wait=2)

	@staticmethod
	def tearDownClass(cls=None) -> None:
		application.stop()


class Application(threading.Thread):

	def run(self) -> None:
		service.load()
		service.start()

	def stop(self):
		service.stop()
		self.join()


WINDOW_NAME = 'test-window-term-name'
application = Application()


def run(cmd, wait : int = 1):
	service.message(cmd)
	time.sleep(wait)


if __name__ == '__main__':
	unittest.main()
