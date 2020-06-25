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
import traceback, gi, re
import pocoy.messages as messages
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, Gdk
from typing import List, Dict, Tuple
from pocoy.names import PROMPT
from pocoy.wm import gdk_window_for, resize, is_visible, \
	get_last_focused, decoration_delta, UserEvent, monitor_of, X_Y_W_H_GEOMETRY_MASK, \
	is_managed, is_buffer, \
	get_active_workspace, get_workspace_outside_primary
from pocoy.decoration import DECORATION_MAP
from pocoy import decoration, state, wm


def impure(mutates: bool = False):
	def decorator(function):
		def read_write_state(self, user_event: UserEvent):
			windows.read(Wnck.Screen.get_default())
			try:
				return function(self, user_event)
			finally:
				if mutates:
					import pocoy.controller as controller
					controller.notify_layout_change()
		return read_write_state
	return decorator


def in_visible_monitor(w: Wnck.Window):
	return (
			is_buffer(w)
			and not w.is_minimized()
			and monitors.id_for(w.get_workspace(), wm.monitor_of(w.get_xid())) in monitors.visible_ids
	)


class Windows:

	def __init__(self):
		self.window_by_xid: Dict[int, Wnck.Window] = {}
		self.buffers: List[int] = []
		self.staging = False

	def read_default_screen(self, force_update=True):
		self.read(Wnck.Screen.get_default(), force_update=force_update)

	def read(self, screen: Wnck.Screen, force_update=True):
		if force_update:
			screen.force_update()  # make sure we query X server

		monitors.read(screen)

		for wnck_window in screen.get_windows():
			xid = wnck_window.get_xid()
			self.window_by_xid[xid] = wnck_window
			if is_buffer(wnck_window):
				self.buffers.append(xid)

		active_window.read_screen()

		for workspace in screen.get_workspaces():
			self._read_workspace(screen, workspace)

	def clean(self):
		del self.buffers[:]
		active_window.clean()
		self.window_by_xid.clear()

	def _read_workspace(self, screen: Wnck.Screen, workspace: Wnck.Workspace):
		for i in range(Gdk.Display.get_default().get_n_monitors()):
			gdk_monitor = Gdk.Display.get_default().get_monitor(i)
			self._read_workspace_monitor(screen, workspace, gdk_monitor)

	def _read_workspace_monitor(self, screen: Wnck.Screen, workspace: Wnck.Workspace, gdk_monitor: Gdk.Monitor):
		monitor = monitors.of(workspace, gdk_monitor)
		clients = monitor.clients

		def monitor_filter(w):
			return w.get_xid() not in clients and is_visible(w, workspace, gdk_monitor) and is_managed(w)

		for old in filter(lambda xid: xid not in self.window_by_xid, clients.copy()):
			clients.remove(old)

		for outside in filter(lambda xid: not is_visible(self.window_by_xid[xid], workspace, gdk_monitor), clients.copy()):
			clients.remove(outside)

		clients.extend(map(lambda w: w.get_xid(), filter(monitor_filter, reversed(screen.get_windows_stacked()))))

	#
	# API
	#
	# TODO: move to ActiveWindow
	def commit_navigation(self, event_time):
		"""
		Commits any staged change in the active window
		"""
		if self.staging and active_window.xid and active_window.get_wnck_window():
			active_window.get_wnck_window().activate_transient(event_time)
		self.staging = False

	def get_window_line(self) -> List[Wnck.Window]:
		def sort_line(w):
			geometry = w.get_geometry()
			return geometry.xp * STRETCH + geometry.yp
		return sorted(filter(in_visible_monitor, Wnck.Screen.get_default().get_windows()), key=sort_line)

	def get_buffers(self):
		return list(map(lambda xid: self.window_by_xid[xid], self.buffers))

	def apply_decoration_config(self):
		if state.is_remove_decorations():
			tiled = []
			floating = []
			for monitor in monitors.all():
				(tiled if monitor.function_key else floating).extend(monitor.clients)
			decoration.remove(tiled)
			decoration.restore(floating)
		else:
			decoration.restore(self.buffers)

	#
	# Query API
	#
	def get_last_focused(self):
		return get_last_focused(window_filter=in_visible_monitor)

	def get_last_managed_focused(self):
		active = Wnck.Screen.get_default().get_active_window()
		if is_buffer(active):
			last = active
		else:
			last = get_last_focused(window_filter=in_visible_monitor)
		return last if is_managed(last) else None

	def get_previous(self):
		last = self.get_last_focused()
		if not last:
			return
		return get_last_focused(window_filter=lambda w: in_visible_monitor(w) and w is not last)

	def find_by_name(self, name):
		return next((w for w in self.get_buffers() if name.lower().strip() in w.get_name().lower()), None)

	@impure(mutates=False)
	def complete(self, user_event: UserEvent):
		if not user_event.vim_command_spacer:
			return None
		name = user_event.vim_command_parameter
		names = map(lambda x: x.get_name().strip(), self.get_buffers())
		filtered = filter(lambda x: name.lower().strip() in x.lower(), names)
		return list(filtered)

	#
	# COMMANDS
	#
	@impure(mutates=False)
	def decorate(self, user_event: UserEvent):
		self.apply_decoration_config()

	@impure(mutates=False)
	def list(self, user_event: UserEvent):
		if user_event.text:
			messages.add(messages.Message(PROMPT + user_event.text, 'info'))
		from pocoy.view import BufferName
		for window in self.get_buffers():
			messages.add(BufferName(window, self))

	@impure(mutates=False)
	def activate(self, user_event: UserEvent):
		buffer_number_match = re.match(r'^\s*(buffer|b)\s*([0-9]+)\s*$', user_event.text)
		if buffer_number_match:
			buffer_number = buffer_number_match.group(2)
			index = int(buffer_number) - 1
			if index < len(self.buffers):
				active_window.change_to(self.buffers[index])
			else:
				return messages.Message('Buffer {} does not exist'.format(buffer_number), 'error')
		elif user_event.vim_command_parameter:
			window_title = user_event.vim_command_parameter
			w = self.find_by_name(window_title)
			if w:
				active_window.change_to(w.get_xid())
			else:
				return messages.Message('No matching buffer for ' + window_title, 'error')

	@impure(mutates=False)
	def delete(self, user_event: UserEvent):
		to_delete = []

		if not user_event.vim_command_parameter:
			if active_window.xid:
				to_delete.append(active_window.xid)
			else:
				return messages.Message('There is no active window', 'error')
		elif re.match(r'^([0-9]+\s*)+$', user_event.vim_command_parameter):
			for number in re.findall(r'\d+', user_event.vim_command_parameter):
				index = int(number) - 1
				if index < len(self.buffers):
					to_delete.append(self.buffers[index])
				else:
					return messages.Message('No buffers were deleted', 'error')
		else:
			by_name = self.find_by_name(user_event.vim_command_parameter)
			if by_name:
				to_delete.append(by_name.get_xid())
			else:
				return messages.Message('No matching buffer for ' + user_event.vim_command_parameter, 'error')

		for xid in to_delete:
			self.window_by_xid[xid].close(user_event.time)

		messages.clean()

	@impure(mutates=True)
	def zoom(self, user_event: UserEvent):
		active = windows.get_last_managed_focused()
		visible_monitors = monitors.get_visible()

		if not active or len(visible_monitors) < 2:
			return

		origin = monitors.get_active(active)
		index = visible_monitors.index(origin)
		destination = visible_monitors[1 if index == 0 else 0]

		origin.switch_with(destination)

		if origin.primary and origin.clients:
			active_window.change_to(origin.clients[0])

		origin.apply()
		destination.apply()

	@impure(mutates=True)
	def pushmonitor(self, user_event: UserEvent):
		direction = user_event.parameters[0]
		window = windows.get_last_managed_focused()
		if not window:
			return
		origin = monitors.get_active(window)
		destination = origin.get_adjacent(direction)

		if not destination:
			return

		origin.switch_with(destination)
		# windows.staging = True

		origin.apply()
		destination.apply()

	@impure(mutates=False)
	def geometry(self, user_event: UserEvent):
		# TODO: if the first parameter remains the lib, can convert all to int
		parameters = list(map(lambda word: int(word), user_event.vim_command_parameter.split()))
		lib = parameters[0]
		index = parameters[1]
		monitor = monitors.get_active()
		window = list(map(lambda xid: self.window_by_xid[xid], monitor.clients))[index]

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


