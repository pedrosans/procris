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
import procris.persistor as persistor
from procris import scratchpads, wm

gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, GLib, Gdk
from procris.windows import Windows
from procris.wm import monitor_work_area_for, set_geometry, is_visible


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


def monocle(stack, monitor):
	layout = []
	for c in stack:
		layout.append([monitor.wx, monitor.wy, monitor.ww, monitor.wh])
	return layout


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
	if not stack:
		return None

	layout = []
	tw = mw = monitor.ww
	mx = my = 0
	oty = ety = 0
	n = len(stack)

	if n > monitor.nmaster:
		mw = int(monitor.ww * monitor.mfact) if monitor.nmaster else 0
		tw = monitor.ww - mw

		if n - monitor.nmaster > 1:
			mx = int((monitor.ww - mw) / 2)
			tw = int((monitor.ww - mw) / 2)

	for i in range(len(stack)):
		c = stack[i]
		if i < monitor.nmaster:
			# nmaster clients are stacked vertically, in the center of the screen
			h = int((monitor.wh - my) / (min(n, monitor.nmaster) - i))
			layout.append([monitor.wx + mx, monitor.wy + my, mw, h])
			my += h
		else:
			# stack clients are stacked vertically
			if (i - monitor.nmaster) % 2:
				h = int((monitor.wh - ety) / int((1 + n - i) / 2))
				layout.append([monitor.wx, monitor.wy + ety, tw, h])
				ety += h
			else:
				h = int((monitor.wh - oty) / int((1 + n - i) / 2))
				layout.append([monitor.wx + mx + mw, monitor.wy + oty, tw, h])
				oty += h

	return layout


def biasedstack(stack, monitor):
	layout = []
	oty = 0
	n = len(stack)

	mw = int(monitor.ww * monitor.mfact) if monitor.nmaster else 0
	mx = tw = int((monitor.ww - mw) / 2)
	my = 0

	for i in range(len(stack)):
		c = stack[i]
		if i < monitor.nmaster:
			# nmaster clients are stacked vertically, in the center of the screen
			h = int((monitor.wh - my) / (min(n, monitor.nmaster) - i))
			layout.append([monitor.wx + mx, monitor.wy + my, mw, h])
			my += h
		else:
			# stack clients are stacked vertically
			if (i - monitor.nmaster) == 0:
				layout.append([monitor.wx, monitor.wy, tw, monitor.wh])
			else:
				h = int((monitor.wh - oty) / (n - i))
				layout.append([monitor.wx + mx + mw, monitor.wy + oty, tw, h])
				oty += h

	return layout


FUNCTIONS_MAP = {'M': monocle, 'T': tile, 'C': centeredmaster, 'B': biasedstack}
FUNCTIONS_NAME_MAP = {'M': 'monocle', 'T': 'tile', 'C': 'centeredmaster', 'B': 'biasedstack'}


