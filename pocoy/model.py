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
import traceback
import gi, os, re
import pocoy.messages as messages
import pocoy.state as state
from pocoy import decoration, desktop, scratchpads
from pocoy.layout import FUNCTIONS_MAP
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, Gdk
from typing import List, Dict, Callable
from pocoy.names import PROMPT
from pocoy.wm import gdk_window_for, resize, is_visible, \
	get_active_window, decoration_delta, UserEvent, Monitor, monitor_for, DirtyState, Trap, X_Y_W_H_GEOMETRY_MASK, \
	is_buffer
from pocoy.decoration import DECORATION_MAP


class Windows:

	stacks: Dict[int, List[int]] = {}
	window_by_xid: Dict[int, Wnck.Window] = {}

	def __init__(self):
		self.visible: List[Wnck.Window] = []
		self.buffers: List[Wnck.Window] = []
		self.line: List[Wnck.Window] = None
		self.staging = False

	def read_default_screen(self, force_update=True):
		self.read(Wnck.Screen.get_default(), force_update=force_update)

	def read(self, screen: Wnck.Screen, force_update=True):
		del self.buffers[:]
		del self.visible[:]
		active_window.clean()
		self.window_by_xid.clear()

		if force_update:
			screen.force_update()  # make sure we query X server

		for wnck_window in screen.get_windows():
			self.window_by_xid[wnck_window.get_xid()] = wnck_window
			if wnck_window.get_pid() == os.getpid() or wnck_window.is_skip_tasklist():
				continue

			self.buffers.append(wnck_window)

			if wnck_window.is_in_viewport(screen.get_active_workspace()) and not wnck_window.is_minimized():
				self.visible.append(wnck_window)

		active_window.read_screen()
		self.line = sorted(self.visible, key=sort_line)

		for workspace in screen.get_workspaces():
			primary_monitor: Monitor = monitors.primary_monitor_for(workspace)
			self._read_workspace(screen, workspace, primary_monitor)

	def _read_workspace(self, screen: Wnck.Screen, workspace: Wnck.Workspace, primary_monitor):
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

		copy = stack.copy()
		stack.sort(key=lambda xid: copy.index(xid) + (10000 if not primary_monitor.contains(self.window_by_xid[xid]) else 0))

	#
	# API
	#
	def commit_navigation(self, event_time):
		"""
		Commits any staged change in the active window
		"""
		if self.staging and active_window.xid and active_window.get_wnck_window():
			active_window.get_wnck_window().activate_transient(event_time)
		self.staging = False

	# TODO: keep the 'stack' name?
	def get_active_stack(self) -> List[int]:
		return self.stack_for(Wnck.Screen.get_default().get_active_workspace())

	def stack_for(self, workspace: Wnck.Workspace) -> List[int]:
		if workspace.get_number() not in self.stacks:
			self.stacks[workspace.get_number()] = []
		return self.stacks[workspace.get_number()]

	def get_active_windows_as_list(self) -> List[Wnck.Window]:
		return list(map(lambda xid: self.window_by_xid[xid], self.get_active_stack()))

	def get_stack_index(self, increment):
		stack = self.get_active_stack()
		active = get_active_managed_window()
		old_index = stack.index(active.get_xid())
		new_index = old_index + increment
		return min(max(new_index, 0), len(stack) - 1)

	def remove(self, window, time):
		window.close(time)
		if window in self.visible:
			self.remove_from_visible(window)
		self.buffers.remove(window)
		active_window.read_screen()

	def remove_from_visible(self, window: Wnck.Window):
		self.visible.remove(window)
		self.line.remove(window)

	def apply_decoration_config(self):
		if state.is_remove_decorations():
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
	def decorate(self, user_event: UserEvent):
		self.apply_decoration_config()

	def list(self, user_event: UserEvent):
		if user_event.text:
			messages.add(messages.Message(PROMPT + user_event.text, 'info'))
		from pocoy.view import BufferName
		for window in self.buffers:
			messages.add(BufferName(window, self))

	def activate(self, c_in):
		buffer_number_match = re.match(r'^\s*(buffer|b)\s*([0-9]+)\s*$', c_in.text)
		if buffer_number_match:
			buffer_number = buffer_number_match.group(2)
			index = int(buffer_number) - 1
			if index < len(self.buffers):
				active_window.xid = self.buffers[index].get_xid()
				self.staging = True
			else:
				return messages.Message('Buffer {} does not exist'.format(buffer_number), 'error')
		elif c_in.vim_command_parameter:
			window_title = c_in.vim_command_parameter
			w = self.find_by_name(window_title)
			if w:
				active_window.xid = w.get_xid()
				self.staging = True
			else:
				return messages.Message('No matching buffer for ' + window_title, 'error')

	def delete(self, c_in):

		if not c_in.vim_command_parameter:
			if active_window.xid:
				self.remove(active_window.get_wnck_window(), c_in.time)
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

	def geometry(self, user_event: UserEvent):
		# TODO: if the first parameter remains the lib, can convert all to int
		parameters = list(map(lambda word: int(word), user_event.vim_command_parameter.split()))
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
		windows.staging = True

	#
	# COMMAND OPERATIONS
	#
	def get_top_two_windows(self):
		top = active_window.get_wnck_window()
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


