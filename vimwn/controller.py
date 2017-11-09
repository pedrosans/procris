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
import gi, signal, re, setproctitle, logging
gi.require_version('Gtk', '3.0')
gi.require_version("Keybinder", "3.0")
from gi.repository import Gtk, Gdk, Keybinder
from vimwn.view import NavigatorWindow
from vimwn.windows import Windows
from vimwn.environment import Configurations
from vimwn.status import NavigatorStatus

class Controller ():

	def __init__(self):
		self.reading_command = False
		self.listing_windows = False
		self.multiplier = ""
		self.status_message = None
		self.status_level = None
		self.configurations = Configurations()
		self.windows = Windows(self)
		self.view = NavigatorWindow(self, self.windows)
		self.view.connect("key-press-event", self.on_key_press)
		self.pending_action = None
		self.key_functions = {
				Gdk.KEY_Right : self.windows.navigate_right,
				Gdk.KEY_l     : self.windows.navigate_right,
				Gdk.KEY_L     : self.windows.move_right,
				Gdk.KEY_Down  : self.windows.navigate_down,
				Gdk.KEY_j     : self.windows.navigate_down,
				Gdk.KEY_J     : self.windows.move_down,
				Gdk.KEY_Left  : self.windows.navigate_left,
				Gdk.KEY_h     : self.windows.navigate_left,
				Gdk.KEY_H     : self.windows.move_left,
				Gdk.KEY_Up    : self.windows.navigate_up,
				Gdk.KEY_k     : self.windows.navigate_up,
				Gdk.KEY_K     : self.windows.move_up,
				Gdk.KEY_w     : self.windows.cycle,
				Gdk.KEY_o     : self.only_key_handler,
				Gdk.KEY_colon : self.colon,
				Gdk.KEY_Return: self.enter,
				Gdk.KEY_Escape: self.escape
				}
		self.commands = [
			{ 'pattern' : re.compile("^\s*(only|on)\s*$"), 'f' : self.only },
			{ 'pattern' : re.compile("^\s*(buffers|ls)\s*$"), 'f' : self.buffers },
			{ 'pattern' : re.compile("^\s*(buffer|b)\s*[0-9]+\s*$"), 'f' : self.open_indexed_buffer },
			{ 'pattern' : re.compile("^\s*(buffer|b)\s+\w+\s*$"), 'f' : self.open_named_buffer }
		]

	def _configure_ui_process_and_wait(self):
		setproctitle.setproctitle("vimwn")
		signal.signal(signal.SIGINT, signal.SIG_DFL)
		signal.signal(signal.SIGTERM, signal.SIG_DFL)
		signal.signal(signal.SIGHUP, signal.SIG_DFL)
		Gtk.main()

	def open(self):
		self.view.connect("focus-out-event", Gtk.main_quit)
		self.show_ui(0)
		self._configure_ui_process_and_wait()

	def start(self):
		self.view.connect("focus-out-event", self.hide_and_propagate_focus)
		Keybinder.init()
		hotkeys = self.configurations.get_hotkeys()
		logging.debug("Configuring hotkeys: " + hotkeys)
		for hotkey in hotkeys.split(","):
			bound = Keybinder.bind(hotkey, self.handle_keybind, None)
			if not bound:
				logging.error("Could not bind the hotkey: " + hotkey)
				exit(1)
			logging.debug("vimwn is istening to " + hotkey)

		NavigatorStatus(self.configurations)
		self._configure_ui_process_and_wait()

	def handle_keybind(self, key, data):
		self.show_ui(Keybinder.get_current_event_time())

	def show_ui(self, time):
		self.windows.read_screen()
		self.view.show(time)

	def clear_state(self):
		self.reading_command = False
		self.multiplier = ""
		self.status_message = None
		self.status_level = None

	def open_window(self, window, time):
		window.activate_transient(time)

	def hide_and_propagate_focus(self, widget, event):
		self.clear_state()
		self.listing_windows = False
		self.view.hide()
		self.windows.shutdown()
		return True;

	def get_current_event_time(self):
		gtk_event_time = Gtk.get_current_event_time()
		if gtk_event_time is not None:
			return gtk_event_time
		if Keybinder is not None:
			return Keybinder.get_current_event_time()
		return 0

	def on_key_press(self, widget, event):
		if event.keyval == Gdk.KEY_Escape:
			self.escape(None, None)
		if self.reading_command:
			return
		if Gdk.keyval_name(event.keyval).isdigit():
			self.multiplier = self.multiplier + Gdk.keyval_name(event.keyval)
			return
		if event.keyval in self.key_functions:
			function = self.key_functions[event.keyval]
			if function is not None:
				multiplier_int = int(self.multiplier) if self.multiplier else 1
				for i in range(multiplier_int):
					function(event.keyval, event.time)
				self.windows.syncronize_state(event.time)

	def on_command(self, pane_owner, current):
		if not self.reading_command:
			return
		cmd = self.view.entry.get_text()[1:]
		time = self.get_current_event_time()
		input_matches = False
		for command in self.commands:
			if command['pattern'].match(cmd):
				input_matches = True
				command['f'](cmd, time)
				break;
		if not input_matches:
			self.clear_state()
			self.status_message = 'Not an editor command: ' + cmd
			self.status_level = 'error'
			self.view.show (time)
		self.clear_state()

	def colon(self, keyval, time):
		self.reading_command = True
		self.view.show (time)

	def enter(self, keyval, time):
		self.listing_windows = False
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

	def buffers(self, cmd, time):
		self.listing_windows = True
		self.reading_command = False
		self.status_message = 'Press ENTER or type command to continue'
		self.status_level = 'info'
		self.view.show(time)

	def open_indexed_buffer(self, cmd, time):
		buffer_number = re.findall(r'\d+', cmd)[0]
		index = int(buffer_number) - 1
		if index < len(self.windows.buffers):
			self.open_window(self.windows.buffers[index], time)
		else:
			self.show_error_message('Buffer {} does not exist'.format(buffer_number), time)

	def open_named_buffer(self, cmd, time):
		window_title = re.findall(r'\s+\w+', cmd.strip())[0].strip().lower()
		print window_title
		matching_buffer = False
		for w in self.windows.buffers:
			if window_title in w.get_name().lower():
				self.open_window(w, time)
				matching_buffer = True
				break;
		if not matching_buffer:
			self.show_error_message('No matching buffer for ' + window_title, time)

	def show_error_message(self, message, time):
		self.clear_state()
		self.status_message = message
		self.status_level = 'error'
		self.view.show(time)

