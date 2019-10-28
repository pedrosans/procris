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

import gi, os, re
import poco.messages as messages
import poco.configurations as configurations
import poco.state as state

gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, GdkX11, Gdk


class Axis:
	def __init__(self, position_mask, size_mask):
		self.position_mask = position_mask
		self.size_mask = size_mask


"""
ALL - all decorations should be applied.
BORDER - a frame should be drawn around the window.
MAXIMIZE - a maximize button should be included.
MENU - a button for opening a menu should be included.
MINIMIZE - a minimize button should be included.
RESIZEH - the frame should have resize handles.
TITLE - a titlebar should be placed above the window.
"""
DECORATION_MAP = {'ALL': Gdk.WMDecoration.ALL,
					'BORDER': Gdk.WMDecoration.BORDER,
					'MAXIMIZE': Gdk.WMDecoration.MAXIMIZE,
					'MENU': Gdk.WMDecoration.MENU,
					'MINIMIZE ': Gdk.WMDecoration.MINIMIZE,
					'RESIZEH': Gdk.WMDecoration.RESIZEH,
					'TITLE': Gdk.WMDecoration.TITLE,
					'NONE': 0}

INCREMENT = 0.1
DECREMENT = -0.1
CENTER = 0.5
VERTICAL = Axis(Wnck.WindowMoveResizeMask.Y, Wnck.WindowMoveResizeMask.HEIGHT)
HORIZONTAL = Axis(Wnck.WindowMoveResizeMask.X, Wnck.WindowMoveResizeMask.WIDTH)
HORIZONTAL.perpendicular_axis = VERTICAL
VERTICAL.perpendicular_axis = HORIZONTAL
X_Y_W_H_GEOMETRY_MASK = Wnck.WindowMoveResizeMask.HEIGHT | Wnck.WindowMoveResizeMask.WIDTH |\
							Wnck.WindowMoveResizeMask.X | Wnck.WindowMoveResizeMask.Y
STRETCH = 1000


def gdk_window_for(window):
	display = GdkX11.X11Display.get_default()
	xid = window.get_xid()
	return GdkX11.X11Window.foreign_new_for_display(display, xid)


def monitor_work_area_for(window):
	gdk_window = gdk_window_for(window)
	gdk_display = gdk_window.get_display()
	gdk_monitor = gdk_display.get_monitor_at_window(gdk_window)
	return gdk_monitor.get_workarea()


def decoration_size_for(window):
	gdk_w = gdk_window_for(window)
	is_decorated, decorations = gdk_w.get_decorations()
	x, y, w, h = window.get_geometry()
	cx, cy, cw, ch = window.get_client_window_geometry()
	decoration_width = cx - x
	decoration_height = cy - y

	return is_decorated, decorations, decoration_width, decoration_height


def unsnap(window):
	if window.is_maximized():
		window.unmaximize()
	if window.is_maximized_horizontally():
		window.unmaximize_horizontally()
	if window.is_maximized_vertically():
		window.unmaximize_vertically()


