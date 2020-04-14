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
import traceback, gi, os, re
import pocoy.messages as messages
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, Gdk, Gtk
from typing import List, Dict, Callable
from pocoy.names import PROMPT
from pocoy.wm import gdk_window_for, resize, is_visible, \
	get_active_window, decoration_delta, UserEvent, monitor_for, X_Y_W_H_GEOMETRY_MASK, \
	is_managed, get_active_managed_window
from pocoy.decoration import DECORATION_MAP
from pocoy import decoration, state


def statefull(function):
	def read_screen_before(self, user_event: UserEvent):
		screen = Wnck.Screen.get_default()
		windows.read(screen)
		function(self, user_event)
	return read_screen_before


def persistent(function):
	def notify_changes_after(self, user_event: UserEvent):
		function(self, user_event)
		import pocoy.controller as controller
		controller.notify_layout_change()
	return notify_changes_after


class Windows:

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

		monitors.read(screen)

		for wnck_window in screen.get_windows():
			self.window_by_xid[wnck_window.get_xid()] = wnck_window
			if wnck_window.get_pid() == os.getpid() or wnck_window.is_skip_tasklist():
				continue

			self.buffers.append(wnck_window)

			if wnck_window.is_in_viewport(screen.get_active_workspace()) and not wnck_window.is_minimized():
				self.visible.append(wnck_window)

		active_window.read_screen()

		def sort_line(w):
			geometry = w.get_geometry()
			return geometry.xp * STRETCH + geometry.yp

		self.line = sorted(self.visible, key=sort_line)

		for workspace in screen.get_workspaces():
			monitor = monitors.get_primary(workspace)
			while monitor:
				stack = monitor.stack
				monitor = monitor.next()

		for workspace in screen.get_workspaces():
			self._read_workspace(screen, workspace)

	def _read_workspace(self, screen: Wnck.Screen, workspace: Wnck.Workspace):
		for i in range(Gdk.Display.get_default().get_n_monitors()):
			gdk_monitor = Gdk.Display.get_default().get_monitor(i)
			self._read_workspace_monitor(screen, workspace, gdk_monitor)

	def _read_workspace_monitor(self, screen: Wnck.Screen, workspace: Wnck.Workspace, gdk_monitor: Gdk.Monitor):
		primary = monitors.get_primary(workspace)
		monitor = primary if gdk_monitor.is_primary() else primary.next()
		stack = monitor.stack

		def monitor_filter(w):
			return w.get_xid() not in stack and is_visible(w, workspace, gdk_monitor) and is_managed(w)

		for old in filter(lambda xid: xid not in self.window_by_xid, stack.copy()):
			stack.remove(old)

		for outside in filter(lambda xid: not is_visible(self.window_by_xid[xid], workspace, gdk_monitor), stack.copy()):
			stack.remove(outside)

		stack.extend(map(lambda w: w.get_xid(), filter(monitor_filter, reversed(screen.get_windows_stacked()))))

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

	# TODO: does need to clean stacked xid???
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

	def complete(self, user_event: UserEvent):
		if not user_event.vim_command_spacer:
			return None
		name = user_event.vim_command_parameter
		names = map(lambda x: x.get_name().strip(), self.buffers)
		filtered = filter(lambda x: name.lower().strip() in x.lower(), names)
		return list(filtered)

	#
	# COMMANDS
	#
	@statefull
	def decorate(self, user_event: UserEvent):
		self.apply_decoration_config()

	@statefull
	def list(self, user_event: UserEvent):
		if user_event.text:
			messages.add(messages.Message(PROMPT + user_event.text, 'info'))
		from pocoy.view import BufferName
		for window in self.buffers:
			messages.add(BufferName(window, self))

	@statefull
	def activate(self, user_event: UserEvent):
		buffer_number_match = re.match(r'^\s*(buffer|b)\s*([0-9]+)\s*$', user_event.text)
		if buffer_number_match:
			buffer_number = buffer_number_match.group(2)
			index = int(buffer_number) - 1
			if index < len(self.buffers):
				active_window.xid = self.buffers[index].get_xid()
				self.staging = True
			else:
				return messages.Message('Buffer {} does not exist'.format(buffer_number), 'error')
		elif user_event.vim_command_parameter:
			window_title = user_event.vim_command_parameter
			w = self.find_by_name(window_title)
			if w:
				active_window.xid = w.get_xid()
				self.staging = True
			else:
				return messages.Message('No matching buffer for ' + window_title, 'error')

	@statefull
	def delete(self, user_event: UserEvent):

		if not user_event.vim_command_parameter:
			if active_window.xid:
				self.remove(active_window.get_wnck_window(), user_event.time)
				self.staging = True
				return
			return messages.Message('There is no active window', 'error')

		if re.match(r'^([0-9]+\s*)+$', user_event.vim_command_parameter):
			to_delete = []
			for number in re.findall(r'\d+', user_event.vim_command_parameter):
				index = int(number) - 1
				if index < len(self.buffers):
					to_delete.append(self.buffers[index])
				else:
					return messages.Message('No buffers were deleted', 'error')
			for window in to_delete:
				self.remove(window, user_event.time)
			self.staging = True if to_delete else False
			return

		w = self.find_by_name(user_event.vim_command_parameter)
		if w:
			self.remove(w, user_event.time)
			self.staging = True
		else:
			return messages.Message('No matching buffer for ' + user_event.vim_command_parameter, 'error')

	@statefull
	def geometry(self, user_event: UserEvent):
		# TODO: if the first parameter remains the lib, can convert all to int
		parameters = list(map(lambda word: int(word), user_event.vim_command_parameter.split()))
		lib = parameters[0]
		index = parameters[1]
		monitor = monitors.get_active()
		window = list(map(lambda xid: self.window_by_xid[xid], monitor.stack))[index]

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

	@statefull
	def only(self, user_event: UserEvent):
		for w in windows.visible.copy():
			if self.xid != w.get_xid():
				w.minimize()
				windows.remove_from_visible(w)
		windows.staging = True

	@statefull
	def minimize(self, user_event: UserEvent):
		if self.xid:
			active_window = self.get_wnck_window()
			active_window.minimize()
			windows.remove_from_visible(active_window)
			self.read_screen()
			windows.staging = True

	@statefull
	def maximize(self, user_event: UserEvent):
		if self.xid:
			self.get_wnck_window().maximize()
			windows.staging = True

	@statefull
	def move_right(self, user_event: UserEvent):
		self._snap_active_window(HORIZONTAL, 0.5)

	@statefull
	def move_left(self, user_event: UserEvent):
		self._snap_active_window(HORIZONTAL, 0)

	@statefull
	def move_up(self, user_event: UserEvent):
		self._snap_active_window(VERTICAL, 0)

	@statefull
	def move_down(self, user_event: UserEvent):
		self._snap_active_window(VERTICAL, 0.5)

	def _snap_active_window(self, axis, position):
		self._move_on_axis(self.get_wnck_window(), axis, position, 0.5)

	def _move_on_axis(self, window, axis, position, proportion):
		if axis == HORIZONTAL:
			resize(window, l=position, t=0, w=proportion, h=1)
		else:
			resize(window, l=0, t=position, w=1, h=proportion)
		windows.staging = True

	@statefull
	def centralize(self, user_event: UserEvent):
		resize(self.get_wnck_window(), l=0.1, t=0.1, w=0.8, h=0.8)
		windows.staging = True

	@statefull
	def decorate(self, user_event: UserEvent):
		decoration_parameter = user_event.vim_command_parameter
		if decoration_parameter in DECORATION_MAP.keys():
			opt = DECORATION_MAP[decoration_parameter]
		gdk_window = gdk_window_for(self.get_wnck_window())
		gdk_window.set_decorations(opt)
		windows.staging = True

	@statefull
	@persistent
	def zoom(self, user_event: UserEvent):
		active = get_active_managed_window()
		monitor = monitors.get_active(active)
		stack = monitor.stack
		if not active or len(stack) < 2:
			return

		old_index = stack.index(active.get_xid())
		if old_index == 0:
			stack.insert(1, stack.pop(old_index))
		else:
			stack.insert(0, stack.pop(old_index))
		active_window.xid = stack[0]
		windows.staging = True
		monitor.apply()

	@statefull
	@persistent
	def pushstack(self, user_event: UserEvent):
		active = get_active_managed_window()
		if not active:
			return
		direction = user_event.parameters[0]
		monitor = monitors.get_active()
		old_index = monitor.index(active.get_xid())
		new_index = monitor.index(active.get_xid(), direction)

		if new_index != old_index:
			stack = monitor.stack
			stack.insert(new_index, stack.pop(old_index))
			monitor.apply()

	@statefull
	def focusstack(self, user_event: UserEvent):
		active = get_active_managed_window()
		if not active:
			return
		direction = user_event.parameters[0]
		monitor = monitors.get_active()
		new_index = monitor.index(active.get_xid(), direction)
		active_window.change_to(monitor.stack[new_index])

	@statefull
	@persistent
	def killclient(self, user_event: UserEvent):
		active_window = self.get_wnck_window()
		if active_window:
			monitor = monitors.get_active()
			stack = monitor.stack
			index = stack.index(get_active_managed_window().get_xid())
			windows.remove(active_window, user_event.time)
			self.xid = stack[min(index, len(stack) - 1)]
			windows.staging = True
			monitor.apply()

	@statefull
	def focus_right(self, user_event: UserEvent):
		self.move_focus(1, HORIZONTAL)

	@statefull
	def focus_left(self, user_event: UserEvent):
		self.move_focus(-1, HORIZONTAL)

	@statefull
	def focus_up(self, user_event: UserEvent):
		self.move_focus(-1, VERTICAL)

	@statefull
	def focus_down(self, user_event: UserEvent):
		self.move_focus(1, VERTICAL)

	@statefull
	def focus_previous(self, user_event: UserEvent):
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

	@statefull
	def focus_next(self, user_event: UserEvent):
		direction = 1 if not user_event or Gdk.keyval_name(user_event.keyval).islower() else -1
		i = windows.line.index(self.get_wnck_window())
		next_window = windows.line[(i + direction) % len(windows.line)]
		self.xid = next_window.get_xid()
		windows.staging = True


