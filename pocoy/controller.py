from functools import reduce
from typing import List, Dict

import gi
import pocoy.model as model
from pocoy import wm, scratchpads, desktop
from pocoy.layout import apply

gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, Gdk, Gtk
from pocoy.wm import DirtyState, is_managed, is_visible, gdk_window_for, Trap, resize

windows = model.windows
monitors = model.monitors

screen_handlers: List[int] = []
handlers_by_xid: Dict[int, int] = {}


def connect_to(screen: Wnck.Screen):
	opened_handler_id = screen.connect("window-opened", _window_opened)
	closed_handler_id = screen.connect("window-closed", _window_closed)
	viewport_handler_id = screen.connect("viewports-changed", _viewports_changed)
	workspace_handler_id = screen.connect("active-workspace-changed", _active_workspace_changed)
	screen_handlers.extend([opened_handler_id, closed_handler_id, viewport_handler_id, workspace_handler_id])
	_install_present_window_handlers(screen)
	Gdk.Event.handler_set(handle_x_event)


def disconnect_from(screen: Wnck.Screen):
	windows.read(screen, force_update=False)
	for xid in handlers_by_xid.keys():
		if xid in windows.window_by_xid:
			windows.window_by_xid[xid].disconnect(handlers_by_xid[xid])
	for handler_id in screen_handlers:
		screen.disconnect(handler_id)


def handle_x_event(event: Gdk.Event):
	Gtk.main_do_event(event)
	if event.get_event_type() == Gdk.EventType.PROPERTY_NOTIFY:
		w = event.window
		xid = w.get_xid()
		if xid in wm.geometry_cache and xid in windows.window_by_xid:
			ww: Wnck.Window = windows.window_by_xid[xid]
			g: Gdk.Rectangle = ww.get_geometry()
			c = wm.geometry_cache[xid]
			delta = reduce(lambda x, y: x + y, map(lambda i: abs(g[i] - c[i]), range(4)))
			if not wm.adjustment_cache[xid] and (
					event.property.atom.name() in ('_GTK_FRAME_EXTENTS', '_NET_FRAME_EXTENTS')
					and delta > 30):
				try:
					wm.set_geometry(ww, x=c[0], y=c[1], w=c[2], h=c[3])
				except DirtyState:
					pass  # just a try
				wm.adjustment_cache[xid] = True
			# print('adjusting {} to {}. Original: {}'.format(xid, c, g))


def _install_present_window_handlers(screen: Wnck.Screen):
	for window in screen.get_windows():
		if window.get_xid() not in handlers_by_xid and is_managed(window):
			handler_id = window.connect("state-changed", _state_changed)
			handlers_by_xid[window.get_xid()] = handler_id


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
		apply(monitors, windows)
		model.persist()


def _window_closed(screen: Wnck.Screen, window):
	try:
		if window.get_xid() in handlers_by_xid:
			window.disconnect(handlers_by_xid[window.get_xid()])
			del handlers_by_xid[window.get_xid()]
		if is_visible(window) and is_managed(window):
			windows.read(screen, force_update=False)
			apply(monitors, windows)
	except DirtyState:
		pass  # It was just a try


def _window_opened(screen: Wnck.Screen, window: Wnck.Window):
	gdk_window_for(window).flush()
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
		model.persist()
	try:
		with Trap():
			windows.apply_decoration_config()
			apply(monitors, windows)
	except DirtyState:
		pass  # It was just a try


def _viewports_changed(scree: Wnck.Screen):
	desktop.show_monitor(monitors.get_active_primary_monitor())


def _active_workspace_changed(screen: Wnck.Screen, workspace: Wnck.Workspace):
	desktop.show_monitor(monitors.get_active_primary_monitor())
	desktop.update()
