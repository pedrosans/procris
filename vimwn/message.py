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
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango

ENTER_TO_CONTINUE = 'Press ENTER or type command to continue'


# TODO move to status.py
class Messages:

	def __init__(self, controller, windows):
		self.controller = controller
		self.windows = windows
		self.command_placeholder = None
		self.list = []

	def clean(self):
		del self.list[:]
		self.command_placeholder = '^W'

	def list_buffers(self):
		for window in self.windows.buffers:
			self.add_message(Messages.BufferName(window, self.windows))

	def add(self, content, type):
		self.add_message(Messages.Plain(content, type))

	def add_message(self, message):
		self.list.append(message)
		self.command_placeholder = ENTER_TO_CONTINUE

	class Plain:

		def __init__(self, content, level):
			self.content = content
			self.level = level

		def get_pixbuf(self):
			return None

		def get_content(self, size):
			return self.content

	class BufferName(Plain):

		def __init__(self, window, windows):
			super().__init__(None, None)
			self.window = window
			self.index = 1 + windows.buffers.index(self.window)
			self.flags = ''
			top, below = windows.get_left_right_top_windows()
			if self.window is top:
				self.flags += '%a'
			elif self.window is below:
				self.flags = '#'

		def get_pixbuf(self):
			return self.window.get_mini_icon()

		def get_content(self, size):
			buffer_columns = min(100, size - 3)
			description_columns = buffer_columns - 19
			window_name = self.window.get_name().ljust(description_columns)[:description_columns]
			name = '{:>2} {:2} {} {:12}'.format(
				self.index, self.flags, window_name, self.window.get_workspace().get_name().lower())
			return name