# TODO: the the window is maximized, the layout function fails
class Layout:
	window: Windows

	def __init__(self, windows):
		self.function_key = None
		self.window_monitor_map = {}
		self.gap = 0
		self.border = 4
		self.windows = windows
		self.monitor = Monitor()
		self.windows.read_screen()
		self.stack = filter(
			lambda x: x in self.windows.visible, reversed(self.windows.screen.get_windows_stacked()))
		self.stack = list(map(lambda x: x.get_xid(), self.stack))

		try:
			self.from_json(persistor.read_layout())
		except KeyError as e:
			print('can not load last state, there is a unknown key in the json')

		self._install_present_window_handlers()
		self.windows.screen.connect("window-opened", self._window_opened)
		self.windows.screen.connect("window-closed", self._window_closed)

	def from_json(self, json):
		if not json:
			return
		self.monitor.nmaster = json['nmaster']
		self.monitor.mfact = json['mfact']
		self.function_key = json['function']
		copy = self.stack.copy()
		self.stack.sort(
			key=lambda xid:
			json['stack_state'][str(xid)]['stack_index']
			if str(xid) in json['stack_state']
			else copy.index(xid))

	def to_json(self):
		stack_state = {}
		state = {
			'stack_state': stack_state,
			'nmaster': self.monitor.nmaster, 'mfact': self.monitor.mfact,
			'function': self.function_key}
		for w in self.windows.buffers:
			w_id = w.get_xid()
			key = str(w_id)
			if key not in stack_state:
				stack_state[key] = {}
			stack_state[key]['name'] = w.get_name()
			stack_state[key]['stack_index'] = self.stack.index(w_id) if w_id in self.stack else -1

		for client_key in list(stack_state.keys()):
			if client_key not in map(lambda x: str(x.get_xid()), self.windows.buffers):
				del stack_state[client_key]

		return state

	#
	# INTERNAL INTERFACE
	#
	def _install_present_window_handlers(self):
		for window in self.windows.buffers:
			if window.get_xid() not in self.window_monitor_map:
				handler_id = window.connect("state-changed", self._state_changed)
				self.window_monitor_map[window.get_xid()] = handler_id

	def _incremented_index(self, increment):
		old_index = self.stack.index(self.windows.active.xid)
		new_index = old_index + increment
		return min(max(new_index, 0), len(self.stack) - 1)

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
		if is_visible(window):
			self.windows.read_screen(force_update=False)
			self.apply()

	def _window_opened(self, screen, window):
		if is_visible(window):
			if window.get_name() in scratchpads.names():
				scratchpad = scratchpads.get(window.get_name())
				wm.resize(window, l=scratchpad.l, t=scratchpad.t, w=scratchpad.w, h=scratchpad.h)
			else:
				self.stack.insert(0, window.get_xid())
			self.windows.read_screen(force_update=False)
			self.windows.apply_decoration_config()
			self.apply()

	def _state_changed(self, window, changed_mask, new_state):
		if changed_mask & Wnck.WindowState.MINIMIZED and window.get_name() not in scratchpads.names():
			if is_visible(window):
				self.stack.insert(0, window.get_xid())
			else:
				self.stack.remove(window.get_xid())
			self.windows.read_screen(force_update=False)
			self.apply()

	#
	# COMMANDS
	#
	def swap_focused_with(self, c_in):
		if self.windows.active.xid:
			direction = c_in.parameters[0]
			old_index = self.stack.index(self.windows.active.xid)
			new_index = self._incremented_index(direction)
			if new_index != old_index:
				self.stack.insert(new_index, self.stack.pop(old_index))
				self.apply()

	def move_focus(self, c_in):
		if self.windows.active.xid:
			direction = c_in.parameters[0]
			new_index = self._incremented_index(direction)
			self.windows.active.change_to(self.stack[new_index])

	def change_function(self, c_in):
		function_key = c_in.parameters[0]
		self.set_function(function_key)

	def move_to_master(self, c_in):
		if self.windows.active.xid:
			old_index = self.stack.index(self.windows.active.xid)
			self.stack.insert(0, self.stack.pop(old_index))
			self.apply()

	def increase_master_area(self, c_in):
		increment = c_in.parameters[0]
		self.monitor.mfact += increment
		self.monitor.mfact = max(0.1, self.monitor.mfact)
		self.monitor.mfact = min(0.9, self.monitor.mfact)
		self.apply()

	def increment_master(self, c_in):
		increment = c_in.parameters[0]
		self.monitor.nmaster += increment
		self.monitor.nmaster = max(0, self.monitor.nmaster)
		self.monitor.nmaster = min(len(self.stack), self.monitor.nmaster)
		self.apply()

	def move_stacked(self, c_in):
		parameter = c_in.vim_command_parameter
		array = list(map(lambda x: int(x), parameter.split()))
		w_stack = list(filter(
			lambda x: x is not None,
			map(lambda xid: self.windows.visible_map[xid] if xid in self.windows.visible_map else None, self.stack)))
		set_geometry(w_stack[array[0]], array[1], array[2], array[3], array[4])

	def apply(self):
		persistor.persist_layout(self.to_json())
		self._install_present_window_handlers()

		if not self.function_key:
			return

		w_stack = list(filter(
			lambda x: x is not None,
			map(lambda xid: self.windows.visible_map[xid] if xid in self.windows.visible_map else None, self.stack)))

		if not w_stack:
			return

		wa = monitor_work_area_for(w_stack[0])

		self.monitor.set_workarea(
			x=wa.x + self.gap, y=wa.y + self.gap, width=wa.width - self.gap * 2, height=wa.height - self.gap * 2)

		arrange = FUNCTIONS_MAP[self.function_key](w_stack, self.monitor)
		separation = self.gap + self.border

		# map(lambda x: [x[0] + separation, x[1] + separation, x[2] - separation * 2, x[3] - separation * 2], arrange)

		for i in range(len(arrange)):
			a = arrange[i]
			w = w_stack[i]
			set_geometry(
				w, x=a[0] + separation, y=a[1] + separation, w=a[2] - separation * 2, h=a[3] - separation * 2)
