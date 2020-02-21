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
from gi.repository import Wnck, Gdk, GLib
from typing import List, Dict
from procris import scratchpads
from procris.windows import Windows
from procris.wm import set_geometry, is_visible, resize, is_buffer, get_active_window, is_on_primary_monitor, \
	get_height, DirtyState, X_Y_W_H_GEOMETRY_MASK, gdk_window_for, Trap


# https://valadoc.org/gdk-3.0/Gdk.Monitor.html
class Monitor:

	def __init__(self, primary: bool = False, nmaster: int = 1, mfact: float = 0.5, gap: int = 0, border: int = 0, function_key: str = 'T'):
		self.primary: bool = primary
		self.function_key: str = function_key
		self.nmaster: int = nmaster
		self.nservant: int = 0
		self.mfact: float = mfact
		self.gap = gap
		self.border = border
		self.wx = self.wy = self.ww = self.wh = None
		self.visible_area: Gdk.Rectangle = None
		self.pointer: Monitor = None

	def get_window_padding(self):
		return self.border + self.gap

	def set_border(self, border):
		self.border = border
		self._update_work_area()

	def set_gap(self, gap):
		self.gap = gap
		self._update_work_area()

	def set_rectangle(self, rectangle: Gdk.Rectangle):
		self.visible_area = rectangle
		self._update_work_area()

	def _update_work_area(self):
		self.wx = self.visible_area.x + self.gap
		self.wy = self.visible_area.y + self.gap
		self.ww = self.visible_area.width - self.gap * 2
		self.wh = self.visible_area.height - self.gap * 2

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

	def bind_to(self, screen: Wnck.Screen):
		self._install_present_window_handlers(screen)
		screen.connect("window-opened", self._window_opened)
		screen.connect("window-closed", self._window_closed)

	def _install_present_window_handlers(self, screen: Wnck.Screen):
		# TODO: uninstall when closed
		for window in screen.get_windows():
			if window.get_xid() not in self.transient_callbacks and is_managed(window):
				handler_id = window.connect("state-changed", self._state_changed)
				self.transient_callbacks[window.get_xid()] = handler_id

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

	def _incremented_index(self, increment):
		stack = self.get_active_stack()
		active = get_active_stacked_window()
		old_index = stack.index(active.get_xid())
		new_index = old_index + increment
		return min(max(new_index, 0), len(stack) - 1)

	def _read_default_display(self):
		self.read_from(Wnck.Screen.get_default())

	def read_from(self, screen: Wnck.Screen):
		self.read.clear()
		for window in screen.get_windows():
			self.read[window.get_xid()] = window

		for workspace in screen.get_workspaces():

			if workspace.get_number() not in self.stacks:
				self.primary_monitors[workspace.get_number()] = Monitor(primary=True)
				self.stacks[workspace.get_number()] = []

			primary_monitor: Monitor = self.primary_monitors[workspace.get_number()]
			stack: List[int] = self.stacks[workspace.get_number()]
			stack.extend(map(lambda w: w.get_xid(), filter(
				lambda w: w.get_xid() not in stack and is_visible(w, workspace) and is_managed(w),
				reversed(screen.get_windows_stacked()))))

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

	#
	# PUBLIC INTERFACE
	#
	def get_function_key(self):
		monitor = self.get_active_primary_monitor()
		return monitor.function_key

	def set_function(self, function_key):
		monitor = self.get_active_primary_monitor()
		monitor.function_key = function_key
		self.windows.read_default_screen()
		self._read_default_display()
		self.apply()

	#
	# CALLBACKS
	#
	def _window_closed(self, screen: Wnck.Screen, window):
		try:
			if is_visible(window):
				self.read_from(screen)
				self.apply()
		except DirtyState:
			pass  # It was just a try

	def _window_opened(self, screen: Wnck.Screen, window: Wnck.Window):
		self._install_present_window_handlers(screen)
		if is_visible(window, screen.get_active_workspace()):
			self.read_from(screen)
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

			try:
				with Trap():
					self.windows.read_default_screen(force_update=False)
					self.windows.apply_decoration_config()
					self.apply()
			except DirtyState:
				pass  # It was just a try

	def _state_changed(self, window: Wnck.Window, changed_mask, new_state):
		if changed_mask & Wnck.WindowState.MINIMIZED and is_managed(window):
			self.read_from(window.get_screen())
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
		promote_selected = False if len(c_in.parameters) < 2 else c_in.parameters[1]
		active = get_active_stacked_window()
		if promote_selected and active:
			stack = self.get_active_stack()
			old_index = stack.index(active.get_xid())
			stack.insert(0, stack.pop(old_index))
		self.set_function(function_key)

	def set_border(self, c_in):
		border = int(c_in.vim_command_parameter)
		self.get_active_primary_monitor().set_border(border)
		self.windows.staging = True
		self.apply()

	def set_gap(self, c_in):
		gap = int(c_in.vim_command_parameter)
		self.get_active_primary_monitor().set_gap(gap)
		self.windows.staging = True
		self.apply()

	def swap_focused_with(self, c_in):
		active = get_active_stacked_window()
		if active:

			direction = c_in.parameters[0]
			retain_focus = True if len(c_in.parameters) < 2 else c_in.parameters[1]

			stack = self.get_active_stack()
			old_index = stack.index(active.get_xid())
			new_index = self._incremented_index(direction)

			if new_index != old_index:
				stack.insert(new_index, stack.pop(old_index))
				if not retain_focus:
					self.windows.active.change_to(stack[old_index])
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

	def wnck_move(self, c_in):
		parameter = c_in.vim_command_parameter
		monitor: Monitor = self.get_active_primary_monitor()
		array = list(map(lambda x: int(x), parameter.split()))
		visible_windows = self.get_active_windows_as_list()
		window = visible_windows[array[0]]

		window.set_geometry(
			Wnck.WindowGravity.STATIC, X_Y_W_H_GEOMETRY_MASK,
			array[1] + monitor.wx,
			array[2] + monitor.wy,
			array[3] if len(array) > 3 else window.get_geometry().widthp,
			array[4] if len(array) > 3 else window.get_geometry().heightp)

		self.windows.staging = True

	def gdk_move(self, c_in):
		parameter = c_in.vim_command_parameter
		monitor: Monitor = self.get_active_primary_monitor()
		array = list(map(lambda x: int(x), parameter.split()))
		visible_windows = self.get_active_windows_as_list()
		window = visible_windows[array[0]]
		gdk_window = gdk_window_for(window)

		gdk_window.move(
			array[1] + monitor.wx,
			array[2] + monitor.wy)

		self.windows.staging = True

	def move_gdk_stacked(self, c_in):
		parameter = c_in.vim_command_parameter
		monitor: Monitor = self.get_active_primary_monitor()
		array = list(map(lambda x: int(x), parameter.split()))
		visible_windows = self.get_active_windows_as_list()

		set_geometry(
			visible_windows[array[0]], x=array[1] + monitor.wx, y=array[2] + monitor.wy,
			w=array[3] if len(array) > 3 else None,
			h=array[4] if len(array) > 3 else None, gdk=True)

		self.windows.staging = True

	def apply(self):
		persistor.persist_layout(self.to_json())
		primary_monitor: Monitor = self.get_active_primary_monitor()
		workspace_windows = self.get_active_windows_as_list()

		monitor = primary_monitor
		visible = workspace_windows
		while monitor and visible:
			split_point = len(visible) - monitor.nservant

			if monitor.function_key:
				monitor_windows: List[Wnck.Window] = visible[:split_point]
				FUNCTIONS_MAP[monitor.function_key](monitor_windows, monitor)

			monitor = monitor.next()
			visible = visible[split_point:]

	def resume(self):
		resume = ''
		for workspace in Wnck.Screen.get_default().get_workspaces():
			resume += 'Workspace {}\n'.format(workspace.get_number())
			for i in range(Gdk.Display.get_default().get_n_monitors()):
				m = Gdk.Display.get_default().get_monitor(i)
				rect = m.get_workarea()
				primary_monitor = self.primary_monitors[workspace.get_number()]
				monitor: Monitor = primary_monitor if m.is_primary() else primary_monitor.next()

				resume += '\tMonitor\t\t\tLayout: {}\tPrimary: {}\n'.format(
					FUNCTIONS_NAME_MAP[monitor.function_key] if monitor.function_key else None, m.is_primary())
				resume += '\t\t[GDK]\t\tRectangle: {:5}, {:5}, {:5}, {:5}\n'.format(
					rect.x, rect.y, rect.width, rect.height)
				resume += '\t\t[PROCRIS]\tRectangle: {:5}, {:5}, {:5}, {:5}\tborder: {} gap: {}\n'.format(
					monitor.wx, monitor.wy, monitor.ww, monitor.wh,
					monitor.border, monitor.gap)

				resume += '\t\t[Stack]\t\t('
				for xid in filter(lambda _xid: monitor.contains(self.read[_xid]), self.stacks[workspace.get_number()]):
					resume += '{:10} '.format(xid)
				resume += ')\n'

		return resume

	def from_json(self, json):
		screen = Wnck.Screen.get_default()
		screen.force_update()
		self.read_from(screen)
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
	padding = monitor.get_window_padding()
	for window in stack:
		set_geometry(
			window,
			x=monitor.wx + padding, y=monitor.wy + padding,
			w=monitor.ww - padding * 2, h=monitor.wh - padding * 2)