class Monitors:

	primary_monitors: Dict[int, Monitor] = {}

	#
	# Monitor API
	#
	# TODO: clean, the Monitor work is already at the class name
	def get_active(self) -> Monitor:
		active = get_active_managed_window()
		return self.monitor_of(active) if active else self.get_active_primary_monitor()

	def monitor_of(self, window: Wnck.Window) -> Monitor:
		monitor: Monitor = self.get_active_primary_monitor()
		return monitor if monitor_for(window).is_primary() else monitor.next()

	def get_active_primary_monitor(self) -> Monitor:
		return self.primary_monitor_for(Wnck.Screen.get_default().get_active_workspace())

	def primary_monitor_for(self, workspace: Wnck.Workspace) -> Monitor:
		if workspace.get_number() not in self.primary_monitors:
			self.primary_monitors[workspace.get_number()] = Monitor(primary=True)
		return self.primary_monitors[workspace.get_number()]


class ActiveMonitor:

	last_layout_key = None

	#
	# COMMANDS
	#
	def setlayout(self, user_event: UserEvent):
		promote_selected = False if len(user_event.parameters) < 2 else user_event.parameters[1]
		active = get_active_managed_window()
		if promote_selected and active:
			stack = windows.get_active_stack()
			old_index = stack.index(active.get_xid())
			stack.insert(0, stack.pop(old_index))
		if user_event.parameters:
			function_key = user_event.parameters[0]
		else:
			function_key = self.last_layout_key
		self._set_function(function_key)

	def _set_function(self, new):
		active = monitors.get_active()
		if active.function_key != new:
			self.last_layout_key = active.function_key
		active.function_key = new
		apply()
		persist()
		desktop.show_monitor(monitors.get_active_primary_monitor())

	def gap(self, user_event: UserEvent):
		parameters = user_event.vim_command_parameter.split()
		where = parameters[0]
		pixels = int(parameters[1])
		state.set_outer_gap(pixels) if where == 'outer' else state.set_inner_gap(pixels)
		monitors.get_active_primary_monitor().update_work_area()
		windows.staging = True
		apply()

	def complete_gap_options(self, user_event: UserEvent):
		input = user_event.vim_command_parameter.lower()
		return list(filter(lambda x: input != x and input in x, ['inner', 'outer']))

	def setmfact(self, user_event: UserEvent):
		monitors.get_active_primary_monitor().increase_master_area(increment=user_event.parameters[0])
		apply()
		persist()

	def incnmaster(self, user_event: UserEvent):
		monitors.get_active_primary_monitor().increment_master(
			increment=user_event.parameters[0], upper_limit=len(windows.get_active_stack()))
		apply()
		persist()


