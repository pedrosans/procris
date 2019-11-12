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
		self.modifiers_count = self.modified_count = 0
		self.code_map = {}
		self.composed_code_map = {}
		self.composed_mapping_first_code = None
		self.multiplier = ''

	#
	# API
	#
	def bind(self, key):
		if self.stopped:
			return
		if len(key.accelerators) == 1:
			self._bind_single_accelerator(key)
		elif len(key.accelerators) == 2:
			self._bind_composed_accelerator(key)
		self.well_connection.sync()
		if self.stopped:
			print(
				'Unable to bind: {}'.format(', '.join(key.accelerators)),
				file=sys.stderr)

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
	# Thread targets
	#
	def _drop_key(self):
		while not self.stopped:
			self.well_connection.next_event()

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

	def _bind_single_accelerator(self, key):
		gdk_keyval, code, mask = parse_accelerator(key.accelerators[0])

		self._grab_keys(code, mask)

		if code not in self.code_map:
			self.code_map[code] = {}

		self.code_map[code][mask] = key

	def _bind_composed_accelerator(self, key):
		gdk_keyval, code, mask = parse_accelerator(key.accelerators[0])
		second_gdk_keyval, second_code, second_mask = parse_accelerator(key.accelerators[1])

		self._grab_keys(code, mask)

		if code not in self.composed_code_map:
			self.composed_code_map[code] = {}
		if mask not in self.composed_code_map[code]:
			self.composed_code_map[code][mask] = {}
		if second_code not in self.composed_code_map[code][mask]:
			self.composed_code_map[code][mask][second_code] = {}

		if second_mask in self.composed_code_map[code][mask][second_code]:
			raise Exception('key ({}) already mapped'.format(', '.join(key.accelerators)))

		self.composed_code_map[code][mask][second_code][second_mask] = key

	#
	# Event handling
	#
	def handler(self, reply):
		data = reply.data
		while len(data):
			event, data = rq.EventField(None).parse_binary_value(
				data, self.recording_connection.display, None, None)

			if event.detail in self.mod_keys_set:
				self.modifiers_count += 1 if event.type == X.KeyPress else -1
				self.modified_count = 0
				continue

			if self.modifiers_count:
				self.modified_count += 1 if event.type == X.KeyPress else -1

			if event.type == X.KeyPress:
				self.handle_keypress(event)

	def handle_keypress(self, event):
		_wasmapped, keyval, egroup, level, consumed = Gdk.Keymap.get_default().translate_keyboard_state(
			event.detail, Gdk.ModifierType(event.state), 0)

		code = event.detail
		event.keyval = keyval  # TODO: explain
		mask = normalize_state(event.state)

		if self.composed_mapping_first_code and self.composed_mapping_first_code != (code, mask):

			key_name = Gdk.keyval_name(event.keyval)
			if not mask and key_name and key_name.isdigit():
				self.multiplier = self.multiplier + key_name
				return

			second_code_map = self.composed_code_map[self.composed_mapping_first_code[0]][self.composed_mapping_first_code[1]]
			if code in second_code_map and mask in second_code_map[code]:
				multiplier_int = int(self.multiplier) if self.multiplier else 1
				self.callback(second_code_map[code][mask], event, multiplier=multiplier_int)

			self.composed_mapping_first_code = None

		elif self.modified_count == 1:

			if code in self.code_map and mask in self.code_map[code]:
				self.callback(self.code_map[code][mask], event)

			if code in self.composed_code_map and mask in self.composed_code_map[code]:
				self.composed_mapping_first_code = (code, mask)

		self.multiplier = ''


class Key:

	def __init__(self, accelerators, function, *parameters):
		self.accelerators = accelerators
		self.function = function
		self.parameters = parameters[0] if parameters else None