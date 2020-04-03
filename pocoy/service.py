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
import pocoy.names as names
import pocoy.state as state
import pocoy.applications as applications
import pocoy.messages as messages
import pocoy.terminal as terminal
import pocoy.remote as remote
import pocoy.desktop as desktop
import pocoy.model as model
gi.require_version('Gtk', '3.0')
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, Gtk, GLib
from datetime import datetime
from types import ModuleType
from typing import Callable
from pocoy.reading import Reading
from pocoy.keyboard import KeyboardListener, Key
from pocoy.wm import UserEvent


def load(config_module: str = None):
	applications.load()
	terminal.load()
	state.load(config_module)
	desktop.load()
	_read_environment(Wnck.Screen.get_default(), state.get_config_module())
	_configure_process()


def _read_environment(screen: Wnck.Screen, config: ModuleType):
	for name in config.NAMES:
		names.add(name)
	for key in config.KEYS:
		listener.add(key)
	model.load(screen)


def _configure_process():
	Wnck.set_client_type(Wnck.ClientType.PAGER)
	setproctitle.setproctitle("pocoy")
	unix_signal_add = _signal_function()
	for sig in (SIGINT, SIGTERM, SIGHUP):
		unix_signal_add(GLib.PRIORITY_HIGH, sig, _unix_signal_handler, sig)


#
# Service lifecycle API
#
def start():

	if remote.get_proxy():
		print("pocoy is already running")
		quit()

	remote.export(ipc_handler=message, stop=stop)
	model.start()
	listener.start()
	desktop.connect()
	Gtk.main()
	print("Ending pocoy service, pid: {}".format(os.getpid()))


def stop():
	desktop.unload()
	listener.stop()
	remote.release()
	model.stop()
	GLib.idle_add(Gtk.main_quit, priority=GLib.PRIORITY_HIGH)


#
# Commands
#
def read_screen(user_event: UserEvent):
	messages.add(text=model.resume())


def reload(user_event: UserEvent):
	desktop.update()
	state.reload()
	applications.reload()
	terminal.reload()
	messages.clean()
	reading.reload(recreate_view=True)
	model.windows.read_default_screen()
	model.windows.apply_decoration_config()


#
# Callbacks
#
def keyboard_listener(key: Key, x_key_event, multiplier=1):
	if not key.function:
		return

	user_event = UserEvent(
		time=x_key_event.time, parameters=key.parameters, keyval=x_key_event.keyval, keymod=x_key_event.keymod)

	_execute_inside_main_loop(key.function, user_event, multiplier)


#
# API
#
def message(ipc_message):
	execute(cmd=ipc_message)


def execute(function: Callable = None, cmd: str = None, timestamp: int = None, move_to_main_loop=True):
	if not timestamp:
		timestamp = datetime.now().microsecond
	user_event = UserEvent(text=cmd, time=timestamp)

	if cmd:
		if names.has_multiple_names(cmd):
			raise names.InvalidName('TODO: iterate multiple commands')

		name = names.match(user_event)

		if not name:
			raise names.InvalidName('Not an editor command: ' + cmd)

		function = name.function

	if move_to_main_loop:
		_execute_inside_main_loop(function, user_event)
	else:
		call(function, user_event)

	return True


def call(function, user_event: UserEvent, multiplier=1):
	try:

		_pre_processing()

		for i in range(multiplier):
			return_message = function(user_event)
			if return_message:
				messages.add(return_message)

		_post_processing(user_event)

	except Exception as inst:
		msg = 'ERROR ({}) executing: {}'.format(str(inst), user_event.text)
		print(traceback.format_exc())
		messages.add_error(msg)
		reading.begin(user_event.time)

	return False


def _pre_processing():
	screen = Wnck.Screen.get_default()

	model.windows.read(screen)

	reading.make_transient()


def _post_processing(user_event: UserEvent):

	if model.windows.staging:
		model.windows.commit_navigation(user_event.time)
		messages.clean()

	if messages.has_message():
		reading.begin(user_event.time)

	if reading.is_transient():
		reading.end()

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

reading: Reading = Reading(model.windows, model.active_window)
listener: KeyboardListener = KeyboardListener(callback=keyboard_listener, on_error=stop)