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


class Command:

	COMMANDS = []
	MULTIPLE_COMMANDS_PATTERN = re.compile(r'.*[^\\]\|.*')

	def __init__(self, name, pattern, test_parameter_partial_match, function):
		self.name = name
		self.pattern = re.compile(pattern)
		self.function = function
		self.test_parameter_partial_match = test_parameter_partial_match

	def hint_vim_command_parameter(self, controller, command_parameters):
		if self.name == 'edit':
			return controller.applications.list_completions(command_parameters)
		elif self.name in ['buffer']:
			return controller.windows.list_completions(command_parameters)
		elif self.name == '!':
			return controller.terminal.list_completions(command_parameters)

	@staticmethod
	def has_multiple_commands(command_input):
		return Command.MULTIPLE_COMMANDS_PATTERN.match(command_input)

	@staticmethod
	def get_matching_command(command_input):
		"""
		Returns matching command function if any
		"""
		for command in Command.COMMANDS:
			if command.pattern.match(command_input):
				return command
		return None

	@staticmethod
	def query_vim_commands(user_input):
		striped = user_input.lstrip()
		matches = filter(
				(lambda n : not user_input or n.startswith(striped)),
				map((lambda c : c.name), Command.COMMANDS)
			)
		matches = filter(lambda x : x != striped, matches)
		return sorted(list(set(matches)))

	@staticmethod
	def extract_number_parameter(cmd):
		return re.findall(r'\d+', cmd)[0]

	#TODO remove and make it the input minus the detected command
	@staticmethod
	def extract_text_parameter(cmd):
		if not cmd:
			return None
		command_match = re.findall(r'\s*\w+\s+', cmd)
		if len(command_match) == 0:
			return None
		else:
			return cmd[len(command_match[0]):]

	@staticmethod
	def extract_vim_command(cmd):
		if cmd == None:
			return None
		if not cmd.strip():
			return cmd
		return re.match(r'^\s*(\w+|!)', cmd).group()

	@staticmethod
	def extract_terminal_command(cmd):
		if cmd == None:
			return None
		if not cmd.strip():
			return cmd
		return re.match(r'^\s*\w+', cmd).group()

	@staticmethod
	def map_name_to_function(name, pattern, test_parameter_partial_match, function):
		Command.COMMANDS.append(Command(name, pattern, test_parameter_partial_match, function))

	@staticmethod
	def map_commands(controller, windows):
		if len(Command.COMMANDS) > 0:
			raise Exception('Commands were already mapped')
		Command.map_name_to_function('only',       "^\s*(only|on)\s*$",					False,	controller.only )
		Command.map_name_to_function('edit',       "^\s*(edit|e).*$",					False,	controller.edit )
		Command.map_name_to_function('!',          "^\s*!.*$",							False,	controller.bang )
		Command.map_name_to_function('buffers',    "^\s*(buffers|ls)\s*$",				False,	controller.buffers )
		Command.map_name_to_function('bdelete',    "^\s*(bdelete|bd)\s*$",				True,	controller.delete_current_buffer )
		Command.map_name_to_function('bdelete',    "^\s*(bdelete|bd)\s*([0-9]+\s*)+$",	True,	controller.delete_indexed_buffer )
		Command.map_name_to_function('bdelete',    "^\s*(bdelete|bd)\s+\w+\s*$",		True,	controller.delete_named_buffer )
		Command.map_name_to_function('buffer',     "^\s*(buffer|b)\s*$",				True,	controller.buffer )
		Command.map_name_to_function('buffer',     "^\s*(buffer|b)\s*[0-9]+\s*$",		True,	controller.open_indexed_buffer )
		Command.map_name_to_function('buffer',     "^\s*(buffer|b)\s+\w+.*$",			True,	controller.open_named_buffer )
		Command.map_name_to_function('centralize', "^\s*(centralize|ce)\s*$",	False,	controller.centralize )
		Command.map_name_to_function('maximize',   "^\s*(maximize|ma)\s*$",		False,	controller.maximize )
		Command.map_name_to_function('quit',       "^\s*(quit|q)\s*$",					False,	controller.quit)
		Command.map_name_to_function('reload',     "^\s*(reload)\s*$",					False,	controller.reload)

