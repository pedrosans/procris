import unittest
from procris.names import CommandLine


class CommandInputTestCase(unittest.TestCase):

	def test_parse_vim_command(self):
		i = CommandLine(text='buffers').parse()
		self.assertEqual(i.vim_command, 'buffers')
		self.assertTrue('' == i.vim_command_spacer == i.vim_command_parameter)
		self.assertTrue('' is i.terminal_command is i.terminal_command_spacer is i.terminal_command_parameter)

	def test_parse_empty_input(self):
		i = CommandLine(text='').parse()
		self.assertEqual(i.colon_spacer, '')
		self.assertEqual(i.vim_command, '')

	def test_parse_colon_spacer(self):
		i = CommandLine(text='  buffers').parse()
		self.assertEqual(i.colon_spacer, '  ')
		self.assertEqual(i.vim_command, 'buffers')

	def test_parse_vim_command_with_parameter(self):
		i = CommandLine(text='buffer  term').parse()
		self.assertEqual(i.vim_command, 'buffer')
		self.assertEqual(i.vim_command_spacer, '  ')
		self.assertEqual(i.vim_command_parameter, 'term')
		self.assertTrue('' is i.terminal_command is i.terminal_command_spacer is i.terminal_command_parameter)

	def test_parse_vim_command_with_number_parameter(self):
		i = CommandLine(text='buffer  23').parse()
		self.assertEqual(i.vim_command, 'buffer')
		self.assertEqual(i.vim_command_spacer, '  ')
		self.assertEqual(i.vim_command_parameter, '23')
		self.assertEqual(i.terminal_command, '')
		self.assertEqual(i.terminal_command_spacer, '')
		self.assertEqual(i.terminal_command_parameter, '')

	def test_parse_vim_command_with_number_parameter_without_separation(self):
		i = CommandLine(text='b2').parse()
		self.assertEqual(i.vim_command, 'b')
		self.assertEqual(i.vim_command_spacer, '')
		self.assertEqual(i.vim_command_parameter, '2')
		self.assertEqual(i.terminal_command, '')
		self.assertEqual(i.terminal_command_spacer, '')
		self.assertEqual(i.terminal_command_parameter, '')

	def test_parse_terminal_command(self):
		i = CommandLine(text='!foo').parse()
		self.assertEqual(i.vim_command, '!')
		self.assertEqual(i.vim_command_spacer, '')
		self.assertEqual(i.vim_command_parameter, 'foo')
		self.assertEqual(i.terminal_command, 'foo')
		self.assertEqual(i.terminal_command_spacer, '')
		self.assertEqual(i.terminal_command_parameter, '')

	def test_parse_empty_terminal_command(self):
		i = CommandLine(text='!  ').parse()
		self.assertEqual(i.vim_command, '!')
		self.assertEqual(i.vim_command_spacer, '  ')
		self.assertEqual(i.vim_command_parameter, '')
		self.assertEqual(i.terminal_command, '')
		self.assertEqual(i.terminal_command_spacer, '')
		self.assertEqual(i.terminal_command_parameter, '')

	def test_parse_terminal_command_with_parameter(self):
		i = CommandLine(text='!  git   add').parse()
		self.assertEqual(i.vim_command, '!')
		self.assertEqual(i.vim_command_spacer, '  ')
		self.assertEqual(i.vim_command_parameter, 'git   add')
		self.assertEqual(i.terminal_command, 'git')
		self.assertEqual(i.terminal_command_spacer, '   ')
		self.assertEqual(i.terminal_command_parameter, 'add')

	def test_parse_terminal_command_with_number(self):
		i = CommandLine(text='!  7z').parse()
		self.assertEqual(i.vim_command, '!')
		self.assertEqual(i.vim_command_spacer, '  ')
		self.assertEqual(i.vim_command_parameter, '7z')
		self.assertEqual(i.terminal_command, '7z')
		self.assertEqual(i.terminal_command_spacer, '')
		self.assertEqual(i.terminal_command_parameter, '')


if __name__ == '__main__':
	unittest.main()
