import unittest
from unittest.mock import patch
from unittest.mock import MagicMock
from poco.hint import HintStatus
from poco.commands import Command
from poco.commands import CommandInput


class HintTestCase(unittest.TestCase):

	def setUp(self):
		self.controller = MagicMock()
		self.hint = HintStatus(self.controller)
		self.bang_command = MagicMock()
		self.bang_command.name = '!'
		self.bang_command.hint_vim_command_parameter = MagicMock()
		self.bang_command.hint_vim_command_parameter.return_value = ['foobar']
		self.buffer_command = MagicMock()
		self.buffer_command.name = 'buffer'
		Command.get_matching_command = MagicMock()
		Command.hint_vim_command = MagicMock()

	def tearDown(self):
		self.hint.clear_state()

	def test_query_vim_commands(self):
		self.hint.list_hints(CommandInput(text='foo').parse())
		Command.get_matching_command.assert_called_once_with('foo')
		Command.hint_vim_command.assert_called_once_with('foo')

	def test_query_vim_commands_even_if_partial_match(self) :
		Command.get_matching_command.return_value = self.buffer_command

		self.hint.list_hints(CommandInput(text='b').parse())

		Command.get_matching_command.assert_called_once_with('b')
		Command.hint_vim_command.assert_called_once_with('b')

	def test_mount_spaces(self):
		Command.get_matching_command.return_value = self.bang_command

		self.hint.hint(CommandInput(text='  !   foo').parse())
		self.hint.cycle(1)
		self.assertEqual('  !   foobar', self.hint.mount_input())

	def test_dont_query_vim_command_if_bang(self):
		Command.get_matching_command.return_value = self.bang_command

		command_input = CommandInput(text='!foo').parse()
		self.hint.list_hints(command_input)

		Command.get_matching_command.assert_called_once_with('!foo')
		Command.hint_vim_command.assert_not_called()
		self.bang_command.hint_vim_command_parameter.assert_called_once_with(self.controller, command_input)

	def test_bang_vim_command_is_mounted(self):
		Command.get_matching_command.return_value = self.bang_command

		self.hint.hint(CommandInput(text='!foo').parse())
		self.hint.highlight_index = 0
		self.assertEqual(self.hint.mount_input(), '!foobar')

	def test_bang_vim_command_is_mounted_even_if_empty(self):
		Command.get_matching_command.return_value = self.bang_command

		self.hint.hint(CommandInput(text='!').parse())
		self.hint.highlight_index = 0
		self.assertEqual('!foobar', self.hint.mount_input())


if __name__ == '__main__':
	unittest.main()
