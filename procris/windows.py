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
import procris.messages as messages
import procris.configurations as configurations
import procris.scratchpads as scratchpads
from procris import decoration

gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, Gdk
from typing import List, Dict, Callable
from procris.names import PromptInput
from procris.wm import gdk_window_for, monitor_work_area_for, decoration_size_for, set_geometry, resize
from procris.decoration import DECORATION_MAP


class Axis:
	position_mask: Wnck.WindowMoveResizeMask
	size_mask: Wnck.WindowMoveResizeMask

	def __init__(self, position_mask, size_mask):
		self.position_mask = position_mask
		self.size_mask = size_mask


INCREMENT = 0.1
DECREMENT = -0.1
CENTER = 0.5
VERTICAL = Axis(Wnck.WindowMoveResizeMask.Y, Wnck.WindowMoveResizeMask.HEIGHT)
HORIZONTAL = Axis(Wnck.WindowMoveResizeMask.X, Wnck.WindowMoveResizeMask.WIDTH)
HORIZONTAL.perpendicular_axis = VERTICAL
VERTICAL.perpendicular_axis = HORIZONTAL
STRETCH = 1000


def sort_line(w):
	geometry = w.get_geometry()
	return geometry.xp * STRETCH + geometry.yp


def sort_column(w):
	geometry = w.get_geometry()
	return geometry.yp * STRETCH + geometry.xp


class Windows:

	def __init__(self):
		self.active = Active(windows=self)
		Wnck.set_client_type(Wnck.ClientType.PAGER)
		self.staging = False
		self.visible: List[Wnck.Window] = []
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
			if in_active_workspace or configurations.is_list_workspaces():
				self.buffers.append(wnck_window)
			if (
					in_active_workspace
					and not wnck_window.is_minimized()
					and wnck_window.get_name() not in scratchpads.names()):
				self.visible.append(wnck_window)
				self.visible_map[wnck_window.get_xid()] = wnck_window

		self.update_active()
		self.line   = sorted(list(self.visible), key=sort_line  )
		self.column = sorted(list(self.visible), key=sort_column)

	def update_active(self):
		self.active.xid = None
		for stacked in reversed(self.screen.get_windows_stacked()):
			if stacked in self.visible and self.is_visible(stacked):
				self.active.xid = stacked.get_xid()
				break

	#
	# API
	#
	def commit_navigation(self, event_time):
		"""
		Commits any staged change in the active window
		"""
		if self.staging and self.active.xid:
			self.active.get_wnck_window().activate_transient(event_time)
			self.staging = False

	def remove(self, window, time):
		window.close(time)
		self.visible.remove(window)
		self.buffers.remove(window)
		self.update_active()

	def apply_decoration_config(self):
		if configurations.is_remove_decorations():
			decoration.remove_decorations(self.buffers)
		else:
			decoration.restore_decorations(self.buffers)

	#
	# Query API
	#
	def find_by_name(self, name):
		return next((w for w in self.buffers if name.lower().strip() in w.get_name().lower()), None)

	def complete_window_name(self, c_in: PromptInput):
		if not c_in.vim_command_spacer:
			return None
		name = c_in.vim_command_parameter
		names = map(lambda x: x.get_name().strip(), self.buffers)
		filtered = filter(lambda x: name.lower().strip() in x.lower(), names)
		return list(filtered)

	#
	# COMMANDS
	#
	def list(self, c_in):
		from procris.view import BufferName
		for window in self.buffers:
			messages.add(BufferName(window, self))

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

	#
	# Internal API
	#
	def get_metadata_resume(self):
		resume = ''
		for wn in self.buffers:
			gdk_w = gdk_window_for(wn)
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

	windows: Windows = None

	def __init__(self, windows=None):
		self.windows = windows
		self.xid = None
		self.focus = Focus(windows=windows, active=self)

	def get_wnck_window(self):
		for w in self.windows.buffers:
			if w.get_xid() == self.xid:
				return w
		return None

	def clean(self):
		self.xid = None

	def change_to(self, xid):
		if self.xid != xid:
			self.xid = xid
			self.windows.staging = True

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
		self._snap_active_window(HORIZONTAL, 0.5)

	def move_left(self, c_in):
		self._snap_active_window(HORIZONTAL, 0)

	def move_up(self, c_in):
		self._snap_active_window(VERTICAL, 0)

	def move_down(self, c_in):
		self._snap_active_window(VERTICAL, 0.5)

	def _snap_active_window(self, axis, position):
		self._move_on_axis(self.get_wnck_window(), axis, position, 0.5)

	def _move_on_axis(self, window, axis, position, proportion):
		if axis == HORIZONTAL:
			resize(window, l=position, t=0, w=proportion, h=1)
		else:
			resize(window, l=0, t=position, w=1, h=proportion)
		self.windows.staging = True

	def centralize(self, c_in):
		resize(self.get_wnck_window(), l=0.1, t=0.1, w=0.8, h=0.8)
		self.windows.staging = True

	def decorate(self, c_in):
		decoration_parameter = c_in.vim_command_parameter
		if decoration_parameter in DECORATION_MAP.keys():
			opt = DECORATION_MAP[decoration_parameter]
		gdk_window = gdk_window_for(self.get_wnck_window())
		gdk_window.set_decorations(opt)
		self.windows.staging = True

	def move(self, c_in):
		parameter = c_in.vim_command_parameter
		parameter_a = parameter.split()
		to_x = int(parameter_a[0])
		to_y = int(parameter_a[1])
		work_area = monitor_work_area_for(self.get_wnck_window())
		x = to_x + work_area.x
		y = to_y + work_area.y
		set_geometry(self.get_wnck_window(), x=x, y=y)
		self.windows.staging = True


class Focus:

	windows: Windows = None
	active: Active = None

	def __init__(self, windows=None, active=None):
		self.windows = windows
		self.active = active

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
