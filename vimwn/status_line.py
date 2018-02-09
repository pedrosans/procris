
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
		self.hinting_command_parameter = False
		self.highlight_index = -1
		self.hints = []

	def clear_state(self):
		self.hinting = False
		self.hinting_command_parameter = False
		self.highlight_index = -1
		self.original_command = None
		self.original_command_parameter = None
		self.hints = []

	#TODO move to controller
	def on_entry_key_press(self, widget, event):
		if event.keyval in [Gdk.KEY_Tab, Gdk.KEY_ISO_Left_Tab]:
			if event.state & Gdk.ModifierType.SHIFT_MASK:
				return self.show_highlights(-1)
			else:
				return self.hint()
		elif event.keyval == Gdk.KEY_Left:
			return self.show_highlights(-1)
		elif event.keyval == Gdk.KEY_Right:
			return self.show_highlights(1)
		elif event.keyval in [Gdk.KEY_Shift_L, Gdk.KEY_Shift_R]:
			return False
		elif event.keyval in [Gdk.KEY_Up, Gdk.KEY_Down]:
			return True
		else:
			if self.hinting:
				self.view.clear_hints()
			self.hinting = False
			return False

	def hint(self):
		if self.hinting:
			return self.show_highlights(1)
		else:

			self.original_command_parameter = Command.extract_text_parameter(self.view.get_command())
			self.hinting_command_parameter = self.original_command_parameter != None

			if self.hinting_command_parameter:
				command = Command.find_command(self.view.get_command())
				self.hints = command.hint_parameters(self.controller, self.original_command_parameter)
			else:
				self.hints = Command.query_commands(self.view.get_command())

			if not self.hints or len(self.hints) == 0:
				return True
			else:
				self.highlight_index = -1
				self.original_command = Command.extract_command_name(self.view.get_command())
				return self.show_highlights(1)

	def show_highlights(self, direction):
		self.highlight_index += direction
		if self.highlight_index == len(self.hints):
			self.highlight_index = -1
		elif self.highlight_index < -1:
			self.highlight_index = len(self.hints) - 1

		i = self.highlight_index

		if self.hinting_command_parameter:
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

