"""
Copyright 2017 Pedro Santos <pedrosans@gmail.com>

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

import os, gi, dbus, dbus.service, signal, setproctitle, logging
gi.require_version('Gtk', '3.0')
from vimwn.reading import Reading
from gi.repository import GObject, Gtk, GLib
from dbus.mainloop.glib import DBusGMainLoop
from dbus.gi_service import ExportedGObject
from vimwn.status import StatusIcon
from vimwn.keyboard import KeyboardListener

SERVICE_NAME = "io.github.vimwn"
SERVICE_OBJECT_PATH = "/io/github/vimwn"
SIGINT  = getattr(signal, "SIGINT", None)
SIGTERM = getattr(signal, "SIGTERM", None)
SIGHUP  = getattr(signal, "SIGHUP", None)


class NavigatorService:

	def __init__(self):
		self.bus_object = None
		self.reading = None
		self.status_icon = None
		self.listener = None
		# https://lazka.github.io/pgi-docs/GLib-2.0/functions.html#GLib.log_set_handler
		GLib.log_set_handler(None, GLib.LogLevelFlags.LEVEL_WARNING, self.log_function)
		GLib.log_set_handler(None, GLib.LogLevelFlags.LEVEL_ERROR, self.log_function)
		GLib.log_set_handler(None, GLib.LogLevelFlags.LEVEL_CRITICAL, self.log_function)

	def start(self):
		GObject.threads_init()

		self.reading = Reading(service=self)

		configurations = self.reading.configurations
		normal_prefix = configurations.get_prefix_key()

		self.listener = KeyboardListener(normal_prefix, callback=self.handle_key_press)
		self.listener.start()
		print("Listening keys: '{}', pid: {} ".format(normal_prefix, os.getpid()))

		self.configure_process()

		self.status_icon = StatusIcon(configurations)
		self.status_icon.activate(self)

		self.export_bus_object()
		Gtk.main()

		print("Ending vimwn service, pid: {}".format(os.getpid()))

	def reload(self):
		self.status_icon.reload()

	def handle_key_press(self, xlib_key_event):
		GLib.idle_add(self.forward_to_main_loop, xlib_key_event, priority=GLib.PRIORITY_HIGH);

	def forward_to_main_loop(self, xlib_key_event):
		if xlib_key_event.hot_key:
			self.reading.start(xlib_key_event.time)
		else:
			self.reading.on_window_key(xlib_key_event)
		return False  # so GLib stops calling this callback

	def log_function(self, log_domain, log_level, message):
		if log_level is GLib.LogLevelFlags.LEVEL_WARNING:
			logging.warning('GLib log[%s]:%s',log_domain, message)
			self.reading.view.show_warning(message)
		elif log_level in (GLib.LogLevelFlags.LEVEL_ERROR, GLib.LogLevelFlags.LEVEL_CRITICAL):
			logging.error('GLib log[%s]:%s',log_domain, message)
			self.reading.view.show_error(message)
		else:
			raise Exception(message)

	def configure_process(self):
		setproctitle.setproctitle("vimwn")
		for sig in (SIGINT, SIGTERM, SIGHUP):
			self.install_glib_handler(sig)

	def install_glib_handler(self, sig):
		unix_signal_add = None

		if hasattr(GLib, "unix_signal_add"):
			unix_signal_add = GLib.unix_signal_add
		elif hasattr(GLib, "unix_signal_add_full"):
			unix_signal_add = GLib.unix_signal_add_full

		if unix_signal_add:
			unix_signal_add(GLib.PRIORITY_HIGH, sig, self.unix_signal_handler, sig)
		else:
			print("Can't install GLib signal handler, too old gi.")

	def unix_signal_handler(self, *args):
		signal = args[0]
		if signal in (1, SIGHUP, 2, SIGINT, 15, SIGTERM):
			self.stop()

	def export_bus_object(self):
		self.bus_object = NavigatorBusService(self)

	def release_bus_object(self):
		self.bus_object.release()
		self.bus_object = None

	def stop(self):
		Gtk.main_quit()
		self.listener.stop()
		self.release_bus_object()


class NavigatorBusService (ExportedGObject):

	def __init__(self, service):
		self.service = service
		self.main_loop = DBusGMainLoop(set_as_default=True)
		dbus.mainloop.glib.threads_init()
		self.bus = dbus.Bus()

		if not self.bus:
			print("no session")
			quit()

		if self.bus.name_has_owner(SERVICE_NAME):
			pid = RemoteInterface().get_running_instance_id()
			print("vimwn is already running, pid: " + pid)
			quit()

		bus_name = dbus.service.BusName(SERVICE_NAME, self.bus)
		super(NavigatorBusService, self).__init__(conn=self.bus, object_path=SERVICE_OBJECT_PATH, bus_name=bus_name)

	@dbus.service.method("io.github.vimwn.Service", in_signature='', out_signature='s')
	def get_id(self):
		return str(os.getpid())

	@dbus.service.method("io.github.vimwn.Service", in_signature='', out_signature='')
	def stop_vimwn(self):
		self.service.stop()

	def release(self):
		self.bus.release_name(SERVICE_NAME)
		print('vimwn service were released from bus')

class RemoteInterface():

	def __init__(self):
		self.bus = dbus.Bus()
		if not self.bus:
			print("no session")
			quit()

	def get_status(self):
		if self.bus.name_has_owner(SERVICE_NAME):
			return "Active, pid: " + self.get_running_instance_id()
		else:
			return "Inactive"

	def get_running_instance_id(self):
		service = self.bus.get_object(SERVICE_NAME, SERVICE_OBJECT_PATH)
		get_remote_id = service.get_dbus_method('get_id', 'io.github.vimwn.Service')
		return get_remote_id()

	def stop_running_instance(self):
		if self.bus.name_has_owner(SERVICE_NAME):
			service = self.bus.get_object(SERVICE_NAME, SERVICE_OBJECT_PATH)
			quit_function = service.get_dbus_method('stop_vimwn', 'io.github.vimwn.Service')
			quit_function()
			print("Remote instance were stopped")
		else:
			print("vimwn is not running")
