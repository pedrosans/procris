from typing import List

import Xlib
import gi, threading, sys
from Xlib import X
from Xlib.ext import record
from Xlib.display import Display
from Xlib.protocol import rq
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GObject, GLib

MODIFIERS = [Gdk.ModifierType.CONTROL_MASK, Gdk.ModifierType.SHIFT_MASK,
			Gdk.ModifierType.MOD1_MASK, Gdk.ModifierType.MOD4_MASK]


def normalize_state(state):
	normalized = 0
	for mod in MODIFIERS:
		normalized += int(state & mod)
	return normalized


def parse_accelerator(accelerator_string):
	a = Gtk.accelerator_parse_with_keycode(accelerator_string)

	if not a.accelerator_codes:
		raise Exception('Can not parse the accelerator string {}'.format(accelerator_string))
	if len(a.accelerator_codes) > 1:
		# https://mail.gnome.org/archives/gtk-devel-list/2000-December/msg00034.html
		raise Exception('Support to keycodes with multiple keyvalues not implemented')

	gdk_keyval = a.accelerator_key
	if Gdk.keyval_to_upper(gdk_keyval) != Gdk.keyval_to_lower(gdk_keyval):
		gdk_keyval = Gdk.keyval_from_name(accelerator_string[-1])
	code = a.accelerator_codes[0]
	mapped_the_same, non_virtual_counterpart = Gdk.Keymap.get_for_display(Gdk.Display.get_default()).map_virtual_modifiers(a.accelerator_mods)
	mask = normalize_state(non_virtual_counterpart)
	return gdk_keyval, code, mask


# http://python-xlib.sourceforge.net/doc/html/python-xlib_13.html
def format_key_event(event: Xlib.protocol.event.KeyPress):
	def clean_mask(mask: str):
		return mask.replace('GDK_', '').replace('_MASK', '').replace('<flags ', '').replace(
			' of type Gdk.ModifierType>', '')

	print('\nX:')
	print('\tcode: {}'.format(event.detail))
	print('\tmask: {} named: {}'.format(event.state, clean_mask(str(Gdk.ModifierType(event.state)))))
	print('pwm:')

	normalized_mask = normalize_state(event.state)
	print('\tnormalized mask: {} named: {}'.format(
		normalized_mask,
		clean_mask(str(Gdk.ModifierType(normalized_mask)))
	))

	_wasmapped, keyval, egroup, level, consumed = Gdk.Keymap.get_default().translate_keyboard_state(
		event.detail, Gdk.ModifierType(event.state), 0)

	print('GDK:')
	print('\tname: {}'.format(Gdk.keyval_name(keyval)))
	print('\twasmapped: {}'.format(_wasmapped))
	print('\tkeyval: {}'.format(keyval))
	print('\tegroup: {}'.format(egroup))
	print('\tlevel: {}'.format(level))
	print('\tconsumed: {}'.format(clean_mask(str(consumed))))


class Key:

	def __init__(self, accelerator, function, parameters=[], combinations=[]):
		self.accelerator = accelerator
		self.function = function
		self.parameters = parameters
		self.combinations = combinations


