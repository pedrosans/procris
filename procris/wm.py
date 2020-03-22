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
import os
import gi
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, GdkX11, Gdk

X_Y_W_H_GEOMETRY_MASK = Wnck.WindowMoveResizeMask.HEIGHT | Wnck.WindowMoveResizeMask.WIDTH | Wnck.WindowMoveResizeMask.X | Wnck.WindowMoveResizeMask.Y


def gdk_window_for(window: Wnck.Window) -> Gdk.Window:
	display = GdkX11.X11Display.get_default()
	xid = window.get_xid()
	return GdkX11.X11Window.foreign_new_for_display(display, xid)


def monitor_work_area_for(window: Wnck.Window) -> Gdk.Rectangle:
	gdk_window = gdk_window_for(window)
	gdk_display = gdk_window.get_display()
	gdk_monitor = gdk_display.get_monitor_at_window(gdk_window)
	return gdk_monitor.get_workarea()


def decoration_size_for(window: Wnck.Window):
	gdk_w = gdk_window_for(window)
	is_decorated, decorations = gdk_w.get_decorations()
	x, y, w, h = window.get_geometry()
	cx, cy, cw, ch = window.get_client_window_geometry()
	decoration_width = cx - x
	decoration_height = cy - y

	return is_decorated, decorations, decoration_width, decoration_height


def unsnap(window: Wnck.Window):
	if window.is_maximized():
		window.unmaximize()
	if window.is_maximized_horizontally():
		window.unmaximize_horizontally()
	if window.is_maximized_vertically():
		window.unmaximize_vertically()


def is_visible(window: Wnck.Window):
	if window.get_pid() == os.getpid():
		return False
	if window.is_skip_tasklist():
		return False
	active_workspace = Wnck.Screen.get_default().get_active_workspace()
	return window.is_in_viewport(active_workspace) and not window.is_minimized()


def resize(window: Wnck.Window, l=0, t=0, w=0, h=0):
	"""
	:param l: distance from left edge
	:param t: distance from top edge
	"""
	unsnap(window)
	work_area = monitor_work_area_for(window)

	new_x = int(work_area.width * l) + work_area.x
	new_y = int(work_area.height * t) + work_area.y
	new_width = int(work_area.width * w)
	new_height = int(work_area.height * h)

	set_geometry(window, x=new_x, y=new_y, w=new_width, h=new_height)


def set_geometry(window: Wnck.Window, x=None, y=None, w=None, h=None):
	if not w and not h:
		geometry = window.get_geometry()
		w = geometry.widthp
		h = geometry.heightp

	is_decorated, decorations, decoration_width, decoration_height = decoration_size_for(window)
	has_title = Gdk.WMDecoration.TITLE & decorations or Gdk.WMDecoration.ALL & decorations

	if is_decorated and not has_title and decoration_width >= 0 and decoration_height >= 0:
		x -= decoration_width
		y -= decoration_height
		w += decoration_width
		h += decoration_height

	# print("monitor: x={}  w={} y={}  h={}".format(monitor_geo.x, monitor_geo.width, monitor_geo.y, monitor_geo.height))
	# print("window: x={} y={} width={} height={}".format(x, y, w, h))

	window.set_geometry(Wnck.WindowGravity.STATIC, X_Y_W_H_GEOMETRY_MASK, x, y, w, h)
