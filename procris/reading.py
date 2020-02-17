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
import gi, procris
import procris.messages as messages
import procris.names as names
import procris.cache as configurations

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from procris.view import ReadingWindow
from procris.assistant import Completion
from procris.names import PromptHistory
from procris.names import CommandLine
from procris.windows import Windows
from procris.assistant import Completion

HINT_LAUNCH_KEYS = [Gdk.KEY_Tab, Gdk.KEY_ISO_Left_Tab]
HINT_LEFT = [Gdk.KEY_Left]
HINT_RIGHT = [Gdk.KEY_Right]
HINT_NAVIGATION_KEYS = HINT_LAUNCH_KEYS + HINT_LEFT + HINT_RIGHT
HINT_OPERATION_KEYS = [Gdk.KEY_Shift_L, Gdk.KEY_Shift_R, Gdk.KEY_Return] + HINT_NAVIGATION_KEYS

HISTORY_NAVIGATION_KEYS = [Gdk.KEY_Up, Gdk.KEY_Down]


# TODO chain commands
class Reading:

	view: ReadingWindow = None
	windows: Windows = None
	completions: Completion = None
	prompt_history: PromptHistory = PromptHistory()
	long = False
	command_mode = False
	cmd_handler_ids = []

	def __init__(self, windows=None):
		self.windows = windows
		self.completion = Completion(self.windows)
		self._create_and_install_view()

	def _create_and_install_view(self):
		self.view = ReadingWindow(self, self.windows)
		self.view.connect("key-press-event", self._window_key_press_callback)

	#
	# Lifecycle state API
	#
	def begin(self, time):
		self.clean()
		self.long = True
		self.view.present_and_focus(time)
		self.view.update()

	def is_transient(self):
		return not self.long

	def make_transient(self):
		self.long = False

	def end(self):
		self.view.hide()

	#
	# State API
	#
	def clean(self, recreate_view=False):
		self.command_mode = False
		for handler_id in self.cmd_handler_ids:
			self.view.colon_prompt.disconnect(handler_id)
		self.cmd_handler_ids.clear()
		self.completion.clean()
		if recreate_view:
			self.view.close()
			self._create_and_install_view()

	def set_command_mode(self):
		self.command_mode = True

		self.view.update()

		r_id = self.view.colon_prompt.connect("key-release-event", self.on_entry_key_release)
		p_id = self.view.colon_prompt.connect("key-press-event", self.on_entry_key_press)
		a_id = self.view.colon_prompt.connect("activate", self.on_prompt_input, None)

		self.cmd_handler_ids.extend([r_id, p_id, a_id])

	def in_command_mode(self):
		return self.command_mode

	#
	# CALLBACKS
	#
	def _window_key_press_callback(self, widget, event):
		ctrl = (event.state & Gdk.ModifierType.CONTROL_MASK)

		if event.keyval == Gdk.KEY_Escape or (ctrl and event.keyval == Gdk.KEY_bracketleft):
			self.end()
			messages.clean()
			return

		if self.in_command_mode():
			return

		if event.keyval == Gdk.KEY_colon and not ctrl:
			self.colon()
			return True

		if event.keyval == Gdk.KEY_Return:
			self.enter(CommandLine(time=event.time, keyval=event.keyval))
			return True

	def on_entry_key_release(self, widget, event):
		if event.keyval in HINT_OPERATION_KEYS:
			return False

		if not self.view.colon_prompt.get_text().strip():
			self.clean()
			self.view.update()
			return True

		if configurations.is_auto_hint():
			self.completion.search_for(CommandLine(text=self.view.get_command()).parse())
		else:
			self.completion.clean()

		if self.completion.assisting:
			self.view.offer(self.completion.options, self.completion.index, self.completion.should_auto_assist())
		else:
			self.view.clean_completions()

	def on_entry_key_press(self, widget, event):
		if event.keyval in HISTORY_NAVIGATION_KEYS:
			self.prompt_history.navigate_history(-1 if event.keyval == Gdk.KEY_Up else 1, self.view.get_command())
			self.view.set_command(self.prompt_history.current_command())
			self.view.clean_completions()
			self.completion.clean()
			return True
		else:
			self.prompt_history.reset_history_pointer()

		if event.keyval not in HINT_NAVIGATION_KEYS:
			return False

		if not self.completion.assisting and event.keyval in HINT_LAUNCH_KEYS:
			self.completion.search_for(CommandLine(text=self.view.get_command()).parse())

		if self.completion.assisting:
			shift_mask = event.state & Gdk.ModifierType.SHIFT_MASK
			right = event.keyval in HINT_RIGHT or (event.keyval in HINT_LAUNCH_KEYS and not shift_mask)
			self.completion.cycle(1 if right else -1)
			if len(self.completion.options) == 1:
				self.view.clean_completions()
			else:
				self.view.offer(self.completion.options, self.completion.index, self.completion.should_auto_assist())
			self.view.set_command(self.completion.mount_input())

		return True

	def on_prompt_input(self, pane_owner, current):
		if not self.command_mode:
			return

		gtk_time = Gtk.get_current_event_time()
		cmd = self.view.get_command()

		if self.completion.should_auto_assist():
			self.completion.cycle(1)
			cmd = self.completion.mount_input()

		self.prompt_history.append(cmd)

		try:
			procris.service.execute(cmd, gtk_time)
		except names.InvalidName as e:
			messages.add_error(e.message)
			self.begin(gtk_time)

	#
	# UI handlers
	#
	def colon(self):
		self.set_command_mode()

	def enter(self, c_in):
		messages.clean()
		self.view.update()
