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
from vimwn.command import Command
from vimwn.command import CommandInput
from vimwn.terminal import Terminal


# TODO move to status.py
class HintStatus:

	def __init__(self, controller):
		self.controller = controller
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
		return self.controller.configurations.is_auto_select_first_hint()\
				and self.highlight_index == -1 and self.hinting

	def hint(self, parsed_input):
		self.original_input = parsed_input
		self.highlight_index = -1
		self.hints = self.list_hints(parsed_input)
		self.hinting = self.hints and len(self.hints) > 0

	def list_hints(self, parsed_input):
		command = Command.get_matching_command(parsed_input.text)
		if command and (parsed_input.vim_command_spacer or command.name == '!'):
			return command.hint_vim_command_parameter(self.controller, parsed_input)
		elif not parsed_input.vim_command_spacer:
			return Command.hint_vim_command(parsed_input.text)
		else:
			return None

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
