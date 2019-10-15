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
import os, glob, gi, sys
import xdg.DesktopEntry
import xdg.Exceptions
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Gio
from poco.message import Message

APPS_GLOB = [
		"/usr/share/applications/*.desktop",
		"/var/lib/snapd/desktop/applications/*.desktop",
		os.path.expanduser('~/.local/share/applications')+'/*.desktop']
NAME_MAP = {}
LOCATION_MAP = {}


def launch(c_in):
	name = c_in.vim_command_parameter

	if not name or not name.strip():
		return Message('Missing application name', 'error')

	app_name = None
	if has_perfect_match(name.strip()):
		app_name = name.strip()

	possible_apps = find_by_name(name)
	if possible_apps:
		app_name = possible_apps

	if app_name:
		try:
			launch_by_name(app_name)
		except GLib.GError as exc:
			return Message('Error launching ' + name, 'error')
	elif len(possible_apps) == 0:
		return Message('No matching application for ' + name, 'error')
	else:
		return Message('More than one application matches: ' + name, 'error')


def reload():
	NAME_MAP.clear()
	load()


def load():
	for app_files_glob in APPS_GLOB:
		for file_path in glob.glob(app_files_glob):
			try:
				desktop_entry = xdg.DesktopEntry.DesktopEntry(file_path)
				if not desktop_entry.getExec():
					continue
				name = desktop_entry.getName().strip()
				name = name.replace('\xad', '')
				NAME_MAP[name] = desktop_entry
				LOCATION_MAP[name] = file_path
			except (xdg.Exceptions.ParsingError, TypeError) as e:
				print('Cant read a DesktopEntry from: {} Error: {}'.format(file_path, e), file=sys.stderr)
				continue


def has_perfect_match(name):
	return name in NAME_MAP.keys()


def find_by_name(name_filter):
	striped = name_filter.lower().strip()
	for app_name in NAME_MAP.keys():
		if striped == app_name.strip().lower():
			return app_name;
	return None


def list_completions(name_filter):
	lower = name_filter.lower()
	matches = filter(lambda x: lower in x.lower(), NAME_MAP.keys())
	matches = filter(lambda x: lower != x.lower(), matches)
	return sorted(list(set(matches)), key=str.lower)


def launch_by_name( name):
	launcher = Gio.DesktopAppInfo.new_from_filename(LOCATION_MAP[name])
	launcher.launch_uris()

