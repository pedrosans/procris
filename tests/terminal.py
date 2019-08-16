import unittest, subprocess
from unittest.mock import patch
from unittest.mock import MagicMock
from vimwn.terminal import Terminal

#alias ea =$'echo \'a\'b\'' 18
#alias eb = "echo ab"
#alias ec = 'echo ab'
#alias aa = 'echo aa' ab = 'echo ab'
#alias ed =$'echo "a\'b\'"'
class TerminalTestCase(unittest.TestCase):
	# def setUp(self):
		# proc = MagicMock()
		# proc.communicate = MagicMock(return_value=[ALIASE])
		# subprocess.Popen = MagicMock(return_value=proc)
	def test_parse_alias(self):
		name, cmd = Terminal.parse_alias_line('alias ll=\'ls -alh\'')[0]
		self.assertEqual('ll', name)
		self.assertEqual('ls -alh', cmd)

	def test_parse_alias_with_quote(self):
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
		self.terminal = Terminal()
		print('{}'.format(self.terminal.aliases_map))
		print('{}'.format(self.terminal.aliases_map['add-key']))
		# self.assertEqual(self.terminal.aliases_map['ll'], 'ls -alh')

if __name__ == '__main__':
	unittest.main()
