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
from gi.repository import Wnck, GdkX11, Gdk
from datetime import datetime
from typing import Callable
from pocoy import state

X_Y_W_H_GEOMETRY_MASK = Wnck.WindowMoveResizeMask.HEIGHT | Wnck.WindowMoveResizeMask.WIDTH | Wnck.WindowMoveResizeMask.X | Wnck.WindowMoveResizeMask.Y
CONFIGURE_EVENT_TYPE = Gdk.EventType.CONFIGURE


# https://lazka.github.io/pgi-docs/GdkX11-3.0/classes/X11Display.html
# https://lazka.github.io/pgi-docs/GdkX11-3.0/classes/X11Window.html
def gdk_window_for(window: Wnck.Window) -> GdkX11.X11Window:
	display = GdkX11.X11Display.get_default()
	xid = window.get_xid()
	try:
		return GdkX11.X11Window.foreign_new_for_display(display, xid)
	except TypeError as e:
		raise DirtyState(window=window) from e


# TODO: rename to gdk_monitor_of
def monitor_for(window: Wnck.Window) -> GdkX11.X11Monitor:
	gdk_window: GdkX11.X11Window = gdk_window_for(window)
	gdk_display: GdkX11.X11Display = gdk_window.get_display()
	return gdk_display.get_monitor_at_window(gdk_window)


def monitor_work_area_for(window: Wnck.Window) -> Gdk.Rectangle:
	gdk_monitor = monitor_for(window)
	return gdk_monitor.get_workarea()


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


# TODO: rename to get_top_window
def get_active_window(workspace: Wnck.Workspace = None, window_filter: Callable = None):
	workspace = workspace if workspace else get_active_workspace()
	for stacked in reversed(Wnck.Screen.get_default().get_windows_stacked()):
		if is_visible(stacked, workspace) and (not window_filter or window_filter(stacked)):
			return stacked
	return None


def get_active_workspace() -> Wnck.Workspace:
	return Wnck.Screen.get_default().get_active_workspace()


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


def set_geometry(window: Wnck.Window, x=None, y=None, w=None, h=None, synchronous=False, raise_exceptions=True):

	if not w and not h:
		geometry = window.get_geometry()
		w = geometry.widthp
		h = geometry.heightp

	xo, yo, wo, ho = calculate_geometry_offset(window)
	x, y, w, h = x + xo, y + yo, w + wo, h + ho
	window.set_geometry(Wnck.WindowGravity.STATIC, X_Y_W_H_GEOMETRY_MASK, x, y, w, h)

	if synchronous:
		countdown = 10000
		while countdown > 0:
			countdown -= 1
			e = Gdk.Display.get_default().get_event()
			if e:
				if e.get_event_type() == CONFIGURE_EVENT_TYPE and e.get_window().get_xid() == window.get_xid():
					Gdk.Display.get_default().sync()
					return True
	return False


def get_height(window: Wnck.Window):
	dx, dy, dw, dh = decoration_delta(window)
	with Trap():
		gx, gy, gw, gh = gdk_window_for(window).get_geometry()

	with Trap():
		is_decorated, decorations = gdk_window_for(window).get_decorations()
	client_side_decoration = is_decorated and not decorations and dh > 0

	return gh - dh + (config.get_window_manger_border() * 2 if client_side_decoration else 0)


# TODO: remove duplicated code
def get_width(window: Wnck.Window):
	dx, dy, dw, dh = decoration_delta(window)
	with Trap():
		gx, gy, gw, gh = gdk_window_for(window).get_geometry()

	with Trap():
		is_decorated, decorations = gdk_window_for(window).get_decorations()
	client_side_decoration = is_decorated and not decorations and dw > 0

	return gw - dw + (config.get_window_manger_border() * 2 if client_side_decoration else 0)


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


# TODO: invert and explain
def decoration_delta(window: Wnck.Window):
	with Trap():
		wx, wy, ww, wh = window.get_geometry()
		cx, cy, cw, ch = window.get_client_window_geometry()
	return cx - wx, cy - wy, cw - ww, ch - wh


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
		self.pointer: Monitor = None

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

	def increment_master(self, increment=None, upper_limit=None):
		self.nmaster += increment
		self.nmaster = max(0, self.nmaster)
		self.nmaster = min(upper_limit, self.nmaster)

	def contains(self, window: Wnck.Window):
		rect = self.visible_area
		xp, yp, widthp, heightp = window.get_geometry()
		return rect.x <= xp < (rect.x + rect.width) and rect.y <= yp < (rect.y + rect.height)

	def from_json(self, json):
		self.nmaster = json['nmaster'] if 'nmaster' in json else self.nmaster
		self.mfact = json['mfact'] if 'mfact' in json else self.mfact
		self.function_key = json['function'] if 'function' in json else self.function_key

	def to_json(self):
		return {
			'nmaster': self.nmaster,
			'mfact': self.mfact,
			'function': self.function_key
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