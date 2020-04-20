import queue
from threading import Thread
from typing import Dict

import pocoy.layout
import pocoy.state as state
import xdg.IconTheme
import os
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
gi.require_version('Wnck', '3.0')
from gi.repository import Gtk, GLib, GdkPixbuf, AppIndicator3, Wnck
from pocoy import state as configurations
from pocoy.wm import get_active_workspace, UserEvent, is_workspaces_only_on_primary, get_first_workspace
from pocoy.model import Monitor, monitors, windows


class StatusIcon:

	app_indicator: AppIndicator3.Indicator
	autostart_item: Gtk.CheckMenuItem = Gtk.CheckMenuItem(label="Autostart")
	decorations_item: Gtk.CheckMenuItem = Gtk.CheckMenuItem(label="Remove decorations")
	icons_submenu = Gtk.Menu()
	layout_submenu = Gtk.Menu()
	# Track reloading routine to stop any layout side effect when updating the UI
	_reloading = False

	def __init__(self, windows, monitors, stop_function=None):
		self.stop_function = stop_function
		self.windows = windows
		self.monitors = monitors
		self.menu = Gtk.Menu()

		self.menu.append(self.autostart_item)

		self.menu.append(self.decorations_item)

		self.add_icon_options()
		self.add_layout_options()

		# QUIT MENU
		quit_item = Gtk.MenuItem(label="Quit")
		quit_item.connect("activate", self._quit)
		self.menu.append(quit_item)

	def add_icon_options(self):
		appearance_menu_item = Gtk.MenuItem(label="Appearance")
		appearance_menu_item.set_submenu(self.icons_submenu)

		for key in ICON_STYLES_MAP.keys():
			icon_item = Gtk.RadioMenuItem(
				label=ICON_STYLES_MAP[key],
				group=self.icons_submenu.get_children()[0] if self.icons_submenu.get_children() else None)
			icon_item.icon_style = key
			icon_item.connect("toggled", self._change_icon)
			self.icons_submenu.append(icon_item)

		self.menu.append(appearance_menu_item)

	def add_layout_options(self):
		layout_menu_item = Gtk.MenuItem(label="Layout")
		layout_menu_item.set_submenu(self.layout_submenu)

		for function_key in pocoy.layout.FUNCTIONS_MAP.keys():
			function = pocoy.layout.FUNCTIONS_MAP[function_key]
			name = function.__name__ if function else 'none'
			menu_item = Gtk.RadioMenuItem(
				label=name,
				group=self.layout_submenu.get_children()[0] if self.layout_submenu.get_children() else None)
			menu_item.function_key = function_key
			menu_item.connect("toggled", self._change_layout)
			self.layout_submenu.append(menu_item)

		self.menu.append(layout_menu_item)

	def activate(self):
		self.autostart_item.set_active(configurations.is_autostart())
		self.autostart_item.connect("toggled", self._change_autostart)
		self.decorations_item.set_active(configurations.is_remove_decorations())
		self.decorations_item.connect("toggled", self._change_decorations)

		self.app_indicator = AppIndicator3.Indicator.new("pocoy", ICONNAME, AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
		self.app_indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
		self.app_indicator.set_menu(self.menu)
		self.menu.show_all()
		self.reload()

	def reload(self):
		self._reloading = True

		iconname = configurations.get_desktop_icon()
		function_key = self.monitors.get_primary().function_key

		for item in self.icons_submenu.get_children():
			item.set_active(item.icon_style == iconname)

		for item in self.layout_submenu.get_children():
			item.set_active(item.function_key == function_key)

		sys_icon = 'pocoy'
		if function_key:
			sys_icon = sys_icon + '-' + function_key
		if iconname == "dark" or iconname == "light":
			sys_icon = sys_icon + '-' + iconname
		self.app_indicator.set_icon(sys_icon)

		self._reloading = False

	#
	# CALLBACKS
	#
	def _change_icon(self, radio_menu_item: Gtk.RadioMenuItem):
		if not self._reloading and radio_menu_item.get_active():
			configurations.set_desktop_icon(radio_menu_item.icon_style)
			self.reload()

	def _change_autostart(self, check_menu_item: Gtk.CheckMenuItem):
		configurations.set_autostart(check_menu_item.get_active())

	def _change_layout(self, radio_menu_item: Gtk.RadioMenuItem):
		if not self._reloading and radio_menu_item.get_active():
			function_key = radio_menu_item.function_key
			event = UserEvent(time=Gtk.get_current_event_time())
			event.parameters = [function_key]
			import pocoy.service as service
			service.call(self.monitors.setprimarylayout, event)

	def _change_decorations(self, check_menu_item: Gtk.CheckMenuItem):
		to_remove = check_menu_item.get_active()
		configurations.set_remove_decorations(to_remove)
		import pocoy.service as service
		service.call(self.windows.decorate, None)

	def _quit(self, data):
		self.stop_function()


# https://lazka.github.io/pgi-docs/Notify-0.7/classes/Notification.html
# https://developer.gnome.org/notification-spec
def load():
	icon_path = xdg.IconTheme.getIconPath('pocoy', size=96)
	if icon_path:
		icon_image = GdkPixbuf.Pixbuf.new_from_file(icon_path)
	else:
		print('**********************************************************************************')
		print(' No image found for status icon and notifications.')
		print(' The status icon may be invisible during this run')
		print(' Images for the icon can be installed with "make install" or "./setup.py install"')
		print('**********************************************************************************')
	if state.is_desktop_notifications():
		try:
			gi.require_version('Notify', '0.7')
		except:
			print('Can not load Notify')
			return
		from gi.repository import Notify
		global notification
		Notify.init('pocoy')
		notification = Notify.Notification.new('pocoy')
		notification.set_app_name('pocoy')
		notification.set_hint('resident', GLib.Variant.new_boolean(True))
		notification.set_image_from_pixbuf(icon_image)


def connect():
	import pocoy.service
	global status_icon
	# TODO: pass window and monitor as parameters
	status_icon = StatusIcon(windows, monitors, stop_function=pocoy.service.stop)
	status_icon.activate()
	start_pipes()


def on_layout_changed():
	if is_connected():
		status_icon.reload()

	if state.is_desktop_notifications():
		show_monitor(monitors.get_active())

	serialized = {}
	monitor = monitors.get_primary()
	serialized['primary'] = monitor.to_json()
	serialized['primary']['workspace'] = get_active_workspace().get_number()
	secondary_monitor_workspace = get_first_workspace() if is_workspaces_only_on_primary() else get_active_workspace()
	secondary = monitors.get_primary(workspace=secondary_monitor_workspace).next()
	if secondary:
		serialized['secondary'] = secondary.to_json()
		serialized['secondary']['workspace'] = secondary_monitor_workspace.get_number()

	for pipe in property_queues:
		pipe['queue'].put(serialized)


def start_pipes():
	for pipe in property_queues:
		if not os.path.exists(pipe_path(pipe)):
			os.mkfifo(pipe_path(pipe))
		Thread(target=property_writer(pipe), daemon=True).start()


def property_writer(pipe):
	def write_property_to_pipe():
		while True:
			serialized = pipe['queue'].get()
			with open(pipe_path(pipe), 'w') as f:
				prop = serialized[pipe['object']][pipe['property']]
				f.write(str(prop) + '\n')
				f.flush()
	return write_property_to_pipe


def pipe_path(pipe: Dict):
	return '/tmp/' + pipe['name']


def is_connected():
	return status_icon


def unload():
	if notification:
		notification.close()


def show_monitor(monitor: Monitor):
	html = ''
	count = 0
	while monitor:
		html += '<b>{}</b>: <b>{}</b> <i>nmaster</i>: <b>{}</b>'.format(
			1 if monitor.primary else 2, monitor.function_key, monitor.nmaster)
		count += 1
		monitor = monitor.next()
		if monitor:
			html += '\r'
	workspace_number: int = get_active_workspace().get_number()
	show(summary='pocoy - workspace {}'.format(workspace_number), body=html, icon='pocoy')


def show(summary: str = 'pocoy', body: str = None, icon: str = 'pocoy'):
	if notification:
		notification.update(summary, body, icon)
		notification.show()


ICONNAME = 'pocoy'
ICON_STYLES_MAP = {'dark': "Dark icon", 'light': "Light icon"}
status_icon = None
notification = None
property_queues = [
	{'name': 'pocoy-primary-workspace',   'object': 'primary',   'property': 'workspace', 'queue': queue.Queue()},
	{'name': 'pocoy-primary-layout',      'object': 'primary',   'property': 'function', 'queue': queue.Queue()},
	{'name': 'pocoy-primary-nmaster',     'object': 'primary',   'property': 'nmaster', 'queue': queue.Queue()},
	{'name': 'pocoy-secondary-workspace', 'object': 'secondary', 'property': 'workspace', 'queue': queue.Queue()},
	{'name': 'pocoy-secondary-layout',    'object': 'secondary', 'property': 'function', 'queue': queue.Queue()},
	{'name': 'pocoy-secondary-nmaster',   'object': 'secondary', 'property': 'nmaster', 'queue': queue.Queue()}
]