class ActiveWindow:

	def __init__(self):
		self.xid = None
		self.last = None

	def get_wnck_window(self):
		for buffer_xid in windows.buffers:
			if buffer_xid == self.xid:
				return windows.window_by_xid[self.xid]
		return None

	def read_screen(self):
		active = Wnck.Screen.get_default().get_active_window()
		if not active or not is_buffer(active):
			active = get_last_focused(window_filter=in_visible_monitor)
		self.xid = active.get_xid() if active else None

	def clean(self):
		self.last = self.xid = None

	def change_to(self, xid: int):
		if self.xid != xid:
			self.last = self.xid
			self.xid = xid
			windows.staging = True

	@impure(mutates=False)
	def only(self, user_event: UserEvent):
		if not self.xid:
			return
		monitor = monitors.get_active(self.get_wnck_window())
		for xid in monitor.clients:
			if self.xid != xid:
				windows.window_by_xid[xid].minimize()

	@impure(mutates=False)
	def minimize(self, user_event: UserEvent):
		if self.xid:
			self.get_wnck_window().minimize()

	@impure(mutates=False)
	def maximize(self, user_event: UserEvent):
		if self.xid:
			self.get_wnck_window().maximize()

	@impure(mutates=False)
	def move_right(self, user_event: UserEvent):
		self._snap_active_window(HORIZONTAL, 0.5)

	@impure(mutates=False)
	def move_left(self, user_event: UserEvent):
		self._snap_active_window(HORIZONTAL, 0)

	@impure(mutates=False)
	def move_up(self, user_event: UserEvent):
		self._snap_active_window(VERTICAL, 0)

	@impure(mutates=False)
	def move_down(self, user_event: UserEvent):
		self._snap_active_window(VERTICAL, 0.5)

	def _snap_active_window(self, axis, position):
		self._move_on_axis(self.get_wnck_window(), axis, position, 0.5)

	def _move_on_axis(self, window, axis, position, proportion):
		if axis == HORIZONTAL:
			resize(window, l=position, t=0, w=proportion, h=1)
		else:
			resize(window, l=0, t=position, w=1, h=proportion)

	@impure(mutates=False)
	def centralize(self, user_event: UserEvent):
		resize(self.get_wnck_window(), l=0.1, t=0.1, w=0.8, h=0.8)

	@impure(mutates=False)
	def decorate(self, user_event: UserEvent):
		decoration_parameter = user_event.vim_command_parameter
		if decoration_parameter in DECORATION_MAP.keys():
			opt = DECORATION_MAP[decoration_parameter]
		gdk_window = gdk_window_for(self.get_wnck_window())
		gdk_window.set_decorations(opt)

	@impure(mutates=True)
	def zoom(self, user_event: UserEvent):
		active = windows.get_last_managed_focused()
		if not active:
			return
		monitor = monitors.get_active(active)
		clients = monitor.clients
		if len(clients) < 2:
			return
		old_index = clients.index(active.get_xid())
		if old_index == 0:
			clients.insert(1, clients.pop(old_index))
		else:
			clients.insert(0, clients.pop(old_index))
		active_window.change_to(clients[0])
		monitor.apply()

	@impure(mutates=True)
	def pushstack(self, user_event: UserEvent):
		direction = user_event.parameters[0]
		window = windows.get_last_managed_focused()
		if not window:
			return
		monitor = monitors.get_active(window)
		clients = monitor.clients
		old_index = clients.index(window.get_xid())
		new_index = (old_index + direction) % len(clients)

		if new_index != old_index:
			clients.insert(new_index, clients.pop(old_index))
			monitor.apply()

	@impure(mutates=True)
	def pushmonitor(self, user_event: UserEvent):
		direction = user_event.parameters[0]
		window = windows.get_last_managed_focused()
		if not window:
			return
		origin = monitors.get_active(window)
		destination = origin.get_adjacent(direction)

		if not destination:
			return

		if destination.get_workspace().get_number() != origin.get_workspace().get_number():
			window.move_to_workspace(destination.get_workspace())

		origin.clients.remove(window.get_xid())
		destination.clients.append(window.get_xid())

		origin.apply()
		destination.apply()

	@impure(mutates=False)
	def focusstack(self, user_event: UserEvent):
		direction = user_event.parameters[0]
		window = windows.get_last_managed_focused()
		if not window:
			return
		monitor = monitors.get_active(window)
		clients = monitor.clients

		old_index = clients.index(window.get_xid())
		new_index = (old_index + direction) % len(clients)

		active_window.change_to(clients[new_index])

	@impure(mutates=True)
	def killclient(self, user_event: UserEvent):
		active = self.get_wnck_window()

		if not active:
			return

		active.close(user_event.time)

	@impure(mutates=False)
	def focus_right(self, user_event: UserEvent):
		self.move_focus(1, HORIZONTAL)

	@impure(mutates=False)
	def focus_left(self, user_event: UserEvent):
		self.move_focus(-1, HORIZONTAL)

	@impure(mutates=False)
	def focus_up(self, user_event: UserEvent):
		self.move_focus(-1, VERTICAL)

	@impure(mutates=False)
	def focus_down(self, user_event: UserEvent):
		self.move_focus(1, VERTICAL)

	@impure(mutates=False)
	def focus_previous(self, user_event: UserEvent):
		previous = windows.get_previous()
		if not previous:
			return
		self.change_to(previous.get_xid())

	def move_focus(self, increment, axis):
		active = self.get_wnck_window()

		def key(w):
			axis_position = axis.position_of(w)
			perpendicular_distance = abs(axis.perpendicular.position_of(w) - axis.perpendicular.position_of(active))
			perpendicular_distance *= -1 if axis_position < axis.position_of(active) else 1
			return axis_position + perpendicular_distance

		sorted_windows = sorted(filter(in_visible_monitor, Wnck.Screen.get_default().get_windows()), key=key)

		index = sorted_windows.index(active)
		if 0 <= index + increment < len(sorted_windows):
			index = index + increment
			next_index = index + increment
			while 0 <= next_index < len(sorted_windows) and axis.position_of(sorted_windows[index]) == axis.position_of(active):
				index = next_index
				next_index += increment
		self.change_to(sorted_windows[index].get_xid())

	@impure(mutates=False)
	def focus_next(self, user_event: UserEvent):
		direction = 1 if not user_event or Gdk.keyval_name(user_event.keyval).islower() else -1
		line = windows.get_window_line()
		i = line.index(self.get_wnck_window())
		next_window = line[(i + direction) % len(line)]
		self.change_to(next_window.get_xid())


