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

from xdg import BaseDirectory as base
from xdg import DesktopEntry as desktop
from configparser import ConfigParser
from typing import Dict
import os
import json

PROCRIS_DESKTOP = 'procris.desktop'
PROCRIS_PACKAGE = 'procris'

autostart_dir = base.save_config_path("autostart")
autostart_file = os.path.join(autostart_dir, PROCRIS_DESKTOP)
config_dir = base.save_config_path(PROCRIS_PACKAGE)
cache_dir = base.save_cache_path(PROCRIS_PACKAGE)
layout_file = cache_dir + '/layout.json'
decorations_file = cache_dir + '/decoration.json'
config_file = cache_dir + '/config.json'

memory: Dict = None


def load(default: Dict = None):
	global memory
	config = read_interface_config()
	memory = config if config else default


def reload():
	global memory
	memory = read_interface_config()


def clean():
	if os.path.exists(layout_file):
		os.remove(layout_file)
	if os.path.exists(config_file):
		os.remove(config_file)


def get_css_file_path():
	return os.path.join(config_dir, "procris.css")


def get_custom_mappings_module_path():
	return os.path.join(config_dir, "config.py")


#
# INTERFACE PROPERTIES
#
def get_position() -> str:
	return memory['position']


def get_width() -> str:
	return memory['width']


def is_auto_hint() -> bool:
	return memory['auto_hint']


def is_auto_select_first_hint() -> bool:
	return memory['auto_select_first_hint']


def get_window_manger_border() -> int:
	return memory['window_manger_border']


def get_icon() -> str:
	return memory['icon']


def set_icon(icon):
	memory['icon'] = icon
	persist_interface_config()


def is_remove_decorations() -> bool:
	return memory['remove_decorations']


def set_remove_decorations(remove: bool):
	memory['remove_decorations'] = remove
	persist_interface_config()


#
# JSON CONFIG
#
def persist_interface_config():
	with open(config_file, 'w') as f:
		json.dump(memory, f, indent=True)


def read_interface_config():
	return _read_json(config_file)


def persist_layout(layout: Dict):
	with open(layout_file, 'w') as f:
		json.dump(layout, f, indent=True)


def read_layout(default: Dict = None):
	config = _read_json(layout_file)
	return config if config else default


def persist_decorations(decoration_map: Dict):
	with open(decorations_file, 'w') as f:
		json.dump(decoration_map, f, indent=True)


def read_decorations():
	return _read_json(decorations_file)


def _read_json(file):
	if os.path.exists(file):
		with open(file, 'r') as f:
			try:
				return json.load(f)
			except json.decoder.JSONDecodeError:
				return {}
	return {}


#
# AUTO START
#
def is_autostart():
	dfile = desktop.DesktopEntry(autostart_file)
	return bool(dfile.get("X-GNOME-Autostart-enabled", type="boolean"))


def set_autostart( auto_start):
	dfile = desktop.DesktopEntry(autostart_file)
	dfile.set("X-GNOME-Autostart-enabled", str(auto_start).lower())
	dfile.set("Name", "procris")
	dfile.set("Icon", "procris")
	dfile.set("Exec", "procris start")
	dfile.write(filename=autostart_file)
