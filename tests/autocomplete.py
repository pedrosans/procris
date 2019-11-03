import unittest

import poco.autocomplete
import poco.names as names
from unittest.mock import MagicMock
from poco.autocomplete import Matches
from poco.names import PromptInput


class AutocompleteTestCase(unittest.TestCase):

	def setUp(self):
		self.reading = MagicMock()
		self.autocomplete = Matches(self.reading)
		self.buffer_command = MagicMock()
		self.buffer_command.name = 'buffer'

		names.autocomplete_vim_command = MagicMock()
		poco.autocomplete.autocomplete_parameter = MagicMock()
		poco.autocomplete.autocomplete_parameter.return_value = ['foobar']

	def tearDown(self):
		self.autocomplete.clear_state()

	def test_query_vim_commands(self):
		self.autocomplete.search_for(PromptInput(text='foo').parse())
		names.autocomplete_vim_command.assert_called_once_with('foo')

	def test_query_vim_commands_even_if_partial_match(self):
		self.autocomplete.search_for(PromptInput(text='b').parse())
		names.autocomplete_vim_command.assert_called_once_with('b')

	def test_mount_spaces(self):
		self.autocomplete.search_for(PromptInput(text='  !   foo').parse())
		self.autocomplete.cycle(1)
		self.assertEqual('  !   foobar', self.autocomplete.mount_input())

	def test_dont_query_vim_command_if_bang(self):
		command_input = PromptInput(text='!foo').parse()
		poco.autocomplete.autocomplete(command_input, self.reading)

		names.autocomplete_vim_command.assert_not_called()

	def test_bang_vim_command_is_mounted(self):
		self.autocomplete.search_for(PromptInput(text='!foo').parse())
		self.autocomplete.highlight_index = 0
		self.assertEqual(self.autocomplete.mount_input(), '!foobar')

	def test_bang_vim_command_is_mounted_even_if_empty(self):
		self.autocomplete.search_for(PromptInput(text='!').parse())
		self.autocomplete.highlight_index = 0
		self.assertEqual('!foobar', self.autocomplete.mount_input())


if __name__ == '__main__':
	unittest.main()
