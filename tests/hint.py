import unittest
from unittest.mock import patch
from unittest.mock import MagicMock
from vimwn.hint import HintStatus
from vimwn.command import Command

class HintTestCase(unittest.TestCase):

	def setUp(self):
		self.controller = MagicMock()
		self.status_line = HintStatus(self.controller)
		self.bang_command = MagicMock()
		self.bang_command.name = '!'
		self.bang_command.hint_vim_command_parameter = MagicMock()
		self.buffer_command = MagicMock()
		self.buffer_command.name = 'buffer'
		Command.get_matching_command = MagicMock()
		Command.hint_vim_command = MagicMock()

	def tearDown(self):
		self.status_line.clear_state()

	def test_parse_vim_command(self):
		self.status_line.parse_input('buffers')
		self.assertEqual(self.status_line.vim_command, 'buffers')
		self.assertTrue(''	== self.status_line.vim_command_spacer
							== self.status_line.vim_command_parameter
							== self.status_line.terminal_command
							== self.status_line.terminal_command_spacer
							== self.status_line.terminal_command_parameter)

	def test_parse_vim_command_with_parameter(self):
		self.status_line.parse_input('buffer  term')
		self.assertEqual(self.status_line.vim_command, 'buffer')
		self.assertEqual(self.status_line.vim_command_spacer, '  ')
		self.assertEqual(self.status_line.vim_command_parameter, 'term')
		self.assertTrue(''	== self.status_line.terminal_command
							== self.status_line.terminal_command_spacer
							== self.status_line.terminal_command_parameter)

	def test_parse_terminal_command_with_parameter(self):
		self.status_line.parse_input('!  git   add')
		self.assertEqual(self.status_line.vim_command, '!')
		self.assertEqual(self.status_line.vim_command_spacer, '  ')
		self.assertEqual(self.status_line.vim_command_parameter, 'git   add')
		self.assertEqual(self.status_line.terminal_command, 'git')
		self.assertEqual(self.status_line.terminal_command_spacer, '   ')
		self.assertEqual(self.status_line.terminal_command_parameter, 'add')

	def test_query_vim_commands(self) :
		self.status_line.parse_input('foo')
		self.status_line.list_hints('foo')
		Command.get_matching_command.assert_called_once_with('foo')
		Command.hint_vim_command.assert_called_once_with('foo')

	def test_query_vim_commands_even_if_partial_match(self) :
		Command.get_matching_command.return_value = self.buffer_command

		self.status_line.parse_input('b')
		self.status_line.list_hints('b')

		Command.get_matching_command.assert_called_once_with('b')
		Command.hint_vim_command.assert_called_once_with('b')

	def test_dont_query_vim_command_if_bang(self) :
		Command.get_matching_command.return_value = self.bang_command

		self.status_line.parse_input('!foo')
		self.status_line.list_hints('!foo')

		Command.get_matching_command.assert_called_once_with('!foo')
		Command.hint_vim_command.assert_not_called()

	def test_dont_query_vim_command_parameters_if_bang(self) :
		Command.get_matching_command.return_value = self.bang_command

		self.status_line.parse_input('!foo')
		self.status_line.list_hints('!foo')

		self.bang_command.hint_vim_command_parameter.assert_called_once_with(self.controller, 'foo')

	def test_bang_vim_command_is_mounted(self) :
		Command.get_matching_command.return_value = self.bang_command
		self.bang_command.hint_vim_command_parameter = MagicMock()
		self.bang_command.hint_vim_command_parameter.return_value = ['foobar']

		self.status_line.hint('!foo')
		self.status_line.highlight_index = 0
		self.assertEqual(self.status_line.mount_input(), '!foobar')

	def test_bang_vim_command_is_mounted_even_if_empty(self) :
		Command.get_matching_command.return_value = self.bang_command
		self.bang_command.hint_vim_command_parameter = MagicMock()
		self.bang_command.hint_vim_command_parameter.return_value = ['foobar']

		self.status_line.hint('!')
		self.status_line.highlight_index = 0
		self.assertEqual(self.status_line.mount_input(), '!foobar')


if __name__ == '__main__':
	unittest.main()
