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
import gi
import signal
import re
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
		self.state = 'normal_mode'
		self.multiplier = ""
		self.should_clean_state = False
		self.configurations = Configurations()
		self.windows = Windows(self)
		self.view = NavigatorWindow(self, self.windows)
		self.view.connect("key-press-event", self._on_key_press)
		self.key_functions = {
				Gdk.KEY_l     : self.windows.navigate_right,
				Gdk.KEY_Right : self.windows.navigate_right,
				Gdk.KEY_j     : self.windows.navigate_down,
				Gdk.KEY_Down  : self.windows.navigate_down,
				Gdk.KEY_h     : self.windows.navigate_left,
				Gdk.KEY_Left  : self.windows.navigate_left,
				Gdk.KEY_k     : self.windows.navigate_up,
				Gdk.KEY_Up    : self.windows.navigate_up,
				Gdk.KEY_w     : self.windows.cycle,
				Gdk.KEY_colon : self.colon,
				Gdk.KEY_Return: self.enter,
				Gdk.KEY_Escape: self.escape
				}
		self.commands = [
			{ 'pattern' : re.compile("^(only|on)$"), 'f' : self.only },
			{ 'pattern' : re.compile("^\s*(buffers|ls)\s*$"), 'f' : self.buffers },
			{ 'pattern' : re.compile("^(buffer|b)\s*[0-9]+$\s*"), 'f' : self.open_buffer },
			{ 'pattern' : re.compile("^(buffer|b)\s*\w+$\s*"), 'f' : self.open_named_buffer }
		]

	def open(self):
		self.view.connect("focus-out-event", Gtk.main_quit)
		self.show_ui(0)
		Gtk.main()

	def start(self):
		self.view.connect("focus-out-event", self.hide_and_propagate_focus)
		signal.signal(signal.SIGINT, signal.SIG_DFL)
		signal.signal(signal.SIGTERM, signal.SIG_DFL)
		signal.signal(signal.SIGHUP, signal.SIG_DFL)
		hotkey = self.configurations.get_hotkey()
		Keybinder.init()
		if not Keybinder.bind(hotkey, self.handle_keybind, None):
			print("Could not bind the hotkey: " + hotkey)
			exit()

		print("vimwn is running and listening to " + hotkey)

		NavigatorStatus(self.configurations)

		Gtk.main()

	def handle_keybind(self, key, data):
		self.show_ui(Keybinder.get_current_event_time())

	def show_ui(self, time):
		self.windows.read_screen()
		self.view.show(time)

	def _popup_menu(self, status_icon, button, activate_time, menu):
		menu.popup(None, None, Gtk.StatusIcon.position_menu, status_icon, button, activate_time)

	def clear_state(self):
		self.should_clean_state = True

	#TODO remove, no need
	def _clear_state(self):
		self.state = 'normal_mode'
		self.reading_command = False
		self.multiplier = ""
		self.should_clean_state = False

	def open_window(self, window, time):
		self.should_clean_state = True
		window.activate_transient(time)

	def hide_and_propagate_focus(self, widget, event):
		self._clear_state()
		self.view.hide()
		return True;

	def get_current_event_time(self):
		gtk_event_time = Gtk.get_current_event_time()
		if gtk_event_time is not None:
			return gtk_event_time
		if Keybinder is not None:
			return Keybinder.get_current_event_time()
		return 0

	def _on_key_press(self, widget, event):
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
				if self.should_clean_state:
					self._clear_state()

	def on_command(self, pane_owner, current):
		cmd = self.view.entry.get_text()[1:]
		time = self.get_current_event_time()
		for command in self.commands:
			if command['pattern'].match(cmd):
				command['f'](cmd, time)
				break;
		self.reading_command = False

	def colon(self, keyval, time):
		self.reading_command = True
		self.view.show (time)

	def enter(self, keyval, time):
		self.state = 'normal_mode'
		self.reading_command = False
		self.view.show (time)

	def escape(self, keyval, time):
		self.reading_command = False
		self.state = 'normal_mode'
		self.view.hide()

	def only(self, cmd, time):
		for w in self.windows.visibles:
			if self.windows.active != w:
				w.minimize()
		self.open_window(self.windows.active, time)

	def buffers(self, cmd, time):
		self.state = 'listing_windows'
		self.reading_command = False
		self.view.show(time)

	def open_buffer(self, cmd, time):
		buffer_number = re.findall(r'\d+', cmd)[0]
		index = int(buffer_number) - 1
		self.open_window(self.windows.buffers[index], time)

	def open_named_buffer(self, cmd, time):
		window_title = re.findall(r'\s+\w.+', cmd.strip())[0].strip().lower()
		for w in self.windows.buffers:
			if window_title in w.get_name().lower():
				self.open_window(w, time)
				break;

