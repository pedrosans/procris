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
from typing import List, Dict

import gi, os
import procris.persistor as persistor
from procris import scratchpads, wm

gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, Gdk
from procris.windows import Windows
from procris.wm import set_geometry, is_visible, resize


class Monitor:

	def __init__(self, nmaster: int = 1, rectangle: Gdk.Rectangle = None, gap: int = 0):
		self.nmaster: int = nmaster
		self.nservent: int = 0
		self.mfact: float = 0.5
		self.wx = self.wy = self.ww = self.wh = None
		if rectangle:
			self.set_rectangle(rectangle=rectangle, gap=gap)

	def set_rectangle(self, rectangle: Gdk.Rectangle, gap=0):
		self.wx = rectangle.x + gap
		self.wy = rectangle.y + gap
		self.ww = rectangle.width - gap * 2
		self.wh = rectangle.height - gap * 2

	def increase_master_area(self, increment: float = None):
		self.mfact += increment
		self.mfact = max(0.1, self.mfact)
		self.mfact = min(0.9, self.mfact)

	def increment_master(self, increment=None, upper_limit=None):
		self.nmaster += increment
		self.nmaster = max(0, self.nmaster)
		self.nmaster = min(upper_limit - self.nservent, self.nmaster)

	def increment_servant(self, increment=None, upper_limit=None):
		self.nservent += increment
		self.nservent = max(0, self.nservent)
		self.nservent = min(upper_limit - self.nmaster, self.nservent)


# TODO: the the window is maximized, the layout function fails
def is_managed(window, workspace):
	return is_visible(window, workspace) and window.get_name() not in scratchpads.names()


