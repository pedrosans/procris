import unittest, subprocess
from unittest.mock import patch
from unittest.mock import MagicMock
from vimwn.terminal import Terminal

ALIASE = b'alias ll=\'ls -alh\''
class TerminalTestCase(unittest.TestCase):
	# def setUp(self):
		# proc = MagicMock()
		# proc.communicate = MagicMock(return_value=[ALIASE])
		# subprocess.Popen = MagicMock(return_value=proc)

	def test_read_aliases(self):

		self.terminal = Terminal()
		print('{}'.format(self.terminal.aliases_map))
		print('{}'.format(self.terminal.aliases_map['add-key']))
		# self.assertEqual(self.terminal.aliases_map['ll'], 'ls -alh')

if __name__ == '__main__':
	unittest.main()