class Windows:

	def __init__(self, list_workspaces=False):
		self.list_workspaces = list_workspaces
		self.active = Active(windows=self)
		self.focus = Focus(windows=self)
		Wnck.set_client_type(Wnck.ClientType.PAGER)
		self.staging = False
		self.visible = []
		self.visible_map = {}
		self.buffers = []
		self.screen = None
		self.line = self.column = None

	def is_visible(self, window):
		if window.get_pid() == os.getpid():
			return False
		if window.is_skip_tasklist():
			return False
		active_workspace = self.screen.get_active_workspace()
		return window.is_in_viewport(active_workspace) and not window.is_minimized()

	def read_screen(self, force_update=True):
		del self.buffers[:]
		del self.visible[:]
		self.visible_map.clear()
		self.active.clean()

		if not self.screen:
			self.screen = Wnck.Screen.get_default()

		if force_update:
			self.screen.force_update()  # make sure we query X server

		active_workspace = self.screen.get_active_workspace()
		for wnck_window in self.screen.get_windows():
			if wnck_window.get_pid() == os.getpid():
				continue
			if wnck_window.is_skip_tasklist():
				continue
			in_active_workspace = wnck_window.is_in_viewport(active_workspace)
			if in_active_workspace or self.list_workspaces:
				self.buffers.append(wnck_window)
			if in_active_workspace and not wnck_window.is_minimized():
				self.visible.append(wnck_window)
				self.visible_map[wnck_window.get_xid()] = wnck_window

		self.update_active()
		self.line = sorted(list(self.visible), key=self.sort_line)
		self.column = sorted(list(self.visible), key=self.sort_column)

	def update_active(self):
		for stacked in reversed(self.screen.get_windows_stacked()):
			if stacked in self.visible:
				self.active.xid = stacked.get_xid()
				break

	def sort_line(self, w):
		geometry = w.get_geometry()
		return geometry.xp * STRETCH + geometry.yp

	def sort_column(self, w):
		geometry = w.get_geometry()
		return geometry.yp * STRETCH + geometry.xp

	def clear_state(self):
		self.screen = None
		self.active.clean()
		self.visible =[]
		self.buffers =[]
		self.line = None
		self.column = None

	#
	# API
	#
	def commit_navigation(self, event_time):
		"""
		Commits any staged change in the active window
		"""
		if self.staging:
			self.active.get_wnck_window().activate_transient(event_time)
			self.staging = False

	def remove(self, window, time):
		window.close(time)
		self.visible.remove(window)
		self.buffers.remove(window)
		self.update_active()

	def apply_decoration_config(self):
		if configurations.is_remove_decorations():
			self.remove_decorations()
		else:
			self.restore_decorations()

	def remove_decorations(self):
		decoration_map = state.read_decorations()
		if not decoration_map:
			decoration_map = {}
		for w in self.buffers:
			key = str(w.get_xid())
			is_decorated, decorations = gdk_window_for(w).get_decorations()
			gdk_w = gdk_window_for(w)
			if key not in decoration_map:
				if not is_decorated and not decorations:
					# assume server side decoration
					decorations = Gdk.WMDecoration.ALL
				decoration_map[key] = decorations
			has_title = Gdk.WMDecoration.TITLE & decorations or Gdk.WMDecoration.ALL & decorations
			if not is_decorated or has_title:
				gdk_w.set_decorations(Gdk.WMDecoration.BORDER)
		for key in list(decoration_map.keys()):
			if key not in map(lambda x: str(x.get_xid()), self.buffers):
				del decoration_map[key]
		state.write_decorations(decoration_map)

	def restore_decorations(self):
		decoration_map = state.read_decorations()
		for w in self.buffers:
			key = str(w.get_xid())
			gdk_w = gdk_window_for(w)
			if key in decoration_map:
				original = decoration_map[key]
				gdk_w.set_decorations(Gdk.WMDecoration(original))

	#
	# Query API
	#
	def find_by_name(self, name):
		return next((w for w in self.buffers if name.lower().strip() in w.get_name().lower()), None)

	def list_completions(self, name):
		names = map(lambda x: x.get_name().strip(), self.buffers)
		filtered = filter(lambda x: name.lower().strip() in x.lower(), names)
		return list(filtered)

	def decoration_options_for(self, option_name):
		return list(filter(lambda x: x.lower().startswith(option_name.lower().strip()), DECORATION_MAP.keys()))

	#
	# COMMANDS
	#
	def list(self, c_in):
		for window in self.buffers:
			messages.add_message(messages.BufferName(window, self))

	def activate(self, c_in):
		buffer_number_match = re.match(r'^\s*(buffer|b)\s*([0-9]+)\s*$', c_in.text)
		if buffer_number_match:
			buffer_number = buffer_number_match.group(2)
			index = int(buffer_number) - 1
			if index < len(self.buffers):
				self.active.xid = self.buffers[index].get_xid()
				self.staging = True
			else:
				return messages.Message('Buffer {} does not exist'.format(buffer_number), 'error')
		elif c_in.vim_command_parameter:
			window_title = c_in.vim_command_parameter
			w = self.find_by_name(window_title)
			if w:
				self.active.xid = w.get_xid()
				self.staging = True
			else:
				return messages.Message('No matching buffer for ' + window_title, 'error')

	def delete(self, c_in):
		if re.match(r'^\s*(bdelete|bd)\s*([0-9]+\s*)+$', c_in.text):
			to_delete = []
			for number in re.findall(r'\d+', c_in.text):
				index = int(number) - 1
				if index < len(self.buffers):
					to_delete.append(self.buffers[index])
				else:
					return messages.Message('No buffers were deleted', 'error')
			for window in to_delete:
				self.remove(window, c_in.time)
			self.staging = True if to_delete else False
		elif re.match(r'^\s*(bdelete|bd)\s+\w+\s*$', c_in.text):
			window_title = c_in.vim_command_parameter
			w = self.find_by_name(window_title)
			if w:
				self.remove(w, c_in.time)
				self.staging = True
			else:
				return messages.Message('No matching buffer for ' + window_title, 'error')
		elif self.active.xid:
			self.remove(self.active.get_wnck_window(), c_in.time)
			self.staging = True
		else:
			return messages.Message('There is no active window', 'error')

	#
	# COMMAND OPERATIONS
	#
	def get_top_two_windows(self):
		top = self.active.get_wnck_window()
		below = None
		after_top = False
		for w in reversed(self.screen.get_windows_stacked()):
			if w in self.visible and after_top:
				below = w
				break
			if w is top:
				after_top = True
		return top, below

	def get_left_right_top_windows(self):
		top, below = self.get_top_two_windows()
		if top and below and below.get_geometry().xp < top.get_geometry().xp:
			return below, top
		else:
			return top, below

	def snap_active_window(self, axis, position):
		self.move_on_axis(self.active.get_wnck_window(), axis, position, 0.5)

	def move_on_axis(self, window, axis, position, proportion):
		if axis == HORIZONTAL:
			self.resize(window, position, 0, proportion, 1)
		else:
			self.resize(window, 0, position, 1, proportion)

	def resize(self, window, x_ratio, y_ratio, width_ratio, height_ratio):
		"""
		Moves the window base on the parameter geometry : screen ratio
		"""
		unsnap(window)
		work_area = monitor_work_area_for(window)

		new_x = int(work_area.width * x_ratio) + work_area.x
		new_y = int(work_area.height * y_ratio) + work_area.y
		new_width = int(work_area.width * width_ratio)
		new_height = int(work_area.height * height_ratio)

		self.set_geometry(window, x=new_x, y=new_y, w=new_width, h=new_height)
		self.staging = True

	def move_to(self, to_x, to_y):
		work_area = monitor_work_area_for(self.active.get_wnck_window())
		x = to_x + work_area.x
		y = to_y + work_area.y
		self.set_geometry(self.active.get_wnck_window(), x=x, y=y)
		self.staging = True

	def set_geometry(self, window, x=None, y=None, w=None, h=None):
		if not w and not h:
			geometry = window.get_geometry()
			w = geometry.widthp
			h = geometry.heightp

		is_decorated, decorations, decoration_width, decoration_height = decoration_size_for(window)
		has_title = Gdk.WMDecoration.TITLE & decorations or Gdk.WMDecoration.ALL & decorations

		if is_decorated and not has_title and decoration_width >= 0 and decoration_height >= 0:
			x -= decoration_width
			y -= decoration_height
			w += decoration_width
			h += decoration_height

		# print("monitor: x={}  w={} y={}  h={}".format(monitor_geo.x, monitor_geo.width, monitor_geo.y, monitor_geo.height))
		# print("window: x={} y={} width={} height={}".format(x, y, w, h))

		window.set_geometry(Wnck.WindowGravity.STATIC, X_Y_W_H_GEOMETRY_MASK, x, y, w, h)

	#
	# Internal API
	#
	def get_metadata_resume(self):
		resume = ''
		for wn in self.buffers:
			gdk_w = gdk_window_for(wn)
			is_decorated, decorations = gdk_w.get_decorations()
			x, y, w, h = wn.get_geometry()
			cx, cy, cw, ch = wn.get_client_window_geometry()
			is_decorated, decorations, decoration_width, decoration_height = decoration_size_for(wn)
			compensate = is_decorated and not decorations and decoration_width >= 0 and decoration_height >= 0
			resume += '{:10} - {:20}\n'.format(
				wn.get_xid(), wn.get_name()[:10])
			resume += '\tcompensate({:5} {:3d},{:3d}) g({:3d},{:3d}) c_g({:3d},{:3d})\n'.format(
				str(compensate), decoration_width, decoration_height,
				x, y, cx, cy)
			resume += '\thint({:8}) dec({} {})\n'.format(
				gdk_w.get_type_hint().value_name.replace('GDK_WINDOW_TYPE_HINT_', '')[:8],
				is_decorated, decorations.value_names)
		return resume


