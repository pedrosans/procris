import unittest
from unittest.mock import MagicMock
from unittest.mock import call

import pocoy.wm as wm
wm.set_geometry = MagicMock()
wm.set_geometry.return_value = False
wm.calculate_geometry_offset = lambda x: [0, 0, 0, 0]

import pocoy.state as state
state.get_inner_gap = lambda: 0
state.get_outer_gap = lambda: 0

import pocoy.layout as layout


class LayoutTestCase(unittest.TestCase):

	def setUp(self):
		self.monitor = layout.Monitor(nmaster=1, mfact=0.5)
		self.monitor.ww = 800
		self.monitor.wh = 550
		self.monitor.wx = 0
		self.monitor.wy = 50
		self.window_01 = MagicMock()
		self.window_02 = MagicMock()
		self.window_03 = MagicMock()
		self.window_04 = MagicMock()
		self.window_05 = MagicMock()

	def test_centeredmaster_two_window(self):
		layout.centeredmaster([self.window_01, self.window_02], self.monitor)
		wm.set_geometry.assert_has_calls([
				call(self.window_01, synchronous=True, x=0, y=50, w=400, h=550),
				call(self.window_02, synchronous=True, x=400, y=50, w=400, h=550)
			])

	def test_centeredmaster_three_window(self):
		layout.centeredmaster([self.window_01, self.window_02, self.window_03], self.monitor)
		wm.set_geometry.assert_has_calls([
			call(self.window_01, synchronous=True, x=200, y=50, w=400, h=550),
			call(self.window_02, synchronous=True, x=600, y=50, w=200, h=550),
			call(self.window_03, synchronous=True, x=0, y=50, w=200, h=550)
		])

	def test_centeredmaster_four_window(self):
		layout.centeredmaster([self.window_01, self.window_02, self.window_03, self.window_04], self.monitor)
		wm.set_geometry.assert_has_calls([
			call(self.window_01, synchronous=True, x=200, y=50, w=400, h=550),
			call(self.window_02, synchronous=True, x=600, y=50, w=200, h=275),
			call(self.window_03, synchronous=True, x=0, y=50, w=200, h=550),
			call(self.window_04, synchronous=True, x=600, y=325, w=200, h=275)
		])

	def test_centeredmaster_5_window(self):
		layout.centeredmaster([self.window_01, self.window_02, self.window_03, self.window_04, self.window_05], self.monitor)
		wm.set_geometry.assert_has_calls([
			call(self.window_01, synchronous=True, x=200, y=50, w=400, h=550),
			call(self.window_02, synchronous=True, x=600, y=50, w=200, h=275),
			call(self.window_03, synchronous=True, x=0, y=50, w=200, h=275),
			call(self.window_04, synchronous=True, x=600, y=325, w=200, h=275),
			call(self.window_05, synchronous=True, x=0, y=325, w=200, h=275)
		])


if __name__ == '__main__':
	unittest.main()
