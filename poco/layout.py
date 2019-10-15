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
import gi, os, json
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, GLib, Gdk


from poco.windows import monitor_work_area_for
from poco .windows import gdk_window_for


def to_json(monitor, buffers, stack, old_state=None):
	state = old_state if old_state else {'stack_state': {}}
	state['nmaster'] = monitor.nmaster
	state['mfact'] = monitor.mfact
	stack_state = state['stack_state']
	for w in buffers:
		w_id = w.get_xid()
		key = str(w_id)
		if key not in stack_state:
			stack_state[key] = {}
			stack_state[key]['name'] = w.get_name()
			is_decorated, decorations = gdk_window_for(w).get_decorations()
			stack_state[key]['original_decorations'] = Gdk.WMDecoration.ALL if not decorations else decorations
		stack_state[key]['stack_index'] = stack.index(w_id) if w_id in stack else -1

	for client_key in list(stack_state.keys()):
		if client_key not in map(lambda x: str(x.get_xid()), buffers):
			del stack_state[client_key]

	return state


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


class Serializer:

	def __init__(self, persistence_file):
		self.persistence_file = persistence_file

	def serialize(self, state):
		with open(self.persistence_file, 'w') as f:
			json.dump(state, f, indent=True)

	def deserialize(self):
		if os.path.exists(self.persistence_file):
			with open(self.persistence_file, 'r') as f:
				return json.load(f)
		return None


# TODO: the the window is maximized, the layout function fails
class LayoutManager:

	def __init__(self, windows, remove_decorations=False,  persistence_file='/tmp/poco_windows_state.json'):
		self.window_monitor_map = {}
		self.gap = 10
		self.remove_decorations = remove_decorations
		self.serializer = Serializer(persistence_file)
		self.windows = windows
		self.persistence_file = persistence_file
		self.function = centeredmaster
		self.monitor = Monitor()

		self.windows.read_screen()
		self.stack = list(map(lambda x: x.get_xid(), self.windows.visible))

		self.state_json = self.serializer.deserialize()
		if self.state_json:
			copy = self.stack.copy()
			self.stack.sort(
				key=lambda xid:
					self.state_json['stack_state'][str(xid)]['stack_index']
					if str(xid) in self.state_json['stack_state']
					else copy.index(xid))
			self.monitor.nmaster = self.state_json['nmaster']
			self.monitor.mfact = self.state_json['mfact']
		self._persist_internal_state()
		self.apply_decoration_config()

		self._install_state_handlers()
		self.windows.screen.connect("window-opened", self._window_opened)
		self.windows.screen.connect("window-closed", self._window_closed)
		# self.screen.connect("active-window-changed", self._active_window_changed)
		# def _active_window_changed(self, screen, previously_active_window):

	#
	# INTERNAL INTERFACE
	#
	def _persist_internal_state(self):
		self.state_json = to_json(self.monitor, self.windows.buffers, self.stack, old_state=self.state_json)
		self.serializer.serialize(self.state_json)

	def _install_state_handlers(self):
		for window in self.windows.buffers:
			if window.get_xid() not in self.window_monitor_map:
				handler_id = window.connect("state-changed", self._state_changed)
				self.window_monitor_map[window.get_xid()] = handler_id

	def apply_decoration_config(self):
		if self.remove_decorations:
			self.windows.remove_decorations()
		else:
			self.windows.restore_decorations(self.state_json)

	#
	# CALLBACKS
	#
	def _window_closed(self, screen, window):
		if window.get_xid() in self.stack:
			self.stack.remove(window.get_xid())
		if self.windows.is_visible(window):
			self.windows.read_screen(force_update=False)
			self.layout()

	def _window_opened(self, screen, window):
		if self.windows.is_visible(window):
			self.stack.insert(0, window.get_xid())
			self.apply_decoration_config()
			self.windows.read_screen(force_update=False)
			self.layout()

	def _state_changed(self, window, changed_mask, new_state):
		if self.windows.is_visible(window):
			self.stack.insert(0, window.get_xid())
		else:
			self.stack.remove(window.get_xid())
		self.windows.read_screen(force_update=False)
		self.layout()

	#
	# COMMANDS
	#
	def move_to_master(self, w):
		self.windows.read_screen()
		active = self.windows.active
		if active:
			old_index = self.stack.index(active.get_xid())
			self.stack.insert(0, self.stack.pop(old_index))
		self.layout()

	def increase_master_area(self, c_in):
		self.windows.read_screen()
		increment = c_in.parameters[0]
		self.monitor.mfact += increment
		self.monitor.mfact = max(0.1, self.monitor.mfact)
		self.monitor.mfact = min(0.9, self.monitor.mfact)
		self.layout()

	def increment_master(self, c_in):
		self.windows.read_screen()
		increment = c_in.parameters[0]
		self.monitor.nmaster += increment
		self.monitor.nmaster = max(0, self.monitor.nmaster)
		self.monitor.nmaster = min(len(self.stack), self.monitor.nmaster)
		self.layout()

	def layout(self):
		self._persist_internal_state()
		self._install_state_handlers()

		w_stack = list(filter(
			lambda x: x is not None,
			map(lambda xid: self.windows.visible_map[xid] if xid in self.windows.visible_map else None, self.stack)))

		if not w_stack:
			return

		wa = monitor_work_area_for(w_stack[0])

		self.monitor.set_workarea(
			x=wa.x + self.gap, y=wa.y + self.gap, width=wa.width - self.gap * 2, height=wa.height - self.gap * 2)

		arrange = self.function(w_stack, self.monitor)

		for i in range(len(arrange)):
			a = arrange[i]
			w = w_stack[i]
			self.windows.set_geometry(
				w, x=a[0] + self.gap, y=a[1] + self.gap, w=a[2] - self.gap * 2, h=a[3] - self.gap * 2)


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
		c.bw = 0
		if i < monitor.nmaster:
			# nmaster clients are stacked vertically, in the center of the screen
			h = (monitor.wh - my) / (min(n, monitor.nmaster) - i);
			layout.append([monitor.wx + mx, monitor.wy + my, mw - (2 * c.bw), h - (2 * c.bw), 0])
			my += layout[-1][3]
		else:
			# stack clients are stacked vertically
			if (i - monitor.nmaster) % 2:
				h = (monitor.wh - ety) / int((1 + n - i) / 2)
				layout.append([monitor.wx, monitor.wy + ety, tw - (2 * c.bw), h - (2 * c.bw), 0])
				ety += layout[-1][3]
			else:
				h = (monitor.wh - oty) / int((1 + n - i) / 2)
				layout.append([monitor.wx + mx + mw, monitor.wy + oty, tw - (2 * c.bw), h - (2 * c.bw), 0])
				oty += layout[-1][3]

	return layout
