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
import procris.desktop as desktop
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, Gdk, GLib
from typing import List, Dict
from procris import scratchpads, state
from procris.windows import Windows
from procris.wm import set_geometry, is_visible, resize, is_buffer, get_active_window, is_on_primary_monitor, \
	get_height, DirtyState, X_Y_W_H_GEOMETRY_MASK, gdk_window_for, Trap, Monitor, monitor_for, UserEvent, get_width


def is_managed(window):
	return is_buffer(window) and window.get_name() not in scratchpads.names()


def get_active_managed_window():
	return get_active_window(window_filter=is_managed)


class Layout:

	stacks: Dict[int, List[int]] = {}
	primary_monitors: Dict[int, Monitor] = {}
	window_by_xid: Dict[int, Wnck.Window] = {}
	handlers_by_xid: Dict[int, int] = {}
	screen_handlers: List[int] = []

	def __init__(self, windows: Windows):
		self.windows: Windows = windows

	def get_active_stack(self) -> List[int]:
		return self.stack_for(Wnck.Screen.get_default().get_active_workspace())

	def stack_for(self, workspace: Wnck.Workspace) -> List[int]:
		if workspace.get_number() not in self.stacks:
			self.stacks[workspace.get_number()] = []
		return self.stacks[workspace.get_number()]

	def get_active_windows_as_list(self) -> List[Wnck.Window]:
		return list(map(lambda xid: self.window_by_xid[xid], self.get_active_stack()))

	def get_active_primary_monitor_windows(self) -> List[Wnck.Window]:
		primary_monitor = self.get_active_primary_monitor()
		visible = self.get_active_windows_as_list()
		return list(filter(lambda w: primary_monitor.contains(w), visible))

	def get_active_primary_monitor(self) -> Monitor:
		return self.primary_monitor_for(Wnck.Screen.get_default().get_active_workspace())

	def get_active_monitor(self) -> Monitor:
		current: Gdk.Monitor = monitor_for(get_active_managed_window())
		active_workspace: Wnck.Workspace = Wnck.Screen.get_default().get_active_workspace()
		monitor: Monitor = self.primary_monitors[active_workspace.get_number()]
		return monitor if current.is_primary() else monitor.next()

	def primary_monitor_for(self, workspace: Wnck.Workspace) -> Monitor:
		if workspace.get_number() not in self.primary_monitors:
			self.primary_monitors[workspace.get_number()] = Monitor(primary=True)
		return self.primary_monitors[workspace.get_number()]

	def read(self, screen: Wnck.Screen, workspace_config: Dict):
		self.read_screen(screen)
		try:
			self.read_user_config(workspace_config, screen)
		except (KeyError, TypeError):
			print('Unable to the last execution state, using default ones.')
			traceback.print_exc()
			traceback.print_stack()

	def read_screen(self, screen: Wnck.Screen):
		self.window_by_xid.clear()
		for window in screen.get_windows():
			self.window_by_xid[window.get_xid()] = window

		for workspace in screen.get_workspaces():
			self._read_workspace(screen, workspace)
			self._read_workspace_windows_monitor(workspace)

	def _read_workspace(self, screen: Wnck.Screen, workspace: Wnck.Workspace):
		primary_monitor: Monitor = self.primary_monitor_for(workspace)
		stack: List[int] = self.stack_for(workspace)

		# add window listed in this workspace
		stack.extend(map(lambda w: w.get_xid(), filter(
			lambda w: w.get_xid() not in stack and is_visible(w, workspace) and is_managed(w),
			reversed(screen.get_windows_stacked()))))

		# remove any that no longer is in this workspace
		for outsider in filter(
				lambda xid: xid not in self.window_by_xid or not is_visible(self.window_by_xid[xid], workspace),
				stack.copy()):
			stack.remove(outsider)

		for i in range(Gdk.Display.get_default().get_n_monitors()):
			gdk_monitor = Gdk.Display.get_default().get_monitor(i)
			if gdk_monitor.is_primary():
				primary_monitor.set_rectangle(gdk_monitor.get_workarea())
			elif primary_monitor.next():
				primary_monitor.next().set_rectangle(gdk_monitor.get_workarea())
				break

	def _read_workspace_windows_monitor(self, workspace: Wnck.Workspace):
		primary_monitor: Monitor = self.primary_monitor_for(workspace)
		stack: List[int] = self.stack_for(workspace)
		copy = stack.copy()
		stack.sort(key=lambda xid: copy.index(xid) + (10000 if not primary_monitor.contains(self.window_by_xid[xid]) else 0))

	def read_user_config(self, config_json: Dict, screen: Wnck.Screen):
		number_of_workspaces = len(screen.get_workspaces())
		configured_workspaces = len(config_json['workspaces'])
		for workspace_index in range(min(number_of_workspaces, configured_workspaces)):
			workspace_json = config_json['workspaces'][workspace_index]

			if 'stack' in workspace_json:
				stack = self.stacks[workspace_index]
				copy = stack.copy()
				stack.sort(
					key=lambda xid:
					workspace_json['stack'][str(xid)]['index']
					if str(xid) in workspace_json['stack']
					else copy.index(xid))

			monitor_index = 0
			monitor: Monitor = self.primary_monitors[workspace_index]
			while monitor:
				if monitor_index < len(workspace_json['monitors']):
					monitor.from_json(workspace_json['monitors'][monitor_index])
				monitor_index += 1
				monitor = monitor.next()

	def persist(self):
		state.persist_workspace(self._serialize_workspace())

	def _serialize_workspace(self):
		props = {'workspaces': []}
		for workspace_number in self.stacks.keys():
			stack: List[int] = self.stacks[workspace_number]
			stack_json = {}
			for xid in stack:
				stack_json[str(xid)] = {'name': self.window_by_xid[xid].get_name(), 'index': stack.index(xid)}

			props['workspaces'].append({
				'stack': stack_json,
				'monitors': []
			})

			monitor: Monitor = self.primary_monitors[workspace_number]
			while monitor:
				props['workspaces'][workspace_number]['monitors'].append(monitor.to_json())
				monitor = monitor.next()
		return props

	def connect_to(self, screen: Wnck.Screen):
		self._install_present_window_handlers(screen)
		opened_handler_id = screen.connect("window-opened", self._window_opened)
		closed_handler_id = screen.connect("window-closed", self._window_closed)
		viewport_handler_id = screen.connect("viewports-changed", self._viewports_changed)
		workspace_handler_id = screen.connect("active-workspace-changed", self._active_workspace_changed)
		self.screen_handlers.extend([opened_handler_id, closed_handler_id, viewport_handler_id, workspace_handler_id])

	def _install_present_window_handlers(self, screen: Wnck.Screen):
		for window in screen.get_windows():
			if window.get_xid() not in self.handlers_by_xid and is_managed(window):
				handler_id = window.connect("state-changed", self._state_changed)
				self.handlers_by_xid[window.get_xid()] = handler_id

	def disconnect_from(self, screen: Wnck.Screen):
		self.read_screen(screen)
		for xid in self.handlers_by_xid.keys():
			if xid in self.window_by_xid:
				self.window_by_xid[xid].disconnect(self.handlers_by_xid[xid])
		for handler_id in self.screen_handlers:
			screen.disconnect(handler_id)

	#
	# CALLBACKS
	#
	def _viewports_changed(self, scree: Wnck.Screen):
		desktop.show_monitor(self.get_active_primary_monitor())

	def _active_workspace_changed(self, screen: Wnck.Screen, workspace: Wnck.Workspace):
		desktop.show_monitor(self.get_active_primary_monitor())
		desktop.update()

	def _window_closed(self, screen: Wnck.Screen, window):
		try:
			if window.get_xid() in self.handlers_by_xid:
				window.disconnect(self.handlers_by_xid[window.get_xid()])
				del self.handlers_by_xid[window.get_xid()]
			if is_visible(window) and is_managed(window):
				self.read_screen(screen)
				self.apply()
		except DirtyState:
			pass  # It was just a try

	def _window_opened(self, screen: Wnck.Screen, window: Wnck.Window):
		self._install_present_window_handlers(screen)
		if not is_visible(window, screen.get_active_workspace()):
			return
		if window.get_name() in scratchpads.names():
			scratchpad = scratchpads.get(window.get_name())
			primary = Gdk.Display.get_default().get_primary_monitor().get_workarea()
			resize(window, rectangle=primary, l=scratchpad.l, t=scratchpad.t, w=scratchpad.w, h=scratchpad.h)
		elif is_managed(window):
			self.read_screen(screen)
			stack = self.get_active_stack()
			copy = stack.copy()
			stack.sort(key=lambda xid: -1 if xid == window.get_xid() else copy.index(xid))

		try:
			with Trap():
				self.windows.read_default_screen(force_update=False)
				self.windows.apply_decoration_config()
				self.apply()
				self.persist()
		except DirtyState:
			pass  # It was just a try

	def _state_changed(self, window: Wnck.Window, changed_mask, new_state):
		if changed_mask & Wnck.WindowState.MINIMIZED and is_managed(window):
			self.read_screen(window.get_screen())
			stack = self.get_active_stack()
			if is_visible(window):
				old_index = stack.index(window.get_xid())
				stack.insert(0, stack.pop(old_index))
			self.apply()
			self.persist()

	#
	# COMMANDS
	#
	def change_function(self, c_in: UserEvent):
		function_key = c_in.parameters[0]
		promote_selected = False if len(c_in.parameters) < 2 else c_in.parameters[1]
		active = get_active_managed_window()
		if promote_selected and active:
			stack = self.get_active_stack()
			old_index = stack.index(active.get_xid())
			stack.insert(0, stack.pop(old_index))
		self.get_active_monitor().set_function(function_key)
		self.apply()
		self.persist()
		desktop.show_monitor(self.get_active_primary_monitor())

	def gap(self, c_in: UserEvent):
		parameters = c_in.vim_command_parameter.split()
		where = parameters[0]
		pixels = int(parameters[1])
		state.set_outer_gap(pixels) if where == 'outer' else state.set_inner_gap(pixels)
		self.get_active_primary_monitor().update_work_area()
		self.windows.staging = True
		self.apply()

	def complete_gap_options(self, c_in: UserEvent):
		input = c_in.vim_command_parameter.lower()
		return list(filter(lambda x: input != x and input in x, ['inner', 'outer']))

	def swap_focused_with(self, c_in: UserEvent):
		active = get_active_managed_window()
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
				self.persist()

	def move_focus(self, c_in: UserEvent):
		if get_active_managed_window():
			stack = self.get_active_stack()
			direction = c_in.parameters[0]
			new_index = self._incremented_index(direction)
			self.windows.active.change_to(stack[new_index])

	def move_to_monitor(self, c_in: UserEvent):
		active = get_active_managed_window()
		if active:
			stack = self.get_active_stack()
			old_index = stack.index(active.get_xid())
			stack.insert(0, stack.pop(old_index))
			self.apply(split_points=[])
			self.persist()

	def move_to_master(self, c_in: UserEvent):
		active = get_active_managed_window()
		if active:
			stack = self.get_active_stack()
			old_index = stack.index(active.get_xid())
			stack.insert(0, stack.pop(old_index))
			self.apply()
			self.persist()

	def increase_master_area(self, c_in: UserEvent):
		self.get_active_primary_monitor().increase_master_area(increment=c_in.parameters[0])
		self.apply()
		self.persist()

	def increment_master(self, c_in: UserEvent):
		self.get_active_primary_monitor().increment_master(
			increment=c_in.parameters[0], upper_limit=len(self.get_active_stack()))
		self.apply()
		self.persist()

	def geometry(self, c_in: UserEvent):
		parameters = list(map(lambda word: int(word), c_in.vim_command_parameter.split()))
		lib = parameters[0]
		window = self.get_active_windows_as_list()[parameters[1]]
		x = parameters[2]
		y = parameters[3]
		gdk_monitor = Gdk.Display.get_default().get_monitor_at_point(x, y)
		if 'gdk' == lib:
			gdk_window_for(window).move(x + gdk_monitor.get_workarea().x, y + gdk_monitor.get_workarea().y)
		else:
			window.set_geometry(
				Wnck.WindowGravity.STATIC, X_Y_W_H_GEOMETRY_MASK,
				x + gdk_monitor.get_workarea().x, y + gdk_monitor.get_workarea().y,
				parameters[4] if len(parameters) > 4 else window.get_geometry().widthp,
				parameters[5] if len(parameters) > 5 else window.get_geometry().heightp)
		self.windows.staging = True

	#
	# COMMAND METHODS
	#
	def apply(self, split_points: List[int] = None):
		primary_monitor: Monitor = self.get_active_primary_monitor()
		workspace_windows = self.get_active_windows_as_list()
		monitor = primary_monitor
		visible = workspace_windows
		split_point = len(list(filter(lambda w: primary_monitor.contains(w), visible)))

		while monitor and visible:

			if monitor.function_key:
				monitor_windows: List[Wnck.Window] = visible[:split_point]
				FUNCTIONS_MAP[monitor.function_key](monitor_windows, monitor)

			monitor = monitor.next()
			visible = visible[split_point:]
			split_point = len(visible)

	def _incremented_index(self, increment):
		stack = self.get_active_stack()
		active = get_active_managed_window()
		old_index = stack.index(active.get_xid())
		new_index = old_index + increment
		return min(max(new_index, 0), len(stack) - 1)

	def resume(self):
		resume = ''
		resume += '[gap] inner: {} outer: {}\n'.format(state.get_inner_gap(), state.get_outer_gap())
		for workspace in Wnck.Screen.get_default().get_workspaces():
			resume += 'Workspace {}\n'.format(workspace.get_number())
			for i in range(Gdk.Display.get_default().get_n_monitors()):
				m = Gdk.Display.get_default().get_monitor(i)
				rect = m.get_workarea()
				primary_monitor = self.primary_monitors[workspace.get_number()]
				monitor: Monitor = primary_monitor if m.is_primary() else primary_monitor.next()

				resume += '\tMonitor\t\t\tLayout: {}\tPrimary: {}\n'.format(
					FUNCTIONS_MAP[monitor.function_key].__name__ if monitor.function_key else None, m.is_primary())
				resume += '\t\t[GDK]\t\tRectangle: {:5}, {:5}, {:5}, {:5}\n'.format(
					rect.x, rect.y, rect.width, rect.height)
				resume += '\t\t[PROCRIS]\tRectangle: {:5}, {:5}, {:5}, {:5}\n'.format(
					monitor.wx, monitor.wy, monitor.ww, monitor.wh)

				resume += '\t\t[Stack]\t\t('
				for xid in filter(lambda _xid: monitor.contains(self.window_by_xid[_xid]), self.stacks[workspace.get_number()]):
					resume += '{:10} '.format(xid)
				resume += ')\n'

		return resume


