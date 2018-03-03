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
import gi, signal, re, os, sys
gi.require_version('Gtk', '3.0')
gi.require_version("Keybinder", "3.0")
from gi.repository import Gtk, Gdk, Keybinder, GLib
from vimwn.command import Command

class StatusLine ():

	def __init__(self, controller):
		self.controller = controller
		self.view = controller.view

	def clear_state(self):
		self.hinting = False
		self.highlight_index = -1
		self.vim_command = None
		self.vim_command_parameter = None
		self.terminal_command = None
		self.terminal_command_spacer = None
		self.terminal_command_parameter = None
		self.hints = []

	def auto_hint(self, text):
		self.highlight_index = -1
		self.parse_input(text)
		self.hints = self.list_hints(text)
		self.hinting = self.hints and len(self.hints) > 0

	def hint(self, text):
		self.highlight_index = -1
		self.parse_input(text)
		self.hints = self.list_hints(text)
		self.hinting = self.hints and len(self.hints) > 1

	def list_hints(self, text):
		self.vim_command = Command.extract_vim_command(text)
		command = Command.get_matching_command(text)
		if not self.vim_command_spacer and (not command or command.name != '!'):
			return Command.query_vim_commands(text)
		if not command:
			return None
		if self.vim_command_spacer or command.name == '!':
			return command.hint_vim_command_parameter(self.controller, self.vim_command_parameter)

	def parse_input(self, text):
		self.vim_command = Command.extract_vim_command(text)
		parameter_text = text.replace(self.vim_command, '', 1)
		self.vim_command_spacer = re.match(r'^\s*', parameter_text).group()
		self.vim_command_parameter = parameter_text.replace(self.vim_command_spacer, '', 1)
		if self.vim_command == '!':
			self.terminal_command = Command.extract_terminal_command(self.vim_command_parameter)
			parameter_text = self.vim_command_parameter.replace(self.terminal_command, '', 1)
			self.terminal_command_spacer = re.match(r'^\s*', parameter_text).group()
			self.terminal_command_parameter = parameter_text.replace(self.terminal_command_spacer, '', 1)
		else:
			self.terminal_command = self.terminal_command_spacer = self.terminal_command_parameter = ''

	def get_highlighted_hint(self):
		i = self.highlight_index
		if self.terminal_command_spacer:
			return self.vim_command + self.vim_command_spacer + self.terminal_command + self.terminal_command_spacer + (
					self.hints[i] if i > -1 else
					self.terminal_command_parameter)
		elif self.vim_command_spacer:
			return self.vim_command + self.vim_command_spacer + (
					self.hints[i] if i > -1 else
					self.vim_command_parameter)
		else:
			return self.hints[i] if i > -1 else self.vim_command

	def cycle(self, direction):
		if len(self.hints) == 1:
			self.highlight_index = 0
			return
		self.highlight_index += direction
		if self.highlight_index == len(self.hints):
			self.highlight_index = -1
		elif self.highlight_index < -1:
			self.highlight_index = len(self.hints) - 1
