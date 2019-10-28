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
layout_file = '/tmp/poco_layout.json'
decorations_file = '/tmp/poco_decoration.json'


def write(layout):
	with open(layout_file, 'w') as f:
		json.dump(to_json(layout), f, indent=True)


def write_decorations(decoration_map):
	state_json = {}
	for k in decoration_map.keys():
		state_json[k] = decoration_map[k]
	with open(decorations_file, 'w') as f:
		json.dump(state_json, f, indent=True)


def read_layout():
	if os.path.exists(layout_file):
		with open(layout_file, 'r') as f:
			return json.load(f)
	return None


def read_decorations():
	if os.path.exists(decorations_file):
		with open(decorations_file, 'r') as f:
			try:
				return json.load(f)
			except json.decoder.JSONDecodeError:
				return None
	return None


def to_json(layout):
	stack_state = {}
	state = {
		'stack_state': stack_state,
		'nmaster': layout.monitor.nmaster, 'mfact': layout.monitor.mfact,
		'function': layout.function_key}
	for w in layout.windows.buffers:
		w_id = w.get_xid()
		key = str(w_id)
		if key not in stack_state:
			stack_state[key] = {}
		stack_state[key]['name'] = w.get_name()
		stack_state[key]['stack_index'] = layout.stack.index(w_id) if w_id in layout.stack else -1

	for client_key in list(stack_state.keys()):
		if client_key not in map(lambda x: str(x.get_xid()), layout.windows.buffers):
			del stack_state[client_key]

	return state