class KeyboardListener:

	def __init__(self, callback=None, on_error=None):
		self.keys = []
		self.grabbed: List = []
		self.temporary_grab: List = []
		self.on_error = on_error
		self.callback = callback
		# XLib errors are received asynchronously, thus the need for a running state flag
		self.stopped = False

		self.well_thread = threading.Thread(target=self.x_client_loop, daemon=True, name='hotkey well thread')
		self.well_connection = Display()
		self.well_connection.set_error_handler(self._local_display_error_handler)

		self.mod_keys_set = set()
		for mods in self.well_connection.get_modifier_mapping():
			for mod in mods:
				self.mod_keys_set.add(mod)

		self.root: Xlib.display.Window = self.well_connection.screen().root
		self.root.change_attributes(event_mask=X.KeyPressMask | X.KeyReleaseMask)

		self.accelerators_root = {'level': 0, 'children': []}
		self.contextual_accelerators = self.accelerators_root

	#
	# API
	#
	def add(self, key):
		self.keys.append(key)

	def start(self):
		for key in self.keys:
			self._bind_to_root(key)
		self.well_thread.start()

	def _bind_to_root(self, key):
		self._bind(key, self.accelerators_root)

	def _bind(self, key: Key, node):
		gdk_key_val, code, mask = parse_accelerator(key.accelerator)
		node['has_children'] = True

		if (code, mask) in node:
			raise Exception('key ({}) already mapped'.format(', '.join(key.accelerator)))

		we = {'code': code, 'mask': mask, 'has_children': False, 'children': [], 'level': node['level'] + 1, 'key': key}
		node[(code, mask)] = we
		node['children'].append(we)

		if we['level'] == 1:
			self._grab_keys(code, mask)
			self.well_connection.sync()
			if self.stopped:
				raise Exception('Unable to bind: {}'.format(', '.join(key.accelerator)))

		for combination in key.combinations:
			self._bind(combination, we)

	def stop(self):
		self.stopped = True
		self.well_connection.close()

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
		self.root.grab_key(code, mask, True, X.GrabModeAsync, X.GrabModeAsync)
		self.root.grab_key(code, mask | X.Mod2Mask, True, X.GrabModeAsync, X.GrabModeAsync)
		self.root.grab_key(code, mask | X.LockMask, True, X.GrabModeAsync, X.GrabModeAsync)
		self.root.grab_key(code, mask | X.Mod2Mask | X.LockMask, True, X.GrabModeAsync, X.GrabModeAsync)
		self.grabbed.append((code, mask))

	def _ungrab_keys(self, code, mask):
		self.root.ungrab_key(code, mask)
		self.root.ungrab_key(code, mask | X.Mod2Mask)
		self.root.ungrab_key(code, mask | X.LockMask)
		self.root.ungrab_key(code, mask | X.Mod2Mask | X.LockMask)
		self.grabbed.remove((code, mask))

	#
	# Event handling
	#
	def x_client_loop(self):
		while not self.stopped:
			event = self.well_connection.next_event()

			if event.type == X.KeyPress and event.detail not in self.mod_keys_set:
				self.handle_keypress(event)

	# http://python-xlib.sourceforge.net/doc/html/python-xlib_13.html
	def handle_keypress(self, event: Xlib.protocol.event.KeyPress):
		_wasmapped, keyval, egroup, level, consumed = Gdk.Keymap.get_default().translate_keyboard_state(
			event.detail, Gdk.ModifierType(event.state), 0)

		code = event.detail
		mask = normalize_state(event.state)
		event.keyval = keyval
		event.keymod = Gdk.ModifierType(mask)  # TODO: explain
		key_name = Gdk.keyval_name(event.keyval)
		# print('key: {} wid: {} root_x: {} event_x: {}'.format(key_name, event.window.id, event.root_x, event.event_x))

		if (code, mask) not in self.contextual_accelerators:
			self.reset_key_streak(event.time)

		if (code, mask) in self.contextual_accelerators:

			self.callback(self.contextual_accelerators[(code, mask)]['key'], event)

			if self.contextual_accelerators[(code, mask)]['has_children']:
				self.contextual_accelerators = self.contextual_accelerators[(code, mask)]
				self.root.grab_keyboard(True, X.GrabModeAsync, X.GrabModeAsync, event.time)
				self.temporary_grab = True
			else:
				self.reset_key_streak(event.time)

	def reset_key_streak(self, time):
		self.contextual_accelerators = self.accelerators_root
		if self.temporary_grab:
			self.well_connection.ungrab_keyboard(time)
			self.temporary_grab = False
		# for code, mask in self.temporary_grab: self._ungrab_keys(code, mask)
