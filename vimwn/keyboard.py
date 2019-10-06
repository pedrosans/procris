import gi, threading
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


def parse_accelerator(accelerator_string, keymap=Gdk.Keymap.get_default()):
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
	mapped_the_same, non_virtual_counterpart = keymap.map_virtual_modifiers(a.accelerator_mods)
	mask = normalize_state(non_virtual_counterpart)
	return gdk_keyval, code, mask


class KeyboardListener:

	def __init__(self, callback=None, on_error=None):
		self.on_error = on_error
		self.callback = callback

		self.record_thread = threading.Thread(target=self.record, name='x keyboard listener thread')
		self.well_thread = threading.Thread(target=self.drop_hot_key, daemon=True, name='hotkey well thread')

		self.record_display = Display()
		self.record_display.set_error_handler(self.on_error)
		self.local_display = Display()
		self.local_display.set_error_handler(self.on_error)

		if not self.record_display.has_extension("RECORD"):
			raise Exception("RECORD extension not found")

		r = self.record_display.record_get_version(0, 0)
		print("RECORD extension version %d.%d" % (r.major_version, r.minor_version))
		self.context = self.record_display.record_create_context(0, [record.AllClients], CONTEXT_FILTER)

		self.mod_keys_set = set()
		for mods in self.local_display.get_modifier_mapping():
			for mod in mods:
				self.mod_keys_set.add(mod)

		self.root = self.local_display.screen().root
		self.root.change_attributes(event_mask=X.KeyPressMask | X.KeyReleaseMask)
		self.modifiers_count = self.modified_count = 0
		self.key_map = {}
		self.composed_key_map = {}
		self.composed_mapping_first_keys = set()
		self.composed_mapping_first_key = None
		self.multiplier = ''
		self.keymap = Gdk.Keymap.get_default()

	def grab_keys(self, code, mask):
		self.root.grab_key(code, mask, True, X.GrabModeAsync, X.GrabModeAsync)
		self.root.grab_key(code, mask | X.Mod2Mask, True, X.GrabModeAsync, X.GrabModeAsync)

	def bind(self, key):
		if len(key.accelerators) == 1:
			self.bind_single_accelerator(key)
		elif len(key.accelerators) == 2:
			self.bind_composed_accelerator(key)
		else:
			raise Exception('Cant bind the key')

	def bind_single_accelerator(self, key):
		gdk_keyval, code, mask = parse_accelerator(key.accelerators[0], self.keymap)

		self.grab_keys(code, mask)

		if gdk_keyval not in self.key_map:
			self.key_map[gdk_keyval] = {}

		self.key_map[gdk_keyval][mask] = key

	def bind_composed_accelerator(self, key):
		gdk_keyval, code, mask = parse_accelerator(key.accelerators[0], self.keymap)
		second_gdk_keyval, second_code, second_mask = parse_accelerator(key.accelerators[1], self.keymap)

		self.grab_keys(code, mask)

		if gdk_keyval not in self.composed_key_map:
			self.composed_key_map[gdk_keyval] = {}
		if mask not in self.composed_key_map[gdk_keyval]:
			self.composed_key_map[gdk_keyval][mask] = {}
		if second_gdk_keyval not in self.composed_key_map[gdk_keyval][mask]:
			self.composed_key_map[gdk_keyval][mask][second_gdk_keyval] = {}

		if second_mask in self.composed_key_map[gdk_keyval][mask][second_gdk_keyval]:
			raise Exception('key ({}) already mapped'.format(', '.join(key.accelerators)))

		self.composed_key_map[gdk_keyval][mask][second_gdk_keyval][second_mask] = key

	def handler(self, reply):
		data = reply.data
		while len(data):
			event, data = rq.EventField(None).parse_binary_value(
				data, self.record_display.display, None, None)

			_wasmapped, keyval, egroup, level, consumed = self.keymap.translate_keyboard_state(
				event.detail, Gdk.ModifierType(event.state), 0)

			if event.detail in self.mod_keys_set:
				self.modifiers_count += 1 if event.type == X.KeyPress else -1
				self.modified_count = 0
				continue

			if self.modifiers_count:
				self.modified_count += 1 if event.type == X.KeyPress else -1

			if event.type == X.KeyPress:
				self.handle_keypress(event)

	def handle_keypress(self, event):
		_wasmapped, keyval, egroup, level, consumed = self.keymap.translate_keyboard_state(
			event.detail, Gdk.ModifierType(event.state), 0)

		event.keyval = keyval
		mask = normalize_state(event.state) & ~consumed

		if self.composed_mapping_first_key:

			key_name = Gdk.keyval_name(event.keyval)
			if not mask and key_name and key_name.isdigit():
				self.multiplier = self.multiplier + key_name
				return

			second_key_map = self.composed_key_map[self.composed_mapping_first_key[0]][self.composed_mapping_first_key[1]]
			if keyval in second_key_map and mask in second_key_map[keyval]:
				multiplier_int = int(self.multiplier) if self.multiplier else 1
				self.callback(second_key_map[keyval][mask], event, multiplier=multiplier_int)

			self.composed_mapping_first_key = None

		elif self.modified_count == 1:

			if keyval in self.key_map and mask in self.key_map[keyval]:
				self.callback(self.key_map[keyval][mask], event)

			if keyval in self.composed_key_map and mask in self.composed_key_map[keyval]:
				self.composed_mapping_first_key = (keyval, mask)

		self.multiplier = ''

	def stop(self):
		self.local_display.record_disable_context(self.context)
		self.local_display.close()
		print('display stoped recording')
		self.record_thread.join()
		print('recording thread ended')

	def start(self):
		self.well_thread.start()
		self.record_thread.start()

	def drop_hot_key(self):
		while True:
			event = self.local_display.next_event()

	def record(self):
		self.record_display.record_enable_context(self.context, self.handler)
		self.record_display.record_free_context(self.context)
		self.record_display.close()


class Key:

	def __init__(self, accelerators, function, *parameters):
		self.accelerators = accelerators
		self.function = function
		self.parameters = parameters[0] if parameters else None