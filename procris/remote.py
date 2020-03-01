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
import os, dbus, dbus.service
from typing import Callable

from dbus.mainloop.glib import DBusGMainLoop
from dbus.gi_service import ExportedGObject

SERVICE_NAME = "io.github.procris"
SERVICE_OBJECT_PATH = "/io/github/procris"


# TODO: remove subclass
class BusObject (ExportedGObject):

	def __init__(self, ipc_handler: Callable = None, stop: Callable = None):
		self.ipc_handler = ipc_handler
		self.stop = stop
		self.main_loop = DBusGMainLoop(set_as_default=True)
		dbus.mainloop.glib.threads_init()
		self.bus = dbus.Bus()

		if not self.bus:
			print("no session")
			quit()

		if self.bus.name_has_owner(SERVICE_NAME):
			pid = RemoteInterface().get_running_instance_id()
			print("procris is already running, pid: " + pid)
			quit()

		bus_name = dbus.service.BusName(SERVICE_NAME, self.bus)
		super(BusObject, self).__init__(conn=self.bus, object_path=SERVICE_OBJECT_PATH, bus_name=bus_name)

	@dbus.service.method("io.github.procris.Service", in_signature='', out_signature='s')
	def get_id(self):
		return str(os.getpid())

	@dbus.service.method("io.github.procris.Service", in_signature='s', out_signature='')
	def message(self, ipc_message):
		self.ipc_handler(ipc_message)

	@dbus.service.method("io.github.procris.Service", in_signature='', out_signature='')
	def stop(self):
		self.stop()

	def release(self):
		self.bus.release_name(SERVICE_NAME)
		print('procris service were released from bus')


class RemoteInterface:

	def __init__(self):
		self.bus = dbus.Bus()
		if not self.bus:
			print("no session")
			quit()
		self.service = None
		if self.bus.name_has_owner(SERVICE_NAME):
			self.service = self.bus.get_object(SERVICE_NAME, SERVICE_OBJECT_PATH)

	def get_status(self):
		if self.service:
			return "Active, pid: " + self.get_running_instance_id()
		else:
			return "Inactive"

	def send_message(self, ipc_message):
		self.service.get_dbus_method(
			'message', 'io.github.procris.Service'
		)(ipc_message)

	def get_running_instance_id(self):
		get_remote_id = self.service.get_dbus_method('get_id', 'io.github.procris.Service')
		return get_remote_id()

	def stop_running_instance(self):
		if self.service:
			quit_function = self.service.get_dbus_method('stop', 'io.github.procris.Service')
			quit_function()
			print("Remote instance were stopped")
		else:
			print("procris is not running")