# https://valadoc.org/gdk-3.0/Gdk.Monitor.html
class Monitor:

	def __init__(
			self, primary: bool = False,
			nmaster: int = 1, mfact: float = 0.5,
			model: str = None, workspace: int = None,
			function_key: str = 'T', strut: List = (0, 0, 0, 0)):
		self.primary: bool = primary
		# TODO: rename to layout key
		self.function_key: str = function_key
		self.last_function_key = None
		self.nmaster: int = nmaster
		self.mfact: float = mfact
		self.strut: List = strut
		self.wx = self.wy = self.ww = self.wh = None
		self.visible_area: List[int] = [0, 0, 0, 0]
		self.clients: List[int] = []
		self.pointer: Monitor = None
		self.model = model
		self.workspace = workspace

	def set_layout(self, new_function):
		if self.function_key != new_function:
			self.last_function_key = self.function_key
		self.function_key = new_function

	def apply(self, unmaximize: bool = False):
		from pocoy.layout import FUNCTIONS_MAP
		if self.function_key:
			spread_windows: List[Wnck.Window] = list(map(lambda xid: windows.window_by_xid[xid], self.clients))
			if unmaximize:
				for window in spread_windows:
					wm.unmaximize(window)
			FUNCTIONS_MAP[self.function_key](spread_windows, self)

	def set_rectangle(self, rectangle: Gdk.Rectangle):
		self.visible_area = [
			max(rectangle.x, self.strut[0]),
			max(rectangle.y, self.strut[1]),
			rectangle.width, rectangle.height]
		if rectangle.x < self.strut[0]:
			self.visible_area[2] -= self.strut[0] - rectangle.x
		if rectangle.y < self.strut[1]:
			self.visible_area[3] -= self.strut[1] - rectangle.y
		self.update_work_area()

	def update_work_area(self):
		outer_gap = state.get_outer_gap()
		self.wx = max(self.visible_area[0], self.strut[0]) + outer_gap
		self.wy = max(self.visible_area[1], self.strut[1]) + outer_gap
		self.ww = self.visible_area[2] - outer_gap * 2
		self.wh = self.visible_area[3] - outer_gap * 2

	def increase_master_area(self, increment: float = None):
		self.mfact += increment
		self.mfact = max(0.1, self.mfact)
		self.mfact = min(0.9, self.mfact)

	def increment_master(self, increment=None):
		self.nmaster += increment
		self.nmaster = max(0, self.nmaster)
		self.nmaster = min(len(self.clients), self.nmaster)

	def contains(self, window: Wnck.Window):
		rect = self.visible_area
		xp, yp, widthp, heightp = window.get_geometry()
		return rect[0] <= xp < (rect[0] + rect[2]) and rect[1] <= yp < (rect[1] + rect[3])

	def from_json(self, json):
		self.nmaster = json['nmaster'] if 'nmaster' in json else self.nmaster
		self.mfact = json['mfact'] if 'mfact' in json else self.mfact
		self.function_key = json['function'] if 'function' in json else self.function_key
		self.strut = self.read_strut(json['strut']) if 'strut' in json else self.strut
		self.clients = list(map(lambda w_dict: w_dict['xid'], json['clients']))if 'clients' in json else self.clients

	def read_strut(self, json):
		keys = ['left', 'top', 'right', 'bottom']
		strut = []
		for key in keys:
			strut.append(0 if key not in json else json[key])
		return strut

	def to_json(self):
		return {
			'nmaster': self.nmaster,
			'mfact': self.mfact,
			'function': self.function_key,
			'strut': {
				'left': self.strut[0],
				'top': self.strut[1],
				'right': self.strut[2],
				'bottom': self.strut[3]
			},
			'clients': list(map(
				lambda xid: {'xid': xid, 'name': windows.window_by_xid[xid].get_name(), 'index': self.clients.index(xid)},
				self.clients
			))
		}

	def print(self):
		print('monitor: {} {} {} {}'.format(self.wx, self.wy, self.ww, self.wh))

	def get_workspace(self):
		return Wnck.Screen.get_default().get_workspace(self.workspace)

	def get_adjacent(self, direction):
		origin_x = self.visible_area[0]
		destination = None
		for visible in monitors.get_visible():
			destination_x = visible.visible_area[0]
			if visible is not self and (
					(direction > 0 and destination_x > origin_x) or
					(direction < 0 and destination_x < origin_x)
			):
				destination = visible
		return destination

	def switch_with(self, destination):
		aux = destination.clients
		destination.clients = self.clients
		self.clients = aux

		if destination.get_workspace().get_number() != self.get_workspace().get_number():
			for xid in self.clients:
				windows.window_by_xid[xid].move_to_workspace(self.get_workspace())
			for xid in destination.clients:
				windows.window_by_xid[xid].move_to_workspace(destination.get_workspace())


