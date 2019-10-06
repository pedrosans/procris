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
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk
from gi.repository import AppIndicator3

ICONNAME = 'vimwn'


class StatusIcon:

	def __init__(self, service, configurations, layout_manager):
		self.service = service
		self.configurations = configurations
		self.layout_manager = layout_manager
		self.menu = Gtk.Menu()

		self.autostart_item = Gtk.CheckMenuItem(label="Autostart")
		self.autostart_item.set_active(self.configurations.is_autostart())
		self.autostart_item.connect("toggled", self._change_autostart)
		self.autostart_item.show()
		self.menu.append(self.autostart_item)

		self.decorations_item = Gtk.CheckMenuItem(label="Remove decorations")
		self.decorations_item.set_active(self.configurations.is_remove_decorations())
		self.decorations_item.connect("toggled", self._change_decorations)
		self.decorations_item.show()
		self.menu.append(self.decorations_item)

		self._add_appearance_menu()

		quit_item = Gtk.MenuItem(label="Quit")
		quit_item.connect("activate", self._quit)
		quit_item.show()
		self.menu.append(quit_item)

	def activate(self):
		self.ind = AppIndicator3.Indicator.new("vimwn", ICONNAME, AppIndicator3.IndicatorCategory.APPLICATION_STATUS )
		self.ind.set_status (AppIndicator3.IndicatorStatus.ACTIVE)
		self.ind.set_menu(self.menu)
		self.reload()

	def reload(self):
		iconname = self.configurations.get_icon()
		if iconname == "dark":
			self.ind.set_icon('vimwn-dark')
		elif iconname == "light":
			self.ind.set_icon('vimwn-light')
		else:
			self.ind.set_icon('vimwn')

	def _add_appearance_menu(self):
		appearance_menu_item = Gtk.MenuItem(label="Appearance")
		appearance_menu_item.show()
		self.menu.append(appearance_menu_item)

		icons_submenu = Gtk.Menu()
		self._add_icon_option(icons_submenu, "Dark icon")
		self._add_icon_option(icons_submenu, "Light icon")
		self._add_icon_option(icons_submenu, "Default icon")
		appearance_menu_item.set_submenu(icons_submenu)

	def _add_icon_option(self, icons_submenu, option):
		icon_item = Gtk.MenuItem(label=option)
		icon_item.connect("activate", self._change_icon)
		icon_item.show()
		icons_submenu.append(icon_item)

	def _change_icon(self, data):
		if data.get_label() == "Dark icon":
			self.configurations.set_icon('dark')
		elif data.get_label() == "Light icon":
			self.configurations.set_icon('light')
		else:
			self.configurations.set_icon('default')
		self.reload()

	def _change_autostart(self, data):
		self.configurations.set_autostart(self.autostart_item.get_active())

	def _change_decorations(self, data):
		to_remove = self.decorations_item.get_active()
		self.configurations.set_remove_decorations(to_remove)
		self.layout_manager.remove_decorations = to_remove
		self.layout_manager.apply_decoration_config()

	def _quit(self, data):
		self.service.stop()
