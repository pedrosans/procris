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


def run_inside_x_main_loop(callback, x_key_event):
	GLib.idle_add(callback, x_key_event, priority=GLib.PRIORITY_HIGH);
	return False


class KeyboardListener:

	def __init__(self, unmapped_callback=None, on_error=None):
		self.on_error = on_error
		self.unmapped_callback = unmapped_callback

		self.record_thread = threading.Thread(target=self.record, name='x keyboard listener thread')
		self.well_thread = threading.Thread(target=self.drop_hot_key, daemon=True, name='hotkey well thread')

		self.record_display = Display()
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
		self.callback_map = {}

	def bind(self, accelerator_string, callback):
		a = Gtk.accelerator_parse_with_keycode(accelerator_string)

		if not a.accelerator_codes:
			raise Exception('Can not parse the accelerator string')
		if len(a.accelerator_codes) > 1:
			# https://mail.gnome.org/archives/gtk-devel-list/2000-December/msg00034.html
			raise Exception('Support to keycodes with multiple keyvalues not implemented')

		accelerator_code = a.accelerator_codes[0]
		mapped_the_same, non_virtual_counterpart = Gdk.Keymap.get_default().map_virtual_modifiers(a.accelerator_mods)
		accelerator_mask = normalize_state(non_virtual_counterpart)

		self.root.grab_key(accelerator_code, accelerator_mask, True, X.GrabModeAsync, X.GrabModeAsync)
		self.root.grab_key(accelerator_code, accelerator_mask | X.Mod2Mask, True, X.GrabModeAsync, X.GrabModeAsync)
		if accelerator_code not in self.callback_map:
			self.callback_map[accelerator_code] = {}

		self.callback_map[accelerator_code][accelerator_mask] = callback

	def handler(self, reply):
		data = reply.data
		while len(data):
			event, data = rq.EventField(None).parse_binary_value(data, self.record_display.display, None, None)
			if event.type == X.KeyPress and event.detail not in self.mod_keys_set:
				event.keyval = self.local_display.keycode_to_keysym(event.detail, event.state & Gdk.ModifierType.SHIFT_MASK)
				normalized_state = normalize_state(event.state)
				callback = None
				if event.detail in self.callback_map and normalized_state in self.callback_map[event.detail]:
					callback = self.callback_map[event.detail][normalized_state]
				else:
					callback = self.unmapped_callback
				run_inside_x_main_loop(callback, event)

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

