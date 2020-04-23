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
import re
import gi
import traceback
import pocoy.state as config
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, GdkX11, Gdk, Gio
from datetime import datetime
from typing import Callable
from pocoy import scratchpads


X_Y_W_H_GEOMETRY_MASK = Wnck.WindowMoveResizeMask.HEIGHT | Wnck.WindowMoveResizeMask.WIDTH | Wnck.WindowMoveResizeMask.X | Wnck.WindowMoveResizeMask.Y
geometry_cache = {}
adjustment_cache = {}


# https://lazka.github.io/pgi-docs/GdkX11-3.0/classes/X11Display.html
# https://lazka.github.io/pgi-docs/GdkX11-3.0/classes/X11Window.html
# https://lazka.github.io/pgi-docs/GdkX11-3.0/classes/X11Monitor.html
def gdk_window_for(window: Wnck.Window = None, xid: int = None) -> GdkX11.X11Window:
	return window_for(window.get_xid())


def window_for(xid: int = None) -> GdkX11.X11Window:
	display = GdkX11.X11Display.get_default()
	try:
		return GdkX11.X11Window.foreign_new_for_display(display, xid)
	except TypeError as e:
		raise DirtyState(xid=xid) from e


#
# WORKSPACE
#
def is_workspaces_only_on_primary():
	return 'org.gnome.mutter' in Gio.Settings.list_schemas() and Gio.Settings('org.gnome.mutter').get_value('workspaces-only-on-primary')


def get_first_workspace():
	return Wnck.Screen.get_default().get_workspace(0)


def get_workspace_outside_primary():
	return get_first_workspace() if is_workspaces_only_on_primary() else get_active_workspace()


def get_active_workspace() -> Wnck.Workspace:
	return Wnck.Screen.get_default().get_active_workspace()


#
# MONITOR
#
def monitor_of(xid) -> Gdk.Monitor:
	gdk_window: GdkX11.X11Window = window_for(xid)
	gdk_display: GdkX11.X11Display = gdk_window.get_display()
	return gdk_display.get_monitor_at_window(gdk_window)


#
# WINDOW
#
def is_visible(window: Wnck.Window, workspace: Wnck.Workspace = None, monitor: Gdk.Monitor = None) -> bool:
	return (
			not window.is_minimized()
			and (not workspace or (window.is_in_viewport(workspace) and window.is_visible_on_workspace(workspace)))
			and (not monitor or intersect(window, monitor))
	)


def is_buffer(window: Wnck.Window) -> bool:
	return window.get_pid() != os.getpid() and not window.is_skip_tasklist()


def is_on_primary_monitor(window: Wnck.Window):
	return intersect(window, Gdk.Display.get_default().get_primary_monitor())


def get_last_focused(window_filter: Callable = None):
	for stacked in reversed(Wnck.Screen.get_default().get_windows_stacked()):
		if not window_filter or window_filter(stacked):
			return stacked
	return None


def is_managed(window):
	return is_buffer(window) and window.get_name() not in scratchpads.names()


def get_active_managed_window():
	last_focused_buffer = get_last_focused(is_buffer)
	return last_focused_buffer if last_focused_buffer and is_managed(last_focused_buffer) else None


def intersect(window: Wnck.Window, monitor: Gdk.Monitor):
	rect = monitor.get_workarea()
	xp, yp, widthp, heightp = window.get_geometry()
	return rect.x <= xp < (rect.x + rect.width) and rect.y <= yp < (rect.y + rect.height)


def unmaximize(window: Wnck.Window):
	if window.is_maximized() or window.is_maximized_vertically() or window.is_maximized_horizontally():
		window.unmaximize()


#
# GEOMETRY
#
def resize(window: Wnck.Window, rectangle: Gdk.Rectangle = None, l=0, t=0, w=0, h=0):
	"""
	:param l: distance from left edge
	:param t: distance from top edge
	"""

	if not rectangle:
		rectangle = monitor_of(window.get_xid()).get_workarea()

	new_x = int(rectangle.width * l) + rectangle.x
	new_y = int(rectangle.height * t) + rectangle.y
	new_width = int(rectangle.width * w)
	new_height = int(rectangle.height * h)

	set_geometry(window, x=new_x, y=new_y, w=new_width, h=new_height)


def set_geometry(window: Wnck.Window, x=None, y=None, w=None, h=None, synchronous=False, raise_exceptions=True):

	if not w and not h:
		geometry = window.get_geometry()
		w = geometry.widthp
		h = geometry.heightp

	xo, yo, wo, ho = calculate_geometry_offset(window)
	x, y, w, h = x + xo, y + yo, w + wo, h + ho
	x, y, w, h = int(x), int(y), int(w), int(h)
	geometry_cache[window.get_xid()] = (x, y, w, h)
	adjustment_cache[window.get_xid()] = False
	window.set_geometry(Wnck.WindowGravity.STATIC, X_Y_W_H_GEOMETRY_MASK, x, y, w, h)

	if synchronous:
		synchronized = wait_configure_event(
			window.get_xid(), Gdk.EventType.CONFIGURE, Gdk.Display.get_default())
		return synchronized

	return False