class ActiveWindow:

	def __init__(self):
		self.xid = None

	def get_wnck_window(self):
		for w in windows.buffers:
			if w.get_xid() == self.xid:
				return w
		return None

	def read_screen(self):
		active_window = get_active_window(window_filter=lambda x: x in windows.visible)
		self.xid = active_window.get_xid() if active_window else None

	def clean(self):
		self.xid = None

	def change_to(self, xid: int):
		if self.xid != xid:
			self.xid = xid
			windows.staging = True

	def only(self, c_in):
		for w in windows.visible.copy():
			if self.xid != w.get_xid():
				w.minimize()
				windows.remove_from_visible(w)
		windows.staging = True

	def minimize(self, c_in):
		if self.xid:
			active_window = self.get_wnck_window()
			active_window.minimize()
			windows.remove_from_visible(active_window)
			self.read_screen()
			windows.staging = True

	def maximize(self, c_in):
		if self.xid:
			self.get_wnck_window().maximize()
			windows.staging = True

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
		windows.staging = True

	def centralize(self, c_in):
		resize(self.get_wnck_window(), l=0.1, t=0.1, w=0.8, h=0.8)
		windows.staging = True

	# TODO: apply layout
	def decorate(self, c_in):
		decoration_parameter = c_in.vim_command_parameter
		if decoration_parameter in DECORATION_MAP.keys():
			opt = DECORATION_MAP[decoration_parameter]
		gdk_window = gdk_window_for(self.get_wnck_window())
		# TODO: UnboundLocalError: local variable 'opt' referenced before assignment
		gdk_window.set_decorations(opt)
		windows.staging = True

	def zoom(self, user_event: UserEvent):
		active = get_active_managed_window()
		stack = windows.get_active_stack()
		if not active or len(stack) < 2:
			return

		old_index = stack.index(active.get_xid())
		if old_index == 0:
			stack.insert(1, stack.pop(old_index))
		else:
			stack.insert(0, stack.pop(old_index))
		active_window.xid = stack[0]
		windows.staging = True
		apply()
		persist()

	def pushstack(self, user_event: UserEvent):
		active = get_active_managed_window()
		if not active:
			return
		direction = user_event.parameters[0]

		stack = windows.get_active_stack()
		old_index = stack.index(active.get_xid())
		new_index = windows.get_stack_index(direction)

		if new_index != old_index:
			stack.insert(new_index, stack.pop(old_index))
			apply()
			persist()

	def focus_right(self, c_in):
		self.move_focus(1, HORIZONTAL)

	def focus_left(self, c_in):
		self.move_focus(-1, HORIZONTAL)

	def focus_up(self, c_in):
		self.move_focus(-1, VERTICAL)

	def focus_down(self, c_in):
		self.move_focus(1, VERTICAL)

	def focus_previous(self, c_in):
		stack = list(filter(lambda x: x in windows.visible, Wnck.Screen.get_default().get_windows_stacked()))
		i = stack.index(self.get_wnck_window())
		self.xid = stack[i - 1].get_xid()
		windows.staging = True

	def move_focus(self, increment, axis):
		active = self.get_wnck_window()

		def key(w):
			axis_position = axis.position_of(w)
			perpendicular_distance = abs(axis.perpendicular.position_of(w) - axis.perpendicular.position_of(active))
			perpendicular_distance *= -1 if axis_position < axis.position_of(active) else 1
			return axis_position * STRETCH + perpendicular_distance

		sorted_windows = sorted(windows.visible, key=key)
		index = sorted_windows.index(self.get_wnck_window())
		if 0 <= index + increment < len(sorted_windows):
			index = index + increment
			next_index = index + increment
			while 0 <= next_index < len(sorted_windows) and axis.position_of(sorted_windows[index]) == axis.position_of(active):
				index = next_index
				next_index += increment
		self.xid = sorted_windows[index].get_xid()
		windows.staging = True

	def focus_next(self, c_in):
		direction = 1 if not c_in or Gdk.keyval_name(c_in.keyval).islower() else -1
		i = windows.line.index(self.get_wnck_window())
		next_window = windows.line[(i + direction) % len(windows.line)]
		self.xid = next_window.get_xid()
		windows.staging = True

	def focusstack(self, user_event: UserEvent):
		if get_active_managed_window():
			stack = windows.get_active_stack()
			direction = user_event.parameters[0]
			new_index = windows.get_stack_index(direction)
			active_window.change_to(stack[new_index])


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