#
# LAYOUTS
#
# https://git.suckless.org/dwm/file/dwm.c.html#l1674
# MIT/X Consortium License
#
# © 2006-2019 Anselm R Garbe <anselm@garbe.ca>
# © 2006-2009 Jukka Salmi <jukka at salmi dot ch>
# © 2006-2007 Sander van Dijk <a dot h dot vandijk at gmail dot com>
# © 2007-2011 Peter Hartlich <sgkkr at hartlich dot com>
# © 2007-2009 Szabolcs Nagy <nszabolcs at gmail dot com>
# © 2007-2009 Christof Musik <christof at sendfax dot de>
# © 2007-2009 Premysl Hruby <dfenze at gmail dot com>
# © 2007-2008 Enno Gottox Boland <gottox at s01 dot de>
# © 2008 Martin Hurton <martin dot hurton at gmail dot com>
# © 2008 Neale Pickett <neale dot woozle dot org>
# © 2009 Mate Nagy <mnagy at port70 dot net>
# © 2010-2016 Hiltjo Posthuma <hiltjo@codemadness.org>
# © 2010-2012 Connor Lane Smith <cls@lubutu.com>
# © 2011 Christoph Lohmann <20h@r-36.net>
# © 2015-2016 Quentin Rameau <quinq@fifth.space>
# © 2015-2016 Eric Pruitt <eric.pruitt@gmail.com>
# © 2016-2017 Markus Teich <markus.teich@stusta.mhn.de>
def tile(stack: List[Wnck.Window], m):
	n = len(stack)

	if n > m.nmaster:
		mw = m.ww * m.mfact if m.nmaster else 0
	else:
		mw = m.ww
	my = ty = 0
	padding = state.get_inner_gap()

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


