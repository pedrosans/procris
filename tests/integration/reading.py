import unittest
import threading
import time
import warnings
import pocoy.service as service


class Application(threading.Thread):

	def run(self) -> None:
		service.load()
		service.start()

	def stop(self):
		service.stop()
		self.join()


application = Application()


class ReadingIntegrationTestCase(unittest.TestCase):

	def setUpClass(cls=None) -> None:
		warnings.filterwarnings("ignore", category=DeprecationWarning)
		warnings.filterwarnings("ignore", category=ResourceWarning)
		application.start()
		time.sleep(2)

	def tearDownClass(cls=None) -> None:
		application.stop()

	def test_open_close_window(self):
		service.execute(function=service.reading.show_prompt)
		time.sleep(2)
		self.assertTrue(service.reading.in_command_mode())


if __name__ == '__main__':
	unittest.main()
