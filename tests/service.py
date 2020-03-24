import unittest

from unittest.mock import MagicMock
from pwm.wm import UserEvent
import pwm.service as service


class ServiceTestCase(unittest.TestCase):

	def setUp(self):
		self.foo = MagicMock()
		service.reading = MagicMock()
		service.windows = MagicMock()
		service.layout = MagicMock()
		service.desktop = MagicMock()

	def test_calls_function(self):
		service.call(self.foo, UserEvent())
		self.foo.assert_called()

	def test_is_pre_processed(self):
		service.call(self.foo, UserEvent())
		service.reading.make_transient.assert_called()

	def test_end_conversation(self):
		service.call(self.foo, UserEvent())
		service.reading.end.assert_called()

	def test_dont_end_long_conversation(self):
		service.reading.is_transient = lambda: False
		service.call(self.foo, UserEvent())
		service.reading.end.assert_not_called()


if __name__ == '__main__':
	unittest.main()
