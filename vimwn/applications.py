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
import os, glob, gi, configparser, sys
import xdg.DesktopEntry
import xdg.Exceptions
from gi.repository import Gio

APPS_GLOB = [
		"/usr/share/applications/*.desktop",
		"/var/lib/snapd/desktop/applications/*.desktop",
		os.path.expanduser('~/.local/share/applications')+'/*.desktop']


class Applications:

	def __init__(self):
		self.name_map= {}
		self.location_map= {}
		self._read_desktop_files()

	def reload(self):
		self.name_map.clear()
		self._read_desktop_files()

	def _read_desktop_files(self):
		for app_files_glob in APPS_GLOB:
			for file_path in glob.glob(app_files_glob):
				try:
					desktop_entry = xdg.DesktopEntry.DesktopEntry(file_path)
					if not desktop_entry.getExec():
						continue
					name = desktop_entry.getName().strip()
					name = name.replace('\xad', '')
					self.name_map[name] = desktop_entry
					self.location_map[name] = file_path
				except (xdg.Exceptions.ParsingError, TypeError) as e:
					print('Cant read a DesktopEntry from: {} Error: {}'.format(file_path, e), file=sys.stderr)
					continue

	def has_perfect_match(self, name):
		return name in self.name_map.keys()

	def find_by_name(self, name_filter):
		striped = name_filter.lower().strip()
		for app_name in self.name_map.keys():
			if striped == app_name.strip().lower():
				return app_name;
		return None

	def list_completions(self, name_filter):
		lower = name_filter.lower()
		matches = filter( lambda x : lower in x.lower(), self.name_map.keys())
		matches = filter( lambda x : lower != x.lower(), matches)
		return sorted(list(set(matches)), key=str.lower)

	def launch_by_name(self, name):
		launcher = Gio.DesktopAppInfo.new_from_filename(self.location_map[name])
		launcher.launch_uris()

