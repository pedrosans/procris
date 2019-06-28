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
import gi, re
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from vimwn.view import NavigatorWindow
from vimwn.windows import Windows
from vimwn.environment import Configurations
from vimwn.applications import Applications
from vimwn.terminal import Terminal
from vimwn.hint import HintStatus
from vimwn.command import Command
from vimwn.message import Messages


# TODO chain commands
# TODO hint line shows only '>' if you type :b <long window title start>
class Reading:

	def __init__(self, service=None):
		self.view = None
		# TODO: remove variable e track modes: normal, window, command
		self.reading_command = self.multiplier = None
		self.running_as_service = True if service else False
		self.service = service
		self.windows = Windows(self)
		self.configurations = Configurations()
		self.applications = Applications()
		self.terminal = Terminal()
		self.hint_status = HintStatus(self)
		self.messages = Messages(self, self.windows)
		self.install_callbacks()
		self.clean_command_state()
		self.messages.clean()
		Command.map_to(self, self.windows)

	def clean_command_state(self):
		self.hint_status.clear_state()
		self.reading_command = False
		self.multiplier = ''

	def install_callbacks(self):
		if self.view:
			self.view.close()
		self.view = NavigatorWindow(self, self.windows, self.messages)
		self.view.connect("key-press-event", self.on_window_key_press)
		self.view.entry.connect("key-release-event", self.on_entry_key_release)
		self.view.entry.connect("key-press-event", self.on_entry_key_press)
		self.view.entry.connect("activate", self.on_command, None)
		self.view.connect("focus-out-event", Gtk.main_quit if not self.service else self.end)

	def start(self, time=0):
		self.windows.read_screen()
		# TODO test if read itself at the top
		# TODO test if the prefix is ctrl-w
		if self.windows.read_itself:
			self.windows.cycle(None, None)
			self.windows.commit_navigation(time)
		else:
			self.view.show(time)
		if not self.running_as_service:
			Gtk.main()

	def end(self, *args):
		self.set_normal_mode()

	def set_normal_mode(self):
		self.view.hide()
		self.messages.clean()
		self.clean_command_state()

	def set_window_command_mode(self, time, error_message=None):
		if error_message:
			self.messages.add(error_message, 'error')
		self.clean_command_state()
		self.view.show(time)

	def set_command_mode(self, time):
		self.reading_command = True
		self.view.show(time)

	#
	# CALLBACKS
	#
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
		if event.keyval in Command.KEY_MAP:
			multiplier_int = int(self.multiplier) if self.multiplier else 1
			for i in range(multiplier_int):
				Command.KEY_MAP[event.keyval].function(event.keyval, event.time)
			# TODO error message if not staging a change?
			self.windows.commit_navigation(event.time)

	# TODO no auto hints for commands to prevent the 'b' <> 'bdelete' misslead
	# TODO no auto hint if a command is alreay a match
	def on_entry_key_release(self, widget, event):
		if event.keyval in [
				Gdk.KEY_Shift_L, Gdk.KEY_Shift_R, Gdk.KEY_Return,
				Gdk.KEY_Tab, Gdk.KEY_ISO_Left_Tab,
				Gdk.KEY_Left, Gdk.KEY_Up,
				Gdk.KEY_Right, Gdk.KEY_Down
				]:
			return False

		if not self.view.entry.get_text().strip():
			self.set_window_command_mode(event.time)
			return False

		if not self.view.get_command().strip():
			self.hint_status.clear_state()
			self.view.clean_hints()
			return False

		if self.configurations.is_auto_hint():
			self.hint_status.auto_hint(self.view.get_command())
			if self.hint_status.hinting:
				index = -1
				if self.configurations.is_auto_select_first_hint():
					index = 0
				self.view.hint(self.hint_status.hints, index)
			else:
				self.view.clean_hints()
		else:
			self.hint_status.clear_state()
			self.view.clean_hints()
			return False

	def on_entry_key_press(self, widget, event):
		if event.keyval in [Gdk.KEY_Shift_L, Gdk.KEY_Shift_R, Gdk.KEY_Return]:
			return False

		if self.hint_status.hinting:
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
				self.hint_status.hint(text)
				self.show_highlights(-1)
			else:
				self.hint_status.hint(text)
				self.show_highlights(1)
			return True

	def show_highlights(self, direction):
		if not self.hint_status.hinting:
			return
		self.hint_status.cycle(direction)
		if len(self.hint_status.hints) == 1:
			self.view.clean_hints()
		elif len(self.hint_status.hints) > 1:
			self.view.hint(self.hint_status.hints, self.hint_status.highlight_index)
		self.view.set_command(self.hint_status.get_highlighted_hint())

	def on_command(self, pane_owner, current):
		if not self.reading_command:
			return

		cmd = self.view.get_command()

		if (self.configurations.is_auto_select_first_hint()
				and self.hint_status.highlight_index == -1
				and self.hint_status.hinting
				and len(self.hint_status.hints) > 0):
			self.hint_status.highlight_index = 0
			cmd = self.hint_status.get_highlighted_hint()

		if Command.has_multiple_commands(cmd):
			raise Exception('TODO: iterate multiple commands')

		time = Gtk.get_current_event_time()
		command = Command.get_matching_command(cmd)

		if command:
			command.function(cmd, time)
		else:
			self.set_window_command_mode(time, error_message='Not an editor command: ' + cmd)

	#
	# COMMANDS
	#
	def reload(self, cmd, time):
		self.configurations.reload()
		self.applications.reload()
		self.terminal.reload()
		self.install_callbacks()
		self.messages.clean()
		self.set_window_command_mode(time)
		if self.running_as_service:
			self.service.reload()

	def edit(self, cmd, time):
		name = Command.extract_text_parameter(cmd)
		if name == None or not name.strip():
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
				self.set_window_command_mode(time, error_message='Error launching ' + name)
		elif len(possible_apps) == 0:
			self.set_window_command_mode(time, error_message='No matching application for ' + name)
		else:
			self.set_window_command_mode(time, error_message='More than one application matches: ' + name)

	def bang(self, cmd, time):
		vim_cmd = Command.extract_vim_command(cmd)
		cmd = cmd.replace(vim_cmd, '', 1)
		self.terminal.execute(cmd)
		self.set_normal_mode()

	def colon(self, keyval, time):
		self.set_command_mode(time)

	def enter(self, keyval, time):
		self.messages.clean()
		self.set_window_command_mode(time)

	def escape(self, keyval, time):
		self.set_normal_mode()

	# TODO: move logic to windows
	def only(self, cmd, time):
		for w in self.windows.visible:
			if self.windows.active != w:
				w.minimize()
		self.windows.open(self.windows.active, time)
		self.set_normal_mode()

	def quit(self, cmd, time):
		if self.windows.active:
			self.windows.active.minimize()
			self.set_normal_mode()
		else:
			self.set_window_command_mode(time, error_message='No active window')

	def centralize(self, cmd, time):
		self.windows.centralize_active_window()
		self.windows.commit_navigation(time)

	def maximize(self, cmd, time):
		self.windows.maximize_active_window()
		self.windows.commit_navigation(time)

	def buffers(self, cmd, time):
		self.messages.list_buffers()
		self.set_window_command_mode(time)

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
			self.windows.open(self.windows.buffers[index], time)
		else:
			self.set_window_command_mode(time, error_message='Buffer {} does not exist'.format(buffer_number))

	def open_named_buffer(self, cmd, time):
		window_title = Command.extract_text_parameter(cmd)
		w = self.windows.find_by_name(window_title)
		if w:
			self.windows.open(w, time)
		else:
			self.set_window_command_mode(time, error_message='No matching buffer for ' + window_title)

	# TODO: remove duplicated tokenizer
	def delete_current_buffer(self, cmd, time):
		if self.windows.active:
			self.windows.remove(self.windows.active, time)
			self.set_normal_mode()
		else:
			self.set_window_command_mode(time, error_message='There is no active window')

	def delete_indexed_buffer(self, cmd, time):
		to_delete = []
		for number in re.findall(r'\d+', cmd):
			index = int(number) - 1
			if index < len(self.windows.buffers):
				to_delete.append(self.windows.buffers[index])
			else:
				self.set_window_command_mode(time, error_message='No buffers were deleted')
				return
		for window in to_delete:
			self.windows.remove(window, time)
		self.set_normal_mode()

	def delete_named_buffer(self, cmd, time):
		window_title = Command.extract_text_parameter(cmd)
		w = self.windows.find_by_name(window_title)
		if w:
			self.windows.remove(w, time)
			self.set_normal_mode()
		else:
			self.set_window_command_mode(time, error_message='No matching buffer for ' + window_title)

