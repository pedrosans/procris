"""
Copyright 2017 Pedro Santos

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

import gi
import procris.state as configurations
import procris.layout
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk
from gi.repository import AppIndicator3

ICONNAME = 'procris'
ICON_STYLES = ('default', 'light', 'dark')
ICON_STYLE_NAME_MAP = {'dark': "Dark icon", 'light': "Light icon", 'default': "Default icon"}


class StatusIcon:

	autostart_item: Gtk.CheckMenuItem = None

	def __init__(self, layout, stop_function=None):
		# Track reloading routine to stop any layout side effect when updating the UI
		self._reloading = False
		self.stop_function = stop_function
		self.layout: procris.Layout = layout
		self.menu = Gtk.Menu()

		self.autostart_item = Gtk.CheckMenuItem(label="Autostart")
		self.autostart_item.set_active(configurations.is_autostart())
		self.autostart_item.connect("toggled", self._change_autostart)
		self.autostart_item.show()
		self.menu.append(self.autostart_item)

		self.decorations_item = Gtk.CheckMenuItem(label="Remove decorations")
		self.decorations_item.connect("toggled", self._change_decorations)
		self.decorations_item.show()
		self.menu.append(self.decorations_item)

		# ICON COLOR MENU
		appearance_menu_item = Gtk.MenuItem(label="Appearance")
		appearance_menu_item.show()
		self.menu.append(appearance_menu_item)

		self.icons_submenu = Gtk.Menu()
		appearance_menu_item.set_submenu(self.icons_submenu)

		for icon_style in ICON_STYLES:
			icon_item = Gtk.RadioMenuItem(
				label=ICON_STYLE_NAME_MAP[icon_style],
				group=self.icons_submenu.get_children()[0] if self.icons_submenu.get_children() else None)
			icon_item.icon_style = icon_style
			icon_item.connect("toggled", self._change_icon)
			icon_item.show()
			self.icons_submenu.append(icon_item)

		# LAYOUT MENU
		layout_menu_item = Gtk.MenuItem(label="Layout")
		layout_menu_item.show()
		self.menu.append(layout_menu_item)

		self.layout_submenu = Gtk.Menu()
		layout_menu_item.set_submenu(self.layout_submenu)

		for function_key in procris.layout.FUNCTIONS_MAP.keys():
			name = procris.layout.FUNCTIONS_NAME_MAP[function_key]
			menu_item = Gtk.RadioMenuItem(
				label=name, group=self.layout_submenu.get_children()[0] if self.layout_submenu.get_children() else None)
			menu_item.function_key = function_key
			menu_item.connect("toggled", self._change_layout)
			menu_item.show()
			self.layout_submenu.append(menu_item)

		no_layout_opt = Gtk.RadioMenuItem(label='None', group=self.layout_submenu.get_children()[0])
		no_layout_opt.function_key = None
		no_layout_opt.connect("toggled", self._change_layout)
		no_layout_opt.show()
		self.layout_submenu.append(no_layout_opt)

		# QUIT MENU
		quit_item = Gtk.MenuItem(label="Quit")
		quit_item.connect("activate", self._quit)
		quit_item.show()
		self.menu.append(quit_item)

	def activate(self):
		self.decorations_item.set_active(configurations.is_remove_decorations())
		self.ind = AppIndicator3.Indicator.new("procris", ICONNAME, AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
		self.ind.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
		self.ind.set_menu(self.menu)
		self.reload()

	def reload(self):
		self._reloading = True

		iconname = configurations.get_icon()

		for item in self.icons_submenu.get_children():
			item.set_active(item.icon_style == iconname)

		for item in self.layout_submenu.get_children():
			item.set_active(item.function_key == self.layout.get_function_key())

		sys_icon = 'procris'
		function_key = self.layout.get_function_key()
		if function_key:
			sys_icon = sys_icon + '-' + function_key
		if iconname == "dark" or iconname == "light":
			sys_icon = sys_icon + '-' + iconname
		self.ind.set_icon(sys_icon)

		self._reloading = False

	#
	# CALLBACKS
	#
	def _change_layout(self, radio_menu_item):
		if not self._reloading and radio_menu_item.get_active():
			function_key = radio_menu_item.function_key
			self.layout.set_function(function_key)
			self.reload()

	def _change_icon(self, radio_menu_item):
		if not self._reloading and radio_menu_item.get_active():
			configurations.set_icon(radio_menu_item.icon_style)
			self.reload()

	def _change_autostart(self, data):
		configurations.set_autostart(self.autostart_item.get_active())

	def _change_decorations(self, data):
		to_remove = self.decorations_item.get_active()
		configurations.set_remove_decorations(to_remove)
		self.layout.windows.read_default_screen()
		self.layout.windows.apply_decoration_config()

	def _quit(self, data):
		self.stop_function()
