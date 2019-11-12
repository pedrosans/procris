import unittest, subprocess
from unittest.mock import patch
from unittest.mock import MagicMock
from gi.repository import Gio
from procris.applications import Applications


class ApplicationTestCase(unittest.TestCase):

	def setUp(self):
		proc = MagicMock()

	def test_launch(self):
		apps = Applications()
		for app_name in apps.name_map.keys():
			print('{}  ::: {}'.format(app_name, apps.name_map[app_name].getName()))

