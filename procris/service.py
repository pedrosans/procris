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

import ctypes

x11 = ctypes.cdll.LoadLibrary('libX11.so.6')
x11.XInitThreads()
# add python lock to Xlib internals
from Xlib import threaded

import os, gi, signal, setproctitle, logging, traceback
import procris
import procris.names as names
import procris.configurations as configurations
import procris.applications as applications
import procris.messages as messages
import procris.terminal as terminal

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from procris.reading import Reading
from gi.repository import Gtk, GLib, Gdk
from procris.status import StatusIcon
from procris.keyboard import KeyboardListener
from procris.layout import Layout
from procris.windows import Windows
from procris.names import PromptInput

SIGINT = getattr(signal, "SIGINT", None)
SIGTERM = getattr(signal, "SIGTERM", None)
SIGHUP = getattr(signal, "SIGHUP", None)

reading: Reading
mappings = listener = bus_object = status_icon = windows = layout = None


def load():
	global listener, bus_object, status_icon, windows, reading, layout

	# as soon as possible so new instances are notified
	from procris.remote import BusObject
	bus_object = BusObject(procris.service)

	windows = Windows(configurations.is_list_workspaces())
	reading = Reading(configurations=configurations, windows=windows)
	layout = Layout(reading.windows, )
	status_icon = StatusIcon(layout, stop_function=stop)
	listener = KeyboardListener(callback=keyboard_listener, on_error=stop)

	configure_process()
	applications.load()
	terminal.load()
	load_mappings()


def load_mappings():
	global mappings
	imported = False
	try:
		import importlib.util
		spec = importlib.util.spec_from_file_location("module.name", configurations.get_custom_mappings_module_path())
		mappings = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(mappings)
		imported = True
	except FileNotFoundError as e:
		print(
			'info: it is possible to customize procris bindings by in {}'.format(
				configurations.get_custom_mappings_module_path()))

	if not imported:
		import procris.mappings as default_mappings
		mappings = default_mappings

	for name in mappings.names:
		names.add(name)

	for key in mappings.keys:
		listener.bind(key)


#
# Service lifecycle API
#
def start():
	listener.start()

	status_icon.activate()

	Gtk.main()

	print("Ending procris service, pid: {}".format(os.getpid()))


def read_command_key(c_in):
	reading.begin(c_in.time)


def reload(c_in):
	configurations.reload()
	status_icon.reload()
	applications.reload()
	terminal.reload()
	messages.clean()
	reading.clean(recreate_view=True)


def stop():
	GLib.idle_add(Gtk.main_quit, priority=GLib.PRIORITY_HIGH)
	listener.stop()
	release_bus_object()


def keyboard_listener(key, x_key_event, multiplier=1):
	GLib.idle_add(
		_inside_main_loop, key, x_key_event, multiplier,
		priority=GLib.PRIORITY_HIGH)


def _inside_main_loop(key, x_key_event, multiplier):
	command_input = PromptInput(
		time=x_key_event.time, keyval=x_key_event.keyval, parameters=key.parameters)

	execute(key.function, command_input, multiplier)

	return False


def execute(function, command_input, multiplier=1):
	try:

		pre_processing()

		for i in range(multiplier):
			return_message = function(command_input)
			if return_message:
				messages.add_message(return_message)

		if messages.LIST or messages.prompt_placeholder:
			reading.begin(command_input.time)

		if windows.staging:
			windows.commit_navigation(command_input.time)
			reading.make_transient()

		post_processing(command_input.time)

	except Exception as inst:
		msg = 'ERROR ({}) executing: {}'.format(str(inst), command_input.text)
		print(traceback.format_exc())
		messages.add(msg, 'error')
		reading.begin(command_input.time)


def pre_processing():

	reading.clean()
	windows.read_screen()


def post_processing(time):

	if reading.is_transient():
		reading.end()
		messages.clean()

	reading.make_transient()

	# reload to show the current layout icon
	status_icon.reload()


def message(ipc_message):
	windows.read_screen()
	c_in = PromptInput(time=None, text=ipc_message).parse()
	name = names.match(c_in)
	name.function(c_in)
	for m in messages.LIST:
		print(m.content)


def configure_process():
	# https://lazka.github.io/pgi-docs/GLib-2.0/functions.html#GLib.log_set_handler
	GLib.log_set_handler(None, GLib.LogLevelFlags.LEVEL_WARNING, log_function)
	GLib.log_set_handler(None, GLib.LogLevelFlags.LEVEL_ERROR, log_function)
	GLib.log_set_handler(None, GLib.LogLevelFlags.LEVEL_CRITICAL, log_function)

	setproctitle.setproctitle("procris")

	for sig in (SIGINT, SIGTERM, SIGHUP):
		install_glib_handler(sig)


def debug(c_in):
	return messages.Message(windows.get_metadata_resume(), None)


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


def unix_signal_handler(*args):
	signal_val = args[0]
	if signal_val in (1, SIGHUP, 2, SIGINT, 15, SIGTERM):
		stop()


def release_bus_object():
	global bus_object
	if bus_object:
		bus_object.release()
		bus_object = None


def show_warning(error):
	error_dialog = Gtk.MessageDialog(
		None, Gtk.DialogFlags.MODAL, Gtk.MessageType.WARNING,
		Gtk.ButtonsType.CLOSE, error, title="procris - warning")
	error_dialog.run()
	error_dialog.destroy()


def show_error(error):
	error_dialog = Gtk.MessageDialog(
		None, Gtk.DialogFlags.MODAL, Gtk.MessageType.ERROR,
		Gtk.ButtonsType.CLOSE, error, title="procris error")
	error_dialog.run()
	error_dialog.destroy()


def log_function(log_domain, log_level, message):
	if log_level in (GLib.LogLevelFlags.LEVEL_ERROR, GLib.LogLevelFlags.LEVEL_CRITICAL):
		logging.error('GLib log[%s]:%s', log_domain, message)
		show_error(message)
		Exception(message)
	else:
		logging.warning('GLib log[%s]:%s', log_domain, message)
		show_warning(message)
