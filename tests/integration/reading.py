import unittest
import threading
import time
import procris.service as service


class Procris(threading.Thread):

	def run(self) -> None:
		service.load()
		service.start()

	def stop(self):
		service.stop()
		self.join()


class ReadingIntegrationTestCase(unittest.TestCase):

	def setUp(self) -> None:
		import warnings
		warnings.filterwarnings("ignore", category=DeprecationWarning)
		self.procris = Procris()
		self.procris.start()
		time.sleep(2)

	def tearDown(self) -> None:
		self.procris.stop()

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


if __name__ == '__main__':
	unittest.main()
