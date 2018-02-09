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
from vimwn.status_line import StatusLine
from vimwn.command import Command

KEY_FUNCTIONS = {}

class Controller ():

	def __init__(self):
		self.configurations = Configurations()
		self.reading_command = False
		self.listing_windows = False
		self.multiplier = ""
		self.status_message = None
		self.status_level = None
		self.applications = Applications()
		self.windows = Windows(self)
		self.view = NavigatorWindow(self, self.windows)
		self.status_line = StatusLine(self)
		self.view.connect("key-press-event", self.on_window_key_press)
		self.view.entry.connect("key-press-event", self.status_line.on_entry_key_press)
		map_functions(self, self.windows)
		Command.map_commands(self, self.windows)

	def open(self):
		self.view.connect("focus-out-event", Gtk.main_quit)
		self.show_ui(0)
		Gtk.main()

	def listen_user_events(self):
		self.view.connect("focus-out-event", self.hide_and_propagate_focus)
		Keybinder.init()
		hotkeys = self.configurations.get_hotkeys()
		for hotkey in hotkeys.split(","):
			bound = Keybinder.bind(hotkey, self.handle_keybind, None)
			if not bound:
				print("Could not bind the hotkey: " + hotkey, file=sys.stderr)
				return False
		print("Listening keys: '{}' pid: {} ".format( hotkeys, os.getpid()))
		return True

	def handle_keybind(self, key, data):
		self.show_ui(Keybinder.get_current_event_time())

	def show_ui(self, time):
		self.windows.read_screen()
		self.view.show(time)

	def clear_state(self):
		self.clear_command_ui_state()
		self.listing_windows = False

	def clear_command_ui_state(self):
		self.reading_command = False
		self.multiplier = ""
		self.status_message = None
		self.status_level = None

	def open_window(self, window, time):
		window.activate_transient(time)

	def hide_and_propagate_focus(self, widget, event):
		self.view.hide()
		self.clear_state()
		return True;

	def get_current_event_time(self):
		gtk_event_time = Gtk.get_current_event_time()
		if gtk_event_time is not None:
			return gtk_event_time
		if Keybinder is not None:
			return Keybinder.get_current_event_time()
		return 0

	def on_window_key_press(self, widget, event):
		if event.keyval == Gdk.KEY_Escape:
			self.escape(None, None)
		if self.reading_command:
			return False
		if Gdk.keyval_name(event.keyval).isdigit():
			self.multiplier = self.multiplier + Gdk.keyval_name(event.keyval)
			return
		if event.keyval in KEY_FUNCTIONS:
			function = KEY_FUNCTIONS[event.keyval]
			if function is not None:
				multiplier_int = int(self.multiplier) if self.multiplier else 1
				for i in range(multiplier_int):
					function(event.keyval, event.time)
				self.windows.commit_navigation(event.time)

	def edit(self, cmd, time):
		name = Command.extract_text_parameter(cmd)
		possible_apps = self.applications.query_names(name)
		if len(possible_apps) == 1:
			try:
				self.applications.launch_by_name(possible_apps[0])
				self.view.hide()
			except GLib.GError as exc:
				self.show_error_message('Error launching ' + name, time)
		else:
			self.show_error_message('No matching applicaiton for ' + name, time)

	def on_command(self, pane_owner, current):
		if not self.reading_command:
			return
		cmd = self.view.get_command()
		time = self.get_current_event_time()
		command = Command.find_command(cmd)
		if command:
			command.function(cmd, time)
		else:
			self.show_error_message('Not an editor command: ' + cmd, time)

	def colon(self, keyval, time):
		self.reading_command = True
		self.view.show (time)

	def enter(self, keyval, time):
		self.refresh_view(time)

	def refresh_view(self, time):
		self.clear_state()
		self.view.show (time)

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
		print('??????????')

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
	#TODO: rename close to delete
	def close_current_buffer(self, cmd, time):
		if self.windows.active:
			self.windows.remove(self.windows.active, time)
			self.refresh_view(time)
		else:
			self.show_error_message('There is no active window')

	def close_indexed_buffer(self, cmd, time):
		buffer_number = Command.extract_number_parameter(cmd)
		index = int(buffer_number) - 1
		if index < len(self.windows.buffers):
			self.windows.remove(self.windows.buffers[index], time)
			self.refresh_view(time)
		else:
			self.show_error_message('Buffer {} does not exist'.format(buffer_number), time)

	def close_named_buffer(self, cmd, time):
		window_title = Command.extract_text_parameter(cmd)
		w = self.windows.find_by_name(window_title)
		if w:
			self.windows.remove(w, time)
			self.refresh_view(time)
		else:
			self.show_error_message('No matching buffer for ' + window_title, time)

	def quit(self, keyval, time):
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
	KEY_FUNCTIONS[Gdk.KEY_o      ] = controller.only_key_handler
	KEY_FUNCTIONS[Gdk.KEY_colon  ] = controller.colon
	KEY_FUNCTIONS[Gdk.KEY_Return ] = controller.enter
	KEY_FUNCTIONS[Gdk.KEY_Escape ] = controller.escape
