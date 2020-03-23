import unittest

from unittest.mock import MagicMock
from procris.names import CommandLine
import procris.service as service


class ServiceTestCase(unittest.TestCase):

	def setUp(self):
		self.foo = MagicMock()
		service.status_icon = MagicMock()
		service.reading = MagicMock()
		service.windows = MagicMock()
		service.layout = MagicMock()

	def test_calls_function(self):
		service._execute(self.foo, CommandLine())
		self.foo.assert_called()

	def test_is_pre_processed(self):
		service._execute(self.foo, CommandLine())
		service.reading.make_transient.assert_called()

	def test_end_conversation(self):
		service._execute(self.foo, CommandLine())
		service.reading.end.assert_called()

	def test_dont_end_long_conversation(self):
		service.reading.is_transient = lambda: False
		service._execute(self.foo, CommandLine())
		service.reading.end.assert_not_called()


if __name__ == '__main__':
	unittest.main()