class Active:

	def __init__(self, windows=None):
		self.windows = windows
		self.xid = None

	def get_wnck_window(self):
		for w in self.windows.buffers:
			if w.get_xid() == self.xid:
				return w
		return None

	def clean(self):
		self.xid = None

	def only(self, c_in):
		for w in self.windows.visible:
			if self.xid != w.get_xid():
				w.minimize()
		self.windows.staging = True

	def minimize(self, c_in):
		if self.xid:
			active_window = self.get_wnck_window()
			active_window.minimize()
			self.windows.visible.remove(active_window)
			self.windows.update_active()
			self.windows.staging = True

	def maximize(self, c_in):
		if self.xid:
			self.get_wnck_window().maximize()
			self.windows.staging = True

	def move_right(self, c_in):
		self.windows.snap_active_window(HORIZONTAL, 0.5)

	def move_left(self, c_in):
		self.windows.snap_active_window(HORIZONTAL, 0)

	def move_up(self, c_in):
		self.windows.snap_active_window(VERTICAL, 0)

	def move_down(self, c_in):
		self.windows.snap_active_window(VERTICAL, 0.5)

	def centralize(self, c_in):
		self.windows.resize(self.get_wnck_window(), 0.1, 0.1, 0.8, 0.8)

	def decorate(self, c_in):
		decoration_parameter = c_in.vim_command_parameter
		if decoration_parameter in DECORATION_MAP.keys():
			decoration = DECORATION_MAP[decoration_parameter]
		gdk_window = gdk_window_for(self.get_wnck_window())
		gdk_window.set_decorations(decoration)
		self.windows.staging = True

	def move(self, c_in):
		parameter = c_in.vim_command_parameter
		parameter_a = parameter.split()
		self.windows.move_to(int(parameter_a[0]), int(parameter_a[1]))