class Layout:
	window: Windows
	stacks: Dict[int, List[int]] = {}
	monitors: Dict[int, Monitor] = {}

	def __init__(self, windows):
		self.function_key = None
		self.window_monitor_map = {}
		self.gap = 0
		self.border = 4
		self.windows = windows
		self.read = {}

	def start(self):
		self.read_display()
		self.apply()

		Wnck.Screen.get_default().connect("window-opened", self._window_opened)
		Wnck.Screen.get_default().connect("window-closed", self._window_closed)

	#
	# INTERNAL INTERFACE
	#
	def get_active_stack(self) -> List[int]:
		active_workspace: Wnck.Workspace = Wnck.Screen.get_default().get_active_workspace()
		return self.stacks[active_workspace.get_number()]

	def get_active_monitor(self) -> Monitor:
		active_workspace: Wnck.Workspace = Wnck.Screen.get_default().get_active_workspace()
		return self.monitors[active_workspace.get_number()]

	def servant_monitor(self):
		for i in range(Gdk.Display.get_default().get_n_monitors()):
			m = Gdk.Display.get_default().get_monitor(i)
			if not m.is_primary():
				return Monitor(nmaster=0, rectangle=m.get_workarea(), gap=self.gap)
		return None

	def _install_present_window_handlers(self):
		for window in self.windows.buffers:
			if window.get_xid() not in self.window_monitor_map:
				handler_id = window.connect("state-changed", self._state_changed)
				self.window_monitor_map[window.get_xid()] = handler_id

	def _incremented_index(self, increment):
		stack = self.get_active_stack()
		old_index = stack.index(self.windows.active.xid)
		new_index = old_index + increment
		return min(max(new_index, 0), len(stack) - 1)

	#
	# PUBLIC INTERFACE
	#
	def set_function(self, function_key):
		self.function_key = function_key
		self.windows.read_screen()
		self.read_display()
		self.apply()

	#
	# CALLBACKS
	#
	def _window_closed(self, screen, window):
		stack = self.get_active_stack()
		self.windows.read_screen(force_update=False)
		self.read_display()
		if window.get_xid() in stack:
			stack.remove(window.get_xid())
		if is_visible(window):
			self.apply()

	def _window_opened(self, screen: Wnck.Screen, window):
		if is_visible(window, screen.get_active_workspace()):
			self.windows.read_screen(force_update=False)
			self.read_display()
			if window.get_name() in scratchpads.names():
				scratchpad = scratchpads.get(window.get_name())
				primary = Gdk.Display.get_default().get_primary_monitor().get_workarea()
				resize(window, rectangle=primary, l=scratchpad.l, t=scratchpad.t, w=scratchpad.w, h=scratchpad.h)
			else:
				stack = self.get_active_stack()
				old_index = stack.index(window.get_xid())
				stack.insert(0, stack.pop(old_index))
			self.windows.apply_decoration_config()
			self.apply()

	def _state_changed(self, window, changed_mask, new_state):
		if changed_mask & Wnck.WindowState.MINIMIZED and window.get_name() not in scratchpads.names():
			stack = self.get_active_stack()
			self.windows.read_screen(force_update=False)
			self.read_display()
			if is_visible(window):
				old_index = stack.index(window.get_xid())
				stack.insert(0, stack.pop(old_index))
			self.apply()

	#
	# COMMANDS
	#
	def swap_focused_with(self, c_in):
		if self.windows.active.xid:
			stack = self.get_active_stack()
			direction = c_in.parameters[0]
			old_index = stack.index(self.windows.active.xid)
			new_index = self._incremented_index(direction)
			if new_index != old_index:
				stack.insert(new_index, stack.pop(old_index))
				self.apply()

	def move_focus(self, c_in):
		if self.windows.active.xid:
			stack = self.get_active_stack()
			direction = c_in.parameters[0]
			new_index = self._incremented_index(direction)
			self.windows.active.change_to(stack[new_index])

	def change_function(self, c_in):
		function_key = c_in.parameters[0]
		self.set_function(function_key)

	def move_to_master(self, c_in):
		if self.windows.active.xid:
			stack = self.get_active_stack()
			old_index = stack.index(self.windows.active.xid)
			stack.insert(0, stack.pop(old_index))
			self.apply()

	def increase_master_area(self, c_in):
		self.get_active_monitor().increase_master_area(increment=c_in.parameters[0])
		self.apply()

	def increment_master(self, c_in):
		self.get_active_monitor().increment_master(
			increment=c_in.parameters[0], upper_limit=len(self.get_active_stack()))
		self.apply()

	def increment_servant(self, c_in):
		self.get_active_monitor().increment_servant(
			increment=c_in.parameters[0], upper_limit=len(self.get_active_stack()))
		self.apply()

	def move_stacked(self, c_in):
		parameter = c_in.vim_command_parameter
		array = list(map(lambda x: int(x), parameter.split()))
		# set_geometry(w_stack[array[0]], array[1], array[2], array[3], array[4])

	def apply(self):
		persistor.persist_layout(self.to_json())
		self._install_present_window_handlers()
		stack = self.get_active_stack()

		if not self.function_key or not stack:
			return

		visible_windows = list(map(lambda xid: self.read[xid], stack))
		separation = self.gap + self.border
		servant = self.servant_monitor()
		split_point = len(visible_windows) - (self.get_active_monitor().nservent if servant else 0)

		arrange = FUNCTIONS_MAP[self.function_key](visible_windows[:split_point], self.get_active_monitor())
		if servant:
			arrange += FUNCTIONS_MAP[self.function_key](visible_windows[split_point:], servant)

		for i in range(len(arrange)):
			a = arrange[i]
			w = visible_windows[i]
			try:
				set_geometry(
					w, x=a[0] + separation, y=a[1] + separation, w=a[2] - separation * 2, h=a[3] - separation * 2)
			except wm.DirtyState:
				pass  # we did our best to keep WNCK objects fresh, but it can happens and did got dirty

	def read_display(self):
		self.read.clear()
		for window in Wnck.Screen.get_default().get_windows():
			self.read[window.get_xid()] = window

		for workspace in Wnck.Screen.get_default().get_workspaces():

			if workspace.get_number() not in self.stacks:
				self.monitors[workspace.get_number()] = Monitor()
				self.stacks[workspace.get_number()] = []

			monitor: Monitor = self.monitors[workspace.get_number()]
			monitor.set_rectangle(Gdk.Display.get_default().get_primary_monitor().get_workarea(), gap=self.gap)

			stack: List[int] = self.stacks[workspace.get_number()]
			stack.extend(map(lambda w: w.get_xid(), filter(
					lambda w: w.get_xid() not in stack and is_managed(w, workspace),
					reversed(Wnck.Screen.get_default().get_windows_stacked()))))

			for to_remove in filter(lambda xid: xid not in self.read or not is_managed(self.read[xid], workspace), stack):
				stack.remove(to_remove)

	def from_json(self, json):
		# try:
		# 	self.from_json(persistor.read_layout())
		# except KeyError as e:
		# 	print('can not load last state, there is a unknown key in the json')
		if not json:
			return
		for workspace_number in json['monitors'].keys():
			monitor = self.monitors[int(workspace_number)] = Monitor()
			stack = self.stacks[int(workspace_number)] = []
			monitor.nmaster = json['nmaster']
			monitor.mfact = json['mfact']
			self.function_key = json['function']
			copy = stack.copy()
			self.stack.sort(
				key=lambda xid:
				json['stack_state'][str(xid)]['stack_index']
				if str(xid) in json['stack_state']
				else copy.index(xid))

	def to_json(self):
		state = {'monitors': {}}
		for workspace_number in self.stacks.keys():
			monitor: Monitor = self.monitors[workspace_number]
			stack: List[int] = self.stacks[workspace_number]
			stack_state = {}
			for xid in stack:
				stack_state[str(xid)] = {
					'name': self.read[xid].get_name(),
					'stack_index': stack.index(xid)
				}
			state['monitors'][str(workspace_number)] = {
				'nmaster': monitor.nmaster, 'mfact': monitor.mfact,
				'function': self.function_key,
				'stack': stack_state,
			}
		return state


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
