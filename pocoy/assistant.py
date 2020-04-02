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
import pocoy.names as names
import pocoy.state as configurations
from pocoy.names import Name


class Completion:

	def __init__(self, windows=None):
		self.windows = windows
		self.options = []
		self.assisting = False
		self.index = -1
		self.original_input = None

	def clean(self):
		if self.options:
			del self.options[:]
		self.assisting = False
		self.index = -1
		self.original_input = None

	def should_auto_assist(self):
		return configurations.is_auto_select_first_hint() \
				and self.index == -1 and self.assisting

	def search_for(self, c_in):
		self.original_input = c_in
		self.index = -1
		if c_in.vim_command_parameter or c_in.vim_command == '!' or c_in.vim_command_spacer:
			name: Name = names.match(c_in)
			self.options = name.complete(c_in) if name and name.complete else None
		else:
			self.options = names.completions_for(c_in)
		self.assisting = self.options and len(self.options) > 0

	def mount_input(self):
		if self.index == -1:
			return self.original_input.text
		else:
			original_command = self.original_input.text
			completion = self.options[self.index]
			for i in range(len(original_command)):
				for j in range(len(completion)):
					if completion[j] != original_command[i + j]:
						break
					if j + 1 == len(completion) or i + j + 1 == len(original_command):
						return original_command[:i] + completion
			if not original_command or original_command[-1].isspace() or original_command.strip() == '!':
				return original_command + completion
			else:
				return re.sub(r'[^\s]+$', completion, original_command)

	def cycle(self, direction):
		if len(self.options) == 1:
			self.index = 0
			return
		self.index += direction
		if self.index == len(self.options):
			self.index = -1
		elif self.index < -1:
			self.index = len(self.options) - 1