# https://git.suckless.org/dwm/file/dwm.c.html#l1104
def monocle(stack, monitor):
	padding = state.get_inner_gap()
	for window in stack:
		set_geometry(
			window,
			x=monitor.wx + padding, y=monitor.wy + padding,
			w=monitor.ww - padding * 2, h=monitor.wh - padding * 2)


# https://dwm.suckless.org/patches/centeredmaster/
def centeredmaster(stack: List[Wnck.Window], m: Monitor):
	tw = mw = m.ww
	mx = my = 0
	oty = ety = 0
	n = len(stack)
	padding = state.get_inner_gap()

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


def centeredfloatingmaster(stack: List[Wnck.Window], m: Monitor):
	padding = state.get_inner_gap()
	# i, n, w, mh, mw, mx, mxo, my, myo, tx = 0
	tx = mx = 0

	# count number of clients in the selected monitor
	n = len(stack)

	# initialize nmaster area
	if n > m.nmaster:
		# go mfact box in the center if more than nmaster clients
		if m.ww > m.wh:
			mw = m.ww * m.mfact if m.nmaster else 0
			mh = m.wh * 0.9 if m.nmaster else 0
		else:
			mh = m.wh * m.mfact if m.nmaster else 0
			mw = m.ww * 0.9 if m.nmaster else 0
		mx = mxo = (m.ww - mw) / 2
		my = myo = (m.wh - mh) / 2
	else:
		# go fullscreen if all clients are in the master area
		mh = m.wh
		mw = m.ww
		mx = mxo = 0
		my = myo = 0

	for i in range(len(stack)):
		c = stack[i]
		if i < m.nmaster:
			# nmaster clients are stacked horizontally, in the center of the screen
			w = (mw + mxo - mx) / (min(n, m.nmaster) - i)
			synchronized = set_geometry(
				c, synchronous=True,
				x=m.wx + mx + padding, y=m.wy + my + padding,
				w=w, h=mh - padding * 2)
			mx += get_width(c)
		else:
			# stack clients are stacked horizontally
			w = (m.ww - tx) / (n - i) - (padding * 2)
			synchronized = set_geometry(
				c, synchronous=True,
				x=m.wx + tx + padding, y=m.wy + padding,
				w=w, h=m.wh - padding * 2)
			tx += get_width(c) + padding * 2