class Monitors:

	# primary_monitors: Dict[int, Monitor] = {}
	# by_model: Dict[str, Monitor] = {}
	def __init__(self):
		self.map: Dict[Tuple, Monitor] = {}
		self.primaries: Dict[int, Monitor] = {}
		self.by_workspace: Dict[int, List[Monitor]] = {}
		self.visible_ids = []

	def read(self, screen: Wnck.Screen):
		del self.visible_ids[:]
		active_workspace = get_active_workspace()
		secondary_workspace = get_workspace_outside_primary()
		for workspace in screen.get_workspaces():
			if workspace.get_number() not in self.by_workspace:
				self.by_workspace[workspace.get_number()] = []
			for i in range(Gdk.Display.get_default().get_n_monitors()):
				gdk_monitor = Gdk.Display.get_default().get_monitor(i)
				self.read_monitor(workspace, gdk_monitor)
				if (i == 0 and workspace is active_workspace) or (i > 0 and workspace is secondary_workspace):
					self.visible_ids.append(self.id_for(workspace, gdk_monitor))

	def id_for(self, workspace: Wnck.Workspace, gdk_monitor: Gdk.Monitor):
		return workspace.get_number(), gdk_monitor.get_model()

	def read_monitor(self, workspace: Wnck.Workspace, gdk_monitor: Gdk.Monitor):
		id = self.id_for(workspace, gdk_monitor)
		if id not in self.map.keys():
			self.map[id] = Monitor(
				primary=gdk_monitor.is_primary(), model=gdk_monitor.get_model(), workspace=workspace.get_number())
			self.by_workspace[workspace.get_number()].append(self.map[id])
			if gdk_monitor.is_primary():
				self.primaries[workspace.get_number()] = self.map[id]
		self.map[id].set_rectangle(gdk_monitor.get_workarea())

	#
	# Monitor API
	#
	def all(self):
		return self.map.values()

	def of(self, workspace: Wnck.Workspace, gdk_monitor: Gdk.Monitor):
		return self.map[(workspace.get_number(), gdk_monitor.get_model())]

	def of_client(self, xid: int):
		for monitor in self.map.values():
			if xid in monitor.clients:
				return monitor
		return None

	def get_active(self, window: Wnck.Window = None) -> Monitor:
		if not window:
			window = windows.get_last_managed_focused()
		return self.of(window.get_workspace(), monitor_of(window.get_xid())) if window else self.get_primary()

	def get_primary(self, workspace: Wnck.Workspace = None, index: int = None) -> Monitor:
		if not workspace and index is None:
			workspace = Wnck.Screen.get_default().get_active_workspace()
		if index is None:
			index = workspace.get_number()
		return self.primaries[index]

	def get_secondary(self):
		index = get_workspace_outside_primary().get_number()
		return self.by_workspace[index][1] if len(self.by_workspace[index]) > 1 else None

	def get_visible(self) -> List[Monitor]:
		return list(map(lambda monitor_id: self.map[monitor_id], self.visible_ids))

	@impure(mutates=True)
	def setprimarylayout(self, user_event: UserEvent):
		new_function_key = user_event.parameters[0]
		monitor = monitors.get_primary()
		monitor.set_layout(new_function_key)
		monitor.apply(unmaximize=True)
		windows.apply_decoration_config()


