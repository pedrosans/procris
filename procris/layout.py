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

import gi, traceback
import procris.cache as persistor
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, Gdk
from typing import List, Dict
from procris import scratchpads, wm
from procris.windows import Windows
from procris.wm import set_geometry, is_visible, resize, is_buffer, get_active_window, is_on_primary_monitor


# https://valadoc.org/gdk-3.0/Gdk.Monitor.html
class Monitor:

	def __init__(self, primary: bool = False, nmaster: int = 1, gap: int = 0, border: int = 0, function_key: str = 'T'):
		self.primary: bool = primary
		self.function_key: str = function_key
		self.nmaster: int = nmaster
		self.nservant: int = 0
		self.mfact: float = 0.5
		self.gap = gap
		self.border = border
		self.wx = self.wy = self.ww = self.wh = None
		self.visible_area: Gdk.Rectangle = None
		self.pointer: Monitor = None

	def set_rectangle(self, rectangle: Gdk.Rectangle):
		self.visible_area = rectangle
		self.wx = rectangle.x + self.gap
		self.wy = rectangle.y + self.gap
		self.ww = rectangle.width - self.gap * 2
		self.wh = rectangle.height - self.gap * 2

	def increase_master_area(self, increment: float = None):
		self.mfact += increment
		self.mfact = max(0.1, self.mfact)
		self.mfact = min(0.9, self.mfact)

	def increment_master(self, increment=None, upper_limit=None):
		self.nmaster += increment
		self.nmaster = max(0, self.nmaster)
		self.nmaster = min(upper_limit - self.nservant, self.nmaster)

	def increment_servant(self, increment=None, upper_limit=None):
		self.nservant += increment
		self.nservant = max(0, self.nservant)
		self.nservant = min(upper_limit - self.nmaster, self.nservant)

	def contains(self, window: Wnck.Window):
		rect = self.visible_area
		xp, yp, widthp, heightp = window.get_geometry()
		return rect.x <= xp < (rect.x + rect.width) and rect.y <= yp < (rect.y + rect.height)

	def from_json(self, json):
		self.nmaster = json['nmaster'] if 'nmaster' in json else self.nmaster
		self.nservant = json['nservant'] if 'nservant' in json else self.nservant
		self.mfact = json['mfact'] if 'mfact' in json else self.mfact
		self.function_key = json['function'] if 'function' in json else self.function_key
		self.border = json['border'] if 'border' in json else self.border
		self.gap = json['gap'] if 'gap' in json else self.gap

	def print(self):
		print('monitor: {} {} {} {}'.format(self.wx, self.wy, self.ww, self.wh))

	def next(self):
		n_monitors = Gdk.Display.get_default().get_n_monitors()

		if n_monitors > 2:
			print('BETA VERSION WARN: no support for more than 2 monitors yet.')
			# While it seams easy to implement, there is no thought on
			# how the configuration would look like to assign a position for
			# each monitor on the stack.
			# For now, the Gdk flag does the job for since the second monitor
			# plainly is the one not flagged as primary.

		if n_monitors == 2 and self.primary:
			if not self.pointer:
				self.pointer = Monitor(nmaster=0, primary=False)
			return self.pointer
		else:
			return None


def is_managed(window):
	return is_buffer(window) and window.get_name() not in scratchpads.names()


def get_active_stacked_window():
	return get_active_window(window_filter=is_managed)


