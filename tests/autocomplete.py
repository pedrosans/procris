import unittest
import poco.commands as commands
from unittest.mock import MagicMock
from poco.autocomplete import Autocomplete
from poco.commands import CommandInput


class AutocompleteTestCase(unittest.TestCase):

	def setUp(self):
		self.reading = MagicMock()
		self.hint = Autocomplete(self.reading)
		self.buffer_command = MagicMock()
		self.buffer_command.name = 'buffer'

		commands.autocomplete_vim_command = MagicMock()
		commands.autocomplete_parameter = MagicMock()
		commands.autocomplete_parameter.return_value = ['foobar']

	def tearDown(self):
		self.hint.clear_state()

	def test_query_vim_commands(self):
		self.hint.hint(CommandInput(text='foo').parse())
		commands.autocomplete_vim_command.assert_called_once_with('foo')

	def test_query_vim_commands_even_if_partial_match(self):
		self.hint.hint(CommandInput(text='b').parse())
		commands.autocomplete_vim_command.assert_called_once_with('b')

	def test_mount_spaces(self):
		self.hint.hint(CommandInput(text='  !   foo').parse())
		self.hint.cycle(1)
		self.assertEqual('  !   foobar', self.hint.mount_input())

	def test_dont_query_vim_command_if_bang(self):
		command_input = CommandInput(text='!foo').parse()
		commands.autocomplete(command_input, self.reading)

		commands.autocomplete_vim_command.assert_not_called()

	def test_bang_vim_command_is_mounted(self):
		self.hint.hint(CommandInput(text='!foo').parse())
		self.hint.highlight_index = 0
		self.assertEqual(self.hint.mount_input(), '!foobar')

	def test_bang_vim_command_is_mounted_even_if_empty(self):
		self.hint.hint(CommandInput(text='!').parse())
		self.hint.highlight_index = 0
		self.assertEqual('!foobar', self.hint.mount_input())


if __name__ == '__main__':
	unittest.main()
