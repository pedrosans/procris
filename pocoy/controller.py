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
import gi
from pocoy import wm, scratchpads
from pocoy.model import Monitors, Windows
from pocoy.wm import DirtyState, is_managed, is_visible, gdk_window_for, Trap, resize
from functools import reduce
from typing import List, Dict, Callable
from gi.repository import Wnck, Gdk, Gtk
gi.require_version('Wnck', '3.0')


windows: Windows = None
monitors: Monitors = None
screen_handlers: List[int] = []
handlers_by_xid: Dict[int, int] = {}
layout_change_callbacks: [Callable] = []
mapped = set()
configured = set()


def connect_to(screen: Wnck.Screen, model_windows: Windows, model_monitors: Monitors):
	global windows, monitors
	windows = model_windows
	monitors = model_monitors
	opened_handler_id = screen.connect("window-opened", _window_opened)
	closed_handler_id = screen.connect("window-closed", _window_closed)
	viewport_handler_id = screen.connect("viewports-changed", _viewports_changed)
	workspace_handler_id = screen.connect("active-workspace-changed", _active_workspace_changed)
	screen_handlers.extend([opened_handler_id, closed_handler_id, viewport_handler_id, workspace_handler_id])
	_install_present_window_handlers(screen)
	Gdk.Event.handler_set(_handle_x_event)


def _install_present_window_handlers(screen: Wnck.Screen):
	for window in screen.get_windows():
		if window.get_xid() not in handlers_by_xid and is_managed(window):
			handler_id = window.connect("state-changed", _state_changed)
			handlers_by_xid[window.get_xid()] = handler_id


def disconnect_from(screen: Wnck.Screen):
	windows.read(screen, force_update=False)
	for xid in handlers_by_xid.keys():
		if xid in windows.window_by_xid:
			windows.window_by_xid[xid].disconnect(handlers_by_xid[xid])
	for handler_id in screen_handlers:
		screen.disconnect(handler_id)


def _window_opened(screen: Wnck.Screen, window: Wnck.Window):
	gdk_window_for(window).flush()
	windows.read(screen, force_update=False)
	_install_present_window_handlers(screen)
	if window.get_name() in scratchpads.names():
		scratchpad = scratchpads.get(window.get_name())
		primary = Gdk.Display.get_default().get_primary_monitor().get_workarea()
		resize(window, rectangle=primary, l=scratchpad.l, t=scratchpad.t, w=scratchpad.w, h=scratchpad.h)
	elif is_managed(window):
		monitor = monitors.get_active(window)
		clients = monitor.clients
		copy = clients.copy()
		clients.sort(key=lambda xid: -1 if xid == window.get_xid() else copy.index(xid))
		notify_layout_change()
		try:
			with Trap():
				monitor.apply()
				windows.apply_decoration_config()
		except DirtyState:
			pass  # It was just a try


def _state_changed(window: Wnck.Window, changed_mask, new_state):
	maximization = changed_mask & Wnck.WindowState.MAXIMIZED_HORIZONTALLY or changed_mask & Wnck.WindowState.MAXIMIZED_VERTICALLY
	if maximization and new_state and monitors.get_active(window).function_key:
		window.unmaximize()
	if changed_mask & Wnck.WindowState.MINIMIZED and is_managed(window):
		windows.read(window.get_screen(), force_update=False)
		monitor = monitors.get_active(window)
		clients = monitor.clients
		if is_visible(window):
			old_index = clients.index(window.get_xid())
			clients.insert(0, clients.pop(old_index))
		monitor.apply()
		notify_layout_change()


def _window_closed(screen: Wnck.Screen, window):
	try:
		if window.get_xid() in handlers_by_xid:
			window.disconnect(handlers_by_xid[window.get_xid()])
			del handlers_by_xid[window.get_xid()]
		if is_visible(window) and is_managed(window):
			windows.read(screen, force_update=False)
			for monitor in monitors.all():
				if monitor.contains(window):
					monitor.apply()
	except DirtyState:
		pass  # It was just a try


def _viewports_changed(scree: Wnck.Screen):
	notify_layout_change()


def _active_workspace_changed(screen: Wnck.Screen, workspace: Wnck.Workspace):
	notify_layout_change()


def _handle_x_event(event: Gdk.Event):
	Gtk.main_do_event(event)
	event_type = event.get_event_type()
	if event_type in (Gdk.EventType.MAP, Gdk.EventType.CONFIGURE) and event.window:
		(configured if event_type == Gdk.EventType.CONFIGURE else mapped).add(event.window.get_xid())
	elif event_type == Gdk.EventType.PROPERTY_NOTIFY:
		xid = event.window.get_xid()
		if (
				xid in wm.geometry_cache and xid in windows.window_by_xid and not wm.adjustment_cache[xid]
				and event.property.atom.name() in ('_GTK_FRAME_EXTENTS', '_NET_FRAME_EXTENTS')
		):
			event.window.flush()
			ww: Wnck.Window = windows.window_by_xid[xid]
			g: Gdk.Rectangle = ww.get_geometry()
			c = wm.geometry_cache[xid]
			delta = reduce(lambda x, y: x + y, map(lambda i: abs(g[i] - c[i]), range(4)))
			if delta <= 30 or xid not in mapped or xid not in configured:
				return
			mapped.remove(xid)
			configured.remove(xid)
			# print('{} - because {} move from {} to {}'.format(xid, delta, g, c))
			try:
				wm.set_geometry(ww, x=c[0], y=c[1], w=c[2], h=c[3])
			except DirtyState:
				pass  # just a try
			wm.adjustment_cache[xid] = True


def notify_layout_change():
	for callback in layout_change_callbacks:
		callback()