def is_managed(window):
	return is_buffer(window) and window.get_name() not in scratchpads.names()


# TODO: move to monitors?
def get_active_managed_window():
	active = Wnck.Screen.get_default().get_active_window()
	return active if active and is_managed(active) else None


#
# CALLBACKS
#
def _state_changed(window: Wnck.Window, changed_mask, new_state):
	maximization = changed_mask & Wnck.WindowState.MAXIMIZED_HORIZONTALLY or changed_mask & Wnck.WindowState.MAXIMIZED_VERTICALLY
	if maximization and new_state and monitors.monitor_of(window).function_key:
		window.unmaximize()
	if changed_mask & Wnck.WindowState.MINIMIZED and is_managed(window):
		windows.read(window.get_screen(), force_update=False)
		stack = windows.get_active_stack()
		if is_visible(window):
			old_index = stack.index(window.get_xid())
			stack.insert(0, stack.pop(old_index))
		apply()
		persist()


def _window_closed(screen: Wnck.Screen, window):
	try:
		if window.get_xid() in handlers_by_xid:
			window.disconnect(handlers_by_xid[window.get_xid()])
			del handlers_by_xid[window.get_xid()]
		if is_visible(window) and is_managed(window):
			windows.read(screen, force_update=False)
			apply()
	except DirtyState:
		pass  # It was just a try


def _window_opened(screen: Wnck.Screen, window: Wnck.Window):
	windows.read(screen, force_update=False)
	_install_present_window_handlers(screen)
	if not is_visible(window, screen.get_active_workspace()):
		return
	if window.get_name() in scratchpads.names():
		scratchpad = scratchpads.get(window.get_name())
		primary = Gdk.Display.get_default().get_primary_monitor().get_workarea()
		resize(window, rectangle=primary, l=scratchpad.l, t=scratchpad.t, w=scratchpad.w, h=scratchpad.h)
	elif is_managed(window):
		stack = windows.get_active_stack()
		copy = stack.copy()
		stack.sort(key=lambda xid: -1 if xid == window.get_xid() else copy.index(xid))

	try:
		with Trap():
			windows.apply_decoration_config()
			apply()
			persist()
	except DirtyState:
		pass  # It was just a try


def _viewports_changed(scree: Wnck.Screen):
	desktop.show_monitor(monitors.get_active_primary_monitor())


def _active_workspace_changed(screen: Wnck.Screen, workspace: Wnck.Workspace):
	desktop.show_monitor(monitors.get_active_primary_monitor())
	desktop.update()


def load(screen: Wnck.Screen):
	import pocoy.state as state
	windows.read(screen)
	try:
		workspace_config: Dict = state.get_workspace_config()
		read_user_config(workspace_config, screen)
	except (KeyError, TypeError):
		print('Unable to the last execution state, using default ones.')
		traceback.print_exc()
		traceback.print_stack()


def read_user_config(config_json: Dict, screen: Wnck.Screen):
	number_of_workspaces = len(screen.get_workspaces())
	configured_workspaces = len(config_json['workspaces'])
	for workspace_index in range(min(number_of_workspaces, configured_workspaces)):
		workspace_json = config_json['workspaces'][workspace_index]

		if 'stack' in workspace_json:
			stack = windows.stacks[workspace_index]
			copy = stack.copy()
			stack.sort(
				key=lambda xid:
				workspace_json['stack'][str(xid)]['index']
				if str(xid) in workspace_json['stack']
				else copy.index(xid))

		monitor_index = 0
		monitor: Monitor = monitors.primary_monitors[workspace_index]
		while monitor:
			if monitor_index < len(workspace_json['monitors']):
				monitor.from_json(workspace_json['monitors'][monitor_index])
			monitor_index += 1
			monitor = monitor.next()


