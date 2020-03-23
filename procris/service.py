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
xlib_support_initialized = x11.XInitThreads()
if not xlib_support_initialized:
	raise Exception('Unable to initialize Xlib support for multiple threads.')
import os, gi, signal, setproctitle, traceback
import procris.names as names
import procris.state as cache
import procris.applications as applications
import procris.messages as messages
import procris.terminal as terminal
import procris.remote as remote
import procris.desktop as desktop
gi.require_version('Gtk', '3.0')
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, Gtk, GLib
from types import ModuleType
from procris.reading import Reading
from procris.keyboard import KeyboardListener, Key
from procris.layout import Layout
from procris.windows import Windows
from procris.wm import UserEvent


def load():
	applications.load()
	terminal.load()
	cache.load()
	_read_environment(Wnck.Screen.get_default(), cache.get_config_module())
	_configure_process()


def _read_environment(screen: Wnck.Screen, config: ModuleType):
	for name in config.NAMES:
		names.add(name)
	for key in config.KEYS:
		listener.add(key)
	windows.read(screen)
	layout.read(screen, cache.get_workspace_config())


def _configure_process():
	Wnck.set_client_type(Wnck.ClientType.PAGER)
	setproctitle.setproctitle("procris")
	unix_signal_add = _signal_function()
	for sig in (SIGINT, SIGTERM, SIGHUP):
		unix_signal_add(GLib.PRIORITY_HIGH, sig, _unix_signal_handler, sig)


#
# Service lifecycle API
#
def start():

	if remote.get_proxy():
		print("procris is already running, pid: " + remote.get_proxy().get_running_instance_id())
		quit()

	remote.export(ipc_handler=message, stop=stop)
	layout.connect_to(Wnck.Screen.get_default())
	windows.apply_decoration_config()
	layout.apply()
	listener.start()
	desktop.connect()
	Gtk.main()
	print("Ending procris service, pid: {}".format(os.getpid()))


def stop():
	desktop.disconnect()
	listener.stop()
	remote.release()
	layout.disconnect_from(Wnck.Screen.get_default())
	GLib.idle_add(Gtk.main_quit, priority=GLib.PRIORITY_HIGH)


#
# Commands
#
def read_command_key(c_in):
	messages.prompt_placeholder = Gtk.accelerator_name(c_in.keyval, c_in.keymod)


def escape_reading(c_in: UserEvent):
	messages.clean()


def debug(c_in):
	text = windows.resume()
	text += layout.resume()
	messages.add(text=text)


def reload(c_in):
	desktop.update()
	cache.reload()
	applications.reload()
	terminal.reload()
	messages.clean()
	reading.clean(recreate_view=True)
	windows.read_default_screen()
	windows.apply_decoration_config()


#
# Callbacks
#
def keyboard_listener(key: Key, x_key_event, multiplier=1):
	command_input = UserEvent(
		time=x_key_event.time, parameters=key.parameters, keyval=x_key_event.keyval, keymod=x_key_event.keymod)

	_execute_inside_main_loop(key.function, command_input, multiplier)


def message(ipc_message):
	from datetime import datetime
	execute(cmd=ipc_message, timestamp=datetime.now().microsecond)


#
# API
#
def execute(cmd: str = None, timestamp: int = None, move_to_main_loop=True):
	if names.has_multiple_names(cmd):
		raise names.InvalidName('TODO: iterate multiple commands')

	c_in = UserEvent(text=cmd, time=timestamp)
	name = names.match(c_in)

	if not name:
		raise names.InvalidName('Not an editor command: ' + cmd)

	if move_to_main_loop:
		_execute_inside_main_loop(name.function, c_in)
	else:
		call(name.function, c_in)

	return True


def call(function, command_input, multiplier=1):
	try:

		_pre_processing()

		for i in range(multiplier):
			return_message = function(command_input)
			if return_message:
				messages.add(return_message)

		if messages.has_message():
			reading.begin(command_input.time)

		if windows.staging:
			windows.commit_navigation(command_input.time)
			reading.make_transient()

		_post_processing()

	except Exception as inst:
		msg = 'ERROR ({}) executing: {}'.format(str(inst), command_input.text)
		print(traceback.format_exc())
		messages.add_error(msg)
		reading.begin(command_input.time)

	return False


def _pre_processing():
	screen = Wnck.Screen.get_default()

	windows.read(screen)
	layout.read_screen(screen)

	reading.make_transient()


def _post_processing():

	if reading.is_transient():
		reading.end()
		messages.clean()

	messages.clean_prompt()

	if desktop.is_connected():
		desktop.update()


#
# Util
#
def _execute_inside_main_loop(function, command_input, multiplier=1):

	GLib.idle_add(call, function, command_input, multiplier, priority=GLib.PRIORITY_HIGH)


def _signal_function():
	if hasattr(GLib, "unix_signal_add"):
		return GLib.unix_signal_add
	elif hasattr(GLib, "unix_signal_add_full"):
		return GLib.unix_signal_add_full
	else:
		raise Exception("Can't install GLib signal handler, too old gi.")


def _unix_signal_handler(*args):
	signal_val = args[0]
	if signal_val in (1, SIGHUP, 2, SIGINT, 15, SIGTERM):
		stop()


SIGINT = getattr(signal, "SIGINT", None)
SIGTERM = getattr(signal, "SIGTERM", None)
SIGHUP = getattr(signal, "SIGHUP", None)
windows: Windows = Windows()
reading: Reading = Reading(windows)
layout: Layout = Layout(windows)
listener: KeyboardListener = KeyboardListener(callback=keyboard_listener, on_error=stop)
