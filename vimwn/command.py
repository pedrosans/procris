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
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk

GROUPED_INDEXED_BUFFER_REGEX = r'^\s*(buffer|b)\s*([0-9]+)\s*$'


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
		['buffer'		,GROUPED_INDEXED_BUFFER_REGEX		,None									,controller.open_indexed_buffer		],
		['buffer'		,'^\s*(buffer|b)\s+\w+.*$'			,None									,controller.open_named_buffer		],
		['centralize'	,'^\s*(centralize|ce)\s*$'			,None									,windows.centralize			    	],
		['maximize'		,'^\s*(maximize|ma)\s*$'			,None									,windows.maximize			    	],
		['reload'		,'^\s*(reload)\s*$'					,None									,controller.reload					],
		['decorate'		,'^\s*(decorate)\s+\w+.*$'			,None									,windows.decorate					],
		['report'		,'^\s*(report)\s*$'	          		,None									,controller.debug					],
		['move'			,'^\s*(move)\s+\w+.*$'				,None									,windows.move						],
		['quit'			,'^\s*(quit|q)\s*$'					,[Gdk.KEY_q]							,controller.quit					],
		['only'			,'^\s*(only|on)\s*$'				,[Gdk.KEY_o]							,windows.only		    			],
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
		[None			,None								,[Gdk.KEY_w, Gdk.KEY_W]					,windows.cycle						],
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

	def hint_vim_command_parameter(self, controller, input):
		if self.name == 'edit':
			return controller.applications.list_completions(input.vim_command_parameter)
		elif self.name in ['buffer']:
			return controller.windows.list_completions(input.vim_command_parameter)
		elif self.name == '!':
			return controller.terminal.list_completions(input)
		elif self.name == 'decorate':
			return controller.windows.decoration_options_for(input.vim_command_parameter)

	@staticmethod
	def hint_vim_command(user_input):
		user_input = user_input.lstrip()
		filtered = filter(lambda n: n.startswith(user_input), Command.NAME_MAP.keys())
		return sorted(list(set(filtered)))

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


class CommandInput:

	def __init__(self, time=None, text=None, keyval=None):
		self.time = time
		self.text = text
		self.keyval = keyval
		self.colon_spacer = None
		self.vim_command = None
		self.vim_command_spacer = None
		self.vim_command_parameter = None
		self.terminal_command = None
		self.terminal_command_spacer = None
		self.terminal_command_parameter = None

	def parse(self):
		if not self.text:
			return self

		match = re.match(r'^(\s*)(\w+|!)(.*)', self.text)

		if not match:
			return self

		self.colon_spacer = match.group(1)
		self.vim_command = match.group(2)
		parameter_text = match.group(3)

		grouped_parameter = re.match(r'^(\s*)(.*)', parameter_text)
		self.vim_command_spacer = grouped_parameter.group(1)
		self.vim_command_parameter = grouped_parameter.group(2)

		if self.vim_command == '!' and self.vim_command_parameter:
			grouped_terminal_command = re.match(r'^(\w+)(\s*)(.*)', self.vim_command_parameter)
			self.terminal_command = grouped_terminal_command.group(1)
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


class CommandHistory:

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
