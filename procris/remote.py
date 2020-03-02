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
import os
import dbus
import dbus.service
from typing import Callable
from dbus.mainloop.glib import DBusGMainLoop
from dbus.gi_service import ExportedGObject
from dbus.proxies import ProxyObject


class ForeignInterface (ExportedGObject):

	def __init__(self, ipc_handler: Callable = None, stop: Callable = None):
		self.ipc_handler = ipc_handler
		self.stop = stop

		bus_name = dbus.service.BusName(SERVICE_NAME, BUS)
		super(ForeignInterface, self).__init__(conn=BUS, object_path=SERVICE_OBJECT_PATH, bus_name=bus_name)

	@dbus.service.method("io.github.procris.Service", in_signature='', out_signature='s')
	def get_id(self):
		return str(os.getpid())

	@dbus.service.method("io.github.procris.Service", in_signature='s', out_signature='')
	def message(self, ipc_message):
		self.ipc_handler(ipc_message)

	@dbus.service.method("io.github.procris.Service", in_signature='', out_signature='')
	def stop(self):
		self.stop()


class Proxy:

	def __init__(self, dbus_proxy):
		self.dbus_proxy: ProxyObject = dbus_proxy

	def send_message(self, ipc_message):
		self.dbus_proxy.get_dbus_method(
			'message', 'io.github.procris.Service'
		)(ipc_message)

	def get_running_instance_id(self):
		get_remote_id = self.dbus_proxy.get_dbus_method('get_id', 'io.github.procris.Service')
		return get_remote_id()

	def stop_running_instance(self):
		quit_function = self.dbus_proxy.get_dbus_method('stop', 'io.github.procris.Service')
		quit_function()


def export(ipc_handler: Callable = None, stop: Callable = None) -> ForeignInterface:
	return ForeignInterface(ipc_handler=ipc_handler, stop=stop)


def release():
	BUS.release_name(SERVICE_NAME)
	print('procris service were released from bus')


def get_proxy() -> Proxy:
	if not BUS or not BUS.name_has_owner(SERVICE_NAME):
		return None
	return Proxy(BUS.get_object(SERVICE_NAME, SERVICE_OBJECT_PATH))


DBusGMainLoop(set_as_default=True)
dbus.mainloop.glib.threads_init()
BUS = dbus.Bus()
if not BUS:
	print("no bus session")
SERVICE_NAME = "io.github.procris"
SERVICE_OBJECT_PATH = "/io/github/procris"