def tile(stack: List[Wnck.Window], m):
	n = len(stack)

	if n > m.nmaster:
		mw = m.ww * m.mfact if m.nmaster else 0
	else:
		mw = m.ww
	my = ty = 0
	padding = m.get_window_padding()

	for i in range(len(stack)):
		window = stack[i]
		if i < m.nmaster:
			h = (m.wh - my) / (min(n, m.nmaster) - i) - padding * 2
			synchronized = set_geometry(
				window, synchronous=True, x=m.wx + padding, y=m.wy + my + ty + padding, w=mw - padding * 2, h=h)
			my += (get_height(window) if synchronized else h) + padding * 2
		else:
			h = (m.wh - ty) / (n - i) - padding * 2
			synchronized = set_geometry(
				window, synchronous=True, x=m.wx + mw + padding, y=m.wy + ty + padding, w=m.ww - mw - padding * 2, h=h)
			ty += (get_height(window) if synchronized else h) + padding * 2


def centeredmaster(stack: List[Wnck.Window], m: Monitor):
	tw = mw = m.ww
	mx = my = 0
	oty = ety = 0
	n = len(stack)
	padding = m.get_window_padding()

	if n > m.nmaster:
		mw = int(m.ww * m.mfact) if m.nmaster else 0
		tw = m.ww - mw

		if n - m.nmaster > 1:
			mx = int((m.ww - mw) / 2)
			tw = int((m.ww - mw) / 2)

	for i in range(len(stack)):
		window = stack[i]
		if i < m.nmaster:
			# nmaster clients are stacked vertically, in the center of the screen
			h = int((m.wh - my) / (min(n, m.nmaster) - i)) - padding * 2
			synchronized = set_geometry(
				window, synchronous=True, x=m.wx + mx + padding, y=m.wy + my + padding, w=mw - padding * 2, h=h)
			my += (get_height(window) if synchronized else h) + padding * 2
		else:
			# stack clients are stacked vertically
			if (i - m.nmaster) % 2:
				h = int((m.wh - ety) / int((1 + n - i) / 2)) - padding * 2
				synchronized = set_geometry(
					window, synchronous=True, x=m.wx + padding, y=m.wy + ety + padding, w=tw - padding * 2, h=h)
				ety += (get_height(window) if synchronized else h) + padding * 2
			else:
				h = int((m.wh - oty) / int((1 + n - i) / 2)) - padding * 2
				synchronized = set_geometry(
					window, synchronous=True, x=m.wx + mx + mw + padding, y=m.wy + oty + padding, w=tw - padding * 2, h=h)
				oty += (get_height(window) if synchronized else h) + padding * 2