# https://dwm.suckless.org/patches/fibonacci/
# Credit:
# Niki Yoshiuchi - aplusbi@gmail.com
# Joe Thornber
# Jan Christoph Ebersbach
def fibonacci(mon: Monitor, stack: List[int], s: int):
	n = len(stack)
	nx = mon.wx
	ny = 0
	nw = mon.ww
	nh = mon.wh
	padding = state.get_inner_gap()

	for i in range(n):
		c = stack[i]
		c.bw = 0
		if (i % 2 and nh / 2 > 2 * c.bw) or (not (i % 2) and nw / 2 > 2 * c.bw):
			if i < n - 1:
				if i % 2:
					nh /= 2
				else:
					nw /= 2
				if (i % 4) == 2 and not s:
					nx += nw
				elif (i % 4) == 3 and not s:
					ny += nh
			if (i % 4) == 0:
				if s:
					ny += nh
				else:
					ny -= nh
			elif (i % 4) == 1:
				nx += nw
			elif (i % 4) == 2:
				ny += nh
			elif (i % 4) == 3:
				if s:
					nx += nw
				else:
					nx -= nw
			if i == 0:
				if n != 1:
					nw = mon.ww * mon.mfact
				ny = mon.wy
			elif i == 1:
				nw = mon.ww - nw
		set_geometry(
			c,
			x=nx + padding, y=ny + padding,
			w=nw - padding * 2, h=nh - padding * 2)


def dwindle(stack: List[Wnck.Window], monitor: Monitor):
	fibonacci(monitor, stack, 1)


def spiral(stack: List[Wnck.Window], monitor: Monitor):
	fibonacci(monitor, stack, 0)


def biasedstack(stack: List[Wnck.Window], monitor: Monitor):
	n = len(stack)
	if n == 1:
		resize(stack[0], l=0.15, t=0.1, w=0.7, h=0.86)
		return
	oty = 0
	mw = int(monitor.ww * monitor.mfact) if monitor.nmaster else 0
	mx = tw = int((monitor.ww - mw) / 2)
	my = 0
	padding = state.get_inner_gap()

	for i in range(n):
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


FUNCTIONS_MAP = {
	None: None,
	'M': monocle, 'T': tile,
	'C': centeredmaster, '>': centeredfloatingmaster, 'B': biasedstack,
	'@': spiral, '\\': dwindle
}
