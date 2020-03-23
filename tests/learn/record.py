import warnings

import Xlib
import gi, threading, sys
from Xlib import X
from Xlib.ext import record
from Xlib.display import Display
from Xlib.protocol import rq

from procris.keyboard import normalize_state, format_key_event

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GObject, GLib

CONTEXT_FILTER = [{
		'core_requests': (0, 0), 'core_replies': (0, 0),
		'ext_requests': (0, 0, 0, 0), 'ext_replies': (0, 0, 0, 0),
		'delivered_events': (0, 0),
		'device_events': (X.KeyPress, X.KeyRelease),
		'errors': (0, 0),
		'client_started': False, 'client_died': False,
	}]


class Record:

	def __init__(self):

		self.record_thread = threading.Thread(target=self._record, name='x keyboard listener thread')

		self.recording_connection = Display()
		self.recording_connection.set_error_handler(self._record_display_error_handler)

		if not self.recording_connection.has_extension("RECORD"):
			raise Exception("RECORD extension not found")

		r = self.recording_connection.record_get_version(0, 0)
		print("RECORD extension version %d.%d" % (r.major_version, r.minor_version))
		self.context = self.recording_connection.record_create_context(0, [record.AllClients], CONTEXT_FILTER)

		self.mod_keys_set = set()

	def start(self):
		self.recording_connection.sync()
		self.record_thread.start()

	def stop(self):
		if self.record_thread.is_alive():
			# self.well_connection.record_disable_context(self.context)
			# self.well_connection.close()
			self.recording_connection.record_disable_context(self.context)
			self.recording_connection.close()
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

	def _local_display_error_handler(self, exception, *args):
		print('Error at local display: {}'.format(exception), file=sys.stderr)

	#
	# Event handling
	#
	def handler(self, reply):
		data = reply.data
		while len(data):
			event, data = rq.EventField(None).parse_binary_value(
				data, self.recording_connection.display, None, None)

			if event.detail in self.mod_keys_set:
				continue

			if event.type == X.KeyPress:
				self.handle_keypress(event)

	# http://python-xlib.sourceforge.net/doc/html/python-xlib_13.html
	def handle_keypress(self, event: Xlib.protocol.event.KeyPress):
		format_key_event(event)

warnings.filterwarnings("ignore", category=DeprecationWarning)
listener = Record()
listener.start()
print('ENTER TO STOP THE READING')
sys.stdin.read(1)
listener.stop()
