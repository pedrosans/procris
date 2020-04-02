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
import gi, pocoy
import pocoy.messages as messages
import pocoy.names as names
import pocoy.state as configurations
import pocoy.service as service

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from pocoy.view import ReadingWindow
from pocoy.names import PromptHistory
from pocoy.wm import UserEvent
from pocoy.model import Windows, ActiveWindow
from pocoy.assistant import Completion

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
	active_window: ActiveWindow = None
	completions: Completion = None
	prompt_history: PromptHistory = PromptHistory()
	long = False
	command_mode = False
	cmd_handler_ids = []
	escape_clause_id: int = None

	def __init__(self, windows: Windows, active_window: ActiveWindow):
		self.windows = windows
		self.active_window = active_window
		self.completion = Completion(self.windows)
		self._create_and_install_view()

	def _create_and_install_view(self):
		self.view = ReadingWindow(self, self.windows, self.active_window)
		self.view.connect("key-press-event", self._window_key_press_callback)

	#
	# Lifecycle state API
	#
	def begin(self, time):
		self.reload()
		self.long = True
		self.view.present_and_focus(time)
		self.view.update()
		self.escape_clause_id = self.view.connect("focus-out-event", self.on_focus_out)

	def is_transient(self):
		return not self.long

	def make_transient(self):
		self.remove_focus_callback()
		self.long = False

	def end(self):
		self.remove_focus_callback()
		self.view.hide()
		messages.clean()

	#
	# State API
	#
	def reload(self, recreate_view=False, update_view=False):
		self.command_mode = False
		for handler_id in self.cmd_handler_ids:
			self.view.colon_prompt.disconnect(handler_id)
		self.cmd_handler_ids.clear()
		self.completion.clean()
		if recreate_view:
			self.view.close()
			self._create_and_install_view()
		if update_view:
			self.view.update()

	def remove_focus_callback(self):
		if self.escape_clause_id:
			self.view.disconnect(self.escape_clause_id)
			self.escape_clause_id = None

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
	def on_focus_out(self, widget, event):
		self.end()

	def _window_key_press_callback(self, widget, event):
		ctrl = (event.state & Gdk.ModifierType.CONTROL_MASK)

		if event.keyval == Gdk.KEY_Escape or (ctrl and event.keyval == Gdk.KEY_bracketleft):
			self.end()
			return

		if self.in_command_mode():
			return

		if event.keyval == Gdk.KEY_colon and not ctrl:
			self.set_command_mode()
			return True

		if event.keyval == Gdk.KEY_Return:
			messages.clean()
			self.view.update()
			return True

	def on_entry_key_release(self, widget: Gtk.Entry, event: Gdk.EventKey):
		if event.keyval in HINT_OPERATION_KEYS:
			return False

		if not self.view.colon_prompt.get_text().strip():
			self.reload(update_view=True)
			return True

		self.show_completions()

	def show_completions(self):

		if configurations.is_auto_hint():
			self.completion.search_for(UserEvent(text=self.view.get_command()))
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
			self.completion.search_for(UserEvent(text=self.view.get_command()))

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

	def on_prompt_input(self, pane_owner: Gtk.Entry, current):
		if not self.command_mode:
			return

		gtk_time = Gtk.get_current_event_time()
		cmd = self.view.get_command()

		if self.completion.should_auto_assist():
			self.completion.cycle(1)
			cmd = self.completion.mount_input()

		self.prompt_history.append(cmd)

		try:
			service.execute(cmd=cmd, timestamp=gtk_time, move_to_main_loop=False)
		except names.InvalidName as e:
			messages.add_error(e.message)
			self.begin(gtk_time)

	#
	# Commands
	#
	def show(self, user_event: UserEvent):
		if user_event and user_event.keyval:
			messages.prompt_placeholder = Gtk.accelerator_name(user_event.keyval, user_event.keymod)
		else:
			messages.prompt_placeholder = 'ESQ to close'

	def show_prompt(self, user_event: UserEvent):
		messages.clean()
		self.begin(user_event.time)
		self.set_command_mode()
		self.show_completions()

	def escape(self, c_in: UserEvent):
		messages.clean()