# https://valadoc.org/gdk-3.0/Gdk.Monitor.html
class Monitor:

	def __init__(self, primary: bool = False, nmaster: int = 1, mfact: float = 0.5, function_key: str = 'T'):
		self.primary: bool = primary
		# TODO: rename to layout key
		self.function_key: str = function_key
		self.nmaster: int = nmaster
		self.mfact: float = mfact
		self.wx = self.wy = self.ww = self.wh = None
		self.visible_area: Gdk.Rectangle = None
		self.stack: List[int] = []
		self.pointer: Monitor = None

	def index(self, xid: int, increment: int = 0):
		old_index = self.stack.index(xid)
		new_index = old_index + increment
		return min(max(new_index, 0), len(self.stack) - 1)

	def apply(self, unmaximize: bool = False):
		from pocoy.layout import FUNCTIONS_MAP
		if self.function_key:
			spread_windows: List[Wnck.Window] = list(map(lambda xid: windows.window_by_xid[xid], self.stack))
			if unmaximize:
				for window in spread_windows:
					if window.is_maximized():
						window.unmaximize()
			FUNCTIONS_MAP[self.function_key](spread_windows, self)

	def set_rectangle(self, rectangle: Gdk.Rectangle):
		self.visible_area = rectangle
		self.update_work_area()

	def update_work_area(self):
		outer_gap = state.get_outer_gap()
		self.wx = self.visible_area.x + outer_gap
		self.wy = self.visible_area.y + outer_gap
		self.ww = self.visible_area.width - outer_gap * 2
		self.wh = self.visible_area.height - outer_gap * 2

	def increase_master_area(self, increment: float = None):
		self.mfact += increment
		self.mfact = max(0.1, self.mfact)
		self.mfact = min(0.9, self.mfact)

	def increment_master(self, increment=None):
		self.nmaster += increment
		self.nmaster = max(0, self.nmaster)
		self.nmaster = min(len(self.stack), self.nmaster)

	def contains(self, window: Wnck.Window):
		rect = self.visible_area
		xp, yp, widthp, heightp = window.get_geometry()
		return rect.x <= xp < (rect.x + rect.width) and rect.y <= yp < (rect.y + rect.height)

	def from_json(self, json):
		self.nmaster = json['nmaster'] if 'nmaster' in json else self.nmaster
		self.mfact = json['mfact'] if 'mfact' in json else self.mfact
		self.function_key = json['function'] if 'function' in json else self.function_key

	def to_json(self):
		stack = self.stack
		stack_json = {}
		for xid in stack:
			stack_json[str(xid)] = {
				'name': windows.window_by_xid[xid].get_name(), 'index': stack.index(xid)}
		return {
			'nmaster': self.nmaster,
			'mfact': self.mfact,
			'function': self.function_key,
			'stack': stack_json
		}

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


