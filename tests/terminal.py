import unittest
import poco.terminal as terminal
from poco.commands import CommandInput


class TerminalTestCase(unittest.TestCase):

	def test_parse_alias(self):
		name, cmd = terminal.parse_alias_line('alias ll=\'ls -alh\'')[0]
		self.assertEqual('ll', name)
		self.assertEqual('ls -alh', cmd)

	def test_parse_alias_with_quotes(self):
		# alias ab=$'echo "a\'b\'"'
		# alias to: echo "a'b'"
		line = 'alias ab=$\'echo "a\\\'b\\\'"\''
		name, cmd = terminal.parse_alias_line(line)[0]
		self.assertEqual('ab', name)
		self.assertEqual('echo "a\\\'b\\\'"', cmd)

	def test_parse_multiple_aliases_in_one_line(self):
		line = 'alias aa=\'echo aa\' ab=\'echo ab\''
		name, cmd = terminal.parse_alias_line(line)[0]
		self.assertEqual('aa', name)
		self.assertEqual('echo aa', cmd)
		name, cmd = terminal.parse_alias_line(line)[1]
		self.assertEqual('ab', name)
		self.assertEqual('echo ab', cmd)

	def test_read_aliases(self):
		terminal.get_sys_aliases = lambda: 'alias ll=\'ls -alF\''
		terminal._load_aliases()

		self.assertEqual(terminal.ALIASES_MAP['ll'], 'ls -alF')

	def test_autocomplete_parameters(self):
		terminal.query_command_parameters = lambda x: ['bar']
		self.assertEqual(
			['bar'],
			terminal.list_completions(CommandInput(text='!foo ').parse()))