def wait_configure_event(xid, type, display: Gdk.Display):
	limit = 100000
	queue = []
	try:
		while limit > 0:
			limit -= 1
			e = display.get_event()
			if e:
				queue.append(e)
				if e.get_event_type() == type and e.get_window().get_xid() == xid:
					return True
		return False
	finally:
		for e in queue:
			e.put()
		del queue[:]


def get_width(window: Wnck.Window):
	w, h = get_size(window)
	return w


def get_height(window: Wnck.Window):
	w, h = get_size(window)
	return h


def get_size(window: Wnck.Window):
	dx, dy, dw, dh = decoration_delta(window)
	with Trap():
		gx, gy, gw, gh = gdk_window_for(window).get_geometry()

	with Trap():
		is_decorated, decorations = gdk_window_for(window).get_decorations()
	client_side_decoration = is_decorated and not decorations and dh < 0
	border_compensation = (config.get_window_manger_border() * 2 if client_side_decoration else 0)

	return gw + dw + border_compensation, gh + dh + border_compensation


def calculate_geometry_offset(window: Wnck.Window):
	border_compensation = config.get_window_manger_border()
	with Trap():
		is_decorated, decorations = gdk_window_for(window).get_decorations()
	dx, dy, dw, dh = decoration_delta(window)
	client_side_decoration = is_decorated and not decorations and dx < 0 and dy < 0
	has_title = (
			Gdk.WMDecoration.TITLE & decorations
			or Gdk.WMDecoration.ALL & decorations
			or (not is_decorated and not decorations)  # assume server side decoration
	)

	if client_side_decoration:
		return border_compensation, border_compensation, -border_compensation * 2, -border_compensation * 2

	# this fix is not needed on more recent versions of libgtk
	if not has_title and not client_side_decoration:
		dx -= border_compensation
		dy -= border_compensation
		return -dx, -dy, dx, dy

	return 0, 0, 0, 0


def decoration_delta(window: Wnck.Window):
	with Trap():
		wx, wy, ww, wh = window.get_geometry()
		cx, cy, cw, ch = window.get_client_window_geometry()
	return cx - wx, cy - wy, ww - cw, wh - ch


class DirtyState(Exception):

	def __init__(self, message: str = None, xid: int = None):
		super(DirtyState, self).__init__(message)
		self.xid = xid

	def print(self):
		if self.xid:
			print('\tLooking for: {}'.format(self.xid))
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


class UserEvent:

	colon_spacer = ''
	vim_command = ''
	vim_command_spacer = ''
	vim_command_parameter = ''
	terminal_command = ''
	terminal_command_spacer = ''
	terminal_command_parameter = ''

	def __init__(self, time=None, text=None, parameters=None, keyval=None, keymod=None):
		self.time = time if time else datetime.now().microsecond
		self.text = text
		if text:
			self._parse()
		self.keyval = keyval
		self.keymod = keymod
		self.parameters = parameters

	def _parse(self):
		cmd_match = re.match(r'^(\s*)([a-zA-Z]+|!)(.*)', self.text)

		if not cmd_match:
			return self

		self.colon_spacer = cmd_match.group(1)
		self.vim_command = cmd_match.group(2)

		vim_command_parameter_text = cmd_match.group(3)
		parameters_match = re.match(r'^(\s*)(.*)', vim_command_parameter_text)

		self.vim_command_spacer = parameters_match.group(1)
		self.vim_command_parameter = parameters_match.group(2)

		if self.vim_command == '!' and self.vim_command_parameter:
			grouped_terminal_command = re.match(r'^(\w+)(\s*)(.*)', self.vim_command_parameter)
			self.terminal_command = grouped_terminal_command.group(1)
			self.terminal_command_spacer = grouped_terminal_command.group(2)
			self.terminal_command_parameter = grouped_terminal_command.group(3)

		return self

	def mount_vim_command(self):
		return self.colon_spacer + self.vim_command + self.vim_command_spacer

	def print(self):
		print('------------------------------------------')
		print('vc ::{}::'.format(self.vim_command))
		print('vcs::{}::'.format(self.vim_command_spacer))
		print('vcp::{}::'.format(self.vim_command_parameter))
		print('tc ::{}::'.format(self.terminal_command))
		print('tcs::{}::'.format(self.terminal_command_spacer))
		print('tcp::{}::'.format(self.terminal_command_parameter))
