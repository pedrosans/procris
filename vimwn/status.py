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
from gi.repository import Gtk, Gdk, Keybinder

class NavigatorStatus(Gtk.StatusIcon):

	def __init__(self, configurations):
		Gtk.StatusIcon.__init__(self)
		self.configurations = configurations

		self.set_from_icon_name("gvim")
		self.set_tooltip_text("vimwn tooltip")

		menu = Gtk.Menu()

		self.autostart_item = Gtk.CheckMenuItem(label="Autostart")
		self.autostart_item.set_active(self.configurations.is_autostart())
		self.autostart_item.connect("toggled", self._change_autostart)
		self.autostart_item.show()
		menu.append(self.autostart_item)

		quit_item = Gtk.MenuItem(label="Quit")
		quit_item.connect("activate", self._quit)
		quit_item.show()
		menu.append(quit_item)

		self.connect("popup-menu", self._popup_menu, menu)
		self.set_visible(True)

	def _popup_menu(self, status_icon, button, activate_time, menu):
		menu.popup(None, None, Gtk.StatusIcon.position_menu, status_icon, button, activate_time)

	def _change_autostart(self, data):
		self.configurations.set_autostart(self.autostart_item.get_active())

	def _quit(self, data):
		Gtk.main_quit()
