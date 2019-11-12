import unittest

import procris.assistant
import procris.names as names
import procris.terminal as terminal
from unittest.mock import MagicMock
from procris.assistant import Completion
from procris.names import PromptInput


class AssistantTestCase(unittest.TestCase):

	def setUp(self):
		self.reading = MagicMock()
		self.completion = Completion(self.reading)
		self.buffer_command = MagicMock()
		self.buffer_command.name = 'buffer'
		names.completions_for = MagicMock()
		terminal.list_completions = lambda x: ['foobar']

	def tearDown(self):
		self.completion.clean()

	def test_query_vim_commands(self):
		self.completion.search_for(PromptInput(text='foo').parse())
		names.completions_for.assert_called_once_with('foo')

	def test_query_vim_commands_with_number(self):
		self.completion.search_for(PromptInput(text='b4').parse())
		names.completions_for.assert_not_called()

	def test_query_vim_commands_even_if_partial_match(self):
		self.completion.search_for(PromptInput(text='b').parse())
		names.completions_for.assert_called_once_with('b')

	def test_dont_query_vim_command_if_bang(self):
		command_input = PromptInput(text='!foo').parse()
		procris.assistant.completions_for(command_input, self.reading)
		names.completions_for.assert_not_called()

	def test_mount_spaces(self):
		self.completion.search_for(PromptInput(text='  !   foo').parse())
		self.completion.cycle(1)
		self.assertEqual('  !   foobar', self.completion.mount_input())

	def test_bang_vim_command_is_mounted(self):
		self.completion.search_for(PromptInput(text='!foo').parse())
		self.completion.index = 0
		self.assertEqual(self.completion.mount_input(), '!foobar')

	def test_bang_vim_command_is_mounted_even_if_empty(self):
		self.completion.search_for(PromptInput(text='!').parse())
		self.completion.index = 0
		self.assertEqual('!foobar', self.completion.mount_input())


if __name__ == '__main__':
	unittest.main()
