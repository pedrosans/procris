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
from types import ModuleType
from xdg import BaseDirectory as Base
from xdg import DesktopEntry as Desktop
from typing import Dict, List
import os
import json


POCOY_DESKTOP = 'pocoy.desktop'
POCOY_PACKAGE = 'pocoy'
auto_start_dir = Base.save_config_path("autostart")
auto_start_file = os.path.join(auto_start_dir, POCOY_DESKTOP)
config_dir = Base.save_config_path(POCOY_PACKAGE)
cache_dir = Base.save_cache_path(POCOY_PACKAGE)
workspace_file = cache_dir + '/workspace.json'
decorations_file = cache_dir + '/decoration.json'
config_file = cache_dir + '/config.json'
loaded_workspace_config: Dict = None
loaded_decorations: Dict = None
config_module: ModuleType = None
DEFAULTS = {
	'position': 'bottom',
	'width': 800,
	'auto_hint': True,
	'auto_select_first_hint': False,
	'desktop_icon': 'light',
	'desktop_notifications': False,
	'window_manger_border': 0,
	'remove_decorations': True,
	'inner_gap': 5,
	'outer_gap': 5,
	'workspaces': [
		{
			'monitors': [
				{'nmaster': 1, 'mfact': 0.55, 'strut': [0, 0, 0, 0], 'function': None},
				{'nmaster': 1, 'mfact': 0.55, 'strut': [0, 0, 0, 0], 'function': None}
			]
		},
		{
			'monitors': [
				{'nmaster': 1, 'mfact': 0.55, 'strut': [0, 0, 0, 0], 'function': None},
				{'nmaster': 1, 'mfact': 0.55, 'strut': [0, 0, 0, 0], 'function': None}
			]
		}
	]
}


#
# Wherever exists in between pocoy.stop() and pocoy.start()
#
def load(config_module_parameter: str = None):
	global loaded_workspace_config, loaded_decorations, config_module

	config_module = read_config_module(config_module_parameter)

	loaded_workspace_config = _read_json(workspace_file)
	deep_copy(loaded_workspace_config, DEFAULTS, override=False)
	if hasattr(config_module, 'parameters'):
		deep_copy(loaded_workspace_config, config_module.parameters, override=True)

	loaded_decorations = _read_json(decorations_file)


def deep_copy(destination, origin, override):
	for key in origin.keys():
		if isinstance(origin[key], type({})) and key in destination:
			deep_copy(destination[key], origin[key], override)
		elif isinstance(origin[key], type([])) and key in destination:
			for i in range(min(len(origin[key]), len(destination[key]))):
				if isinstance(origin[key][i], type({})):
					deep_copy(destination[key][i], origin[key][i], override)
		elif origin[key] is not None and (override or (key not in destination or not destination[key])):
			destination[key] = origin[key]


def reload():
	load()


def force_defaults():
	clean()


def clean():
	if os.path.exists(workspace_file):
		os.remove(workspace_file)
	if os.path.exists(config_file):
		os.remove(config_file)


#
# JSON CONFIG
#
def persist_workspace(workspace: List[Dict] = None):
	if workspace:
		loaded_workspace_config['workspaces'] = workspace
	with open(workspace_file, 'w') as f:
		json.dump(loaded_workspace_config, f, indent=True)


def persist_decorations(decoration_map: Dict):
	with open(decorations_file, 'w') as f:
		json.dump(decoration_map, f, indent=True)


def _read_json(file):
	if os.path.exists(file):
		with open(file, 'r') as f:
			try:
				return json.load(f)
			except json.decoder.JSONDecodeError:
				return {}
	return {}


#
# PROGRAMMABLE CONFIG
#
def read_config_module(config_module_parameter: str = None):

	if 'default' != config_module_parameter:
		try:
			import importlib.util
			spec = importlib.util.spec_from_file_location("module.name", get_custom_mappings_module_path())
			user_config = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(user_config)
			return user_config
		except FileNotFoundError as e:
			print(
				'info: not possible to load custom config at: {}'.format(get_custom_mappings_module_path()))

	import pocoy.config as default_config
	return default_config


#
# CONFIG FACADE
#
def get_config_module() -> ModuleType:
	return config_module


def get_workspace_config() -> Dict:
	return loaded_workspace_config


def get_decorations() -> Dict:
	return loaded_decorations


def get_position() -> str:
	return loaded_workspace_config['position']


def get_width() -> str:
	return loaded_workspace_config['width']


def is_auto_hint() -> bool:
	return loaded_workspace_config['auto_hint']


def is_auto_select_first_hint() -> bool:
	return loaded_workspace_config['auto_select_first_hint']


def get_window_manger_border() -> int:
	return loaded_workspace_config['window_manger_border']


def get_desktop_icon() -> str:
	return loaded_workspace_config['desktop_icon']


def set_desktop_icon(icon):
	loaded_workspace_config['desktop_icon'] = icon
	persist_workspace()


def is_desktop_notifications() -> bool:
	return loaded_workspace_config['desktop_notifications']


def is_remove_decorations() -> bool:
	return loaded_workspace_config['remove_decorations']


def set_remove_decorations(remove: bool):
	loaded_workspace_config['remove_decorations'] = remove
	persist_workspace()


def get_inner_gap() -> int:
	return loaded_workspace_config['inner_gap']


def get_outer_gap() -> int:
	return loaded_workspace_config['outer_gap']


def set_inner_gap(gap: int):
	loaded_workspace_config['inner_gap'] = gap
	persist_workspace()


def set_outer_gap(gap: int):
	loaded_workspace_config['outer_gap'] = gap
	persist_workspace()


#
# AUTO START
#
def is_autostart():
	dfile = Desktop.DesktopEntry(auto_start_file)
	return bool(dfile.get("X-GNOME-Autostart-enabled", type="boolean"))


def set_autostart( auto_start):
	dfile = Desktop.DesktopEntry(auto_start_file)
	dfile.set("X-GNOME-Autostart-enabled", str(auto_start).lower())
	dfile.set("Name", "pocoy")
	dfile.set("Icon", "pocoy")
	dfile.set("Exec", "pocoy")
	dfile.write(filename=auto_start_file)


#
# UTIL
#
def get_css_file_path():
	return os.path.join(config_dir, "pocoy.css")


def get_custom_mappings_module_path():
	return os.path.join(config_dir, "config.py")