def biasedstack(stack: List[Wnck.Window], monitor: Monitor):
	oty = 0
	n = len(stack)
	mw = int(monitor.ww * monitor.mfact) if monitor.nmaster else 0
	mx = tw = int((monitor.ww - mw) / 2)
	my = 0
	padding = monitor.get_window_padding()

	for i in range(len(stack)):
		window: Wnck.Window = stack[i]
		if i < monitor.nmaster:
			# nmaster clients are stacked vertically, in the center of the screen
			h = int((monitor.wh - my) / (min(n, monitor.nmaster) - i))
			set_geometry(
				window,
				x=monitor.wx + mx + padding, y=monitor.wy + my + padding,
				w=mw - padding * 2, h=h - padding * 2)
			my += h
		else:
			# stack clients are stacked vertically
			if (i - monitor.nmaster) == 0:
				set_geometry(
					window,
					x=monitor.wx + padding, y=monitor.wy + padding,
					w=tw - padding * 2, h=monitor.wh - padding * 2)
			else:
				h = int((monitor.wh - oty) / (n - i))
				synchronized = set_geometry(
					window, synchronous=True,
					x=monitor.wx + mx + mw + padding, y=monitor.wy + oty + padding,
					w=tw - padding * 2, h=h - padding * 2)

				oty += ((get_height(window) + padding * 2) if synchronized else h)


FUNCTIONS_MAP = {'M': monocle, 'T': tile, 'C': centeredmaster, 'B': biasedstack}
FUNCTIONS_NAME_MAP = {'M': 'monocle', 'T': 'tile', 'C': 'centeredmaster', 'B': 'biasedstack'}
