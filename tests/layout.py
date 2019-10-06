import unittest
from unittest.mock import patch
from unittest.mock import MagicMock
from vimwn.layout import Layout


class LayoutTestCase(unittest.TestCase):

	def setUp(self):
		self.monitor = MagicMock()
		self.monitor.ww = 800
		self.monitor.wh = 550
		self.monitor.wx = 0
		self.monitor.wy = 50
		self.monitor.nmaster = 1
		self.monitor.mfact = 0.5

		self.stack = []
		self.window_01 = MagicMock()
		self.window_01.bw = 0
		self.window_01.get_geometry = MagicMock()
		self.window_01.get_geometry.return_value = [0,0,0,0]

		self.window_02 = MagicMock()
		self.window_02.bw = 0
		self.window_02.get_geometry = MagicMock()
		self.window_02.get_geometry.return_value = [0,0,0,0]

		self.window_03 = MagicMock()
		self.window_03.bw = 0
		self.window_03.get_geometry = MagicMock()
		self.window_03.get_geometry.return_value = [0,0,0,0]

		self.window_04 = MagicMock()
		self.window_04.bw = 0
		self.window_04.get_geometry = MagicMock()
		self.window_04.get_geometry.return_value = [0,0,0,0]

		self.window_05 = MagicMock()
		self.window_05.bw = 0
		self.window_05.get_geometry = MagicMock()
		self.window_05.get_geometry.return_value = [0,0,0,0]

	def test_centeredmaster_two_window(self):
		print('**********************************************************************************************')
		layout = Layout()
		arrange = layout.arrange([self.window_01, self.window_02], self.monitor)
		for a in arrange:
			print('x: {:10}   y: {:10}   w: {:10}   h: {:10}'.format(a[0], a[1], a[2], a[3]))

	def test_centeredmaster_three_window(self):
		print('**********************************************************************************************')
		layout = Layout()
		arrange = layout.arrange([self.window_01, self.window_02, self.window_03], self.monitor)
		for a in arrange:
			print('x: {:10}   y: {:10}   w: {:10}   h: {:10}'.format(a[0], a[1], a[2], a[3]))

	def test_centeredmaster_four_window(self):
		print('**********************************************************************************************')
		layout = Layout()
		arrange = layout.arrange([self.window_01, self.window_02, self.window_03, self.window_04], self.monitor)
		for a in arrange:
			print('x: {:10}   y: {:10}   w: {:10}   h: {:10}'.format(a[0], a[1], a[2], a[3]))

	def test_centeredmaster_x_window(self):
		print('**********************************************************************************************')
		layout = Layout()
		arrange = layout.arrange(
			[self.window_01, self.window_02, self.window_03, self.window_04, self.window_05], self.monitor)
		for a in arrange:
			print('x: {:10}   y: {:10}   w: {:10}   h: {:10}'.format(a[0], a[1], a[2], a[3]))

if __name__ == '__main__':
	unittest.main()
