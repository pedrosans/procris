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
#map <F2> :!sh -xc './bin/vimwn --open'<CR>
#TODO don't allow the entry to loose it focus
import gi, io
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango

COLUMNS = 100
BUFFER_COLUMNS = COLUMNS - 5

class NavigatorWindow(Gtk.Window):

	def __init__(self, controller, windows):
		Gtk.Window.__init__(self, title="vimwn")

		self.controller = controller
		self.windows = windows
		self.set_size_request(self.controller.configurations.get_width(), -1)

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

		self.windows_list_box = Gtk.Box(homogeneous=False, spacing=0)
		self.v_box.pack_start(self.windows_list_box, expand=True, fill=True, padding=0)

		self.status_box = Gtk.Box(homogeneous=False, spacing=0)
		self.status_box.set_name("status-line")
		self.v_box.pack_start(self.status_box, expand=True, fill=True, padding=0)

		self.entry = Gtk.Entry()
		self.entry.set_name("command-input")
		self.entry.set_overwrite_mode(True)
		self.v_box.pack_start(self.entry, expand=True, fill=True, padding=0)

		self.connect("realize", self._on_window_realize)
		#self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
		self.connect("size-allocate", self.on_size)

	def get_command(self):
		return self.entry.get_text()[1:]

	def set_command(self, cmd):
		self.entry.set_text(':'+cmd)
		self.entry.set_position(len(self.entry.get_text()))

	def hint(self, hints, higlight_index, placeholder):
		self.status_box.get_style_context().add_class('hint-status-line')
		for c in self.status_box.get_children(): c.destroy()
		width = 0
		for hint in hints:
			truncated_hint = (hint[:50] + '..') if len(hint) > 75 else hint
			if width + len(hint) + 2 < COLUMNS:
				self.add_status_text(truncated_hint, hints.index(hint) == higlight_index)
				self.add_status_text('  ', False)
				width += len(hint) + 2
			else:
				self.add_status_text('>', False)
				break
		self.set_command(placeholder)
		self.status_box.pack_start(Gtk.Box(), expand=True, fill=True, padding=0)
		self.v_box.show_all()

	def add_status_text(self, text, highlight):
		l = Gtk.Label(text)
		l.get_style_context().add_class('status-text')
		if highlight:
			l.set_name('hint-higlight')
		self.status_box.pack_start(l, expand=False, fill=False, padding=0)

	def clear_hints(self):
		self.status_box.get_style_context().remove_class('hint-status-line')
		for c in self.status_box.get_children(): c.destroy()
		if not self.controller.listing_windows:
			self.add_status_text(' ', False)
		self.v_box.show_all()

	def on_size(self, allocation, data):
		self._move_to_preferred_position()

	def _move_to_preferred_position(self):
		geo = self.get_monitor_geometry()
		wid, hei = self.get_size()
		midx = geo.x + geo.width / 2 - wid / 2
		if self.controller.configurations.get_position() == 'center':
			midy = geo.y + geo.height / 2- hei
		elif self.controller.configurations.get_position() == 'top':
			midy = geo.y
		else:
			midy = geo.y + geo.height - hei
		self.move(midx, midy)

	def get_monitor_geometry(self):
		display = self.get_display()
		screen, x, y, modifiers = display.get_pointer()
		monitor_nr = screen.get_monitor_at_point(x, y)
		return screen.get_monitor_workarea(monitor_nr)

	def show( self, event_time ):
		for c in self.output_box.get_children(): c.destroy()
		for c in self.windows_list_box.get_children(): c.destroy()
		self.clear_hints()
		#self.hint(['debug', 'debuggreedy', 'delcommand', 'delete'], 1, 'b Term')

		if self.windows.active:
			self.populate_navigation_options()
		if self.controller.listing_windows:
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

		start_position = self.windows.x_line.index(self.windows.active)
		length = len(self.windows.x_line)
		for window in self.windows.x_line:
			column_box = Gtk.VBox(homogeneous=False, spacing=0)
			column_box.set_valign(Gtk.Align.CENTER)
			column_box.pack_start(WindowBtn(self.controller, window), expand=False, fill=False, padding=2)

			multiplier = (length + self.windows.x_line.index(window) - start_position) % len(self.windows.x_line)
			navigation_hint = Gtk.Label("." if multiplier == 0 else str(multiplier) + "w")
			#TODO rename to window-index
			navigation_hint.get_style_context().add_class("navigation_hint")
			column_box.pack_start(navigation_hint, expand=False, fill=False, padding=0)

			line.pack_start(column_box, expand=False, fill=False, padding=4)

	def list_windows(self, time):
		lines = Gtk.VBox();
		self.windows_list_box.pack_start(lines, expand=True, fill=True, padding=10)
		for window in self.windows.buffers:
			line = Gtk.HBox(homogeneous=False, spacing=0)
			lines.pack_start(line, expand=False, fill=True, padding=1)

			icon = Gtk.Image()
			icon.set_from_pixbuf( window.get_mini_icon() )
			icon.set_valign(Gtk.Align.START)
			line.pack_start(icon, expand=False, fill=True, padding=0)

			index = 1 + self.windows.buffers.index(window)
			WINDOW_COLUMN = BUFFER_COLUMNS - 16
			window_name = window.get_name().ljust(WINDOW_COLUMN)[:WINDOW_COLUMN]
			name = '{:>2} '.format(index) + window_name + ' {:12}'.format(window.get_workspace().get_name().lower())

			label = Gtk.Label(name)
			label.set_valign(Gtk.Align.END)
			label.set_max_width_chars(BUFFER_COLUMNS)
			label.get_layout().set_ellipsize(Pango.EllipsizeMode.END)
			label.set_ellipsize(Pango.EllipsizeMode.END)
			label.get_style_context().add_class("window-label")
			if self.windows.active == window:
				label.get_style_context().add_class("active-window-label")
			line.pack_start(label, expand=False, fill=False, padding=0)

	def _render_command_line(self):
		self.entry.set_text("")
		self.entry.get_style_context().remove_class('error-message')
		self.entry.get_style_context().add_class('input-ready')

		if self.controller.reading_command is True:
			self.entry.set_can_focus(True)
			self.entry.grab_focus()
			self.entry.set_position(0)
		else:
			self.entry.set_can_focus(False)
			self.entry.hide()
			if self.controller.status_message:
				self.entry.set_text(self.controller.status_message)
				if self.controller.status_level == 'error':
					self.entry.get_style_context().add_class('error-message')
					self.entry.get_style_context().remove_class('input-ready')
				else:
					self.entry.set_position(-1)

	def _on_window_realize(self, widget):
		css_file = self.controller.configurations.get_css_file()
		print(css_file)
		if css_file:
			f = open(css_file, 'r')
			s = f.read()
			f.close()
			css_provider = Gtk.CssProvider()
			css_provider.load_from_data(bytes(s, 'utf-8'))
			Gtk.StyleContext.add_provider_for_screen(
				self.get_screen(), css_provider,
				Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
			)
		else:
			gtk_3_18_style_provider = Gtk.CssProvider()
			gtk_3_18_style_provider.load_from_data(GTK_3_18_CSS)
			Gtk.StyleContext.add_provider_for_screen(
				self.get_screen(),
				gtk_3_18_style_provider,
				Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
			)
			if Gtk.get_major_version() >= 3 and Gtk.get_minor_version() >= 20:
				gtk_3_20_style_provider = Gtk.CssProvider()
				gtk_3_20_style_provider.load_from_data(GTK_3_20_CSS)
				Gtk.StyleContext.add_provider_for_screen(
					self.get_screen(),
					gtk_3_20_style_provider,
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

#	font-size: small;
GTK_3_18_CSS = b"""
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
	padding: 0;
	margin: 0;
}
#vimwn-title {
	background: @bg_color;
	font-weight : bold;
	font-family: sans;
	font-size: 10px;
}
.navigation_hint {
	border: none;
	padding: 2px 0;
	margin: 0;
	font-family: monospace;
}
.window-btn{
	padding: 4px;
	border: 1px solid transparent;
	border-radius: 4px;
	background: @bg_color;
}
.window-btn:hover {
	background: @selected_bg_color;
}
.active-btn{
}
.window-label{
}
.active-window-label{
	font-weight : bold;
}
#status-line {
	border: none;
	font-family: monospace;
}
.status-text{
	border: none;
	padding: 2px 0;
	margin: 0;
}
.hint-status-line {
	background: lighter(@fg_color);
	color: @bg_color;
}
#hint-higlight {
	background: darker(@fg_color);
}
#command-input {
	border: none;
	font-family: monospace;
	padding: 2px;
	margin: 0;
}
.input-ready{
	background: @bg_color;
}
.error-message{
	background: red;
	color: white;
}
"""
GTK_3_20_CSS = b"""
* {
	min-height: initial;
}
"""
