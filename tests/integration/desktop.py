import unittest
import gi
import xdg.IconTheme
gi.require_version('Notify', '0.7')
from gi.repository import Notify, GLib,  GdkPixbuf


class XdgIntegrationTestCase(unittest.TestCase):

	def test_list_application_names(self):
		import xdg.IconTheme
		p = xdg.IconTheme.getIconPath('procris-T')
		GdkPixbuf.Pixbuf.new_from_file(p)

		print(p)



if __name__ == '__main__':
	unittest.main()

