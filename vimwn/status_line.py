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
from vimwn.windows import Windows
from vimwn.environment import Configurations
from vimwn.applications import Applications
from vimwn.command import Command

class StatusLine ():

	def __init__(self, controller):
		self.controller = controller
		self.view = controller.view
		self.windows = controller.windows
		self.applications = controller.applications
		self.hinting = False
		self.highlight_index = -1
		self.hints = []
		self.auto_hinting = False
		self.auto_hints = []

	def clear_state(self):
		if self.hinting or self.auto_hinting:
			self.view.clear_hints_state()
		self.hinting = False
		self.highlight_index = -1
		self.original_command = None
		self.original_command_parameter = None
		self.hints = []
		self.auto_hinting = False
		self.auto_hints = []

	#TODO move the view calls to controller
	def auto_hint(self, text):
		if self.hinting:
			return
		self.auto_hints = self.list_hints_for(text)
		if self.auto_hints and len(self.auto_hints) > 0:
			self.view.hint(self.auto_hints, -1, None)
			self.auto_hinting = True
		else:
			self.clear_state()

	def hint(self, text, direction):
		if self.hinting:
			return self.show_highlights(direction)
		self.original_command_parameter = Command.extract_text_parameter(text)
		self.hints = self.list_hints_for(text)
		if not self.hints or len(self.hints) == 0:
			return True
		else:
			self.highlight_index = -1
			self.original_command = Command.extract_command_name(self.view.get_command())
			return self.show_highlights(direction)

	def list_hints_for(self, command_input):
		if not command_input or not command_input.strip():
			return None
		command_parameter = Command.extract_text_parameter(command_input)
		if command_parameter == None:
			return Command.query_commands(self.view.get_command())
		else:
			command = Command.find_command(command_input)
			if command:
				return command.hint_parameters(self.controller, command_parameter)
			else:
				return None

	def show_highlights(self, direction):
		self.highlight_index += direction
		if self.highlight_index == len(self.hints):
			self.highlight_index = -1
		elif self.highlight_index < -1:
			self.highlight_index = len(self.hints) - 1

		i = self.highlight_index

		hinting_command_parameter = self.original_command_parameter != None
		if hinting_command_parameter:
			hinted_parameter = self.hints[i] if i > -1 else self.original_command_parameter
			placeholder = self.original_command
			if hinted_parameter:
				placeholder += hinted_parameter
		else:
			placeholder = self.hints[i] if i > -1 else self.original_command

		if len(self.hints) == 1:
			self.view.set_command(placeholder)
		else:
			self.view.hint(self.hints, i, placeholder)
			self.hinting = True

		return True

