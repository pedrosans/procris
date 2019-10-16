import unittest, subprocess
from poco.terminal import Terminal
from unittest.mock import patch
from unittest.mock import MagicMock

ALIASES = b'alias ll=\'ls -alh\''


class TerminalTestCase(unittest.TestCase):

	def test_parse_alias(self):
		name, cmd = Terminal.parse_alias_line('alias ll=\'ls -alh\'')[0]
		self.assertEqual('ll', name)
		self.assertEqual('ls -alh', cmd)

	def test_parse_alias_with_quotes(self):
		# alias ab=$'echo "a\'b\'"'
		# alias to: echo "a'b'"
		line = 'alias ab=$\'echo "a\\\'b\\\'"\''
		name, cmd = Terminal.parse_alias_line(line)[0]
		self.assertEqual('ab', name)
		self.assertEqual('echo "a\\\'b\\\'"', cmd)

	def test_parse_multiple_aliases_in_one_line(self):
		line = 'alias aa=\'echo aa\' ab=\'echo ab\''
		name, cmd = Terminal.parse_alias_line(line)[0]
		self.assertEqual('aa', name)
		self.assertEqual('echo aa', cmd)
		name, cmd = Terminal.parse_alias_line(line)[1]
		self.assertEqual('ab', name)
		self.assertEqual('echo ab', cmd)

	def test_read_aliases(self):
		proc = MagicMock()
		proc.communicate = MagicMock(return_value=[ALIASES])
		subprocess.Popen = MagicMock(return_value=proc)

		self.terminal = Terminal()

		self.assertEqual(self.terminal.aliases_map['ll'], 'ls -alh')
		# print('{}'.format(self.terminal.ALIASES_MAP))
		# print('{}'.format(self.terminal.ALIASES_MAP['add-key']))
		# self.assertEqual(self.terminal.ALIASES_MAP['ll'], 'ls -alh')
