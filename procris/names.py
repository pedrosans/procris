"""
Copyright 2017 Pedro Santos

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import re
from typing import Callable

LIST = []
NAME_MAP = {}
ALIAS_MAP = {}
MULTIPLE_COMMANDS_PATTERN = re.compile(r'.*[^\\]\|.*')


class PromptInput:

	def __init__(self, time=None, text=None, parameters=None, keyval=None, keymod=None):
		self.time = time
		self.text = text
		self.keyval = keyval
		self.keymod = keymod
		self.parameters = parameters
		self.colon_spacer = ''
		self.vim_command = ''
		self.vim_command_spacer = ''
		self.vim_command_parameter = ''
		self.terminal_command = ''
		self.terminal_command_spacer = ''
		self.terminal_command_parameter = ''

	def parse(self):
		if not self.text:
			return self

		match = re.match(r'^(\s*)([a-zA-Z]+|!)(.*)', self.text)

		if not match:
			return self

		self.colon_spacer = match.group(1)
		self.vim_command = match.group(2)

		vim_command_parameter_text = match.group(3)
		parameters_match = re.match(r'^(\s*)(.*)', vim_command_parameter_text)

		self.vim_command_spacer = parameters_match.group(1)
		self.vim_command_parameter = parameters_match.group(2)

		if self.vim_command == '!' and self.vim_command_parameter:
			grouped_terminal_command = re.match(r'^(\w+)(\s*)(.*)', self.vim_command_parameter)
			self.terminal_command = grouped_terminal_command.group(1)  # TODO: AttributeError: 'NoneType' object has no attribute 'group'
			self.terminal_command_spacer = grouped_terminal_command.group(2)
			self.terminal_command_parameter = grouped_terminal_command.group(3)

		return self

	def mount_vim_command(self):
		return self.colon_spacer + self.vim_command + self.vim_command_spacer

	def print(self):
		print('------------------------------------------')
		print('vc ::{}::'.format(self.vim_command))
		print('vcs::{}::'.format(self.vim_command_spacer))
		print('vcp::{}::'.format(self.vim_command_parameter))
		print('tc ::{}::'.format(self.terminal_command))
		print('tcs::{}::'.format(self.terminal_command_spacer))
		print('tcp::{}::'.format(self.terminal_command_parameter))


def add(name):
	LIST.append(name)
	NAME_MAP[name.name] = name
	ALIAS_MAP[name.alias] = name


def completions_for(c_in: PromptInput):
	user_input = c_in.vim_command
	filtered = filter(lambda n: n.startswith(user_input) if user_input else True, NAME_MAP.keys())
	filtered = filter(lambda n: n != user_input, filtered)
	return sorted(list(set(filtered)))


def has_multiple_names(command_input):
	return MULTIPLE_COMMANDS_PATTERN.match(command_input)


def match(command_input):
	vim_command = command_input.vim_command
	"""
	Returns matching command function if any
	"""
	if vim_command in NAME_MAP.keys():
		return NAME_MAP[vim_command]
	elif vim_command in ALIAS_MAP.keys():
		return ALIAS_MAP[vim_command]

	return None


class Name:

	def __init__(self, name, function, alias=None, complete: Callable = None):
		self.name = name
		self.alias = alias
		self.function = function
		self.complete = complete


class PromptHistory:

	def __init__(self):
		self.history = []
		self.pointer = None
		self.starting_command = None
		self.filtered_history = None

	def navigate_history(self, direction, user_input):
		if self.starting_command is None:
			self.starting_command = user_input
			self.filtered_history = list(filter(lambda c: c.startswith(self.starting_command), self.history))
		size = len(self.filtered_history)
		if self.pointer is None:
			self.pointer = size
		self.pointer += direction
		self.pointer = min(self.pointer, size)
		self.pointer = max(self.pointer, 0)

	def current_command(self):
		size = len(self.filtered_history)
		if self.pointer == size:
			return self.starting_command
		else:
			return self.filtered_history[self.pointer]

	def reset_history_pointer(self):
		self.pointer = None
		self.starting_command = None
		self.filtered_history = None

	def append(self, cmd):
		if cmd not in self.history:
			self.history.append(cmd)