class Monitors:

	primary_monitors: Dict[int, Monitor] = {}

	def read(self, screen: Wnck.Screen):
		for workspace in screen.get_workspaces():
			primary_monitor: Monitor = self.get_primary(workspace)
			for i in range(Gdk.Display.get_default().get_n_monitors()):
				gdk_monitor = Gdk.Display.get_default().get_monitor(i)
				if gdk_monitor.is_primary():
					primary_monitor.set_rectangle(gdk_monitor.get_workarea())
				elif primary_monitor.next():
					primary_monitor.next().set_rectangle(gdk_monitor.get_workarea())
					break

	#
	# Monitor API
	#
	def get_active(self, window: Wnck.Window = None) -> Monitor:
		if not window:
			window = get_active_managed_window()
		monitor: Monitor = self.get_primary(window.get_workspace())
		return monitor if not window or monitor_for(window).is_primary() else monitor.next()

	def get_primary(self, workspace: Wnck.Workspace = None) -> Monitor:
		if not workspace:
			workspace = Wnck.Screen.get_default().get_active_workspace()
		if workspace.get_number() not in self.primary_monitors:
			self.primary_monitors[workspace.get_number()] = Monitor(primary=True)
		return self.primary_monitors[workspace.get_number()]


class ActiveMonitor:

	last_layout_key = None

	#
	# COMMANDS
	#
	@statefull
	@persistent
	def setlayout(self, user_event: UserEvent):
		promote_selected = False if len(user_event.parameters) < 2 else user_event.parameters[1]
		active = get_active_managed_window()
		monitor = monitors.get_active(active)
		stack = monitor.stack
		if promote_selected and active:
			old_index = stack.index(active.get_xid())
			stack.insert(0, stack.pop(old_index))

		if user_event.parameters:
			new_layout = user_event.parameters[0]
		else:
			new_layout = self.last_layout_key

		if monitor.function_key != new_layout:
			self.last_layout_key = monitor.function_key

		monitor.function_key = new_layout
		monitor.apply(unmaximize=True)

	@statefull
	def gap(self, user_event: UserEvent):
		parameters = user_event.vim_command_parameter.split()
		where = parameters[0]
		pixels = int(parameters[1])
		state.set_outer_gap(pixels) if where == 'outer' else state.set_inner_gap(pixels)
		monitor = monitors.get_active()
		while monitor:
			monitors.get_active().update_work_area()
			# TODO: remove staging logic
			windows.staging = True
			monitor.apply()
			monitor = monitor.next()

	def complete_gap_options(self, user_event: UserEvent):
		input = user_event.vim_command_parameter.lower()
		return list(filter(lambda x: input != x and input in x, ['inner', 'outer']))

	@statefull
	@persistent
	def setmfact(self, user_event: UserEvent):
		monitor = monitors.get_active()
		monitor.increase_master_area(increment=user_event.parameters[0])
		monitor.apply()

	@statefull
	@persistent
	def incnmaster(self, user_event: UserEvent):
		monitor = monitors.get_active()
		monitor.increment_master(increment=user_event.parameters[0])
		monitor.apply()


