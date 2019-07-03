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

import gi, re
from gi.repository import Gdk


class Command:

	LIST = []
	KEY_MAP = {}
	NAME_MAP = {}
	MULTIPLE_COMMANDS_PATTERN = re.compile(r'.*[^\\]\|.*')

	def __init__(self, name, pattern, keys, function):
		self.name = name
		self.pattern = re.compile(pattern) if pattern else None
		self.function = function
		self.keys = keys

	@staticmethod
	def map_to(controller, windows):
		c_array = [
		['edit'			,'^\s*(edit|e).*$'					,None									,controller.edit					],
		['!'			,'^\s*!.*$'							,None									,controller.bang					],
		['buffers'		,'^\s*(buffers|ls)\s*$'				,None									,controller.buffers					],
		['bdelete'		,'^\s*(bdelete|bd)\s*$'				,None									,controller.delete_current_buffer	],
		['bdelete'		,'^\s*(bdelete|bd)\s*([0-9]+\s*)+$'	,None									,controller.delete_indexed_buffer	],
		['bdelete'		,'^\s*(bdelete|bd)\s+\w+\s*$'		,None									,controller.delete_named_buffer		],
		['buffer'		,'^\s*(buffer|b)\s*$'				,None									,controller.buffer					],
		['buffer'		,'^\s*(buffer|b)\s*[0-9]+\s*$'		,None									,controller.open_indexed_buffer		],
		['buffer'		,'^\s*(buffer|b)\s+\w+.*$'			,None									,controller.open_named_buffer		],
		['centralize'	,'^\s*(centralize|ce)\s*$'			,None									,windows.centralize			    	],
		['maximize'		,'^\s*(maximize|ma)\s*$'			,None									,windows.maximize			    	],
		['reload'		,'^\s*(reload)\s*$'					,None									,controller.reload					],
		['quit'			,'^\s*(quit|q)\s*$'					,[Gdk.KEY_q]							,controller.quit					],
		['only'			,'^\s*(only|on)\s*$'				,[Gdk.KEY_o]							,windows.only					],
		[None			,None								,[Gdk.KEY_Right, Gdk.KEY_l]				,windows.navigate_right				],
		[None			,None								,[Gdk.KEY_L]							,windows.move_right					],
		[None			,None								,[Gdk.KEY_Down, Gdk.KEY_j]				,windows.navigate_down				],
		[None			,None								,[Gdk.KEY_J]							,windows.move_down					],
		[None			,None								,[Gdk.KEY_Left, Gdk.KEY_h]				,windows.navigate_left				],
		[None			,None								,[Gdk.KEY_H]							,windows.move_left					],
		[None			,None								,[Gdk.KEY_Up, Gdk.KEY_k]				,windows.navigate_up				],
		[None			,None								,[Gdk.KEY_K]							,windows.move_up					],
		[None			,None								,[Gdk.KEY_less]							,windows.decrease_width				],
		[None			,None								,[Gdk.KEY_greater]						,windows.increase_width				],
		[None			,None								,[Gdk.KEY_equal]						,windows.equalize					],
		[None			,None								,[Gdk.KEY_w]							,windows.cycle						],
		[None			,None								,[Gdk.KEY_p]							,windows.navigate_to_previous		],
		[None			,None								,[Gdk.KEY_colon]						,controller.colon					],
		[None			,None								,[Gdk.KEY_Return]						,controller.enter					],
		[None			,None								,[Gdk.KEY_Escape, Gdk.KEY_bracketleft]	,controller.escape					]]
		for p in c_array:
			name, pattern, keys, function = p
			command = Command(name, pattern, keys, function)
			if name:
				Command.NAME_MAP[name] = command
			if keys:
				for k in keys:
					Command.KEY_MAP[k] = command
			Command.LIST.append(command)


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
		for command in Command.LIST:
			if command.pattern and command.pattern.match(command_input):
				return command
		return None

	@staticmethod
	def query_vim_commands(user_input):
		striped = user_input.lstrip()
		matches = filter(
				(lambda n: not user_input or n.startswith(striped)),
				Command.NAME_MAP.keys()
			)
		matches = filter(lambda x : x != striped, matches)
		return sorted(list(set(matches)))

	@staticmethod
	def extract_number_parameter(cmd):
		return re.findall(r'\d+', cmd)[0]

	# TODO remove and make it the input minus the detected command
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
		if cmd is None:
			return None
		if not cmd.strip():
			return cmd
		return re.match(r'^\s*(\w+|!)', cmd).group()

	@staticmethod
	def extract_terminal_command(cmd):
		if cmd is None:
			return None
		if not cmd.strip():
			return cmd
		return re.match(r'^\s*\w+', cmd).group()


class CommandInput:

	def __init__(self, time, text_input=None, key=None):
		self.time = time
		self.text_input = text_input
		self.key = key
