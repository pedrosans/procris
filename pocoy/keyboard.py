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
import threading, sys, Xlib
from Xlib import X
from Xlib.display import Display
from Xlib.protocol import rq
from gi.repository import Gtk, Gdk
from typing import List, Dict, Tuple


class Key:

	def __init__(self, accelerator=None, code=None, mask=None, function=None, parameters=[], combinations=[]):

		if (code is not None or mask is not None) and accelerator is not None:
			raise Exception('A Key must be defined by an accelerator or by a code+mask pair.')

		self.accelerator = accelerator
		self.code = code
		self.mask = mask

		if accelerator:
			self.parse_accelerator(accelerator)
		elif code is None or mask is None:
			raise Exception('No key was defined')

		self.id = (self.code, self.mask)
		self.function = function
		self.parameters = parameters
		self.combinations = combinations

	def parse_accelerator(self, accelerator_string):
		a = Gtk.accelerator_parse_with_keycode(accelerator_string)

		if not a.accelerator_codes:
			raise Exception('Can not parse the accelerator string {}'.format(accelerator_string))
		if len(a.accelerator_codes) > 1:
			# https://mail.gnome.org/archives/gtk-devel-list/2000-December/msg00034.html
			raise Exception('Support to keycodes with multiple keyvalues not implemented')

		self.code = a.accelerator_codes[0]
		mapped_the_same, non_virtual_counterpart = keymap.map_virtual_modifiers(a.accelerator_mods)
		self.mask = normalize_mask(non_virtual_counterpart)


class Context:

	def __init__(self, level=None, key=None):
		self.level = level
		self.key = key
		self.children: Dict[Tuple, Context] = {}

	def add(self, child):
		self.children[child.key.id] = child
		child.level = self.level + 1


class KeyboardListener:

	def __init__(self, callback=None, on_error=None):
		self.keys = []
		self.temporary_grab: List = []
		self.on_error = on_error
		self.callback = callback
		self.stopped = False

		self.thread = threading.Thread(target=self.x_client_loop, daemon=True, name='key listener thread')
		self.connection = Display()
		self.connection.set_error_handler(self._local_display_error_handler)

		self.mod_keys_set = set()
		for mods in self.connection.get_modifier_mapping():
			for mod in mods:
				self.mod_keys_set.add(mod)

		self.root: Xlib.display.Window = self.connection.screen().root
		self.root.change_attributes(event_mask=X.KeyPressMask | X.KeyReleaseMask)

		self.root_context: Context = Context(level=0)
		self.context: Context = self.root_context

	#
	# API
	#
	def add(self, key):
		self.keys.append(key)

	def start(self):
		for key in self.keys:
			self._bind_to_root(key)
		self.thread.start()

	def _bind_to_root(self, key):
		self._bind(key, self.root_context)

	def _bind(self, key: Key, node: Context):

		if key.id in node.children:
			raise Exception('key ({}) already mapped'.format(', '.join(key.accelerator)))

		key_context = Context(key=key)
		node.add(key_context)

		if key_context.level == 1:
			self._grab_keys(key.code, key.mask)
			self.connection.sync()
			if self.stopped:
				raise Exception('Unable to bind: {}'.format(', '.join(key.accelerator)))

		for combination in key.combinations:
			self._bind(combination, key_context)

	def stop(self):
		self.stopped = True
		self.connection.close()

	#
	# xlib plugs
	#
	def _local_display_error_handler(self, exception, *args):
		print('Error at local display: {}'.format(exception), file=sys.stderr)
		if not self.stopped:
			self.stopped = True
			self.on_error()

	#
	# Internal API
	#
	def _grab_keys(self, code, mask):
		self.root.grab_key(code, mask,                           True, X.GrabModeAsync, X.GrabModeAsync)

		self.root.grab_key(code, mask | X.Mod2Mask,              True, X.GrabModeAsync, X.GrabModeAsync)
		self.root.grab_key(code, mask | X.Mod3Mask,              True, X.GrabModeAsync, X.GrabModeAsync)
		self.root.grab_key(code, mask | X.LockMask,              True, X.GrabModeAsync, X.GrabModeAsync)

		self.root.grab_key(code, mask | X.Mod2Mask | X.LockMask, True, X.GrabModeAsync, X.GrabModeAsync)
		self.root.grab_key(code, mask | X.Mod2Mask | X.Mod3Mask, True, X.GrabModeAsync, X.GrabModeAsync)
		self.root.grab_key(code, mask | X.Mod3Mask | X.LockMask, True, X.GrabModeAsync, X.GrabModeAsync)

		self.root.grab_key(code, mask | X.Mod2Mask | X.Mod3Mask | X.LockMask, True, X.GrabModeAsync, X.GrabModeAsync)

	#
	# Event handling
	#
	def x_client_loop(self):
		while not self.stopped:
			event = self.connection.next_event()

			if event.type == X.KeyPress and event.detail not in self.mod_keys_set:
				self.handle_keypress(event)

	# http://python-xlib.sourceforge.net/doc/html/python-xlib_13.html
	# key_name = Gdk.keyval_name(event.keyval)
	# print('key: {} wid: {} root_x: {} event_x: {}'.format(key_name, event.window.id, event.root_x, event.event_x))
	def handle_keypress(self, e: Xlib.protocol.event.KeyPress):
		mask = normalize_mask(e.state)
		code = e.detail
		key_id = (code, mask)

		if key_id in self.context.children:
			gdk_mask = Gdk.ModifierType(mask)
			_wasmapped, keyval, egroup, level, consumed = keymap.translate_keyboard_state(e.detail, gdk_mask, 0)
			e.keyval = keyval
			e.keymod = gdk_mask
			self.callback(self.context.children[key_id].key, e)

		if key_id in self.context.children and self.context.children[key_id].children:
			self.advance_key_streak(key_id, e.time)
		else:
			self.reset_key_streak(e.time)

	def advance_key_streak(self, key_id: Tuple, time):
		self.context = self.context.children[key_id]
		self.root.grab_keyboard(True, X.GrabModeAsync, X.GrabModeAsync, time)
		self.temporary_grab = True

	def reset_key_streak(self, time):
		self.context = self.root_context
		if self.temporary_grab:
			self.connection.ungrab_keyboard(time)
			self.temporary_grab = False


def normalize_mask(state) -> int:
	normalized = 0
	for mod in MODIFIERS:
		normalized += int(state & mod)
	return normalized


MODIFIERS = [
	Gdk.ModifierType.CONTROL_MASK, Gdk.ModifierType.SHIFT_MASK,
	Gdk.ModifierType.MOD1_MASK, Gdk.ModifierType.MOD4_MASK]

keymap: Gdk.Keymap = Gdk.Keymap.get_default()