class Axis:
	position_mask: Wnck.WindowMoveResizeMask
	size_mask: Wnck.WindowMoveResizeMask

	def __init__(self, position_mask, size_mask):
		self.position_mask = position_mask
		self.size_mask = size_mask

	def position_of(self, window: Wnck.Window):
		return window.get_geometry().xp if self is HORIZONTAL else window.get_geometry().yp


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

		if False and 'stack' in workspace_json:
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
	windows.apply_decoration_config()
	monitor = monitors.get_primary()
	while monitor:
		monitor.apply(unmaximize=True)
		monitor = monitor.next()


def persist():
	screen = Wnck.Screen.get_default()
	workspaces: List[Dict] = []
	props = {'workspaces': workspaces}

	for workspace in screen.get_workspaces():
		workspace_json = {'monitors': []}
		workspaces.append(workspace_json)
		monitor = monitors.get_primary(workspace)
		while monitor:
			workspace_json['monitors'].append(monitor.to_json())
			monitor = monitor.next()

	state.persist_workspace(props)


#
# Internal API
#
def resume():
	from pocoy.layout import FUNCTIONS_MAP
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


INCREMENT = 0.1
DECREMENT = -0.1
CENTER = 0.5
VERTICAL = Axis(Wnck.WindowMoveResizeMask.Y, Wnck.WindowMoveResizeMask.HEIGHT)
HORIZONTAL = Axis(Wnck.WindowMoveResizeMask.X, Wnck.WindowMoveResizeMask.WIDTH)
HORIZONTAL.perpendicular = VERTICAL
VERTICAL.perpendicular = HORIZONTAL
STRETCH = 1000
windows: Windows = Windows()
active_window = ActiveWindow()
monitors: Monitors = Monitors()
active_monitor: ActiveMonitor = ActiveMonitor()
