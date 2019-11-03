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
import poco.names as names
import poco.applications as applications
import poco.terminal as terminal


def completions_for(c_in, reading):
	if c_in.vim_command == '!':
		return terminal.list_completions(c_in)

	if c_in.vim_command_spacer:
		if c_in.vim_command in ['edit', 'e']:
			return applications.list_completions(c_in.vim_command_parameter)
		elif c_in.vim_command in ['buffer', 'b']:
			return reading.windows.list_completions(c_in.vim_command_parameter)
		elif c_in.vim_command == 'decorate':
			return reading.windows.decoration_options_for(c_in.vim_command_parameter)
	else:
		return names.completions_for(c_in.vim_command)

	return None


class Matches:

	def __init__(self, reading):
		self.reading = reading
		self.completions = []
		self.matching = False
		self.index = -1
		self.original_input = None

	def clean(self):
		if self.completions:
			del self.completions[:]
		self.matching = False
		self.index = -1
		self.original_input = None

	def should_auto_hint(self):
		return self.reading.configurations.is_auto_select_first_hint() \
				and self.index == -1 and self.matching

	def search_for(self, c_in):
		self.original_input = c_in
		self.index = -1
		self.completions = completions_for(c_in, self.reading)
		self.matching = self.completions and len(self.completions) > 0

	def mount_input(self):
		i = self.index
		o_in = self.original_input
		if i == -1:
			return o_in.text
		elif o_in.terminal_command_spacer:
			return o_in.mount_vim_command() + o_in.terminal_command + o_in.terminal_command_spacer + self.completions[i]
		elif o_in.vim_command_spacer or o_in.vim_command == '!':
			return o_in.mount_vim_command() + self.completions[i]
		else:
			return o_in.colon_spacer + self.completions[i]

	def cycle(self, direction):
		if len(self.completions) == 1:
			self.index = 0
			return
		self.index += direction
		if self.index == len(self.completions):
			self.index = -1
		elif self.index < -1:
			self.index = len(self.completions) - 1
