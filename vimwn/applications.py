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
import os, glob, gi, configparser
import xdg.DesktopEntry
import xdg.Exceptions
from gi.repository import GLib
from vimwn import desktop_parse
from vimwn import desktop_launch
from configparser import SafeConfigParser

APPS_GLOB = [
		"/usr/share/applications/*.desktop",
		"/var/lib/snapd/desktop/applications/*.desktop",
		os.path.expanduser('~/.local/share/applications')+'/*.desktop' ]

class Applications():

	def __init__(self):
		self.name_map= {}
		for app_files_glob in APPS_GLOB:
			for f in glob.glob(app_files_glob):
				try:
					desktop_info = self.read_desktop_info(f)
				except:
					#TODO print
					continue
				if desktop_info:
					self.name_map[desktop_info['Name']] = desktop_info

	def has_perfect_match(self, name):
		return name in self.name_map.keys()

	def query_names(self, name_filter):
		striped = name_filter.lower().lstrip()
		matches = filter( lambda x : striped in x.lower().strip(), self.name_map.keys())
		matches = filter( lambda x : striped != x.lower().strip(), matches)
		return sorted(list(set(matches)), key=str.lower)

	def launch_by_name(self, name):
		desktop_info = self.name_map[name]
		workdir = desktop_info["Path"] or None
		if not workdir or not os.path.exists(workdir):
			workdir = "."
		argv = desktop_parse.parse_unesc_argv(desktop_info['Exec'])
		desktop_file = desktop_info['Location']
		multiple_needed, missing_format, launch_argv = desktop_launch.replace_format_specs(argv, desktop_file, desktop_info, [])
		GLib.spawn_async(argv=launch_argv, flags=GLib.SpawnFlags.SEARCH_PATH, working_directory=workdir)

	def gtk_to_unicode(self, gtkstring):
		"""
		Kupfer code from: https://github.com/kupferlauncher/kupfer/blob/feca5b98af28d77b8a8d3af60d5782449fa71563/kupfer/desktop_launch.py
		Return unicode for a GTK/GLib string (bytestring or unicode)
		"""
		if isinstance(gtkstring, str):
			return gtkstring
		return gtkstring.decode("UTF-8", "ignore")

	def read_desktop_info(self, desktop_file):
		"""
		Kupfer code from: https://github.com/kupferlauncher/kupfer/blob/feca5b98af28d77b8a8d3af60d5782449fa71563/kupfer/desktop_launch.py
		Get the keys StartupNotify, Terminal, Exec, Path, Icon
		Return dict with bool and unicode values
		"""
		de = xdg.DesktopEntry.DesktopEntry(desktop_file)

		if not de.getExec():
			return None

		return {
			"Terminal": de.getTerminal(),
			"StartupNotify": de.getStartupNotify(),
			"Exec": self.gtk_to_unicode(de.getExec()),
			"Path": self.gtk_to_unicode(de.getPath()),
			"Icon": self.gtk_to_unicode(de.getIcon()),
			"Name": self.gtk_to_unicode(de.getName()),
			"Location" : desktop_file,
		}
