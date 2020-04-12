import unittest
import pocoy.model as model
from pocoy.wm import Monitor
from unittest.mock import MagicMock

workspace = MagicMock()
workspace.get_number = lambda: 0
screen = MagicMock()
screen.get_workspaces = lambda: [workspace]
model.monitors.primary_monitors = {0: Monitor(primary=True)}


class ModelTestCase(unittest.TestCase):

	def test_read_user_config(self):
		model.read_user_config(DEFAULTS, screen)
		primary: Monitor = model.monitors.get_primary(workspace)
		self.assertEqual(primary.nmaster, 1)
		self.assertEqual(primary.mfact, 0.55)
		self.assertEqual(primary.function_key, 'T')


DEFAULTS = {
	'position': 'bottom',
	'width': 800,
	'auto_hint': True,
	'auto_select_first_hint': False,
	'desktop_icon': 'light',
	'desktop_notifications': False,
	'window_manger_border': 0,
	'remove_decorations': False,
	'inner_gap': 5,
	'outer_gap': 5,
	'workspaces': [
		{
			'monitors': [
				{'nmaster': 1, 'mfact': 0.55, 'function': 'T'},
				{'nmaster': 1, 'mfact': 0.55, 'function': None}
			]
		},
		{
			'monitors': [
				{'nmaster': 1, 'mfact': 0.55, 'function': None},
				{'nmaster': 1, 'mfact': 0.55, 'function': None}
			]
		}
	]
}


if __name__ == '__main__':
	unittest.main()