def start():
	screen = Wnck.Screen.get_default()
	connect_to(screen)
	windows.apply_decoration_config()
	apply()


def connect_to(screen: Wnck.Screen):
	opened_handler_id = screen.connect("window-opened", _window_opened)
	closed_handler_id = screen.connect("window-closed", _window_closed)
	viewport_handler_id = screen.connect("viewports-changed", _viewports_changed)
	workspace_handler_id = screen.connect("active-workspace-changed", _active_workspace_changed)
	screen_handlers.extend([opened_handler_id, closed_handler_id, viewport_handler_id, workspace_handler_id])
	_install_present_window_handlers(screen)


def _install_present_window_handlers(screen: Wnck.Screen):
	for window in screen.get_windows():
		if window.get_xid() not in handlers_by_xid and is_managed(window):
			handler_id = window.connect("state-changed", _state_changed)
			handlers_by_xid[window.get_xid()] = handler_id


def stop():
	screen = Wnck.Screen.get_default()
	disconnect_from(screen)


def disconnect_from(screen: Wnck.Screen):
	windows.read(screen, force_update=False)
	for xid in handlers_by_xid.keys():
		if xid in windows.window_by_xid:
			windows.window_by_xid[xid].disconnect(handlers_by_xid[xid])
	for handler_id in screen_handlers:
		screen.disconnect(handler_id)


def persist():
	props = {'workspaces': []}
	for workspace_number in windows.stacks.keys():
		stack: List[int] = windows.stacks[workspace_number]
		stack_json = {}
		for xid in stack:
			stack_json[str(xid)] = {'name': windows.window_by_xid[xid].get_name(), 'index': stack.index(xid)}

		props['workspaces'].append({
			'stack': stack_json,
			'monitors': []
		})

		monitor: Monitor = monitors.primary_monitors[workspace_number]
		while monitor:
			props['workspaces'][workspace_number]['monitors'].append(monitor.to_json())
			monitor = monitor.next()
	state.persist_workspace(props)


#
# COMMAND METHODS
#
def apply(split_points: List[int] = None):
	primary_monitor: Monitor = monitors.get_active_primary_monitor()
	workspace_windows = windows.get_active_windows_as_list()
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


#
# Internal API
#
def resume():
	resume = ''
	for wn in windows.buffers:
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

	resume += '[gap] inner: {} outer: {}\n'.format(state.get_inner_gap(), state.get_outer_gap())
	for workspace in Wnck.Screen.get_default().get_workspaces():
		resume += 'Workspace {}\n'.format(workspace.get_number())
		for i in range(Gdk.Display.get_default().get_n_monitors()):
			m = Gdk.Display.get_default().get_monitor(i)
			rect = m.get_workarea()
			primary_monitor = monitors.primary_monitors[workspace.get_number()]
			monitor: Monitor = primary_monitor if m.is_primary() else primary_monitor.next()

			resume += '\tMonitor\t\t\tLayout: {}\tPrimary: {}\n'.format(
				FUNCTIONS_MAP[monitor.function_key].__name__ if monitor.function_key else None, m.is_primary())
			resume += '\t\t[GDK]\t\tRectangle: {:5}, {:5}, {:5}, {:5}\n'.format(
				rect.x, rect.y, rect.width, rect.height)
			resume += '\t\t[pocoy]\tRectangle: {:5}, {:5}, {:5}, {:5}\n'.format(
				monitor.wx, monitor.wy, monitor.ww, monitor.wh)

			resume += '\t\t[Stack]\t\t('
			for xid in filter(lambda _xid: monitor.contains(windows.window_by_xid[_xid]), windows.stacks[workspace.get_number()]):
				resume += '{:10} '.format(xid)
			resume += ')\n'

	return resume


screen_handlers: List[int] = []
handlers_by_xid: Dict[int, int] = {}
windows: Windows = Windows()
active_window = ActiveWindow()
monitors: Monitors = Monitors()
active_monitor: ActiveMonitor = ActiveMonitor()
