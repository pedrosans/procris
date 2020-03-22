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
import configparser
import os
import json

PROCRIS_DESKTOP = 'procris.desktop'
PROCRIS_PACKAGE = 'procris'

autostart_dir = base.save_config_path("autostart")
autostart_file = os.path.join(autostart_dir, PROCRIS_DESKTOP)
config_dir = base.save_config_path(PROCRIS_PACKAGE)
config_file = os.path.join(config_dir, "procris.cfg")
cache_dir = base.save_cache_path(PROCRIS_PACKAGE)
layout_file = cache_dir + '/layout.json'
decorations_file = cache_dir + '/decoration.json'
parser = ConfigParser(interpolation=None)
parser.read(config_file)


def _write_interface_config():
	with open(config_file, 'w') as f:
		parser.write(f)


def _read_json(file):
	if os.path.exists(file):
		with open(file, 'r') as f:
			try:
				return json.load(f)
			except json.decoder.JSONDecodeError:
				return {}
	return {}


def set_default(section, property_name, property_value):
	if not parser.has_section(section):
		parser.add_section(section)
	if not parser.has_option(section, property_name):
		parser.set(section, property_name, property_value)


def set_defaults(defaults: Dict):
	set_default('interface', 'position', defaults['position'])
	set_default('interface', 'width', defaults['width'])
	set_default('interface', 'auto_hint', defaults['auto_hint'])
	set_default('interface', 'auto_select_first_hint', defaults['auto_select_first_hint'])
	set_default('interface', 'icon', defaults['icon'])
	set_default('layout', 'remove_decorations', defaults['remove_decorations'])
	_write_interface_config()


def reload():
	parser.read(config_file)


def get_css_file_path():
	return os.path.join(config_dir, "procris.css")


def get_custom_mappings_module_path():
	return os.path.join(config_dir, "mappings.py")


#
# INTERFACE PROPERTIES
#
def get_position():
	return parser.get('interface', 'position')


def get_width():
	return parser.get('interface', 'width')


def is_auto_hint():
	return parser.getboolean('interface', 'auto_hint')


def is_auto_select_first_hint():
	return parser.getboolean('interface', 'auto_select_first_hint')


def get_icon():
	return parser.get('interface', 'icon')


def set_icon(icon):
	parser.set('interface', 'icon', icon)
	_write_interface_config()


def is_remove_decorations():
	return parser.getboolean('layout', 'remove_decorations')


def set_remove_decorations(remove):
	parser.set('layout', 'remove_decorations', str(remove).lower())
	_write_interface_config()


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


#
# JSON CONFIG
#
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

