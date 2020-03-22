import unittest

from unittest.mock import MagicMock
from procris.names import PromptInput
from procris.windows import Windows
import procris.service as service


class WindowsTestCase(unittest.TestCase):

	windows: Windows = Windows()

	def setUp(self):
		print('asdf')

	def test_calls_function(self):
		self.windows.delete(PromptInput(text='bdelete foo').parse())
		# self.foo.assert_called()
		# service.reading.end.assert_not_called()


if __name__ == '__main__':
	unittest.main()
