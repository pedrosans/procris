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
CONTEXT_FILTER = [{
		'core_requests': (0, 0), 'core_replies': (0, 0),
		'ext_requests': (0, 0, 0, 0), 'ext_replies': (0, 0, 0, 0),
		'delivered_events': (0, 0),
		'device_events': (X.KeyPress, X.KeyRelease),
		'errors': (0, 0),
		'client_started': False, 'client_died': False,
	}]


def normalize_state(state):
	normalized = 0
	for mod in MODIFIERS:
		normalized += int(state & mod)
	return normalized


def parse_accelerator(accelerator_string):
	a = Gtk.accelerator_parse_with_keycode(accelerator_string)

	if not a.accelerator_codes:
		raise Exception('Can not parse the accelerator string')
	if len(a.accelerator_codes) > 1:
		# https://mail.gnome.org/archives/gtk-devel-list/2000-December/msg00034.html
		raise Exception('Support to keycodes with multiple keyvalues not implemented')

	gdk_keyval = a.accelerator_key
	if Gdk.keyval_to_upper(gdk_keyval) != Gdk.keyval_to_lower(gdk_keyval):
		gdk_keyval = Gdk.keyval_from_name(accelerator_string[-1])
	code = a.accelerator_codes[0]
	mapped_the_same, non_virtual_counterpart = Gdk.Keymap.get_default().map_virtual_modifiers(a.accelerator_mods)
	mask = normalize_state(non_virtual_counterpart)
	return gdk_keyval, code, mask


class KeyboardListener:

	def __init__(self, callback=None, on_error=None):
		self.on_error = on_error
		self.callback = callback
		# XLib errors are received asynchronously, thus the need for a running state flag
		self.stopped = False

		self.record_thread = threading.Thread(target=self._record, name='x keyboard listener thread')
		self.well_thread = threading.Thread(target=self._drop_key, daemon=True, name='hotkey well thread')

		self.recording_connection = Display()
		self.well_connection = Display()
		self.recording_connection.set_error_handler(self._record_display_error_handler)
		self.well_connection.set_error_handler(self._local_display_error_handler)

		if not self.recording_connection.has_extension("RECORD"):
			raise Exception("RECORD extension not found")

		r = self.recording_connection.record_get_version(0, 0)
		print("RECORD extension version %d.%d" % (r.major_version, r.minor_version))
		self.context = self.recording_connection.record_create_context(0, [record.AllClients], CONTEXT_FILTER)

		self.mod_keys_set = set()
		for mods in self.well_connection.get_modifier_mapping():
			for mod in mods:
				self.mod_keys_set.add(mod)

		self.root = self.well_connection.screen().root
		self.root.change_attributes(event_mask=X.KeyPressMask | X.KeyReleaseMask)
		self.contextual_accelerators = self.accelerators_root = {}
		self.accelerators_root['level'] = 0
		self.multiplier = ''

	#
	# API
	#
	def bind(self, key):
		if self.stopped:
			return

		last_node = self.accelerators_root

		for accelerator_string in key.accelerators:
			gdk_key_val, code, mask = parse_accelerator(accelerator_string)
			last_node['has_children'] = True

			if (code, mask) not in last_node:
				last_node[(code, mask)] = {}
				last_node[(code, mask)]['has_children'] = False

			child = last_node[(code, mask)]
			child['level'] = last_node['level'] + 1
			if child['level'] == 1:
				self._grab_keys(code, mask)
			last_node = child

		if 'key' in last_node:
			raise Exception('key ({}) already mapped'.format(', '.join(key.accelerators)))

		last_node['key'] = key

		self.well_connection.sync()

		if self.stopped:
			print('Unable to bind: {}'.format(', '.join(key.accelerators)), file=sys.stderr)

	def start(self):
		self.well_connection.sync()
		self.recording_connection.sync()
		if self.stopped:
			return
		self.well_thread.start()
		self.record_thread.start()

	def stop(self):
		self.stopped = True
		if self.record_thread.is_alive():
			self.well_connection.record_disable_context(self.context)
			self.well_connection.close()
			print('display stopped recording')
			self.record_thread.join()
		print('recording thread ended')

	#
	# xlib plugs
	#
	def _record(self):
		self.recording_connection.record_enable_context(self.context, self.handler)
		self.recording_connection.record_free_context(self.context)
		self.recording_connection.close()

	def _record_display_error_handler(self, exception, *args):
		print('Error at record display: {}'.format(exception), file=sys.stderr)
		if not self.stopped:
			self.stopped = True
			self.on_error()

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

	#
	# Event handling
	#
	def _drop_key(self):
		while not self.stopped:
			self.well_connection.next_event()

	def handler(self, reply):
		data = reply.data
		while len(data):
			event, data = rq.EventField(None).parse_binary_value(
				data, self.recording_connection.display, None, None)

			if event.detail in self.mod_keys_set:
				continue

			if event.type == X.KeyPress:
				self.handle_keypress(event)

	def handle_keypress(self, event):
		_wasmapped, keyval, egroup, level, consumed = Gdk.Keymap.get_default().translate_keyboard_state(
			event.detail, Gdk.ModifierType(event.state), 0)

		code = event.detail
		event.keyval = keyval  # TODO: explain
		mask = normalize_state(event.state)
		key_name = Gdk.keyval_name(event.keyval)

		if key_name and key_name.isdigit() and self.contextual_accelerators['level'] == 1:
			self.multiplier = self.multiplier + key_name
			return

		if (code, mask) not in self.contextual_accelerators:
			self.reset_key_streak()

		if (code, mask) in self.contextual_accelerators:
			multiplier_int = int(self.multiplier) if self.multiplier else 1
			self.callback(self.contextual_accelerators[(code, mask)]['key'], event, multiplier=multiplier_int)
			if self.contextual_accelerators[(code, mask)]['has_children']:
				self.contextual_accelerators = self.contextual_accelerators[(code, mask)]
			else:
				self.reset_key_streak()

	def reset_key_streak(self):
		self.contextual_accelerators = self.accelerators_root
		self.multiplier = ''


class Key:

	def __init__(self, accelerators, function, *parameters):
		self.accelerators = accelerators
		self.function = function
		self.parameters = parameters[0] if parameters else None