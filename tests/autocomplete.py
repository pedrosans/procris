import unittest

import poco.completions
import poco.names as names
import poco.terminal as terminal
from unittest.mock import MagicMock
from poco.completions import Matches
from poco.names import PromptInput


class AutocompleteTestCase(unittest.TestCase):

	def setUp(self):
		self.reading = MagicMock()
		self.matches = Matches(self.reading)
		self.buffer_command = MagicMock()
		self.buffer_command.name = 'buffer'

		names.completions_for = MagicMock()
		terminal.list_completions = lambda x: ['foobar']

	def tearDown(self):
		self.matches.clean()

	def test_query_vim_commands(self):
		self.matches.search_for(PromptInput(text='foo').parse())
		names.completions_for.assert_called_once_with('foo')

	def test_query_vim_commands_even_if_partial_match(self):
		self.matches.search_for(PromptInput(text='b').parse())
		names.completions_for.assert_called_once_with('b')

	def test_mount_spaces(self):
		self.matches.search_for(PromptInput(text='  !   foo').parse())
		self.matches.cycle(1)
		self.assertEqual('  !   foobar', self.matches.mount_input())

	def test_dont_query_vim_command_if_bang(self):
		command_input = PromptInput(text='!foo').parse()
		poco.completions.completions_for(command_input, self.reading)

		names.completions_for.assert_not_called()

	def test_bang_vim_command_is_mounted(self):
		self.matches.search_for(PromptInput(text='!foo').parse())
		self.matches.index = 0
		self.assertEqual(self.matches.mount_input(), '!foobar')

	def test_bang_vim_command_is_mounted_even_if_empty(self):
		self.matches.search_for(PromptInput(text='!').parse())
		self.matches.index = 0
		self.assertEqual('!foobar', self.matches.mount_input())


if __name__ == '__main__':
	unittest.main()
