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
import time
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck

class IndexedWindow():
	def __init__(self, window):
		self.window = windows
		start_position = self.windows.x_line.index(self.windows.active)
		length = len(self.windows.x_line)
		multiplier = (length + self.windows.x_line.index(window) - start_position) % len(self.windows.x_line)

class Windows():

	def __init__(self, controller):
		self.controller = controller
		self.active = None
		self.visibles =[]
		self.buffers =[]
		self.horizontal_axis = { 'coordinate_function' : self.get_x }
		self.vertical_axis   = { 'coordinate_function' : self.get_y }
		self.horizontal_axis['perpendicular_axis'] = self.vertical_axis
		self.vertical_axis  ['perpendicular_axis'] = self.horizontal_axis

	def read_screen(self):
		del self.visibles[:]
		del self.buffers[:]
		self.screen = Wnck.Screen.get_default()
		self.screen.force_update()  # recommended per Wnck documentation
		workspace = self.screen.get_active_workspace()

		for wnck_window in self.screen.get_windows():
			if not wnck_window.is_in_viewport(workspace):
				continue
			if wnck_window.is_skip_tasklist():
				continue
			self.buffers.append(wnck_window)
			if wnck_window.is_minimized():
				continue
			self.visibles.append(wnck_window)

		self.active = self.screen.get_active_window()
		if self.active not in self.visibles:
			self.active = None
		if self.active is None:
			for w in reversed(self.screen.get_windows_stacked()):
				if w in self.visibles:
					self.active = w
					break

		self.x_line = list(self.visibles)
		self.x_line.sort(key=lambda w: w.get_geometry().xp * 1000 + w.get_geometry().yp)
		self.y_line = list(self.visibles)
		self.y_line.sort(key=lambda w: w.get_geometry().yp)
		width = self.screen.get_width()
		self.grid = list(self.visibles)
		self.grid.sort(key=lambda w: ((w.get_geometry().xp * 12) / width) * 1000 + w.get_geometry().yp)
		self.visibles = list(self.x_line)

	def get_x(self, window):
		return window.get_geometry().xp

	def get_y(self, window):
		return window.get_geometry().yp

	def cycle(self, keyval, time):
		next_window = self.x_line[(self.x_line.index(self.active) + 1) % len(self.x_line)]
		self.controller.open_window(next_window, time)
		self.active = next_window

	def navigate_right(self, keyval, time):
		self.navigate(self.x_line, 1, self.horizontal_axis, time)

	def navigate_left(self, keyval, time):
		self.navigate(self.x_line, -1, self.horizontal_axis, time)

	def navigate_up(self, keyval, time):
		self.navigate(self.y_line, -1, self.vertical_axis, time)

	def navigate_down(self, keyval, time):
		self.navigate(self.y_line, 1, self.vertical_axis, time)

	def navigate(self, oriented_list, increment, axis, time):
		at_the_side = self.look_at(oriented_list, self.active, increment, axis)
		if at_the_side:
			self.controller.open_window(at_the_side, time)
			self.active = at_the_side

	def calculate_x_line(self):
		result = [self.active]
		right = self.active
		while right:
			right = self.look_at(self.x_line, right, 1, self.horizontal_axis)
			if right:
				result.append(right)
		left = self.active
		while left:
			left = self.look_at(self.x_line, left, -1, self.horizontal_axis)
			if left:
				result.insert(0, left)
		return result

	def calculate_y_line(self):
		result = [self.active]
		below = self.active
		while below:
			below = self.look_at(self.y_line, below, 1, self.vertical_axis)
			if below:
				result.append(below)
		above = self.active
		while above:
			above = self.look_at(self.y_line, above, -1, self.vertical_axis)
			if above:
				result.insert(0, above)
		return result

	def look_at(self, oriented_list, reference, increment, axis):
		destination = self.get_candidates(oriented_list, reference, increment, axis['coordinate_function'])
		coordinate_function = axis['perpendicular_axis']['coordinate_function']
		pos = coordinate_function(reference)
		if destination:
			return min(destination, key=lambda w: abs( pos - coordinate_function(w)))
		return None

	def get_candidates(self, oriented_list, reference, increment, position_function):
		line = []
		coordinate = position_function(reference)
		index = oriented_list.index(reference) + increment
		while index >= 0 and index < len(oriented_list):
			if position_function(oriented_list[index]) != coordinate:
				line.append(oriented_list[index])
			index = index + increment
		return line

