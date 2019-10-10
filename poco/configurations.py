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

import configparser, os
from xdg import BaseDirectory as base
from xdg import DesktopEntry as desktop
from configparser import ConfigParser

POCO_DESKTOP = 'poco.desktop'
POCO_PACKAGE = 'poco'
DEFAULT_PREFIX_KEY = '<ctrl>q'
DEFAULT_LIST_WORKSPACES = 'true'
DEFAULT_POSITION = 'bottom'
DEFAULT_WIDTH = '800'
DEFAULT_AUTO_HINT = 'true'
DEFAULT_AUTO_SELECT_FIRST_HINT = 'true'


autostart_dir = base.save_config_path("autostart")
autostart_file = os.path.join(autostart_dir, POCO_DESKTOP)
config_dir = base.load_first_config(POCO_PACKAGE)
if not config_dir:
	config_dir = base.save_config_path(POCO_PACKAGE)

config_file_path = os.path.join(config_dir, "poco.cfg")


parser = ConfigParser(interpolation=None)
parser.read(config_file_path)
need_write = False
if not parser.has_section('interface'):
	parser.add_section('interface')
	need_write = True
if not parser.has_option('interface', 'prefix_key'):
	parser.set('interface', 'prefix_key', DEFAULT_PREFIX_KEY)
	need_write = True
if not parser.has_option('interface', 'list_workspaces'):
	parser.set('interface', 'list_workspaces', DEFAULT_LIST_WORKSPACES)
	need_write = True
if not parser.has_option('interface', 'position'):
	parser.set('interface', 'position', DEFAULT_POSITION)
	need_write = True
if not parser.has_option('interface', 'width'):
	parser.set('interface', 'width', DEFAULT_WIDTH)
	need_write = True
if not parser.has_option('interface', 'auto_hint'):
	parser.set('interface', 'auto_hint', DEFAULT_AUTO_HINT)
	need_write = True
if not parser.has_option('interface', 'auto_select_first_hint'):
	parser.set('interface', 'auto_select_first_hint', DEFAULT_AUTO_SELECT_FIRST_HINT)
	need_write = True
if not parser.has_option('interface', 'icon'):
	parser.set('interface', 'icon', 'default')
	need_write = True
if not parser.has_section('layout'):
	parser.add_section('layout')
	need_write = True
if not parser.has_option('layout', 'remove_decorations'):
	parser.set('layout', 'remove_decorations', 'false')
	need_write = True
if need_write:
	with open(config_file_path, 'w') as f:
		parser.write(f)


def get_css_file_path():
	return os.path.join(config_dir, "poco.css")


def reload():
	parser.read(config_file_path)


def is_list_workspaces():
	return parser.getboolean('interface', 'list_workspaces')


def get_prefix_key():
	return parser.get('interface', 'prefix_key')


def get_position():
	return parser.get('interface', 'position')


def get_width():
	return parser.get('interface', 'width')


def is_auto_hint():
	try:
		return parser.getboolean('interface', 'auto_hint')
	except configparser.NoOptionError:
		return True


def is_auto_select_first_hint():
	try:
		return parser.getboolean('interface', 'auto_select_first_hint')
	except configparser.NoOptionError:
		return True


def get_icon():
	try:
		return parser.get('interface', 'icon')
	except configparser.NoOptionError:
		return None


def set_icon( icon):
	parser.set('interface', 'icon', icon)
	with open(config_file_path, 'w') as f:
		parser.write(f)


def is_remove_decorations():
	return parser.getboolean('layout', 'remove_decorations')


def set_remove_decorations( remove):
	parser.set('layout', 'remove_decorations', str(remove).lower())
	# TODO: extract method
	with open(config_file_path, 'w') as f:
		parser.write(f)


def is_autostart():
	dfile = desktop.DesktopEntry(autostart_file)
	return bool(dfile.get("X-GNOME-Autostart-enabled", type="boolean"))


def set_autostart( auto_start):
	dfile = desktop.DesktopEntry(autostart_file)
	dfile.set("X-GNOME-Autostart-enabled", str(auto_start).lower())
	dfile.set("Name", "poco")
	dfile.set("Icon", "poco")
	dfile.set("Exec", "poco start")
	dfile.write(filename=autostart_file)
