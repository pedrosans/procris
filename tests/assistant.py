import unittest

import procris.assistant
import procris.names as names
import procris.terminal as terminal
from unittest.mock import MagicMock
from procris.assistant import Completion
from procris.wm import UserEvent


class AssistantTestCase(unittest.TestCase):

	def setUp(self):
		self.reading = MagicMock()
		self.completion = Completion(self.reading)
		names.completions_for = MagicMock()
		names.add(names.Name('!', None, None, lambda x: ['foobar']))
		names.add(names.Name('buffer', 'b', None, lambda x: None))
		names.add(names.Name('bdelete', 'bd', None, lambda x: []))
		names.add(names.Name('buffers', None, None, None))
		names.add(names.Name('bar', None, None, lambda x: ['foobar']))

	def tearDown(self):
		self.completion.clean()

	def test_query_vim_commands(self):
		c_in = UserEvent(text='buf')
		self.completion.search_for(c_in)
		names.completions_for.assert_called_once_with(c_in)

	def test_dont_query_vim_commands_if_input_with_parameter(self):
		self.completion.search_for(UserEvent(text='b 4'))
		names.completions_for.assert_not_called()

	def test_dont_query_vim_commands_if_input_with_parameter_not_separated(self):
		self.completion.search_for(UserEvent(text='b4'))
		names.completions_for.assert_not_called()

	def test_query_vim_commands_if_name_completions_is_none(self):
		c_in = UserEvent(text='b')
		self.completion.search_for(c_in)
		names.completions_for.assert_called_once_with(c_in)

	def test_query_vim_commands_if_name_completions_is_empty(self):
		c_in = UserEvent(text='bd')
		self.completion.search_for(c_in)
		names.completions_for.assert_called_once_with(c_in)

	def test_dont_query_vim_command_if_bang(self):
		command_input = UserEvent(text='!foo')
		self.completion.search_for(command_input)
		names.completions_for.assert_not_called()

	def test_mount_spaces(self):
		self.completion.search_for(UserEvent(text='  !   foo'))
		self.completion.cycle(1)
		self.assertEqual('  !   foobar', self.completion.mount_input())

	def test_mount_bang_plus_completion(self):
		self.completion.search_for(UserEvent(text='!'))
		self.completion.index = 0
		self.assertEqual('!foobar', self.completion.mount_input())

	def test_mount_bang_plus_match(self):
		self.completion.search_for(UserEvent(text='!foo'))
		self.completion.index = 0
		self.assertEqual(self.completion.mount_input(), '!foobar')

	def test_mount_name_plus_partial_match(self):
		self.completion.search_for(UserEvent(text='bar o'))
		self.completion.index = 0
		self.assertEqual(self.completion.mount_input(), 'bar foobar')


if __name__ == '__main__':
	unittest.main()
