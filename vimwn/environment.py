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

import configparser
import os
from xdg import BaseDirectory as base
from xdg import DesktopEntry as desktop
from configparser import SafeConfigParser

VIMWN_DESKTOP='vimwn.desktop'
VIMWN_PACKAGE='vimwn'
DEFAULT_HOTKEYS='<ctrl>q'
DEFAULT_LIST_WORKSPACES='true'

class Configurations():

	def __init__(self):

		autostart_dir = base.save_config_path("autostart")
		self.autostart_file = os.path.join(autostart_dir, VIMWN_DESKTOP)

		self.parser = SafeConfigParser()
		self.parser.read(self.get_config_file())
		need_write = False
		if not self.parser.has_section('interface'):
			self.parser.add_section('interface')
			need_write = True
		if not self.parser.has_option('interface', 'hotkeys'):
			self.parser.set('interface', 'hotkeys', DEFAULT_HOTKEYS)
			need_write = True
		if not self.parser.has_option('interface', 'list_workspaces'):
			self.parser.set('interface', 'list_workspaces', DEFAULT_LIST_WORKSPACES)
			need_write = True
		if need_write:
			with open(self.get_config_file(), 'w') as f:
				self.parser.write(f)

	def is_list_workspaces(self):
		return self.parser.getboolean('interface', 'list_workspaces')

	def get_hotkeys(self):
		return self.parser.get('interface', 'hotkeys')

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
		dfile.write(filename=self.autostart_file)
