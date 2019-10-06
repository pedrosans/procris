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

from vimwn.windows import monitor_work_area_for


class Monitor:

	def __init__(self):
		self.nmaster = 1
		self.mfact = 0.55
		self.wx = self.wy = self.ww = self.wh = None

	def set_workarea(self, x, y, width, height):
		self.wx = x
		self.wy = y
		self.ww = width
		self.wh = height


class LayoutManager:

	def __init__(self, windows):
		self.gap = 10
		self.windows = windows
		self.layout_function = centeredmaster
		self.layout_monitor = Monitor()
		self.windows.read_screen()
		self.stack = list(map(lambda x: x.get_xid(), self.windows.visible))
		# self.screen.connect("active-window-changed", self._active_window_changed)
		# def _active_window_changed(self, screen, previously_active_window):
		self.windows.screen.connect("window-opened", self._window_opened)
		self.windows.screen.connect("window-closed", self._window_closed)

	def layout(self):
		w_stack = map(lambda x: self.windows.visible_map[x] if x in self.windows.visible_map else None, self.stack)
		w_stack = filter(lambda x: x is not None, w_stack)
		w_stack = list(w_stack)

		if not w_stack:
			return

		wa = monitor_work_area_for(w_stack[0])

		self.layout_monitor.set_workarea(x=wa.x + self.gap, y=wa.y + self.gap,
										width=wa.width - self.gap * 2, height=wa.height - self.gap * 2)

		arrange = self.layout_function(w_stack, self.layout_monitor)

		for i in range(len(arrange)):
			a = arrange[i]
			w = w_stack[i]
			# print('w({}): {:30}  x: {:10}   y: {:10}   w: {:10}   h: {:10}'.format(i, w.get_name(), a[0], a[1], a[2], a[3]))
			self.windows.set_geometry(w, x=a[0] + self.gap, y=a[1] + self.gap,
										w=a[2] - self.gap * 2, h=a[3] - self.gap * 2)

	def move_to_master(self, w):
		if w:
			old_index = self.stack.index(w.get_xid())
			self.stack.insert(0, self.stack.pop(old_index))

	def _window_opened(self, screen, window):
		if window.get_pid() != os.getpid():
			self.windows.read_screen(force_update=False)
			if window in self.windows.visible:
				self.stack.insert(0, window.get_xid())
			self.layout()

	def _window_closed(self, screen, window):
		if window.get_xid() in self.stack:
			self.stack.remove(window.get_xid())
		if window.get_pid() != os.getpid():
			self.windows.read_screen(force_update=False)
			self.layout()


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
