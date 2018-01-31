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

import sys, os, gi, dbus, dbus.service, signal, setproctitle
gi.require_version('Gtk', '3.0')
from vimwn.controller import Controller
from vimwn.status import NavigatorStatus
from gi.repository import GObject, Gtk
from dbus.mainloop.glib import DBusGMainLoop
from dbus.gi_service import ExportedGObject

SERVICE_NAME = "io.github.vimwn"
SERVICE_OBJECT_PATH = "/io/github/vimwn"

class NavigatorService:

	def __init__(self):
		self.bus_object = None

	def start(self, redirect_output):
		self.controller = Controller()
		self.configurations = self.controller.configurations

		if redirect_output:
			self.redirect_output(self.configurations.get_log_file())

		self.configure_process()
		self.export_bus_object()

		self.controller.listen_user_events()

		NavigatorStatus(self.configurations, self).activate()

		Gtk.main()
		print("Ending vimwn service, pid: {}".format(os.getpid()))

	def stop(self):
		self.bus_object.quit()

	def configure_process(self):
		setproctitle.setproctitle("vimwn")
		signal.signal(signal.SIGINT, signal.SIG_DFL)
		signal.signal(signal.SIGTERM, signal.SIG_DFL)
		signal.signal(signal.SIGHUP, signal.SIG_DFL)

	def export_bus_object(self):
		self.bus_object = NavigatorBusService()

	def signal_handler(self, signal, frame):
		"""
		Implemented for reference, should be used
		when python-gi version 3.27.0 gets into stable distros
		https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=743208
		usage: signal.signal(signal.SIGINT, self.signal_handler)
		"""
		print('You pressed Ctrl+C!')
		self.bus_object.quit()

	def daemonize(self):
		"""
		do the UNIX double-fork magic, see Stevens' "Advanced
		Programming in the UNIX Environment" for details (ISBN 0201563177)
		http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16

		Code from Sander Marechal  found at
		http://web.archive.org/web/20131017130434/http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/
		rational from Sander's answer:
		"... A true daemon has no environment. No parent process, no working directory and no stdin, stdout and stderr. That's why I redirect everything to /dev/null and that's why you need to fork() twice.
		Using stdout and flush() can sorta work, but you don't have a real daemon anymore. Consider this. Open a terminal, start your program and then close the terminal. What happens to stdout now? It's gone. That's why it needs to be redirected to /dev/null. And that's why all daemons use logfiles or log to the syslog."
		"""
		try:
			pid = os.fork()
			if pid > 0:
				# exit first parent
				sys.exit(0)
		except OSError as e:
			sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
			sys.exit(1)

		# decouple from parent environment
		os.chdir("/")
		os.setsid()
		os.umask(0)

		# do second fork
		try:
			pid = os.fork()
			if pid > 0:
				# exit from second parent
				sys.exit(0)
		except OSError as e:
			sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
			sys.exit(1)

	def redirect_output(self, logfile='/dev/null' ):
		# redirect standard file descriptors
		sys.stdout.flush()
		sys.stderr.flush()
		try:
			so = open(logfile, 'a+')
			se = open(logfile, 'a+')
		except PermissionError:
			so = open(os.devnull, 'a+')
			se = open(os.devnull, 'a+')

		os.dup2(so.fileno(), sys.stdout.fileno())
		os.dup2(se.fileno(), sys.stderr.fileno())

class NavigatorBusService (ExportedGObject):

	def __init__(self):
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
	def quit(self):
		Gtk.main_quit()
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
			quit_function = service.get_dbus_method('quit', 'io.github.vimwn.Service')
			quit_function()
			print("Remote instance were stopped")
		else:
			print("vimwn is not running")
