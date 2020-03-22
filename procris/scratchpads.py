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

import gi, procris.service

from procris.wm import is_visible

gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, Gdk
from typing import List, Dict, Callable


class Scratchpad:
	name: str
	launch: Callable
	l: float
	t: float
	w: float
	h: float

	def __init__(
			self,
			name: str = None, launch: Callable = None,
			l: float = None, t: float = None, w: float = None, h: float = None):
		self.name = name
		self.l = l
		self.t = t
		self.w = w
		self.h = h
		self.launch = launch


memory: Dict[str, Scratchpad] = {}


def add(
		scratchpad: Scratchpad = None, name: str = None, launch: Callable = None,
		l: float = None, t: float = None, w: float = None, h: float = None):
	if not scratchpad:
		scratchpad = Scratchpad(name=name, launch=launch, l=l, t=t, w=w, h=h)
	memory[scratchpad.name] = scratchpad


def get(name: str):
	return memory[name]


def names():
	return memory.keys()


def toggle(c_in):
	name = c_in.parameters[0]
	windows = procris.service.windows
	matching: Wnck.Window = list(filter(lambda x: x.get_name() == name, windows.buffers))
	if matching:
		if len(matching) > 1:
			return 'scratchpad name matches more than one window title'
		if is_visible(matching[0]):
			matching[0].minimize()
		else:
			windows.active.xid = matching[0].get_xid()
		windows.staging = True
	else:
		scratchpad = memory[name]
		scratchpad.launch()