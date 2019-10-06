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

import os, gi, signal, setproctitle, logging
import vimwn.command
import vimwn.configurations as configurations
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from vimwn.reading import Reading
from gi.repository import GObject, Gtk, GLib, Gdk
from vimwn.status import StatusIcon
from vimwn.keyboard import KeyboardListener
from vimwn.layout import LayoutManager
from vimwn.windows import Windows
from vimwn.command import CommandInput
from vimwn.remote import NavigatorBusService

SIGINT = getattr(signal, "SIGINT", None)
SIGTERM = getattr(signal, "SIGTERM", None)
SIGHUP = getattr(signal, "SIGHUP", None)


listener = None
bus_object = None
status_icon = None
windows = Windows(configurations.is_list_workspaces())
GObject.threads_init()
reading = Reading(configurations=configurations, windows=windows)
layout_manager = LayoutManager(
	reading.windows, remove_decorations=configurations.is_remove_decorations())


def start():
	global listener, bus_object, status_icon
	import vimwn.mapping as mappings

	# as soon as possible so new instances as notified
	bus_object = NavigatorBusService(stop)
	configure_process()

	for command in mappings.commands:
		vimwn.command.add(command)

	listener = KeyboardListener(callback=keyboard_listener, on_error=keyboard_error)

	for key in mappings.keys:
		listener.bind(key)

	listener.start()

	status_icon = StatusIcon(configurations, layout_manager, stop_function=quit)
	status_icon.activate()

	Gtk.main()

	print("Ending vimwn service, pid: {}".format(os.getpid()))


def keyboard_error(exception, *args):
	print('Unable to listen to {}'.format(configurations.get_prefix_key()))
	stop()


def keyboard_listener(key, x_key_event, multiplier=1):
	GLib.idle_add(
		_inside_main_loop, key, x_key_event, multiplier,
		priority=GLib.PRIORITY_HIGH);


def _inside_main_loop(key, x_key_event, multiplier):

	command_input = CommandInput(
		time=x_key_event.time, keyval=x_key_event.keyval, parameters=key.parameters)

	for i in range(multiplier):
		key.function(command_input)

	windows.commit_navigation(x_key_event.time)

	if len(key.accelerators) > 1:
		reading.set_normal_mode()

	return False


# TODO: remove
def reload():
	configurations.reload()
	status_icon.reload()


def configure_process():
	# https://lazka.github.io/pgi-docs/GLib-2.0/functions.html#GLib.log_set_handler
	GLib.log_set_handler(None, GLib.LogLevelFlags.LEVEL_WARNING, log_function)
	GLib.log_set_handler(None, GLib.LogLevelFlags.LEVEL_ERROR, log_function)
	GLib.log_set_handler(None, GLib.LogLevelFlags.LEVEL_CRITICAL, log_function)

	setproctitle.setproctitle("vimwn")

	for sig in (SIGINT, SIGTERM, SIGHUP):
		install_glib_handler(sig)


def install_glib_handler(sig):
	unix_signal_add = None

	if hasattr(GLib, "unix_signal_add"):
		unix_signal_add = GLib.unix_signal_add
	elif hasattr(GLib, "unix_signal_add_full"):
		unix_signal_add = GLib.unix_signal_add_full

	if unix_signal_add:
		unix_signal_add(GLib.PRIORITY_HIGH, sig, unix_signal_handler, sig)
	else:
		print("Can't install GLib signal handler, too old gi.")


def unix_signal_handler(self, *args):
	signal = args[0]
	if signal in (1, SIGHUP, 2, SIGINT, 15, SIGTERM):
		stop()


def release_bus_object():
	global bus_object
	if bus_object:
		bus_object.release()
		bus_object = None


def stop():
	Gtk.main_quit()
	listener.stop()
	release_bus_object()


def show_warning(error):
	error_dialog = Gtk.MessageDialog(
		None, Gtk.DialogFlags.MODAL, Gtk.MessageType.WARNING,
		Gtk.ButtonsType.CLOSE, error, title="vimwn - warning")
	error_dialog.run()
	error_dialog.destroy()


def show_error(error):
	error_dialog = Gtk.MessageDialog(
		None, Gtk.DialogFlags.MODAL, Gtk.MessageType.ERROR,
		Gtk.ButtonsType.CLOSE, error, title="vimwn error")
	error_dialog.run()
	error_dialog.destroy()


def log_function(log_domain, log_level, message):
	if log_level in (GLib.LogLevelFlags.LEVEL_ERROR, GLib.LogLevelFlags.LEVEL_CRITICAL):
		logging.error('GLib log[%s]:%s',log_domain, message)
		show_error(message)
		Exception(message)
	else:
		logging.warning('GLib log[%s]:%s',log_domain, message)
		show_warning(message)
