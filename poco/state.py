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
import os, json
import poco.configurations as configurations

layout_file = configurations.get_cache_dir() + '/layout.json'
decorations_file = configurations.get_cache_dir() + '/decoration.json'


def write_layout(layout):
	with open(layout_file, 'w') as f:
		json.dump(layout, f, indent=True)


def read_layout():
	return _read_json(layout_file)


def write_decorations(decoration_map):
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

