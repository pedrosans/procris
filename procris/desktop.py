import procris.layout
import procris.state as state
import xdg.IconTheme
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
gi.require_version('Notify', '0.7')
from procris import state as configurations
from gi.repository import Notify, Gtk, GLib, GdkPixbuf, AppIndicator3
from procris.wm import Monitor, get_active_workspace, UserEvent


class StatusIcon:

	app_indicator: AppIndicator3.Indicator
	autostart_item: Gtk.CheckMenuItem = Gtk.CheckMenuItem(label="Autostart")
	decorations_item: Gtk.CheckMenuItem  = Gtk.CheckMenuItem(label="Remove decorations")
	icons_submenu = Gtk.Menu()
	layout_submenu = Gtk.Menu()
	# Track reloading routine to stop any layout side effect when updating the UI
	_reloading = False

	def __init__(self, layout, stop_function=None):
		self.stop_function = stop_function
		self.layout: procris.layout.Layout = layout
		self.menu = Gtk.Menu()

		self.autostart_item.connect("toggled", self._change_autostart)
		self.menu.append(self.autostart_item)

		self.decorations_item.connect("toggled", self._change_decorations)
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

		for function_key in procris.layout.FUNCTIONS_MAP.keys():
			function = procris.layout.FUNCTIONS_MAP[function_key]
			name = function.__name__ if function else 'none'
			menu_item = Gtk.RadioMenuItem(
				label=name,
				group=self.layout_submenu.get_children()[0] if self.layout_submenu.get_children() else None)
			menu_item.function_key = function_key
			menu_item.connect("toggled", self._change_layout)
			self.layout_submenu.append(menu_item)

		self.menu.append(layout_menu_item)

	def activate(self):
		self.decorations_item.set_active(configurations.is_remove_decorations())
		self.autostart_item.set_active(configurations.is_autostart())

		self.app_indicator = AppIndicator3.Indicator.new("procris", ICONNAME, AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
		self.app_indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
		self.app_indicator.set_menu(self.menu)
		self.menu.show_all()
		self.reload()

	def reload(self):
		self._reloading = True

		iconname = configurations.get_desktop_icon()
		function_key = self.layout.get_active_primary_monitor().function_key

		for item in self.icons_submenu.get_children():
			item.set_active(item.icon_style == iconname)

		for item in self.layout_submenu.get_children():
			item.set_active(item.function_key == function_key)

		sys_icon = 'procris'
		if function_key:
			sys_icon = sys_icon + '-' + function_key
		if iconname == "dark" or iconname == "light":
			sys_icon = sys_icon + '-' + iconname
		self.app_indicator.set_icon(sys_icon)

		self._reloading = False

	#
	# CALLBACKS
	#
	def _change_layout(self, radio_menu_item: Gtk.RadioMenuItem):
		if not self._reloading and radio_menu_item.get_active():
			function_key = radio_menu_item.function_key
			event = UserEvent(time=Gtk.get_current_event_time())
			event.parameters = [function_key]
			import procris.service as service
			service.call(self.layout.change_function, event)

	def _change_icon(self, radio_menu_item: Gtk.RadioMenuItem):
		if not self._reloading and radio_menu_item.get_active():
			configurations.set_desktop_icon(radio_menu_item.icon_style)
			self.reload()

	def _change_autostart(self, check_menu_item: Gtk.CheckMenuItem):
		configurations.set_autostart(check_menu_item.get_active())

	def _change_decorations(self, check_menu_item: Gtk.CheckMenuItem):
		to_remove = check_menu_item.get_active()
		configurations.set_remove_decorations(to_remove)
		self.layout.windows.read_default_screen()
		self.layout.windows.apply_decoration_config()

	def _quit(self, data):
		self.stop_function()


ICONNAME = 'procris'
ICON_STYLES_MAP = {'dark': "Dark icon", 'light': "Light icon"}

# https://lazka.github.io/pgi-docs/Notify-0.7/classes/Notification.html
# https://developer.gnome.org/notification-spec
IMAGE_PATHS = {
	'procris': xdg.IconTheme.getIconPath('procris', size=96),
	'procris-T': xdg.IconTheme.getIconPath('procris-T', size=96),
	'procris-B': xdg.IconTheme.getIconPath('procris-B', size=96),
}
IMAGES = {
	'procris': GdkPixbuf.Pixbuf.new_from_file(IMAGE_PATHS['procris']),
	'procris-T': GdkPixbuf.Pixbuf.new_from_file(IMAGE_PATHS['procris-T']),
	'procris-B': GdkPixbuf.Pixbuf.new_from_file(IMAGE_PATHS['procris-B']),
}


status_icon: StatusIcon = None
Notify.init('procris')
notification = Notify.Notification.new('Procris')
notification.set_app_name('procris')
notification.set_image_from_pixbuf(IMAGES['procris'])
notification.set_hint('resident', GLib.Variant.new_boolean(True))


def show_monitor(monitor: Monitor):
	if not state.is_desktop_notifications():
		return
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
	show(summary='Procris - workspace {}'.format(workspace_number), body=html, icon='procris')


def show(summary: str = 'Procris', body: str = None, icon: str = 'procris'):
	if not state.is_desktop_notifications():
		return
	notification.update(summary, body, icon)
	notification.show()


def connect():
	import procris.service
	global status_icon
	status_icon = StatusIcon(procris.service.layout, stop_function=procris.service.stop)
	status_icon.activate()


def is_connected():
	return status_icon


def update():
	status_icon.reload()


def disconnect():
	notification.close()
