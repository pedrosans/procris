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

import gi, time, logging, os
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, GdkX11, Gdk


def get_x(window):
	return window.get_geometry().xp


def get_y(window):
	return window.get_geometry().yp


class Axis:
	def __init__(self, coordinate_function, position_mask, size_mask):
		self.coordinate_function = coordinate_function
		self.position_mask = position_mask
		self.size_mask = size_mask


VERTICAL = Axis(get_y, Wnck.WindowMoveResizeMask.Y, Wnck.WindowMoveResizeMask.HEIGHT)
HORIZONTAL = Axis(get_x, Wnck.WindowMoveResizeMask.X, Wnck.WindowMoveResizeMask.WIDTH)
HORIZONTAL.perpendicular_axis = VERTICAL
VERTICAL.perpendicular_axis = HORIZONTAL


# TODO a better name would be screen
class Windows:

	def __init__(self, controller):
		self.controller = controller
		Wnck.set_client_type(Wnck.ClientType.PAGER)
		self.active = None
		self.staging = False
		self.visible = []
		self.buffers = []
		self.read_itself = False
		self.window_handlers = {}
		self.window_original_decorations = {}
		self.screen = None

	def read_screen(self):
		del self.visible[:]
		del self.buffers[:]
		self.read_itself = False
		if not self.screen:
			self.screen = Wnck.Screen.get_default()
		self.screen.force_update()  # make sure we query X server

		active_workspace = self.screen.get_active_workspace()
		for wnck_window in self.screen.get_windows():
			if wnck_window.get_pid() == os.getpid():
				self.read_itself = True
				continue
			if wnck_window.is_skip_tasklist():
				continue
			in_active_workspace = wnck_window.is_in_viewport(active_workspace)
			if in_active_workspace or self.controller.configurations.is_list_workspaces():
				self.buffers.append(wnck_window)
			if in_active_workspace and not wnck_window.is_minimized():
				self.visible.append(wnck_window)
		self._update_internal_state()

	def _update_internal_state(self):
		self.active = None
		for w in reversed(self.screen.get_windows_stacked()):
			if w in self.visible:
				self.active = w
				break
		self.x_line = list(self.visible)
		self.x_line.sort(key=lambda w: w.get_geometry().xp * 1000 + w.get_geometry().yp)
		self.y_line = list(self.visible)
		self.y_line.sort(key=lambda w: w.get_geometry().yp)

	def clear_state(self):
		self.screen = None
		self.active = None
		self.visible =[]
		self.buffers =[]
		self.x_line = None
		self.y_line = None

	#Commits any staged change in the active window
	def commit_navigation(self, time):
		if self.staging:
			self.open(self.active, time)
			self.staging = False

	#
	# API
	#
	def open(self, window, time):
		window.activate_transient(time)

	def remove(self, window, time):
		window.close(time)
		self.visible.remove(window)
		self.buffers.remove(window)
		self._update_internal_state()

	def find_by_name(self, window_title):
		for w in self.buffers:
			if window_title.lower().strip() in w.get_name().lower():
				return w;
		return None

	# TODO: move from here
	def list_completions(self, name_filter):
		striped = name_filter.lower()
		names = map(lambda x : x.get_name().strip(), self.buffers )
		names = filter(lambda x :striped in x.lower(), names)
		names = filter(lambda x : striped != x.lower(), names)
		return sorted(list(names), key=str.lower)

	#
	# COMMANDS
	#
	def navigate_to_previous(self, c_in):
		top, below = self.get_top_two_windows()
		if below:
			self.active = below
			self.staging = True

	def cycle(self, c_in):
		next_window = self.x_line[(self.x_line.index(self.active) + 1) % len(self.x_line)]
		self.active = next_window
		self.staging = True

	def decrease_width(self, c_in):
		left, right = self.get_top_two_windows()
		if left is self.active:
			self.shift_center(0.4, left, right)
		else:
			self.shift_center(0.6, left, right)

	def increase_width(self, c_in):
		left, right = self.get_top_two_windows()
		if left is self.active:
			self.shift_center(0.6, left, right)
		else:
			self.shift_center(0.4, left, right)

	def equalize(self, c_in):
		left, right = self.get_top_two_windows()
		self.shift_center(0.5, left, right)

	def maximize(self, c_in):
		self.active.maximize()
		self.staging = True

	def move_right(self, c_in):
		self.snap_active_window(HORIZONTAL, 0.5)

	def move_left(self, c_in):
		self.snap_active_window(HORIZONTAL, 0)

	def move_up(self, c_in):
		self.snap_active_window(VERTICAL, 0)

	def move_down(self, c_in):
		self.snap_active_window(VERTICAL, 0.5)

	def centralize(self, c_in):
		# TODO: move the staging flag logic from self.resize to here
		self.resize(self.active, 0.1, 0.1, 0.8, 0.8)

	def navigate_right(self, c_in):
		self.navigate(self.x_line, 1, HORIZONTAL, c_in.time)

	def navigate_left(self, c_in):
		self.navigate(self.x_line, -1, HORIZONTAL, c_in.time)

	def navigate_up(self, c_in):
		self.navigate(self.y_line, -1, VERTICAL, c_in.time)

	def navigate_down(self, c_in):
		self.navigate(self.y_line, 1, VERTICAL, c_in.time)

	#
	# COMMAND OPERATIONS
	#
	def shift_center(self, new_center, left, right):
		if left:
			self.move_on_axis(left, HORIZONTAL, 0, new_center)
		if right:
			self.move_on_axis(right, HORIZONTAL, new_center, 1 - new_center)

	def get_top_two_windows(self):
		top = self.active
		below = None
		after_top = False
		for w in reversed(self.screen.get_windows_stacked()):
			if w is self.active:
				after_top = True
				continue
			if after_top and w in self.visible and w is not top:
				below = w
				break
		return top, below

	def get_left_right_top_windows(self):
		top, below = self.get_top_two_windows()
		if top and below and below.get_geometry().xp < top.get_geometry().xp:
			return below, top
		else:
			return top, below

	def snap_active_window(self, axis, position):
		self.move_on_axis(self.active, axis, position, 0.5)

	def move_on_axis(self, window, axis, position, proportion):
		if axis == HORIZONTAL:
			self.resize(window, position, 0, proportion, 1)
		else:
			self.resize(window, 0, position, 1, proportion)

	def resize(self, window, x_ratio, y_ratio, width_ratio, height_ratio):
		"""
		Moves the window base on the parameter geometry : screen ratio
		"""
		geometry_mask = Wnck.WindowMoveResizeMask.HEIGHT | Wnck.WindowMoveResizeMask.WIDTH
		monitor_geo = self.controller.view.get_monitor_geometry()

		if window.is_maximized():
			window.unmaximize()
		if window.is_maximized_horizontally():
			window.unmaximize_horizontally()
		if window.is_maximized_vertically():
			window.unmaximize_vertically()

		new_width = int(monitor_geo.width * width_ratio)
		new_height = int(monitor_geo.height * height_ratio)
		new_x = int(monitor_geo.x + monitor_geo.width * x_ratio)
		new_y = int(monitor_geo.y + monitor_geo.height * y_ratio)

		geometry_mask = geometry_mask | Wnck.WindowMoveResizeMask.X
		geometry_mask = geometry_mask | Wnck.WindowMoveResizeMask.Y

		#print("window: x={} y={} width={} heigh={}".format(new_x, new_y, new_width, new_height))
		#print("monitor: x={}  w={} y={}  h={}".format(monitor_geo.x, monitor_geo.width, monitor_geo.y, monitor_geo.height))

		y_offset = (monitor_geo.width + monitor_geo.x) - (new_x + new_width)
		if y_offset < 5:
			new_width += y_offset

		window.set_geometry(Wnck.WindowGravity.STATIC, geometry_mask, new_x, new_y, new_width, new_height)

		self.staging = True

	def _restore_decorations( self, window, changed_mask, new_state ):
		if window.is_maximized_vertically():
			return
		gdk_window = self.get_gdk_window(window.get_xid())
		original_decorations = self.window_original_decorations[window.get_xid()]
		if original_decorations != None:
			gdk_window.set_decorations(original_decorations)
		else:
			gdk_window.set_decorations(Gdk.WMDecoration.ALL)
		window.disconnect(self.window_handlers[window.get_xid()])
		del self.window_handlers[window.get_xid()]

	def get_gdk_window(self, pid):
		gdkdisplay = GdkX11.X11Display.get_default()
		gdkwindow  = GdkX11.X11Window.foreign_new_for_display(gdkdisplay, pid)
		return gdkwindow

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

