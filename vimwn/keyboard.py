import gi, threading
from Xlib import X
from Xlib.ext import record
from Xlib.display import Display
from Xlib.protocol import rq
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GObject

MODIFIERS = [Gdk.ModifierType.CONTROL_MASK, Gdk.ModifierType.SHIFT_MASK,
			Gdk.ModifierType.MOD2_MASK, Gdk.ModifierType.MOD3_MASK, Gdk.ModifierType.MOD4_MASK,
			Gdk.ModifierType.MOD5_MASK]
CONTEXT_FILTER = [{
		'core_requests': (0, 0), 'core_replies': (0, 0),
		'ext_requests': (0, 0, 0, 0), 'ext_replies': (0, 0, 0, 0),
		'delivered_events': (0, 0),
		'device_events': (X.KeyPress, X.KeyRelease),
		'errors': (0, 0),
		'client_started': False, 'client_died': False,
	}]


class KeyboardListener:

	def __init__(self, hotkey, callback=None, on_error=None):
		self.callback = callback
		self.on_error = on_error

		self.record_thread = threading.Thread(target=self.record, name='x keyboard listener thread')
		self.well_thread = threading.Thread(target=self.drop_hot_key, daemon=True, name='hotkey well thread')

		self.record_display = Display()
		self.local_display = Display()
		self.local_display.set_error_handler(self.on_error)

		a = Gtk.accelerator_parse_with_keycode(hotkey)

		if not a.accelerator_codes:
			raise Exception('Can not parse the accelerator string')
		if len(a.accelerator_codes) > 1:
			# https://mail.gnome.org/archives/gtk-devel-list/2000-December/msg00034.html
			raise Exception('Support to keycodes with multiple keyvalues not implemented')

		self.accelerator_key = a.accelerator_key
		self.accelerator_code = a.accelerator_codes[0]
		self.accelerator_mask = 0

		mapped_the_same, non_virtual_counterpart = Gdk.Keymap.get_default().map_virtual_modifiers(a.accelerator_mods)
		for mod in MODIFIERS:
			self.accelerator_mask += int(non_virtual_counterpart & mod)

		if not self.record_display.has_extension("RECORD"):
			raise Exception("RECORD extension not found")

		r = self.record_display.record_get_version(0, 0)
		print("RECORD extension version %d.%d" % (r.major_version, r.minor_version))
		self.context = self.record_display.record_create_context(0, [record.AllClients], CONTEXT_FILTER)

		self.mod_keys_set = set()
		for mods in self.local_display.get_modifier_mapping():
			for mod in mods:
				self.mod_keys_set.add(mod)

		root = self.local_display.screen().root
		root.change_attributes(event_mask=X.KeyPressMask | X.KeyReleaseMask)
		root.grab_key(self.accelerator_code, self.accelerator_mask, True, X.GrabModeAsync, X.GrabModeAsync)

	def handler(self, reply):
		data = reply.data
		while len(data):
			event, data = rq.EventField(None).parse_binary_value(data, self.record_display.display, None, None)
			if event.type == X.KeyPress and event.detail not in self.mod_keys_set:
				event.keyval = self.local_display.keycode_to_keysym(event.detail, event.state & Gdk.ModifierType.SHIFT_MASK)
				event.hot_key = (event.detail == self.accelerator_code
									and event.state & self.accelerator_mask == self.accelerator_mask)
				self.callback(event)

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
		while self.local_display:
			event = self.local_display.next_event()

	def record(self):
		self.record_display.record_enable_context(self.context, self.handler)
		self.record_display.record_free_context(self.context)
		self.record_display.close()

