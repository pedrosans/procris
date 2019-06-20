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
import gi, signal, re, os, sys, logging
gi.require_version('Gtk', '3.0')
gi.require_version("Keybinder", "3.0")
from gi.repository import Gtk, Gdk, Keybinder, GLib
from vimwn.view import NavigatorWindow
from vimwn.windows import Windows
from vimwn.environment import Configurations
from vimwn.applications import Applications
from vimwn.terminal import Terminal
from vimwn.status_line import StatusLine
from vimwn.command import Command
from vimwn.status import StatusIcon

KEY_FUNCTIONS = {}


# TODO chain commands
class Controller:

	def __init__(self, as_service=None):
		self.status_icon = None
		self.running_as_service = as_service
		self.configurations = Configurations()
		self.applications = Applications()
		self.terminal = Terminal()
		self.windows = Windows(self)
		self.status_line = StatusLine(self)
		map_functions(self, self.windows)
		Command.map_commands(self, self.windows)
		self._initialize_view()
		self.clear_state()

	def indicate_running_service(self, service):
		self.status_icon = StatusIcon(self.configurations)
		self.status_icon.activate(service)

	def _initialize_view(self):
		self.view = NavigatorWindow(self, self.windows)
		self.view.connect("key-press-event", self.on_window_key_press)
		self.view.entry.connect("key-release-event", self.on_entry_key_release)
		self.view.entry.connect("key-press-event", self.on_entry_key_press)
		self.view.entry.connect("activate", self.on_command, None)
		if self.running_as_service:
			self.view.connect("focus-out-event", self.hide_ui)
		else:
			self.view.connect("focus-out-event", Gtk.main_quit)
		# https://lazka.github.io/pgi-docs/GLib-2.0/functions.html#GLib.log_set_handler
		GLib.log_set_handler(None, GLib.LogLevelFlags.LEVEL_WARNING, self.log_function)
		GLib.log_set_handler(None, GLib.LogLevelFlags.LEVEL_ERROR, self.log_function)
		GLib.log_set_handler(None, GLib.LogLevelFlags.LEVEL_CRITICAL, self.log_function)

	def reload(self, cmd, time):
		self.configurations.reload()
		self.applications.reload()
		self.terminal.reload()
		self.view.close()
		self._initialize_view()
		self.refresh_view(time)
		if self.status_icon:
			self.status_icon.reload()

	def open(self):
		self.show_ui(0)
		Gtk.main()

	def listen_user_events(self):
		normal_prefix = self.configurations.get_prefix_key()
		command_prefix = self.configurations.get_command_prefix_key()
		Keybinder.init()

		for hotkey in normal_prefix.split(","):
			if not Keybinder.bind(hotkey, self.handle_prefix_key, None):
				raise Exception("Could not bind the hotkey: " + hotkey)

		if command_prefix:
			bound = Keybinder.bind(command_prefix, self.handle_command_prefix_key, None)
			if not bound:
				raise Exception("Could not bind the command prefix key: " + command_prefix)

		print("Listening keys: '{}', '{}' pid: {} ".format(normal_prefix, command_prefix, os.getpid()))

	def log_function(self, log_domain, log_level, message):
		if log_level is GLib.LogLevelFlags.LEVEL_WARNING:
			logging.warning('GLib log[%s]:%s',log_domain, message)
			self.view.show_warning(message)
		elif log_level in (GLib.LogLevelFlags.LEVEL_ERROR, GLib.LogLevelFlags.LEVEL_CRITICAL):
			logging.error('GLib log[%s]:%s',log_domain, message)
			self.view.show_error(message)
		else:
			raise Exception(message)

	def handle_prefix_key(self, key, data):
		self.show_ui(Keybinder.get_current_event_time())

	def handle_command_prefix_key(self, key, data):
		self.reading_command = True
		self.show_ui(Keybinder.get_current_event_time())
		self.view.set_command('')
		#if self.configurations.is_auto_hint():
		#	self.status_line.auto_hint('')

	def show_ui(self, time):
		self.windows.read_screen()
		if self.windows.read_itself:
			self.windows.cycle(None, None)
			self.windows.commit_navigation(time)
		else:
			self.view.show(time)

	def hide_ui(self, widget, event):
		self.view.hide()
		self.clear_state()
		return True;

	#TODO rename to refresh_ui
	def refresh_view(self, time):
		"""
		Repaints the UI at its default state
		"""
		self.clear_state()
		self.view.show (time)

	def clear_state(self):
		self.clear_command_ui_state()
		self.listing_windows = False

	def clear_command_ui_state(self):
		self.status_line.clear_state()
		self.reading_command = False
		self.reading_multiple_commands = False
		self.multiplier = ""
		self.status_message = None
		self.status_level = None
		self.status_message = '^W'

	def open_window(self, window, time):
		window.activate_transient(time)

	def get_current_event_time(self):
		gtk_event_time = Gtk.get_current_event_time()
		if gtk_event_time is not None:
			return gtk_event_time
		if Keybinder is not None:
			return Keybinder.get_current_event_time()
		return 0

	def on_window_key_press(self, widget, event):
		ctrl = (event.state & Gdk.ModifierType.CONTROL_MASK)
		if event.keyval == Gdk.KEY_Escape or (ctrl and event.keyval == Gdk.KEY_bracketleft) :
			self.escape(None, None)
		if self.reading_command:
			return False
		gdk_key = Gdk.keyval_name(event.keyval)
		if gdk_key and gdk_key.isdigit():
			self.multiplier = self.multiplier + Gdk.keyval_name(event.keyval)
			return
		if event.keyval in KEY_FUNCTIONS:
			multiplier_int = int(self.multiplier) if self.multiplier else 1
			for i in range(multiplier_int):
				KEY_FUNCTIONS[event.keyval](event.keyval, event.time)
			#TODO error message if not staging a change?
			self.windows.commit_navigation(event.time)

	#TODO no auto hints for commands to prevent the 'b' <> 'bdelete' misslead
	#TODO no auto hint if a command is alreay a match
	def on_entry_key_release(self, widget, event):
		if event.keyval in [
				Gdk.KEY_Shift_L, Gdk.KEY_Shift_R, Gdk.KEY_Return,
				Gdk.KEY_Tab, Gdk.KEY_ISO_Left_Tab,
				Gdk.KEY_Left, Gdk.KEY_Up,
				Gdk.KEY_Right, Gdk.KEY_Down
				]:
			return False

		if not self.view.entry.get_text().strip():
			self.clear_command_ui_state()
			self.view.show(event.time)
			return False

		if not self.view.get_command().strip():
			self.status_line.clear_state()
			self.view.clear_hints_state()
			return False

		if self.configurations.is_auto_hint():
			self.status_line.auto_hint(self.view.get_command())
			if self.status_line.hinting:
				index = -1
				if self.configurations.is_auto_select_first_hint():
					index = 0
				self.view.hint(self.status_line.hints, index)
			else:
				self.view.clear_hints_state()
		else:
			self.status_line.clear_state()
			self.view.clear_hints_state()
			return False

	def on_entry_key_press(self, widget, event):
		if event.keyval in [Gdk.KEY_Shift_L, Gdk.KEY_Shift_R, Gdk.KEY_Return]:
			return False

		if self.status_line.hinting:
			if event.keyval in [Gdk.KEY_Left, Gdk.KEY_Up]:
				self.show_highlights(-1)
				return True
			elif event.keyval in [Gdk.KEY_Right, Gdk.KEY_Down]:
				self.show_highlights(1)
				return True
			elif event.keyval in [Gdk.KEY_Tab, Gdk.KEY_ISO_Left_Tab]:
				if event.state & Gdk.ModifierType.SHIFT_MASK:
					self.show_highlights(-1)
				else:
					self.show_highlights(1)
				return True

		if event.keyval in [Gdk.KEY_Up, Gdk.KEY_Down]:
			return True

		text = self.view.get_command()
		if event.keyval in [Gdk.KEY_Tab, Gdk.KEY_ISO_Left_Tab]:
			if event.state & Gdk.ModifierType.SHIFT_MASK:
				self.status_line.hint(text)
				self.show_highlights(-1)
			else:
				self.status_line.hint(text)
				self.show_highlights(1)
			return True

	def show_highlights(self, direction):
		if not self.status_line.hinting:
			return
		self.status_line.cycle(direction)
		if len(self.status_line.hints) == 1:
			self.view.clear_hints_state()
		elif len(self.status_line.hints) > 1:
			self.view.hint(self.status_line.hints, self.status_line.highlight_index)
		self.view.set_command(self.status_line.get_highlighted_hint())

	def on_command(self, pane_owner, current):
		if not self.reading_command:
			return

		cmd = self.view.get_command()

		if (self.configurations.is_auto_select_first_hint()
				and self.status_line.highlight_index == -1
				and self.status_line.hinting
				and len(self.status_line.hints) > 0 ):
			self.status_line.highlight_index = 0
			cmd = self.status_line.get_highlighted_hint()

		if Command.has_multiple_commands(cmd):
			self.reading_multiple_commands = True
			#TODO iterate multiple commands

		time = self.get_current_event_time()
		command = Command.get_matching_command(cmd)

		if command:
			command.function(cmd, time)
		else:
			self.show_error_message('Not an editor command: ' + cmd, time)

	def edit(self, cmd, time):
		name = Command.extract_text_parameter(cmd)
		if name == None or not name.strip():
			self.view.hide()
			return

		app_name = None
		if self.applications.has_perfect_match(name.strip()):
			app_name = name.strip()

		possible_apps = self.applications.find_by_name(name)
		if possible_apps:
			app_name = possible_apps

		if app_name:
			try:
				self.applications.launch_by_name(app_name)
				self.view.hide()
			except GLib.GError as exc:
				self.show_error_message('Error launching ' + name, time)
		elif len(possible_apps) == 0:
			self.show_error_message('No matching application for ' + name, time)
		else:
			self.show_error_message('More than one application matches: ' + name, time)

	def bang(self, cmd, time):
		vim_cmd = Command.extract_vim_command(cmd)
		cmd = cmd.replace(vim_cmd, '', 1)
		self.terminal.execute(cmd)
		self.view.hide()

	def colon(self, keyval, time):
		self.reading_command = True
		self.view.show (time)

	def enter(self, keyval, time):
		self.refresh_view(time)

	def escape(self, keyval, time):
		self.view.hide()

	def only_key_handler(self, keyval, time):
		self.only(None, time)

	def only(self, cmd, time):
		for w in self.windows.visibles:
			if self.windows.active != w:
				w.minimize()
		self.open_window(self.windows.active, time)

	def centralize(self, cmd, time):
		self.windows.centralize_active_window()
		self.windows.commit_navigation(time)

	def maximize(self, cmd, time):
		self.windows.maximize_active_window()
		self.windows.commit_navigation(time)

	def buffers(self, cmd, time):
		self.listing_windows = True
		self.reading_command = False
		self.status_message = 'Press ENTER or type command to continue'
		self.status_level = 'info'
		self.view.show(time)

	def buffer(self, cmd, time):
		"""
		vim original behaviour is to take the focus away from the command entry,
		but given this focus change can't be clearly signalized, just ignoring
		the command will cause to focus to remain at the command entry, which
		is a good alternative
		"""

	def open_indexed_buffer(self, cmd, time):
		buffer_number = Command.extract_number_parameter(cmd)
		index = int(buffer_number) - 1
		if index < len(self.windows.buffers):
			self.open_window(self.windows.buffers[index], time)
		else:
			self.show_error_message('Buffer {} does not exist'.format(buffer_number), time)

	def open_named_buffer(self, cmd, time):
		window_title = Command.extract_text_parameter(cmd)
		w = self.windows.find_by_name(window_title)
		if w:
			self.open_window(w, time)
		else:
			self.show_error_message('No matching buffer for ' + window_title, time)

	#TODO: remove duplicated tokenizer
	#TODO: close vimwn ui after the command?
	def quit_current_window(self, keyval, time):
		self.delete_current_buffer(None, time)

	def delete_current_buffer(self, cmd, time):
		if self.windows.active:
			self.windows.remove(self.windows.active, time)
			self.view.hide()
		else:
			self.show_error_message('There is no active window')

	def delete_indexed_buffer(self, cmd, time):
		to_delete = []
		for number in re.findall(r'\d+', cmd):
			index = int(number) - 1
			if index < len(self.windows.buffers):
				to_delete.append(self.windows.buffers[index])
			else:
				self.show_error_message('No buffers were deleted', time)
				return
		for window in to_delete:
			self.windows.remove(window, time)
			self.view.hide()

	def delete_named_buffer(self, cmd, time):
		window_title = Command.extract_text_parameter(cmd)
		w = self.windows.find_by_name(window_title)
		if w:
			self.windows.remove(w, time)
			self.view.hide()
		else:
			self.show_error_message('No matching buffer for ' + window_title, time)

	def quit(self, cmd, time):
		self.view.hide()

	def show_error_message(self, message, time):
		self.clear_command_ui_state()
		self.status_message = message
		self.status_level = 'error'
		self.view.show(time)

