import unittest
import pwm.desktop


class XdgIntegrationTestCase(unittest.TestCase):

	def test_load_theme(self):
		pwm.desktop.load()
		self.assertIsNotNone(pwm.desktop.ICON_STYLES_MAP.keys())
		pwm.desktop.unload()


if __name__ == '__main__':
	unittest.main()

