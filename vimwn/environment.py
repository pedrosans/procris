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
from configparser import SafeConfigParser

VIMWN_DESKTOP='vimwn.desktop'
VIMWN_PACKAGE='vimwn'
DEFAULT_LOG_FILE='~/.vimwn/vimwn.log'
DEFAULT_PREFIX_KEY='<ctrl>q'
DEFAULT_LIST_WORKSPACES='true'
DEFAULT_COMPACT_OPTION='false'
DEFAULT_POSITION='bottom'
DEFAULT_WIDTH='800'
DEFAULT_AUTO_HINT='true'

class Configurations():

	def __init__(self):

		autostart_dir = base.save_config_path("autostart")
		self.autostart_file = os.path.join(autostart_dir, VIMWN_DESKTOP)

		self.parser = SafeConfigParser(interpolation=None)
		self.parser.read(self.get_config_file())
		need_write = False
		if not self.parser.has_section('service'):
			self.parser.add_section('service')
			need_write = True
		if not self.parser.has_option('service', 'log_file'):
			self.parser.set('service', 'log_file', DEFAULT_LOG_FILE)
			need_write = True
		if not self.parser.has_section('interface'):
			self.parser.add_section('interface')
			need_write = True
		if not self.parser.has_option('interface', 'prefix_key'):
			self.parser.set('interface', 'prefix_key', DEFAULT_PREFIX_KEY)
			need_write = True
		if not self.parser.has_option('interface', 'compact'):
			self.parser.set('interface', 'compact', DEFAULT_COMPACT_OPTION)
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
			self.parser.set('interface', 'auto_select_first_hint', 'false')
			need_write = True
		if not self.parser.has_option('interface', 'save_vertical_space'):
			self.parser.set('interface', 'save_vertical_space', 'false')
			need_write = True
		if not self.parser.has_option('interface', 'icon'):
			self.parser.set('interface', 'icon', 'default')
			need_write = True
		if need_write:
			with open(self.get_config_file(), 'w') as f:
				self.parser.write(f)

	def is_list_workspaces(self):
		return self.parser.getboolean('interface', 'list_workspaces')

	def is_compact_interface(self):
		try:
			return self.parser.getboolean('interface', 'compact')
		except configparser.NoOptionError:
			return False

	def get_prefix_key(self):
		return self.parser.get('interface', 'prefix_key')

	def get_command_prefix_key(self):
		try:
			return self.parser.get('interface', 'command_prefix_key')
		except configparser.NoOptionError:
			return None

	def get_position(self):
		return self.parser.get('interface', 'position')

	#TODO how to avoid to need to scape %
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

	def is_save_vertical_space(self):
		try:
			return self.parser.getboolean('interface', 'save_vertical_space')
		except configparser.NoOptionError:
			return True

	def get_icon(self):
		try:
			return self.parser.get('interface', 'icon')
		except configparser.NoOptionError:
			return None

	def set_icon(self, icon):
		self.parser.set('interface', 'icon', icon)
		with open(self.get_config_file(), 'w') as f:
			self.parser.write(f)

	def get_css_file(self):
		try:
			path = self.parser.get('interface', 'css_file')
			return os.path.expanduser(path)
		except configparser.NoOptionError:
			return None

	def get_log_file(self):
		try:
			path = self.parser.get('service', 'log_file')
			return os.path.expanduser(path)
		except configparser.NoOptionError:
			return None

	def get_config_file(self):
		d = base.load_first_config(VIMWN_PACKAGE)
		if not d:
			d = base.save_config_path(VIMWN_PACKAGE)
		return os.path.join(d, "vimwn.cfg")

	def is_autostart(self):
		dfile = desktop.DesktopEntry(self.autostart_file)
		return bool(dfile.get("X-GNOME-Autostart-enabled", type="boolean"))

	def set_autostart(self, auto_start):
		dfile = desktop.DesktopEntry(self.autostart_file)
		dfile.set("X-GNOME-Autostart-enabled", str(auto_start).lower())
		dfile.set("Name", "Vimwn")
		dfile.set("Icon", "vimwn")
		dfile.set("Exec", "vimwn start --redirect-output")
		dfile.write(filename=self.autostart_file)
