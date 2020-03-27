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
import pwm.names as names
import pwm.state as cache
import pwm.applications as applications
import pwm.messages as messages
import pwm.terminal as terminal
import pwm.remote as remote
import pwm.desktop as desktop
gi.require_version('Gtk', '3.0')
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, Gtk, GLib
from datetime import datetime
from types import ModuleType
from typing import Callable
from pwm.reading import Reading
from pwm.keyboard import KeyboardListener, Key
from pwm.layout import Monitors
from pwm.model import Windows
from pwm.wm import UserEvent


def load():
	applications.load()
	terminal.load()
	cache.load()
	desktop.load()
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
	setproctitle.setproctitle("pwm")
	unix_signal_add = _signal_function()
	for sig in (SIGINT, SIGTERM, SIGHUP):
		unix_signal_add(GLib.PRIORITY_HIGH, sig, _unix_signal_handler, sig)


#
# Service lifecycle API
#
def start():

	if remote.get_proxy():
		print("pwm is already running, pid: " + remote.get_proxy().get_running_instance_id())
		quit()

	remote.export(ipc_handler=message, stop=stop)
	layout.connect_to(Wnck.Screen.get_default())
	windows.apply_decoration_config()
	layout.apply()
	listener.start()
	desktop.connect()
	Gtk.main()
	print("Ending pwm service, pid: {}".format(os.getpid()))


def stop():
	desktop.unload()
	listener.stop()
	remote.release()
	layout.disconnect_from(Wnck.Screen.get_default())
	GLib.idle_add(Gtk.main_quit, priority=GLib.PRIORITY_HIGH)


#
# Commands
#
def show_reading(c_in):
	messages.prompt_placeholder = Gtk.accelerator_name(c_in.keyval, c_in.keymod)


def show_prompt(user_event: UserEvent):
	messages.clean()
	reading.begin(user_event.time)
	reading.set_command_mode()
	reading.show_completions()


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

	windows.read(screen)
	layout.read_screen(screen)

	reading.make_transient()


def _post_processing(user_event: UserEvent):
	if messages.has_message():
		reading.begin(user_event.time)

	if windows.staging:
		windows.commit_navigation(user_event.time)
		reading.make_transient()

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
layout: Monitors = Monitors(windows)
listener: KeyboardListener = KeyboardListener(callback=keyboard_listener, on_error=stop)
