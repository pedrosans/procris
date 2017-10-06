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
from gi.repository import Gtk, Gdk, Pango

class NavigatorWindow(Gtk.Window):

	def __init__(self, controller, windows):
		Gtk.Window.__init__(self, title="vimwn")

		self.controller = controller
		self.windows = windows
		self.set_size_request(800, -1)

		self.set_keep_above(True)
		self.set_skip_taskbar_hint(True)
		self.set_decorated(False)
		self.set_redraw_on_allocate(True)
		self.set_resizable(False)
		self.set_type_hint(Gdk.WindowTypeHint.UTILITY)

		self.v_box = Gtk.VBox()
		self.add(self.v_box)

		title = Gtk.Label("vimwn ")
		title.set_name("vimwn-title")
		title.set_halign(Gtk.Align.END)
		self.v_box.pack_start(title, expand=False, fill=False, padding=2)

		self.output_box = Gtk.Box(homogeneous=False, spacing=0)
		self.v_box.pack_start(self.output_box, expand=True, fill=True, padding=0)

		self.entry = Gtk.Entry()
		self.entry.set_name("command-input")
		self.entry.set_overwrite_mode(True)
		self.entry.connect("activate", self.controller.on_command, None)
		self.v_box.pack_start(self.entry, expand=True, fill=True, padding=2)

		self.connect("realize", self._on_window_realize)
		self.connect("size-allocate", self.on_size)

	def on_size(self, allocation, data):
		self._move_to_bottom()

	def _move_to_bottom(self):
		display = self.get_display()
		screen, x, y, modifiers = display.get_pointer()
		monitor_nr = screen.get_monitor_at_point(x, y)
		geo = screen.get_monitor_geometry(monitor_nr)
		wid, hei = self.get_size()
		midx = geo.x + geo.width / 2 - wid / 2
		midy = geo.y + geo.height - hei
		self.move(midx, midy)

	def show( self, event_time ):
		for c in self.output_box.get_children():
			c.destroy()

		if self.controller.state == 'normal_mode':
			self.populate_navigation_options()
		elif self.controller.state == 'listing_windows':
			self.list_windows(event_time)

		self._render_command_line()

		self.v_box.show_all()
		self.stick()
		self.present_with_time(event_time)
		self.get_window().focus(event_time)

	def populate_navigation_options(self):
		line = Gtk.HBox(homogeneous=False, spacing=0);
		line.set_halign(Gtk.Align.CENTER)
		self.output_box.pack_start(line, expand=True, fill=True, padding=0)

		for window in self.windows.x_line:
			line.pack_start(WindowBtn(self.controller, window), expand=False, fill=False, padding=4)

	def list_windows(self, time):
		lines = Gtk.VBox();
		self.output_box.pack_start(lines, expand=True, fill=True, padding=10)
		for window in self.windows.buffers:
			line = Gtk.HBox(homogeneous=False, spacing=0)
			lines.pack_start(line, expand=False, fill=True, padding=1)

			icon = Gtk.Image()
			icon.set_from_pixbuf( window.get_mini_icon() )
			icon.set_valign(Gtk.Align.START)
			line.pack_start(icon, expand=False, fill=True, padding=0)

			index = self.windows.buffers.index(window)
			label = Gtk.Label(" " + str( index + 1 ) + " - " + window.get_name())
			label.set_valign(Gtk.Align.END)
			label.set_max_width_chars(80)
			label.get_layout().set_ellipsize(Pango.EllipsizeMode.END)
			label.set_ellipsize(Pango.EllipsizeMode.END)
			label.get_style_context().add_class("window-label")
			if self.windows.active == window:
				label.get_style_context().add_class("active-window-label")
			line.pack_start(label, expand=False, fill=False, padding=0)

	def _render_command_line(self):
		self.entry.set_text("")
		if self.controller.reading_command is True:
			self.entry.set_can_focus(True)
			self.entry.grab_focus()
		else:
			self.entry.set_can_focus(False)
			if self.controller.state == 'listing_windows':
				self.entry.set_text("Press ENTER or type command to continue")
				self.entry.set_position(-1)
			else:
				self.entry.hide()


	def _on_window_realize(self, widget):
		style_provider = Gtk.CssProvider()
		style_provider.load_from_data(CSS)

		Gtk.StyleContext.add_provider_for_screen(
			self.get_screen(),
			style_provider,
			Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
		)



class WindowBtn(Gtk.Button):
	def __init__(self, controller, window):
		Gtk.Button.__init__(self)
		self.get_style_context().add_class("window-btn")
		self.window = window
		self.controller = controller
		icon = Gtk.Image()
		icon.set_from_pixbuf( window.get_icon() )
		self.add(icon)
		if window is controller.windows.active:
			self.get_style_context().add_class("active-btn")
		self.connect("clicked", self.on_clicked)

	def on_clicked(self, btn):
		self.window.activate_transient(self.controller.get_current_event_time())


CSS = b"""
* {
	box-shadow: initial;
	border-top-style: initial;
	border-top-width: initial;
	border-left-style: initial;
	border-left-width: initial;
	border-bottom-style: initial;
	border-bottom-width: initial;
	border-right-style: initial;
	border-right-width: initial;
	border-top-left-radius: initial;
	border-top-right-radius: initial;
	border-bottom-right-radius: initial;
	border-bottom-left-radius: initial;
	outline-style: initial;
	outline-width: initial;
	outline-offset: initial;
	font-family: monospace;
	transition-property: initial;
	transition-duration: initial;
	transition-timing-function: initial;
	transition-delay: initial;
	engine: initial;
	gtk-key-bindings: initial;
}
#vimwn-title {
	background: @bg_color;
	font-weight : bold;
	font-family: sans;
	font-size: 10px;
}
.window-btn{
	padding: 4px;
	border: 1px dotted @border_color;
	border-radius: 4px;
	background: @bg_color;
}
.window-btn:hover {
	background: @selected_bg_color;
	border: 1px solid @border_color;
}
.active-btn{
	background: @selected_bg_color;
	border: 1px solid @border_color;
}
.window-label{
}
.active-window-label{
	font-weight : bold;
}
#command-input {
	background: @bg_color;
	border: none;
	font-family: monospace;
}
"""
