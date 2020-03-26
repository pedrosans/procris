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
import pwm.messages as messages
import pwm.state as configurations
from pwm import decoration

gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, Gdk
from typing import List, Dict, Callable
from pwm.names import PROMPT
from pwm.wm import gdk_window_for, monitor_work_area_for, set_geometry, resize, is_visible, \
	get_active_window, decoration_delta, UserEvent
from pwm.decoration import DECORATION_MAP


class Axis:
	position_mask: Wnck.WindowMoveResizeMask
	size_mask: Wnck.WindowMoveResizeMask

	def __init__(self, position_mask, size_mask):
		self.position_mask = position_mask
		self.size_mask = size_mask

	def position_of(self, window: Wnck.Window):
		return window.get_geometry().xp if self is HORIZONTAL else window.get_geometry().yp


INCREMENT = 0.1
DECREMENT = -0.1
CENTER = 0.5
VERTICAL = Axis(Wnck.WindowMoveResizeMask.Y, Wnck.WindowMoveResizeMask.HEIGHT)
HORIZONTAL = Axis(Wnck.WindowMoveResizeMask.X, Wnck.WindowMoveResizeMask.WIDTH)
HORIZONTAL.perpendicular = VERTICAL
VERTICAL.perpendicular = HORIZONTAL
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
		self.visible: List[Wnck.Window] = []
		self.buffers: List[Wnck.Window] = []
		self.line: List[Wnck.Window] = None
		self.staging = False
		self.count = 0

	def read_default_screen(self, force_update=True):
		self.read(Wnck.Screen.get_default(), force_update=force_update)

	def read(self, screen: Wnck.Screen, force_update=True):
		del self.buffers[:]
		del self.visible[:]
		self.active.clean()

		if force_update:
			screen.force_update()  # make sure we query X server

		for wnck_window in screen.get_windows():
			if wnck_window.get_pid() == os.getpid() or wnck_window.is_skip_tasklist():
				continue

			self.buffers.append(wnck_window)

			if wnck_window.is_in_viewport(screen.get_active_workspace()) and not wnck_window.is_minimized():
				self.visible.append(wnck_window)

		self.update_active()
		self.line = sorted(self.visible, key=sort_line)

	def update_active(self):
		active_window = get_active_window(window_filter=lambda x: x in self.visible)
		self.active.xid = active_window.get_xid() if active_window else None

	#
	# API
	#
	def commit_navigation(self, event_time):
		"""
		Commits any staged change in the active window
		"""
		if self.staging and self.active.xid and self.active.get_wnck_window():
			self.active.get_wnck_window().activate_transient(event_time)
		self.staging = False

	def remove(self, window, time):
		window.close(time)
		if window in self.visible:
			self.remove_from_visible(window)
		self.buffers.remove(window)
		self.update_active()

	def remove_from_visible(self, window: Wnck.Window):
		self.visible.remove(window)
		self.line.remove(window)

	def apply_decoration_config(self):
		if configurations.is_remove_decorations():
			decoration.remove(self.buffers)
		else:
			decoration.restore(self.buffers)

	#
	# Query API
	#
	def find_by_name(self, name):
		return next((w for w in self.buffers if name.lower().strip() in w.get_name().lower()), None)

	def complete(self, c_in: UserEvent):
		if not c_in.vim_command_spacer:
			return None
		name = c_in.vim_command_parameter
		names = map(lambda x: x.get_name().strip(), self.buffers)
		filtered = filter(lambda x: name.lower().strip() in x.lower(), names)
		return list(filtered)

	#
	# COMMANDS
	#
	def list(self, user_event: UserEvent):
		if user_event.text:
			messages.add(messages.Message(PROMPT + user_event.text, 'info'))
		from pwm.view import BufferName
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

		if not c_in.vim_command_parameter:
			if self.active.xid:
				self.remove(self.active.get_wnck_window(), c_in.time)
				self.staging = True
				return
			return messages.Message('There is no active window', 'error')

		if re.match(r'^([0-9]+\s*)+$', c_in.vim_command_parameter):
			to_delete = []
			for number in re.findall(r'\d+', c_in.vim_command_parameter):
				index = int(number) - 1
				if index < len(self.buffers):
					to_delete.append(self.buffers[index])
				else:
					return messages.Message('No buffers were deleted', 'error')
			for window in to_delete:
				self.remove(window, c_in.time)
			self.staging = True if to_delete else False
			return

		w = self.find_by_name(c_in.vim_command_parameter)
		if w:
			self.remove(w, c_in.time)
			self.staging = True
		else:
			return messages.Message('No matching buffer for ' + c_in.vim_command_parameter, 'error')

	#
	# COMMAND OPERATIONS
	#
	def get_top_two_windows(self):
		top = self.active.get_wnck_window()
		below = None
		after_top = False
		for w in reversed(Wnck.Screen.get_default().get_windows_stacked()):
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
	def resume(self):
		resume = ''
		for wn in self.buffers:
			gdk_w = gdk_window_for(wn)

			resume += '\n'
			resume += '[{:8}] - {}\n'.format(wn.get_xid(), wn.get_name())

			x, y, w, h = wn.get_geometry()
			resume += '\t[WNCK   ] x: {:4d} y: {:3d} w: {:7.2f} h: {:7.2f}\n'.format(x, y, w, h)
			cx, cy, cw, ch = wn.get_client_window_geometry()
			resume += '\t[WNCK WN] x: {:4d} y: {:3d} w: {:7.2f} h: {:7.2f} \n'.format(cx, cy, cw, ch)
			gx, gy, gw, gh = gdk_w.get_geometry()
			resume += '\t[GDK    ] x: {:4d} y: {:3d} w: {:7.2f} h: {:7.2f} \n'.format(gx, gy, gw, gh)

			is_decorated, decorations = gdk_w.get_decorations()
			resume += '\ttype: {:8}\t\t\tdecorated: {:5}\t\tflags: {}\n'.format(
				gdk_w.get_type_hint().value_name.replace('GDK_WINDOW_TYPE_HINT_', '')[:8],
				str(is_decorated), list(map(lambda n: n.replace('GDK_DECOR_', ''), decorations.value_names)))

			dx, dy, dw, dh = decoration_delta(wn)
			compensate = is_decorated and not decorations and dx >= 0 and dy >= 0
			resume += '\tdecoration delta: {:3d} {:3d} {:3d} {:3d}\tcompensate: {:5}\n'.format(
				dx, dy, dw, dh, str(compensate))

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

	def change_to(self, xid: int):
		if self.xid != xid:
			self.xid = xid
			self.windows.staging = True

	def only(self, c_in):
		for w in self.windows.visible:
			if self.xid != w.get_xid():
				w.minimize()
				self.windows.remove_from_visible(w)
		self.windows.staging = True

	def minimize(self, c_in):
		if self.xid:
			active_window = self.get_wnck_window()
			active_window.minimize()
			self.windows.remove_from_visible(active_window)
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

	# TODO: apply layout
	def decorate(self, c_in):
		decoration_parameter = c_in.vim_command_parameter
		if decoration_parameter in DECORATION_MAP.keys():
			opt = DECORATION_MAP[decoration_parameter]
		gdk_window = gdk_window_for(self.get_wnck_window())
		# TODO: UnboundLocalError: local variable 'opt' referenced before assignment
		gdk_window.set_decorations(opt)
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
		stack = list(filter(lambda x: x in self.windows.visible, Wnck.Screen.get_default().get_windows_stacked()))
		i = stack.index(self.active.get_wnck_window())
		self.active.xid = stack[i - 1].get_xid()
		self.windows.staging = True

	def move(self, increment, axis):
		active = self.active.get_wnck_window()

		def key(w):
			axis_position = axis.position_of(w)
			perpendicular_distance = abs(axis.perpendicular.position_of(w) - axis.perpendicular.position_of(active))
			perpendicular_distance *= -1 if axis_position < axis.position_of(active) else 1
			return axis_position * STRETCH + perpendicular_distance

		sorted_windows = sorted(self.windows.visible, key=key)
		index = sorted_windows.index(self.active.get_wnck_window())
		if 0 <= index + increment < len(sorted_windows):
			index = index + increment
			next_index = index + increment
			while 0 <= next_index < len(sorted_windows) and axis.position_of(sorted_windows[index]) == axis.position_of(active):
				index = next_index
				next_index += increment
		self.active.xid = sorted_windows[index].get_xid()
		self.windows.staging = True

	def cycle(self, c_in):
		direction = 1 if not c_in or Gdk.keyval_name(c_in.keyval).islower() else -1
		i = self.windows.line.index(self.active.get_wnck_window())
		next_window = self.windows.line[(i + direction) % len(self.windows.line)]
		self.active.xid = next_window.get_xid()
		self.windows.staging = True