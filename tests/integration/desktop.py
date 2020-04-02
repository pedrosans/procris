import unittest
import pocoy.desktop


class XdgIntegrationTestCase(unittest.TestCase):

	def test_load_theme(self):
		pocoy.desktop.load()
		self.assertIsNotNone(pocoy.desktop.ICON_STYLES_MAP.keys())
		pocoy.desktop.unload()


if __name__ == '__main__':
	unittest.main()