class Focus:

	def __init__(self, windows=None):
		self.windows = windows
		self.active = windows.active

	def move_right(self, c_in):
		self.move(1, HORIZONTAL)

	def move_left(self, c_in):
		self.move(-1, HORIZONTAL)

	def move_up(self, c_in):
		self.move(-1, VERTICAL)

	def move_down(self, c_in):
		self.move(1, VERTICAL)

	def move_to_previous(self, c_in):
		stack = list(filter(lambda x: x in self.windows.visible, self.windows.screen.get_windows_stacked()))
		i = stack.index(self.active.get_wnck_window())
		self.active.xid = stack[i - 1].get_xid()
		self.windows.staging = True

	def move(self, increment, axis):
		oriented_list = self.windows.line if axis is HORIZONTAL else self.windows.column
		index = oriented_list.index(self.active.get_wnck_window()) + increment
		if 0 <= index < len(oriented_list):
			self.active.xid = oriented_list[index].get_xid()
		self.windows.staging = True

	def cycle(self, c_in):
		# TODO: update after case insensitive bindings
		direction = 1 if not c_in or Gdk.keyval_name(c_in.keyval).islower() else -1
		i = self.windows.line.index(self.active.get_wnck_window())
		next_window = self.windows.line[(i + direction) % len(self.windows.line)]
		self.active.xid = next_window.get_xid()
		self.windows.staging = True