class ActiveMonitor:


	#
	# COMMANDS
	#
	@impure(mutates=True)
	def setlayout(self, user_event: UserEvent):
		promote_selected = False if len(user_event.parameters) < 2 else user_event.parameters[1]
		active = windows.get_last_managed_focused()
		monitor = monitors.get_active(active)
		clients = monitor.clients
		if promote_selected and active:
			old_index = clients.index(active.get_xid())
			clients.insert(0, clients.pop(old_index))

		if user_event.parameters:
			new_function_key = user_event.parameters[0]
		else:
			new_function_key = monitor.last_function_key
		monitor.set_layout(new_function_key)
		monitor.apply(unmaximize=True)
		windows.apply_decoration_config()

	@impure(mutates=False)
	def gap(self, user_event: UserEvent):
		parameters = user_event.vim_command_parameter.split()
		where = parameters[0]
		pixels = int(parameters[1])
		state.set_outer_gap(pixels) if where == 'outer' else state.set_inner_gap(pixels)
		for monitor in monitors.all():
			monitor.update_work_area()
			monitor.apply()

	def complete_gap_options(self, user_event: UserEvent):
		input = user_event.vim_command_parameter.lower()
		return list(filter(lambda x: input != x and input in x, ['inner', 'outer']))

	@impure(mutates=True)
	def setmfact(self, user_event: UserEvent):
		monitor = monitors.get_active()
		monitor.increase_master_area(increment=user_event.parameters[0])
		monitor.apply()

	@impure(mutates=True)
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
	try:
		workspace_config: Dict = state.get_workspace_config()
		windows.read_default_screen()
		read_user_config(workspace_config, screen)
	except (KeyError, TypeError):
		print('Unable to the last execution state, using default ones.')
		traceback.print_exc()
		traceback.print_stack()
	windows.read(screen)


