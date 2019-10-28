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
import gi, os
import poco.state as state
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, GLib, Gdk


from poco.windows import monitor_work_area_for


class Monitor:

	def __init__(self):
		self.nmaster = 1
		self.mfact = 0.5
		self.wx = self.wy = self.ww = self.wh = None

	def set_workarea(self, x, y, width, height):
		self.wx = x
		self.wy = y
		self.ww = width
		self.wh = height


def tile(stack, monitor):
	layout = []

	if not stack:
		return None
	n = len(stack)

	if n > monitor.nmaster:
		mw = monitor.ww * monitor.mfact if monitor.nmaster else 0
	else:
		mw = monitor.ww
	my = ty = 0
	for i in range(len(stack)):
		if i < monitor.nmaster:
			h = (monitor.wh - my) / (min(n, monitor.nmaster) - i);
			layout.append([monitor.wx, monitor.wy + my, mw, h])
			my += layout[-1][3]
		else:
			h = (monitor.wh - ty) / (n - i);
			layout.append([monitor.wx + mw, monitor.wy + ty, monitor.ww - mw, h])
			ty += layout[-1][3]

	return layout


def centeredmaster(stack, monitor):
	# i, n, h, mw, mx, my, oty, ety, tw = None
	layout = []

	if not stack:
		return None
	n = len(stack)

	mw = monitor.ww;
	mx = 0;
	my = 0;
	tw = mw;

	if n > monitor.nmaster:
		# go mfact box in the center if more than nmaster clients
		mw = monitor.ww * monitor.mfact if monitor.nmaster else 0
		tw = monitor.ww - mw

		if n - monitor.nmaster > 1:
			# only one client
			mx = (monitor.ww - mw) / 2
			tw = (monitor.ww - mw) / 2
	#  +
	oty = 0;
	ety = 0;
	for i in range(len(stack)):
		c = stack[i]
		if i < monitor.nmaster:
			# nmaster clients are stacked vertically, in the center of the screen
			h = (monitor.wh - my) / (min(n, monitor.nmaster) - i);
			layout.append([monitor.wx + mx, monitor.wy + my, mw, h])
			my += layout[-1][3]
		else:
			# stack clients are stacked vertically
			if (i - monitor.nmaster) % 2:
				h = (monitor.wh - ety) / int((1 + n - i) / 2)
				layout.append([monitor.wx, monitor.wy + ety, tw, h])
				ety += layout[-1][3]
			else:
				h = (monitor.wh - oty) / int((1 + n - i) / 2)
				layout.append([monitor.wx + mx + mw, monitor.wy + oty, tw, h])
				oty += layout[-1][3]

	return layout


FUNCTIONS_MAP = {'C': centeredmaster, 'T': tile}
FUNCTIONS_NAME_MAP = {'C': 'centeredmaster', 'T': 'tile'}


# TODO: the the window is maximized, the layout function fails
class Layout:

	def __init__(self, windows):
		self.function_key = 'T'
		self.window_monitor_map = {}
		self.gap = 10
		self.windows = windows
		self.monitor = Monitor()
		self.windows.read_screen()
		self.stack = list(map(lambda x: x.get_xid(), self.windows.visible))

		try:
			self.set_state(state.read_layout())
		except KeyError as e:
			print('can not load last state, there is a unknown key in the json')

		self._install_state_handlers()
		self.windows.screen.connect("window-opened", self._window_opened)
		self.windows.screen.connect("window-closed", self._window_closed)
		# self.screen.connect("active-window-changed", self._active_window_changed)
		# def _active_window_changed(self, screen, previously_active_window):

	def set_state(self, json):
		if not json:
			return
		self.monitor.nmaster = json['nmaster']
		self.monitor.mfact = json['mfact']
		self.function_key = json['function']
		# TODO: change to window stack
		copy = self.stack.copy()
		self.stack.sort(
			key=lambda xid:
			json['stack_state'][str(xid)]['stack_index']
			if str(xid) in json['stack_state']
			else copy.index(xid))

	#
	# INTERNAL INTERFACE
	#
	def _install_state_handlers(self):
		for window in self.windows.buffers:
			if window.get_xid() not in self.window_monitor_map:
				handler_id = window.connect("state-changed", self._state_changed)
				self.window_monitor_map[window.get_xid()] = handler_id

	#
	# PUBLIC INTERFACE
	#
	def set_function(self, function_key):
		self.function_key = function_key
		self.windows.read_screen()
		self.apply()

	#
	# CALLBACKS
	#
	def _window_closed(self, screen, window):
		if window.get_xid() in self.stack:
			self.stack.remove(window.get_xid())
		if self.windows.is_visible(window):
			self.windows.read_screen(force_update=False)
			self.apply()

	def _window_opened(self, screen, window):
		if self.windows.is_visible(window):
			self.stack.insert(0, window.get_xid())
			self.windows.read_screen(force_update=False)
			self.windows.apply_decoration_config()
			self.apply()

	def _state_changed(self, window, changed_mask, new_state):
		if changed_mask & Wnck.WindowState.MINIMIZED:
			if self.windows.is_visible(window):
				self.stack.insert(0, window.get_xid())
			else:
				self.stack.remove(window.get_xid())
			self.windows.read_screen(force_update=False)
			self.apply()

	#
	# COMMANDS
	#
	def swap_focused_with(self, c_in):
		direction = c_in.parameters[0]
		self.windows.read_screen()

		active_xid = self.windows.active.xid

		if active_xid:
			old_index = self.stack.index(active_xid)
			new_index = old_index + direction
			new_index = min(new_index, len(self.stack) - 1)
			new_index = max(new_index, 0)
			if new_index != old_index:
				self.stack.insert(new_index, self.stack.pop(old_index))
				self.apply()

	def change_function(self, c_in):
		function_key = c_in.parameters[0]
		self.set_function(function_key)

	def move_to_master(self, c_in):
		self.windows.read_screen()
		active_xid = self.windows.active.xid
		if active_xid:
			old_index = self.stack.index(active_xid)
			self.stack.insert(0, self.stack.pop(old_index))
		self.apply()

	def increase_master_area(self, c_in):
		self.windows.read_screen()
		increment = c_in.parameters[0]
		self.monitor.mfact += increment
		self.monitor.mfact = max(0.1, self.monitor.mfact)
		self.monitor.mfact = min(0.9, self.monitor.mfact)
		self.apply()

	def increment_master(self, c_in):
		self.windows.read_screen()
		increment = c_in.parameters[0]
		self.monitor.nmaster += increment
		self.monitor.nmaster = max(0, self.monitor.nmaster)
		self.monitor.nmaster = min(len(self.stack), self.monitor.nmaster)
		self.apply()

	def apply(self):
		state.write(self)
		self._install_state_handlers()

		w_stack = list(filter(
			lambda x: x is not None,
			map(lambda xid: self.windows.visible_map[xid] if xid in self.windows.visible_map else None, self.stack)))

		if not w_stack:
			return

		wa = monitor_work_area_for(w_stack[0])

		self.monitor.set_workarea(
			x=wa.x + self.gap, y=wa.y + self.gap, width=wa.width - self.gap * 2, height=wa.height - self.gap * 2)

		arrange = FUNCTIONS_MAP[self.function_key](w_stack, self.monitor)

		for i in range(len(arrange)):
			a = arrange[i]
			w = w_stack[i]
			self.windows.set_geometry(
				w, x=a[0] + self.gap, y=a[1] + self.gap, w=a[2] - self.gap * 2, h=a[3] - self.gap * 2)
