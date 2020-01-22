import unittest

from unittest.mock import MagicMock
from procris.names import PromptInput
import procris.service as service


class ServiceTestCase(unittest.TestCase):

	def setUp(self):
		self.foo = MagicMock()
		service.status_icon = MagicMock()
		service.reading = MagicMock()
		service.windows = MagicMock()

	def test_calls_function(self):
		service.execute(self.foo, PromptInput())
		self.foo.assert_called()

	def test_end_conversation(self):
		service.execute(self.foo, PromptInput())
		service.reading.end.assert_called()

	def test_end_conversation(self):
		service.execute(self.foo, PromptInput())
		service.reading.end.assert_called()


# self.assertEqual('!foobar', self.completion.mount_input())


if __name__ == '__main__':
	unittest.main()
