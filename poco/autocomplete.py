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
import poco.commands as commands
from poco import applications as applications, terminal as terminal


def autocomplete(c_in, reading):

	if not c_in.vim_command_spacer and c_in.vim_command != '!':
		return commands.autocomplete_vim_command(c_in.text)

	if c_in.vim_command_spacer or c_in.vim_command == '!':
		return autocomplete_parameter(c_in, reading)

	return None


def autocomplete_parameter(c_in, reading):
	if c_in.vim_command == 'edit':
		return applications.list_completions(c_in.vim_command_parameter)
	elif c_in.vim_command in ['buffer', 'b']:
		return reading.windows.list_completions(c_in.vim_command_parameter)
	elif c_in.vim_command == '!':
		return terminal.list_completions(c_in)
	elif c_in.vim_command == 'decorate':
		return reading.windows.decoration_options_for(c_in.vim_command_parameter)


class Autocomplete:

	def __init__(self, reading):
		self.reading = reading
		self.hints = []
		self.hinting = False
		self.highlight_index = -1
		self.original_input = None

	def clear_state(self):
		if self.hints:
			del self.hints[:]
		self.hinting = False
		self.highlight_index = -1
		self.original_input = None

	def should_auto_hint(self):
		return self.reading.configurations.is_auto_select_first_hint()\
				and self.highlight_index == -1 and self.hinting

	def hint(self, parsed_input):
		self.original_input = parsed_input
		self.highlight_index = -1
		self.hints = autocomplete(parsed_input, self.reading)
		self.hinting = self.hints and len(self.hints) > 0

	def mount_input(self):
		i = self.highlight_index
		o_in = self.original_input
		if i == -1:
			return o_in.text
		elif o_in.terminal_command_spacer:
			return o_in.mount_vim_command() + o_in.terminal_command + o_in.terminal_command_spacer + self.hints[i]
		elif o_in.vim_command_spacer or o_in.vim_command == '!':
			return o_in.mount_vim_command() + self.hints[i]
		else:
			return o_in.colon_spacer + self.hints[i]

	def cycle(self, direction):
		if len(self.hints) == 1:
			self.highlight_index = 0
			return
		self.highlight_index += direction
		if self.highlight_index == len(self.hints):
			self.highlight_index = -1
		elif self.highlight_index < -1:
			self.highlight_index = len(self.hints) - 1
