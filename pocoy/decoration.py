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
import pocoy.state as persistor
from pocoy.wm import gdk_window_for, UserEvent

gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, GdkX11, Gdk
from typing import List


DECORATION_MAP = {
	'ALL': Gdk.WMDecoration.ALL,
	'BORDER': Gdk.WMDecoration.BORDER,
	'MAXIMIZE': Gdk.WMDecoration.MAXIMIZE,
	'MENU': Gdk.WMDecoration.MENU,
	'MINIMIZE ': Gdk.WMDecoration.MINIMIZE,
	'RESIZEH': Gdk.WMDecoration.RESIZEH,
	'TITLE': Gdk.WMDecoration.TITLE,
	'NONE': 0}


def remove(buffers: List[Wnck.Window]):
	decoration_map = persistor.get_decorations()

	for w in buffers:

		key = str(w.get_xid())
		gdk_w = gdk_window_for(w)

		is_decorated, decorations = gdk_w.get_decorations()
		has_title = Gdk.WMDecoration.TITLE & decorations or Gdk.WMDecoration.ALL & decorations
		ssd = not is_decorated and not decorations

		if has_title or ssd:
			if key not in decoration_map:
				decoration_map[key] = decorations if not ssd else Gdk.WMDecoration.ALL
			gdk_w.set_decorations(Gdk.WMDecoration.BORDER)

	for key in list(decoration_map.keys()):
		if key not in map(lambda x: str(x.get_xid()), buffers):
			del decoration_map[key]

	persistor.persist_decorations(decoration_map)


def restore(buffers: List[Wnck.Window]):
	original_decorations = persistor.get_decorations()
	for w in buffers:
		if str(w.get_xid()) in original_decorations:
			gdk_window_for(w).set_decorations(Gdk.WMDecoration(original_decorations[str(w.get_xid())]))


def complete(c_in: UserEvent):
	option_name = c_in.vim_command_parameter
	return list(filter(lambda x: x.lower().startswith(option_name.lower().strip()), DECORATION_MAP.keys()))


"""
ALL - all decorations should be applied.
BORDER - a frame should be drawn around the window.
MAXIMIZE - a maximize button should be included.
MENU - a button for opening a menu should be included.
MINIMIZE - a minimize button should be included.
RESIZEH - the frame should have resize handles.
TITLE - a titlebar should be placed above the window.
"""
