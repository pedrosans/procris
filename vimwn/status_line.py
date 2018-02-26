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
from vimwn.view import NavigatorWindow
from vimwn.environment import Configurations
from vimwn.command import Command

class StatusLine ():

	def __init__(self, controller):
		self.controller = controller
		self.view = controller.view

	def clear_state(self):
		self.hinting = False
		self.highlight_index = -1
		self.original_command = None
		self.original_command_parameter = None
		self.hints = []

	def auto_hint(self, text):
		self.setup_hints(text)
		if self.hints and len(self.hints) > 0:
			self.view.hint(self.hints, -1, None)
			self.hinting = True
		else:
			self.hinting = False

	def hint(self, text, direction):
		self.setup_hints(text)

		if not self.hints or len(self.hints) == 0:
			return

		self.hinting = len(self.hints) > 1

	def setup_hints(self, command_input):
		self.highlight_index = -1
		self.original_command = Command.extract_command_name(command_input)
		self.original_command_parameter = Command.extract_text_parameter(command_input)
		if self.original_command_parameter == None:
			self.hints = Command.query_commands(command_input)
		else:
			#TODO rename to find by text pattern
			command = Command.find_command(command_input)
			if command:
				self.hints = command.hint_parameters(self.controller, self.original_command_parameter)
			else:
				self.hints = None

	def get_highlighted_hint(self):
		i = self.highlight_index
		if self.original_command_parameter != None:
			hinted_parameter = self.hints[i] if i > -1 else self.original_command_parameter
			return self.original_command + hinted_parameter
		else:
			return self.hints[i] if i > -1 else self.original_command

	def cycle(self, direction):
		if len(self.hints) == 1:
			self.highlight_index = 0
			return
		self.highlight_index += direction
		if self.highlight_index == len(self.hints):
			self.highlight_index = -1
		elif self.highlight_index < -1:
			self.highlight_index = len(self.hints) - 1
