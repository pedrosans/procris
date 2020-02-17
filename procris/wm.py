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
import traceback
import procris.cache as config
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, GdkX11, Gdk
from typing import Callable

X_Y_W_H_GEOMETRY_MASK = Wnck.WindowMoveResizeMask.HEIGHT | Wnck.WindowMoveResizeMask.WIDTH | Wnck.WindowMoveResizeMask.X | Wnck.WindowMoveResizeMask.Y


def gdk_window_for(window: Wnck.Window) -> GdkX11.X11Window:
	display = GdkX11.X11Display.get_default()
	xid = window.get_xid()
	try:
		return GdkX11.X11Window.foreign_new_for_display(display, xid)
	except TypeError as e:
		raise DirtyState(window=window) from e


def monitor_work_area_for(window: Wnck.Window) -> Gdk.Rectangle:
	gdk_window: GdkX11.X11Window = gdk_window_for(window)
	gdk_display: GdkX11.X11Display = gdk_window.get_display()
	gdk_monitor: GdkX11.X11Monitor = gdk_display.get_monitor_at_window(gdk_window)
	return gdk_monitor.get_workarea()


def decoration_size_for(window: Wnck.Window):
	border_compensation = config.get_window_manger_border()
	gdk_w = gdk_window_for(window)

	with Trap():
		is_decorated, decorations = gdk_w.get_decorations()
		x, y, w, h = window.get_geometry()
		cx, cy, cw, ch = window.get_client_window_geometry()

	decoration_width = cx - x - border_compensation
	decoration_height = cy - y - border_compensation

	return is_decorated, decorations, decoration_width, decoration_height


def unmaximize(window: Wnck.Window):
	if window.is_maximized():
		window.unmaximize()
	if window.is_maximized_horizontally():
		window.unmaximize_horizontally()
	if window.is_maximized_vertically():
		window.unmaximize_vertically()


def is_buffer(window: Wnck.Window) -> bool:
	return window.get_pid() != os.getpid() and not window.is_skip_tasklist()


def is_visible(window: Wnck.Window, workspace: Wnck.Workspace = None) -> bool:
	workspace = workspace if workspace else Wnck.Screen.get_default().get_active_workspace()
	return (
			is_buffer(window)
			and not window.is_minimized()
			and window.is_in_viewport(workspace)
			and window.is_visible_on_workspace(workspace))


def is_on_primary_monitor(window: Wnck.Window):
	rect = Gdk.Display.get_default().get_primary_monitor().get_workarea()
	xp, yp, widthp, heightp = window.get_geometry()
	return rect.x <= xp < (rect.x + rect.width) and rect.y <= yp < (rect.y + rect.height)


def get_active_window(workspace: Wnck.Workspace = None, window_filter: Callable = None):
	workspace = workspace if workspace else Wnck.Screen.get_default().get_active_workspace()
	for stacked in reversed(Wnck.Screen.get_default().get_windows_stacked()):
		if is_visible(stacked, workspace):
			return stacked if (not window_filter or window_filter(stacked)) else None
	return None


def resize(window: Wnck.Window, rectangle: Gdk.Rectangle = None, l=0, t=0, w=0, h=0):
	"""
	:param l: distance from left edge
	:param t: distance from top edge
	"""

	if not rectangle:
		rectangle = monitor_work_area_for(window)

	new_x = int(rectangle.width * l) + rectangle.x
	new_y = int(rectangle.height * t) + rectangle.y
	new_width = int(rectangle.width * w)
	new_height = int(rectangle.height * h)

	set_geometry(window, x=new_x, y=new_y, w=new_width, h=new_height)


def set_geometry(window: Wnck.Window, x=None, y=None, w=None, h=None):

	unmaximize(window)

	if not w and not h:
		geometry = window.get_geometry()
		w = geometry.widthp
		h = geometry.heightp

	xo, yo, wo, ho = calculate_geometry_offset(window)
	window.set_geometry(Wnck.WindowGravity.STATIC, X_Y_W_H_GEOMETRY_MASK, x + xo, y + yo, w + wo, h + ho)


def calculate_geometry_offset(window: Wnck.Window):
	border_compensation = config.get_window_manger_border()
	is_decorated, decorations, decoration_width, decoration_height = decoration_size_for(window)
	client_side_decoration = is_decorated and not decorations and decoration_width < 0 and decoration_height < 0
	has_title = (
			Gdk.WMDecoration.TITLE & decorations
			or Gdk.WMDecoration.ALL & decorations
			or (not is_decorated and not decorations)  # assume server side decoration
	)

	if client_side_decoration:
		return border_compensation, border_compensation, -border_compensation * 2, -border_compensation * 2

	if not has_title and not client_side_decoration:
		return -decoration_width, -decoration_height, decoration_width, decoration_height

	return 0, 0, 0, 0


class DirtyState(Exception):

	def __init__(self, message: str = None, window: Wnck.Window = None):
		super(DirtyState, self).__init__(message)
		self.window = window

	def print(self):
		if self.window:
			print('\tLooking for: {} - {}'.format(self.window.get_xid(), self.window.get_name()))
		print('\tOn screen:')
		for listed in Wnck.Screen.get_default().get_windows():
			print('\t\t {} - {}'.format(listed.get_xid(), listed.get_name()))
		traceback.print_exc()
		traceback.print_stack()


class Trap:

	# https://lazka.github.io/pgi-docs/GdkX11-3.0/classes/X11Display.html
	display: GdkX11.X11Display = None

	def __init__(self):
		self.display = GdkX11.X11Display.get_default()

	def __enter__(self):
		self.display.error_trap_push()
		return self

	def __exit__(self, type, exception, traceback):
		error: int = self.display.error_trap_pop()
		if error:
			raise DirtyState(message='X11 Error code {}'.format(error)) from exception
