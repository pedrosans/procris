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

import gi, time, logging
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck

def get_x(window):
	return window.get_geometry().xp

def get_y(window):
	return window.get_geometry().yp

class Axis():
	def __init__(self, coordinate_function, position_mask, size_mask):
		self.coordinate_function = coordinate_function
		self.position_mask = position_mask
		self.size_mask = size_mask

VERTICAL = Axis(get_y, Wnck.WindowMoveResizeMask.Y, Wnck.WindowMoveResizeMask.HEIGHT)
HORIZONTAL = Axis(get_x, Wnck.WindowMoveResizeMask.X, Wnck.WindowMoveResizeMask.WIDTH)
HORIZONTAL.perpendicular_axis = VERTICAL
VERTICAL.perpendicular_axis = HORIZONTAL

#TODO a better name would be screen
class Windows():

	def __init__(self, controller):
		self.controller = controller
		Wnck.set_client_type(Wnck.ClientType.PAGER)
		self.active = None
		self.staging = False
		self.unity_wm = False
		self.visibles =[]
		self.buffers =[]

	def remove(self, window, time):
		window.close(time)
		self.visibles.remove(window)
		self.buffers.remove(window)
		self._update_internal_state()

	def read_screen(self):
		del self.visibles[:]
		del self.buffers[:]
		self.screen = Wnck.Screen.get_default()
		self.screen.force_update()  #make sure we query X server

		active_workspace = self.screen.get_active_workspace()
		for wnck_window in self.screen.get_windows():
			if wnck_window.get_name() == 'XdndCollectionWindowImp':
				self.unity_wm = True
			if wnck_window.is_skip_tasklist():
				continue
			in_active_workspace = wnck_window.is_in_viewport(active_workspace)
			if in_active_workspace or self.controller.configurations.is_list_workspaces():
				self.buffers.append(wnck_window)
			if in_active_workspace and not wnck_window.is_minimized():
				self.visibles.append(wnck_window)
		self._update_internal_state()

	def find_by_name(self, window_title):
		for w in self.buffers:
			if window_title.lower().strip() in w.get_name().lower():
				return w;
		return None

	def query_names(self, name_filter):
		return list(
				filter(
					(lambda x :
						not name_filter or name_filter.lower().strip() in x.lower().strip()),
					map( (lambda x : x.get_name()), self.buffers )))

	def _update_internal_state(self):
		self.active = None
		for w in reversed(self.screen.get_windows_stacked()):
			if w in self.visibles:
				self.active = w
				break
		self.x_line = list(self.visibles)
		self.x_line.sort(key=lambda w: w.get_geometry().xp * 1000 + w.get_geometry().yp)
		self.y_line = list(self.visibles)
		self.y_line.sort(key=lambda w: w.get_geometry().yp)

	def clear_state(self):
		self.screen = None
		self.active = None
		self.visibles =[]
		self.buffers =[]
		self.x_line = None
		self.y_line = None

	#Commits any staged change in the active window
	def commit_navigation(self, time):
		if self.staging:
			self.controller.open_window(self.active, time)
			self.staging = False

	def cycle(self, keyval, time):
		next_window = self.x_line[(self.x_line.index(self.active) + 1) % len(self.x_line)]
		self.active = next_window
		self.staging = True

	def decrease_width(self, keyval, time):
		left, right = self.get_top_two_windows()
		if left is self.active:
			self.shift_center(0.4, left, right)
		else:
			self.shift_center(0.6, left, right)

	def increase_width(self, keyval, time):
		left, right = self.get_top_two_windows()
		if left is self.active:
			self.shift_center(0.6, left, right)
		else:
			self.shift_center(0.4, left, right)

	def equalize(self, keyval, time):
		left, right = self.get_top_two_windows()
		self.shift_center(0.5, left, right)

	def shift_center(self, new_center, left, right):
		self.move_on_axis(left, HORIZONTAL, 0, new_center)
		self.move_on_axis(right, HORIZONTAL, new_center, 1 - new_center)

	def get_top_two_windows(self):
		top = below = None
		for w in reversed(self.screen.get_windows_stacked()):
			if w in self.visibles:
				if not top:
					top = w
					continue
				else:
					below = w
					break

		if top and below and below.get_geometry().xp < top.get_geometry().xp:
			return below, top
		else:
			return top, below

	def maximize_active_window(self):
		self.active.maximize()
		self.staging = True

	def move_right(self, keyval, time):
		self.snap_active_window(HORIZONTAL, 0.5)

	def move_left(self, keyval, time):
		self.snap_active_window(HORIZONTAL, 0)

	def move_up(self, keyval, time):
		self.snap_active_window(VERTICAL, 0)

	def move_down(self, keyval, time):
		self.snap_active_window(VERTICAL, 0.5)

	def snap_active_window(self, axis, position):
		self.move_on_axis(self.active, axis, position, 0.5)

	def move_on_axis(self, window, axis, position, proportion):
		if axis == HORIZONTAL:
			self.resize(window, position, 0, proportion, 1)
		else:
			self.resize(window, 0, position, 1, proportion)

	def centralize_active_window(self):
		self.resize(self.active, 0.1, 0.1, 0.8, 0.8)

	def resize(self, window, x_ratio, y_ratio, width_ratio, height_ratio):
		"""
		Moves the window base on the parameter geometry : screen ratio
		"""
		was_maximized_horizontally = False
		was_maximized_vertically = False
		geometry_mask = Wnck.WindowMoveResizeMask.HEIGHT | Wnck.WindowMoveResizeMask.WIDTH
		old_x, old_y, old_width, old_height = window.get_geometry()
		monitor_geo = self.controller.view.get_monitor_geometry()

		if window.is_maximized():
			window.unmaximize()
		if window.is_maximized_horizontally():
			window.unmaximize_horizontally()
			was_maximized_horizontally = True
		if window.is_maximized_vertically():
			window.unmaximize_vertically()
			was_maximized_vertically = True

		new_width = int(monitor_geo.width * width_ratio)
		new_height = int(monitor_geo.height * height_ratio)
		new_x = int(monitor_geo.x + monitor_geo.width * x_ratio)
		new_y = int(monitor_geo.y + monitor_geo.height * y_ratio)

		if not self.unity_wm:
			geometry_mask = geometry_mask | Wnck.WindowMoveResizeMask.X
			geometry_mask = geometry_mask | Wnck.WindowMoveResizeMask.Y
		else:
			if width_ratio == 1:
				window.maximize_horizontally()
			else:
				if new_x != old_x or was_maximized_horizontally:
					geometry_mask = geometry_mask | Wnck.WindowMoveResizeMask.X
					if new_x == monitor_geo.x:
						new_width -= 10
			if height_ratio == 1:
				window.maximize_vertically()
			else:
				if new_y != old_y or was_maximized_vertically:
					geometry_mask = geometry_mask | Wnck.WindowMoveResizeMask.Y
					if new_y == monitor_geo.y:
						new_height -= 10

		#print("window: x={} y={} width={} heigh={}".format(new_x, new_y, new_width, new_height))
		#print("monitor: x={}  w={} y={}  h={}".format(monitor_geo.x, monitor_geo.width, monitor_geo.y, monitor_geo.height))

		y_offset = (monitor_geo.width + monitor_geo.x) - (new_x + new_width)
		if y_offset < 5:
			new_width += y_offset

		window.set_geometry(Wnck.WindowGravity.STATIC, geometry_mask, new_x, new_y, new_width, new_height)
		self.staging = True

	def navigate_right(self, keyval, time):
		self.navigate(self.x_line, 1, HORIZONTAL, time)

	def navigate_left(self, keyval, time):
		self.navigate(self.x_line, -1, HORIZONTAL, time)

	def navigate_up(self, keyval, time):
		self.navigate(self.y_line, -1, VERTICAL, time)

	def navigate_down(self, keyval, time):
		self.navigate(self.y_line, 1, VERTICAL, time)

	def navigate(self, oriented_list, increment, axis, time):
		at_the_side = self.look_at(oriented_list, self.active, increment, axis)
		if at_the_side:
			self.active = at_the_side
			self.staging = True

	def look_at(self, oriented_list, reference, increment, axis):
		destination = self.get_candidates(oriented_list, reference, increment, axis.coordinate_function)
		coordinate_function = axis.perpendicular_axis.coordinate_function
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

