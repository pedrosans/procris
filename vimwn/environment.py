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

VIMWN_DESKTOP = 'vimwn.desktop'
VIMWN_PACKAGE = 'vimwn'
DEFAULT_PREFIX_KEY = '<ctrl>q'
DEFAULT_LIST_WORKSPACES = 'true'
DEFAULT_POSITION = 'bottom'
DEFAULT_WIDTH = '800'
DEFAULT_AUTO_HINT = 'true'
DEFAULT_AUTO_SELECT_FIRST_HINT = 'true'


class Configurations:

	def __init__(self):

		autostart_dir = base.save_config_path("autostart")
		self.autostart_file = os.path.join(autostart_dir, VIMWN_DESKTOP)

		self.parser = ConfigParser(interpolation=None)
		self.parser.read(self.get_config_file_path())
		need_write = False
		if not self.parser.has_section('interface'):
			self.parser.add_section('interface')
			need_write = True
		if not self.parser.has_option('interface', 'prefix_key'):
			self.parser.set('interface', 'prefix_key', DEFAULT_PREFIX_KEY)
			need_write = True
		if not self.parser.has_option('interface', 'list_workspaces'):
			self.parser.set('interface', 'list_workspaces', DEFAULT_LIST_WORKSPACES)
			need_write = True
		if not self.parser.has_option('interface', 'position'):
			self.parser.set('interface', 'position', DEFAULT_POSITION)
			need_write = True
		if not self.parser.has_option('interface', 'width'):
			self.parser.set('interface', 'width', DEFAULT_WIDTH)
			need_write = True
		if not self.parser.has_option('interface', 'auto_hint'):
			self.parser.set('interface', 'auto_hint', DEFAULT_AUTO_HINT)
			need_write = True
		if not self.parser.has_option('interface', 'auto_select_first_hint'):
			self.parser.set('interface', 'auto_select_first_hint', DEFAULT_AUTO_SELECT_FIRST_HINT)
			need_write = True
		if not self.parser.has_option('interface', 'icon'):
			self.parser.set('interface', 'icon', 'default')
			need_write = True
		if need_write:
			with open(self.get_config_file_path(), 'w') as f:
				self.parser.write(f)

	def get_config_dir(self):
		d = base.load_first_config(VIMWN_PACKAGE)
		if not d:
			d = base.save_config_path(VIMWN_PACKAGE)
		return d

	def reload(self):
		self.parser.read(self.get_config_file_path())

	def is_list_workspaces(self):
		return self.parser.getboolean('interface', 'list_workspaces')

	def get_prefix_key(self):
		return self.parser.get('interface', 'prefix_key')

	def get_position(self):
		return self.parser.get('interface', 'position')

	def get_width(self):
		return self.parser.get('interface', 'width')

	def is_auto_hint(self):
		try:
			return self.parser.getboolean('interface', 'auto_hint')
		except configparser.NoOptionError:
			return True

	def is_auto_select_first_hint(self):
		try:
			return self.parser.getboolean('interface', 'auto_select_first_hint')
		except configparser.NoOptionError:
			return True

	def get_icon(self):
		try:
			return self.parser.get('interface', 'icon')
		except configparser.NoOptionError:
			return None

	def set_icon(self, icon):
		self.parser.set('interface', 'icon', icon)
		with open(self.get_config_file_path(), 'w') as f:
			self.parser.write(f)

	def get_css_file_path(self):
		return os.path.join(self.get_config_dir(), "vimwn.css")

	def get_config_file_path(self):
		return os.path.join(self.get_config_dir(), "vimwn.cfg")

	def is_autostart(self):
		dfile = desktop.DesktopEntry(self.autostart_file)
		return bool(dfile.get("X-GNOME-Autostart-enabled", type="boolean"))

	def set_autostart(self, auto_start):
		dfile = desktop.DesktopEntry(self.autostart_file)
		dfile.set("X-GNOME-Autostart-enabled", str(auto_start).lower())
		dfile.set("Name", "Vimwn")
		dfile.set("Icon", "vimwn")
		dfile.set("Exec", "vimwn start")
		dfile.write(filename=self.autostart_file)