class Layout:
	window: Windows
	stacks: Dict[int, List[int]] = {}
	primary_monitors: Dict[int, Monitor] = {}
	read: Dict[int, Wnck.Window] = {}

	def __init__(self, windows):
		self.transient_callbacks = {}
		self.windows = windows

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

	def get_active_windows_as_list(self) -> List[Wnck.Window]:
		return list(map(lambda xid: self.read[xid], self.get_active_stack()))

	def get_active_primary_monitor(self) -> Monitor:
		active_workspace: Wnck.Workspace = Wnck.Screen.get_default().get_active_workspace()
		return self.primary_monitors[active_workspace.get_number()]

	def _install_present_window_handlers(self):
		for window in Wnck.Screen.get_default().get_windows():
			if window.get_xid() not in self.transient_callbacks and is_managed(window):
				handler_id = window.connect("state-changed", self._state_changed)
				self.transient_callbacks[window.get_xid()] = handler_id

	def _incremented_index(self, increment):
		stack = self.get_active_stack()
		active = get_active_stacked_window()
		old_index = stack.index(active.get_xid())
		new_index = old_index + increment
		return min(max(new_index, 0), len(stack) - 1)

	#
	# PUBLIC INTERFACE
	#
	def get_function_key(self):
		monitor = self.get_active_primary_monitor()
		return monitor.function_key

	def set_function(self, function_key):
		monitor = self.get_active_primary_monitor()
		monitor.function_key = function_key
		self.windows.read_screen()
		self.read_display()
		self.apply()

	#
	# CALLBACKS
	#
	def _window_closed(self, screen, window):
		if is_visible(window):
			self.read_display()
			self.apply()

	def _window_opened(self, screen: Wnck.Screen, window):
		if is_visible(window, screen.get_active_workspace()):
			self.read_display()
			if window.get_name() in scratchpads.names():
				scratchpad = scratchpads.get(window.get_name())
				primary = Gdk.Display.get_default().get_primary_monitor().get_workarea()
				resize(window, rectangle=primary, l=scratchpad.l, t=scratchpad.t, w=scratchpad.w, h=scratchpad.h)
			else:
				stack = self.get_active_stack()
				monitor = self.get_active_primary_monitor()
				start_index = 0
				while monitor:
					end_index = len(stack) - monitor.nservant
					if monitor.contains(window):
						old_index = stack.index(window.get_xid())
						stack.insert(start_index, stack.pop(old_index))
					monitor = monitor.next()
					start_index = end_index

			self.windows.read_screen(force_update=False)
			self.windows.apply_decoration_config()
			self.apply()

	def _state_changed(self, window, changed_mask, new_state):
		if changed_mask & Wnck.WindowState.MINIMIZED and is_managed(window):
			self.read_display()
			stack = self.get_active_stack()
			if is_visible(window):
				old_index = stack.index(window.get_xid())
				stack.insert(0, stack.pop(old_index))
			self.apply()

	#
	# COMMANDS
	#
	def change_function(self, c_in):
		function_key = c_in.parameters[0]
		self.set_function(function_key)

	def set_border(self, c_in):
		self.get_active_primary_monitor().border = int(c_in.vim_command_parameter)
		self.read_display()
		self.windows.staging = True
		self.apply()

	def set_gap(self, c_in):
		self.get_active_primary_monitor().gap = int(c_in.vim_command_parameter)
		self.read_display()
		self.windows.staging = True
		self.apply()

	def swap_focused_with(self, c_in):
		active = get_active_stacked_window()
		if active:
			stack = self.get_active_stack()
			direction = c_in.parameters[0]
			old_index = stack.index(active.get_xid())
			new_index = self._incremented_index(direction)
			if new_index != old_index:
				stack.insert(new_index, stack.pop(old_index))
				self.apply()

	def move_focus(self, c_in):
		if get_active_stacked_window():
			stack = self.get_active_stack()
			direction = c_in.parameters[0]
			new_index = self._incremented_index(direction)
			self.windows.active.change_to(stack[new_index])

	def move_to_master(self, c_in):
		active = get_active_stacked_window()
		if active:
			stack = self.get_active_stack()
			old_index = stack.index(active.get_xid())
			stack.insert(0, stack.pop(old_index))
			self.apply()

	def increase_master_area(self, c_in):
		self.get_active_primary_monitor().increase_master_area(increment=c_in.parameters[0])
		self.apply()

	def increment_master(self, c_in):
		self.get_active_primary_monitor().increment_master(
			increment=c_in.parameters[0], upper_limit=len(self.get_active_stack()))
		self.apply()

	def increment_servant(self, c_in):
		self.get_active_primary_monitor().increment_servant(
			increment=c_in.parameters[0], upper_limit=len(self.get_active_stack()))
		self.apply()

	def move_stacked(self, c_in):
		parameter = c_in.vim_command_parameter
		monitor: Monitor = self.get_active_primary_monitor()
		array = list(map(lambda x: int(x), parameter.split()))
		visible_windows = self.get_active_windows_as_list()

		set_geometry(
			visible_windows[array[0]], x=array[1] + monitor.wx, y=array[2] + monitor.wy,
			w=array[3] if len(array) > 3 else None,
			h=array[4] if len(array) > 3 else None)

		self.windows.staging = True

	def apply(self):
		self._install_present_window_handlers()
		persistor.persist_layout(self.to_json())
		primary_monitor: Monitor = self.get_active_primary_monitor()
		workspace_windows = self.get_active_windows_as_list()

		separation = primary_monitor.gap + primary_monitor.border
		arrange = []
		monitor = primary_monitor
		visible = workspace_windows
		while monitor and visible:
			# primary_monitor.set_rectangle(Gdk.Display.get_default().get_primary_monitor().get_workarea())
			split_point = len(visible) - monitor.nservant
			arrange += FUNCTIONS_MAP[monitor.function_key](visible[:split_point], monitor)

			monitor = monitor.next()
			visible = visible[split_point:]

		for i in range(len(arrange)):
			try:
				set_geometry(
					workspace_windows[i],
					x=arrange[i][0] + separation, y=arrange[i][1] + separation,
					w=arrange[i][2] - separation * 2, h=arrange[i][3] - separation * 2)
			except wm.DirtyState:
				pass  # we did our best to keep WNCK objects fresh, but it can happens and did got dirty

	def read_display(self):
		self.read.clear()
		for window in Wnck.Screen.get_default().get_windows():
			self.read[window.get_xid()] = window

		for workspace in Wnck.Screen.get_default().get_workspaces():

			if workspace.get_number() not in self.stacks:
				self.primary_monitors[workspace.get_number()] = Monitor(primary=True)
				self.stacks[workspace.get_number()] = []

			primary_monitor: Monitor = self.primary_monitors[workspace.get_number()]
			stack: List[int] = self.stacks[workspace.get_number()]
			stack.extend(map(lambda w: w.get_xid(), filter(
					lambda w: w.get_xid() not in stack and is_visible(w, workspace) and is_managed(w),
					reversed(Wnck.Screen.get_default().get_windows_stacked()))))

			for to_remove in filter(
					lambda xid: xid not in self.read or not is_visible(self.read[xid], workspace),
					stack.copy()):
				stack.remove(to_remove)

			primary_monitor.nservant = len(list(filter(lambda xid: not is_on_primary_monitor(self.read[xid]), stack)))
			copy = stack.copy()
			stack.sort(key=lambda xid: copy.index(xid) + (10000 if not is_on_primary_monitor(self.read[xid]) else 0))

			for i in range(Gdk.Display.get_default().get_n_monitors()):
				gdk_monitor = Gdk.Display.get_default().get_monitor(i)
				if gdk_monitor.is_primary():
					primary_monitor.set_rectangle(gdk_monitor.get_workarea())
				elif primary_monitor.next():
					primary_monitor.next().set_rectangle(gdk_monitor.get_workarea())
					break

	def resume(self):
		resume = ''
		for workspace in Wnck.Screen.get_default().get_workspaces():
			resume += 'Workspace {}\n'.format(workspace.get_number())
			for i in range(Gdk.Display.get_default().get_n_monitors()):
				m = Gdk.Display.get_default().get_monitor(i)
				rect = m.get_workarea()
				resume += '\tMonitor {}\tPrimary: {}\tRectangle: {:5}, {:5}, {:5}, {:5}\n'.format(
					i, m.is_primary(), rect.x, rect.y, rect.width, rect.height)

				stack = self.stacks[workspace.get_number()]
				resume += '\t\tLayout: {}\n'.format(self.primary_monitors[workspace.get_number()].function_key)
				resume += '\t\tStack: ['
				for xid in stack:
					w = self.read[xid]
					xp, yp, widthp, heightp = w.get_geometry()
					if rect.x <= xp < (rect.x + rect.width) and rect.y <= yp < (rect.y + rect.height):
						resume += '{:10} '.format(xid)
				resume += ']\n'

		return resume

	def from_json(self, json):
		Wnck.Screen.get_default().force_update()
		self.read_display()
		try:
			for key in json['workspaces']:
				index = int(key)

				monitor = self.primary_monitors[index] = Monitor(primary=True)
				monitor.from_json(json['workspaces'][key])

				if 'stack' in json['workspaces'][key] and index in self.stacks:
					stack = self.stacks[index]
					copy = stack.copy()
					stack.sort(
						key=lambda xid:
						json['workspaces'][key]['stack'][str(xid)]['index']
						if str(xid) in json['workspaces'][key]['stack']
						else copy.index(xid))
		except (KeyError, TypeError):
			traceback.print_exc()
			traceback.print_stack()

	def to_json(self):
		props = {'workspaces': {}}
		for workspace_number in self.stacks.keys():
			stack: List[int] = self.stacks[workspace_number]
			monitor: Monitor = self.primary_monitors[workspace_number]
			stack_json = {}
			for xid in stack:
				stack_json[str(xid)] = {
					'name': self.read[xid].get_name(),
					'index': stack.index(xid)
				}
			props['workspaces'][str(workspace_number)] = {
				'nmaster': monitor.nmaster, 'nservants': monitor.nservant,
				'mfact': monitor.mfact,
				'border': monitor.border, 'gap': monitor.gap,
				'function': monitor.function_key,
				'stack': stack_json,
			}
		return props


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
