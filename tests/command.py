import unittest
from unittest.mock import patch
from unittest.mock import MagicMock
from vimwn.hint import HintStatus
from vimwn.command import CommandInput


class CommandInputTestCase(unittest.TestCase):

	def test_parse_vim_command(self):
		i = CommandInput(text='buffers').parse()
		self.assertEqual(i.vim_command, 'buffers')
		self.assertTrue('' == i.vim_command_spacer == i.vim_command_parameter)
		self.assertTrue(None is i.terminal_command is i.terminal_command_spacer is i.terminal_command_parameter)

	def test_parse_vim_command_with_parameter(self):
		i = CommandInput(text='buffer  term').parse()
		self.assertEqual(i.vim_command, 'buffer')
		self.assertEqual(i.vim_command_spacer, '  ')
		self.assertEqual(i.vim_command_parameter, 'term')
		self.assertTrue(None is i.terminal_command is i.terminal_command_spacer is i.terminal_command_parameter)

	def test_parse_terminal_command_with_parameter(self):
		i = CommandInput(text='!  git   add').parse()
		self.assertEqual(i.vim_command, '!')
		self.assertEqual(i.vim_command_spacer, '  ')
		self.assertEqual(i.vim_command_parameter, 'git   add')
		self.assertEqual(i.terminal_command, 'git')
		self.assertEqual(i.terminal_command_spacer, '   ')
		self.assertEqual(i.terminal_command_parameter, 'add')


if __name__ == '__main__':
	unittest.main()
