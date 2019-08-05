import unittest
from unittest.mock import patch
from unittest.mock import MagicMock
from vimwn.hint import HintStatus
from vimwn.command import Command
from vimwn.command import CommandInput


class HintTestCase(unittest.TestCase):

	def setUp(self):
		self.controller = MagicMock()
		self.hint = HintStatus(self.controller)
		self.bang_command = MagicMock()
		self.bang_command.name = '!'
		self.bang_command.hint_vim_command_parameter = MagicMock()
		self.buffer_command = MagicMock()
		self.buffer_command.name = 'buffer'
		Command.get_matching_command = MagicMock()
		Command.hint_vim_command = MagicMock()

	def tearDown(self):
		self.hint.clear_state()

	def test_query_vim_commands(self) :
		self.hint.list_hints(CommandInput(text_input='foo').parse())
		Command.get_matching_command.assert_called_once_with('foo')
		Command.hint_vim_command.assert_called_once_with('foo')

	def test_query_vim_commands_even_if_partial_match(self) :
		Command.get_matching_command.return_value = self.buffer_command

		self.hint.list_hints(CommandInput(text_input='b').parse())

		Command.get_matching_command.assert_called_once_with('b')
		Command.hint_vim_command.assert_called_once_with('b')

	def test_dont_query_vim_command_if_bang(self):
		Command.get_matching_command.return_value = self.bang_command

		command_input = CommandInput(text_input='!foo').parse()
		self.hint.list_hints(command_input)

		Command.get_matching_command.assert_called_once_with('!foo')
		Command.hint_vim_command.assert_not_called()
		self.bang_command.hint_vim_command_parameter.assert_called_once_with(self.controller, command_input)

	def test_bang_vim_command_is_mounted(self) :
		Command.get_matching_command.return_value = self.bang_command
		self.bang_command.hint_vim_command_parameter = MagicMock()
		self.bang_command.hint_vim_command_parameter.return_value = ['foobar']

		self.hint.hint(CommandInput(text_input='!foo').parse())
		self.hint.highlight_index = 0
		self.assertEqual(self.hint.mount_input(), '!foobar')

	def test_bang_vim_command_is_mounted_even_if_empty(self) :
		Command.get_matching_command.return_value = self.bang_command
		self.bang_command.hint_vim_command_parameter = MagicMock()
		self.bang_command.hint_vim_command_parameter.return_value = ['foobar']

		self.hint.hint(CommandInput(text_input='!').parse())
		self.hint.highlight_index = 0
		self.assertEqual('!foobar', self.hint.mount_input())


if __name__ == '__main__':
	unittest.main()
