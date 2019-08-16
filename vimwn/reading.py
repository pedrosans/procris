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
import gi, re, time, traceback
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from vimwn.view import NavigatorWindow
from vimwn.windows import Windows
from vimwn.environment import Configurations
from vimwn.applications import Applications
from vimwn.terminal import Terminal
from vimwn.hint import HintStatus
from vimwn.command import Command
from vimwn.command import CommandHistory
from vimwn.message import Messages
from vimwn.command import CommandInput

HINT_LAUNCH_KEYS = [Gdk.KEY_Tab, Gdk.KEY_ISO_Left_Tab]
HINT_LEFT = [Gdk.KEY_Left]
HINT_RIGHT = [Gdk.KEY_Right]
HINT_NAVIGATION_KEYS = HINT_LAUNCH_KEYS + HINT_LEFT + HINT_RIGHT
HINT_OPERATION_KEYS = [Gdk.KEY_Shift_L, Gdk.KEY_Shift_R, Gdk.KEY_Return] + HINT_NAVIGATION_KEYS

HISTORY_NAVIGATION_KEYS = [Gdk.KEY_Up, Gdk.KEY_Down]


# TODO chain commands
# TODO hint line shows only '>' if you type :b <long window title start>
class Reading:

	def __init__(self, service=None):
		self.view = self.pressed_key = None
		self.last_out = self.last_start = 0
		self.reading_command = self.multiplier = None
		self.running_as_service = True if service else False
		self.service = service
		self.windows = Windows(self)
		self.configurations = Configurations()
		self.applications = Applications()
		self.terminal = Terminal()
		self.hint_status = HintStatus(self)
		self.messages = Messages(self, self.windows)
		self.command_history = CommandHistory()
		self.create_and_install_view()
		self.clean_command_state()
		self.messages.clean()
		Command.map_to(self, self.windows)

	def clean_key_combination_state(self):
		self.multiplier = ''

	def clean_command_state(self):
		self.hint_status.clear_state()
		self.reading_command = False

	def create_and_install_view(self):
		if self.view:
			self.view.close()
		self.view = NavigatorWindow(self, self.windows, self.messages)
		self.view.entry.connect("key-release-event", self.on_entry_key_release)
		self.view.entry.connect("key-press-event", self.on_entry_key_press)
		self.view.entry.connect("activate", self.on_command, None)
		self.view.connect("key-press-event", self.on_window_key_press)
		self.view.connect("key-release-event", self.on_window_key_release)
		self.view.connect("focus-out-event", Gtk.main_quit if not self.service else self.end)
		self.view.connect("focus-in-event", self.focus_in)

	def start(self, event_time=0):
		self.last_start = time.time()
		time_since_focus_out = self.last_start - self.last_out

		if time_since_focus_out < 0.1:
			# TODO test if the prefix is ctrl-w
			self.windows.cycle(None)
			self.windows.commit_navigation(event_time)
			self.set_normal_mode()
			return

		if not self.view.get_window():
			self.view.show(event_time)

		self.view.present_with_time(event_time)
		self.view.get_window().focus(event_time)

		if not self.running_as_service:
			Gtk.main()

	def end(self, widget, event):
		self.last_out = time.time()
		self.set_normal_mode()

	def set_normal_mode(self):
		self.view.hide()
		self.messages.clean()
		self.clean_command_state()
		self.pressed_key = None

	def set_key_mode(self, event_time, error_message=None):
		self.windows.read_screen()
		if error_message:
			self.messages.add(error_message, 'error')
		self.clean_command_state()
		self.clean_key_combination_state()
		self.view.show(event_time)

	def set_command_mode(self, time):
		self.reading_command = True
		self.view.show(time)

	#
	# CALLBACKS
	#
	def focus_in(self, widget, event):
		self.set_key_mode(event.get_time())

	def on_window_key_release(self, widget, event):
		if not self.pressed_key or self.pressed_key != event.keyval:
			# print('got -> {}'.format(Gdk.keyval_name(event.keyval)))
			self.on_window_key(event)
		self.pressed_key = None

	def on_window_key_press(self, widget, event):
		self.pressed_key = event.keyval
		# print('got <- {}'.format(Gdk.keyval_name(event.keyval)))
		self.on_window_key(event)

	def on_window_key(self, event):
		ctrl = (event.state & Gdk.ModifierType.CONTROL_MASK)
		key_name = Gdk.keyval_name(event.keyval)

		if event.keyval == Gdk.KEY_Escape or (ctrl and event.keyval == Gdk.KEY_bracketleft):
			self.escape(None)
			return

		if self.reading_command:
			return

		if key_name and key_name.isdigit():
			self.multiplier = self.multiplier + key_name
			return

		if event.keyval in Command.KEY_MAP:
			multiplier_int = int(self.multiplier) if self.multiplier else 1
			for i in range(multiplier_int):
				Command.KEY_MAP[event.keyval].function(CommandInput(time=event.time, keyval=event.keyval))
			self.windows.commit_navigation(event.time)

	def on_entry_key_release(self, widget, event):
		if event.keyval in HINT_OPERATION_KEYS:
			return False

		if not self.view.entry.get_text().strip():
			self.set_key_mode(event.time)
			return True

		if self.configurations.is_auto_hint():
			self.hint_status.hint(CommandInput(text=self.view.get_command()).parse())
		else:
			self.hint_status.clear_state()

		if self.hint_status.hinting:
			self.view.hint(self.hint_status.hints, self.hint_status.highlight_index, self.configurations.is_auto_select_first_hint())
		else:
			self.view.clean_hints()

	def on_entry_key_press(self, widget, event):
		if event.keyval in HISTORY_NAVIGATION_KEYS:
			self.command_history.navigate_history(-1 if event.keyval == Gdk.KEY_Up else 1, self.view.get_command())
			self.view.set_command(self.command_history.current_command())
			self.view.clean_hints()
			self.hint_status.clear_state()
			return True
		else:
			self.command_history.reset_history_pointer()

		if event.keyval not in HINT_NAVIGATION_KEYS:
			return False

		if not self.hint_status.hinting and event.keyval in HINT_LAUNCH_KEYS:
			self.hint_status.hint(CommandInput(text=self.view.get_command()).parse())

		if self.hint_status.hinting:
			shift_mask = event.state & Gdk.ModifierType.SHIFT_MASK
			right = event.keyval in HINT_RIGHT or (event.keyval in HINT_LAUNCH_KEYS and not shift_mask )
			self.hint_status.cycle(1 if right else -1)
			if len(self.hint_status.hints) == 1:
				self.view.clean_hints()
			else:
				self.view.hint(self.hint_status.hints, self.hint_status.highlight_index, self.configurations.is_auto_select_first_hint())
			self.view.set_command(self.hint_status.mount_input())

		return True

	def on_command(self, pane_owner, current):
		if not self.reading_command:
			return

		time = Gtk.get_current_event_time()
		cmd = self.view.get_command()
		command_input = CommandInput(time=time, text=cmd).parse()

		self.command_history.append(cmd)

		if (self.configurations.is_auto_select_first_hint()
				and self.hint_status.highlight_index == -1
				and self.hint_status.hinting ):
			self.hint_status.cycle(1)
			cmd = self.hint_status.mount_input()

		if Command.has_multiple_commands(cmd):
			raise Exception('TODO: iterate multiple commands')

		command = Command.get_matching_command(cmd)

		if command:
			try:
				command.function(command_input)
				self.windows.commit_navigation(time)
			except Exception as inst:
				msg = 'ERROR ({}) executing: {}'.format(str(inst), command_input.text)
				print(traceback.format_exc())
				self.set_key_mode(time, error_message=msg)
		else:
			self.set_key_mode(time, error_message='Not an editor command: ' + cmd)

	#
	# COMMANDS
	#
	def reload(self, c_in):
		self.configurations.reload()
		self.applications.reload()
		self.terminal.reload()
		self.messages.clean()
		self.create_and_install_view()
		self.view.present_with_time(c_in.time)
		self.set_key_mode(c_in.time)
		if self.running_as_service:
			self.service.reload()

	def edit(self, c_in):
		name = Command.extract_text_parameter(c_in.text)
		if not name or not name.strip():
			self.set_normal_mode()
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
				self.set_normal_mode()
			except GLib.GError as exc:
				self.set_key_mode(time, error_message='Error launching ' + name)
		elif len(possible_apps) == 0:
			self.set_key_mode(time, error_message='No matching application for ' + name)
		else:
			self.set_key_mode(time, error_message='More than one application matches: ' + name)

	def bang(self, c_in):
		cmd = c_in.vim_command_parameter
		if not cmd:
			self.set_key_mode(time, error_message='ERROR: empty command')
			return
		stdout, stderr = self.terminal.execute(cmd)
		if stdout:
			for line in stdout.splitlines():
				self.messages.add(line, None)
		if stderr:
			for line in stderr.splitlines():
				self.messages.add(line, 'error')
		self.set_key_mode(c_in.time)

	def colon(self, c_in):
		self.set_command_mode(c_in.time)

	def enter(self, c_in):
		self.messages.clean()
		self.set_key_mode(c_in.time)

	def escape(self, c_in):
		self.set_normal_mode()

	def quit(self, c_in):
		if self.windows.active:
			self.windows.active.minimize()
			self.set_normal_mode()
		else:
			self.set_key_mode(c_in.time, error_message='No active window')

	def buffers(self, c_in):
		self.messages.list_buffers()
		self.set_key_mode(c_in.time)

	def debug(self, c_in):
		self.messages.add(self.windows.get_metadata_resume(), None)
		self.set_key_mode(c_in.time)

	def buffer(self, c_in):
		self.set_key_mode(c_in.time)

	def open_indexed_buffer(self, c_in):
		buffer_number = Command.extract_number_parameter(c_in.text)
		index = int(buffer_number) - 1
		if index < len(self.windows.buffers):
			self.windows.show(self.windows.buffers[index])
		else:
			self.set_key_mode(time, error_message='Buffer {} does not exist'.format(buffer_number))

	def open_named_buffer(self, c_in):
		window_title = Command.extract_text_parameter(c_in.text)
		w = self.windows.find_by_name(window_title)
		if w:
			self.windows.show(w)
		else:
			self.set_key_mode(c_in.time, error_message='No matching buffer for ' + window_title)

	def delete_current_buffer(self, c_in):
		if self.windows.active:
			self.windows.remove(self.windows.active, c_in.time)
			self.set_normal_mode()
		else:
			self.set_key_mode(c_in.time, error_message='There is no active window')

	def delete_indexed_buffer(self, c_in):
		to_delete = []
		for number in re.findall(r'\d+', c_in.text):
			index = int(number) - 1
			if index < len(self.windows.buffers):
				to_delete.append(self.windows.buffers[index])
			else:
				self.set_key_mode(c_in.time, error_message='No buffers were deleted')
				return
		for window in to_delete:
			self.windows.remove(window, c_in.time)
		self.set_normal_mode()

	def delete_named_buffer(self, c_in):
		window_title = Command.extract_text_parameter(c_in.text)
		w = self.windows.find_by_name(window_title)
		if w:
			self.windows.remove(w, c_in.time)
			self.set_normal_mode()
		else:
			self.set_key_mode(c_in.time, error_message='No matching buffer for ' + window_title)