def map_functions(controller, windows):
	if len(KEY_FUNCTIONS) > 0:
		raise Exception('Functions were already mapped')
	KEY_FUNCTIONS[Gdk.KEY_Right  ] = windows.navigate_right
	KEY_FUNCTIONS[Gdk.KEY_l      ] = windows.navigate_right
	KEY_FUNCTIONS[Gdk.KEY_L      ] = windows.move_right
	KEY_FUNCTIONS[Gdk.KEY_Down   ] = windows.navigate_down
	KEY_FUNCTIONS[Gdk.KEY_j      ] = windows.navigate_down
	KEY_FUNCTIONS[Gdk.KEY_J      ] = windows.move_down
	KEY_FUNCTIONS[Gdk.KEY_Left   ] = windows.navigate_left
	KEY_FUNCTIONS[Gdk.KEY_h      ] = windows.navigate_left
	KEY_FUNCTIONS[Gdk.KEY_H      ] = windows.move_left
	KEY_FUNCTIONS[Gdk.KEY_Up     ] = windows.navigate_up
	KEY_FUNCTIONS[Gdk.KEY_k      ] = windows.navigate_up
	KEY_FUNCTIONS[Gdk.KEY_K      ] = windows.move_up
	KEY_FUNCTIONS[Gdk.KEY_less   ] = windows.decrease_width
	KEY_FUNCTIONS[Gdk.KEY_greater] = windows.increase_width
	KEY_FUNCTIONS[Gdk.KEY_equal  ] = windows.equalize
	KEY_FUNCTIONS[Gdk.KEY_w      ] = windows.cycle
	KEY_FUNCTIONS[Gdk.KEY_p      ] = windows.navigate_to_previous
	KEY_FUNCTIONS[Gdk.KEY_q      ] = controller.quit_current_window
	KEY_FUNCTIONS[Gdk.KEY_o      ] = controller.only_key_handler
	KEY_FUNCTIONS[Gdk.KEY_colon  ] = controller.colon
	KEY_FUNCTIONS[Gdk.KEY_Return ] = controller.enter
	KEY_FUNCTIONS[Gdk.KEY_Escape ] = controller.escape
	KEY_FUNCTIONS[Gdk.KEY_bracketleft ] = controller.escape
