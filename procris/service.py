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
import os, gi, signal, setproctitle, traceback
import procris
import procris.names as names
import procris.persistent_config as configurations
import procris.applications as applications
import procris.messages as messages
import procris.terminal as terminal
import Xlib
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, Gtk, GLib, Gdk
from procris.reading import Reading
from procris.status import StatusIcon
from procris.keyboard import KeyboardListener
from procris.layout import Layout
from procris.windows import Windows
from procris.names import PromptInput

SIGINT = getattr(signal, "SIGINT", None)
SIGTERM = getattr(signal, "SIGTERM", None)
SIGHUP = getattr(signal, "SIGHUP", None)

reading: Reading = None
listener: KeyboardListener = None
windows: Windows = None
layout: Layout = None
status_icon: StatusIcon = None
config = bus_object = None


def load():
	global listener, bus_object, status_icon, windows, reading, layout

	# as soon as possible so new instances are notified
	from procris.remote import BusObject
	bus_object = BusObject(procris.service)

	windows = Windows()
	reading = Reading(windows=windows)
	layout = Layout(reading.windows)
	status_icon = StatusIcon(layout, stop_function=stop)
	listener = KeyboardListener(callback=keyboard_listener, on_error=stop)

	configure_process()
	applications.load()
	terminal.load()
	load_mappings()


def load_mappings():
	global config
	imported = False
	try:
		import importlib.util
		spec = importlib.util.spec_from_file_location("module.name", configurations.get_custom_mappings_module_path())
		config = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(config)
		imported = True
	except FileNotFoundError as e:
		print(
			'info: not possible to load custom config at: {}'.format(
				configurations.get_custom_mappings_module_path()))

	if not imported:
		import procris.config as default_config
		config = default_config

	for name in config.names:
		names.add(name)

	for key in config.keys:
		listener.bind(key)

	configurations.set_defaults(config.default_interface)
	layout.from_json(configurations.read_layout(default=config.default_layout))


#
# Service lifecycle API
#
def start():
	Wnck.set_client_type(Wnck.ClientType.PAGER)
	windows.read_screen()
	layout.start()
	windows.apply_decoration_config()
	listener.start()
	status_icon.activate()
	Gtk.main()

	print("Ending procris service, pid: {}".format(os.getpid()))


def read_command_key(c_in):
	messages.prompt_placeholder = Gtk.accelerator_name(c_in.keyval, c_in.keymod)


def debug(c_in):
	return messages.Message(windows.get_metadata_resume(), None)


def reload(c_in):
	configurations.reload()
	status_icon.reload()
	applications.reload()
	terminal.reload()
	messages.clean()
	reading.clean(recreate_view=True)
	windows.read_screen()
	windows.apply_decoration_config()


def stop():
	GLib.idle_add(Gtk.main_quit, priority=GLib.PRIORITY_HIGH)
	listener.stop()
	release_bus_object()


def keyboard_listener(key, x_key_event, multiplier=1):
	command_input = PromptInput(
		time=x_key_event.time, parameters=key.parameters, keyval=x_key_event.keyval, keymod=x_key_event.keymod)

	_execute_inside_main_loop(key.function, command_input, multiplier)


def message(ipc_message):
	from datetime import datetime
	execute(cmd=ipc_message, timestamp=datetime.now().microsecond)


def execute(cmd: str = None, timestamp: int = None):
	if names.has_multiple_names(cmd):
		raise names.InvalidName('TODO: iterate multiple commands')

	c_in = PromptInput(text=cmd, time=timestamp).parse()
	name = names.match(c_in)

	if not name:
		raise names.InvalidName('Not an editor command: ' + cmd)

	_execute_inside_main_loop(name.function, c_in)

	return True


def _execute_inside_main_loop(function, command_input, multiplier=1):

	GLib.idle_add(_execute, function, command_input, multiplier,  priority=GLib.PRIORITY_HIGH)


def _execute(function, command_input, multiplier=1):
	try:

		pre_processing()

		for i in range(multiplier):
			return_message = function(command_input)
			if return_message:
				messages.add(return_message)

		if messages.has_message():
			reading.begin(command_input.time)

		if windows.staging:
			windows.commit_navigation(command_input.time)
			reading.make_transient()

		post_processing()

	except Exception as inst:
		msg = 'ERROR ({}) executing: {}'.format(str(inst), command_input.text)
		print(traceback.format_exc())
		messages.add_error(msg)
		reading.begin(command_input.time)

	return False


def pre_processing():

	reading.make_transient()
	windows.read_screen()
	layout.read_display()


def post_processing():

	if reading.is_transient():
		reading.end()
		messages.clean()

	messages.clean_prompt()

	# reload to show the current layout icon
	status_icon.reload()


def configure_process():
	setproctitle.setproctitle("procris")

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


def unix_signal_handler(*args):
	signal_val = args[0]
	if signal_val in (1, SIGHUP, 2, SIGINT, 15, SIGTERM):
		stop()


def release_bus_object():
	global bus_object
	if bus_object:
		bus_object.release()
		bus_object = None