def read_user_config(config_json: Dict, screen: Wnck.Screen):
	for workspace_index in range(len(config_json['workspaces'])):
		if workspace_index >= len(monitors.by_workspace):
			continue
		workspace_json = config_json['workspaces'][workspace_index]
		for monitor_index in range(len(workspace_json['monitors'])):
			if monitor_index >= len(monitors.by_workspace[workspace_index]):
				continue
			monitors.by_workspace[workspace_index][monitor_index].from_json(
				workspace_json['monitors'][monitor_index]
			)


def start():
	for monitor in monitors.all():
		monitor.apply(unmaximize=True)
	windows.apply_decoration_config()


def stop():
	windows.read_default_screen()
	decoration.restore(windows.buffers)


def persist():
	screen = Wnck.Screen.get_default()
	workspaces: List[Dict] = []

	for workspace in screen.get_workspaces():
		workspace_json = {'monitors': []}
		workspaces.append(workspace_json)
		for monitor in monitors.by_workspace[workspace.get_number()]:
			workspace_json['monitors'].append(monitor.to_json())

	state.persist_workspace(workspaces)


#
# Internal API
#
def resume():
	resume = ''
	# for w in reversed(Wnck.Screen.get_default().get_windows_stacked()): resume += '{}\n'.format(w.get_name())
	from pocoy.layout import FUNCTIONS_MAP
	for wn in windows.get_buffers():
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
			monitor: Monitor = monitors.by_workspace[workspace.get_number()][i]
			rect = m.get_workarea()

			resume += '\tMonitor Layout: {} Primary: {} Manufacturer: {} Model: {}\n'.format(
				FUNCTIONS_MAP[monitor.function_key].__name__ if monitor.function_key else None, m.is_primary(),
				m.get_manufacturer(), m.get_model()
			)
			resume += '\t\t[GDK]\t\tRectangle: {:5}, {:5}, {:5}, {:5}\n'.format(
				rect.x, rect.y, rect.width, rect.height)
			resume += '\t\t[pocoy]\tRectangle: {:5}, {:5}, {:5}, {:5}\n'.format(
				monitor.wx, monitor.wy, monitor.ww, monitor.wh)

			resume += '\t\t[Stack]\t\t('
			for xid in filter(lambda _xid: monitor.contains(windows.window_by_xid[_xid]), monitor.clients):
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
