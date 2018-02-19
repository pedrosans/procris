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


class NavigatorWindow(Gtk.Window):

	def __init__(self, controller, windows):
		Gtk.Window.__init__(self, title="vimwn")

		self.columns = 100

		self.controller = controller
		self.windows = windows
		self.single_line_view = True
		self.show_app_name = False

		self.set_keep_above(True)
		self.set_skip_taskbar_hint(True)
		self.set_decorated(False)
		self.set_redraw_on_allocate(True)
		self.set_resizable(False)
		self.set_type_hint(Gdk.WindowTypeHint.UTILITY)

		self.v_box = Gtk.VBox()
		self.add(self.v_box)

		if self.show_app_name:
			title = Gtk.Label("vimwn ")
			title.set_name("vimwn-title")
			title.set_halign(Gtk.Align.END)
			self.v_box.pack_start(title, expand=False, fill=False, padding=2)

		self.output_box = Gtk.Box(homogeneous=False, spacing=0)
		self.v_box.pack_start(self.output_box, expand=True, fill=True, padding=0)

		self.windows_list_box = Gtk.Box(homogeneous=False, spacing=0)
		self.v_box.pack_start(self.windows_list_box, expand=True, fill=True, padding=0)

		self.status_box = StatusBox()
		self.v_box.pack_start(self.status_box, expand=True, fill=True, padding=0)

		self.entry = Gtk.Entry()
		self.entry.get_style_context().add_class('command-input')
		self.entry.set_overwrite_mode(True)
		self.v_box.pack_start(self.entry, expand=True, fill=True, padding=0)

		self.connect("realize", self._on_window_realize)
		self.connect("size-allocate", self._move_to_preferred_position)

	def _move_to_preferred_position(self, allocation, data):
		geo = self.get_monitor_geometry()
		wid, hei = self.get_size()
		midx = geo.x + geo.width / 2 - wid / 2
		if self.controller.configurations.get_position() == 'top':
			self.set_gravity(Gdk.Gravity.NORTH_WEST)
			midy = geo.y
		elif self.controller.configurations.get_position() == 'center':
			self.set_gravity(Gdk.Gravity.SOUTH_WEST)
			midy = geo.y + geo.height / 2
		else:
			self.set_gravity(Gdk.Gravity.SOUTH_WEST)
			midy = geo.y + geo.height
		self.move(midx, midy)

	def hint(self, hints, higlight_index, placeholder):
		self.status_box.show(hints, higlight_index)
		if placeholder:
			self.set_command(placeholder)

	def get_command(self):
		return self.entry.get_text()[1:]

	def set_command(self, cmd):
		self.entry.set_text(':'+cmd)
		self.entry.set_position(len(self.entry.get_text()))

	def clear_state(self):
		width_config = self.controller.configurations.get_width()
		if '100%' == width_config:
			self.window_width = self.get_monitor_geometry().width
		else:
			self.window_width = int(width_config)
		self.set_size_request(self.window_width, -1)

		for c in self.output_box.get_children(): c.destroy()
		for c in self.windows_list_box.get_children(): c.destroy()
		self.clear_hints_state()

		self.v_box.show_all()

	def clear_hints_state(self):
		self.status_box.clear_state()
		if not self.controller.listing_windows:
			self.status_box.add_status_text(' ', False)
		self.v_box.show_all()

	def calculate_width(self):
		layout = self.entry.create_pango_layout("W")
		layout.set_font_description(self.entry.get_style_context().get_font(Gtk.StateFlags.NORMAL))
		char_size = layout.get_pixel_extents().logical_rect.width
		self.columns = int(self.window_width / char_size)
		self.status_box.page_size = self.columns

	def get_monitor_geometry(self):
		display = self.get_display()
		screen, x, y, modifiers = display.get_pointer()
		monitor_nr = screen.get_monitor_at_point(x, y)
		return screen.get_monitor_workarea(monitor_nr)

	def show( self, event_time ):
		self.clear_state()

		if self.controller.listing_windows:
			self.list_windows(event_time)

		self._render_command_line()

		self.v_box.show_all()
		self.stick()
		self.present_with_time(event_time)
		self.calculate_width()

		if self.windows.active:
			if self.single_line_view:
				self.list_navigation_windows()
			else:
				self.populate_navigation_options()

		self.v_box.show_all()
		self.get_window().focus(event_time)

	def list_navigation_windows(self):
		if self.controller.reading_command or self.controller.listing_windows:
			return
		for c in self.status_box.get_children(): c.destroy()

		start_position = self.windows.x_line.index(self.windows.active)
		length = len(self.windows.x_line)
		for window in self.windows.x_line:
			name = window.get_name()
			name = truncated_hint = (name[:8] + '..') if len(name) > 10 else name

			multiplier = (length + self.windows.x_line.index(window) - start_position) % len(self.windows.x_line)
			nav_index = "" if multiplier == 0 else str(multiplier) + "w "
			nav_index += '' + name
			self.status_box.add_status_icon(window, multiplier == 0)
			self.status_box.add_status_text(' ', multiplier == 0)
			self.status_box.add_status_text(nav_index, multiplier == 0)
			self.status_box.add_status_text(' ', False)


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
			navigation_hint.get_style_context().add_class('window-relative-number')
			column_box.pack_start(navigation_hint, expand=False, fill=False, padding=0)

			line.pack_start(column_box, expand=False, fill=False, padding=4)

	def list_windows(self, time):
		buffer_columns = self.columns - 4
		lines = Gtk.VBox();
		self.windows_list_box.pack_start(lines, expand=True, fill=True, padding=10)
		top, below = self.windows.get_top_two_windows()
		for window in self.windows.buffers:
			line = Gtk.HBox(homogeneous=False, spacing=0)
			lines.pack_start(line, expand=False, fill=True, padding=1)

			icon = Gtk.Image()
			icon.set_from_pixbuf( window.get_mini_icon() )
			icon.get_style_context().add_class('application-icon')
			#icon.set_valign(Gtk.Align.START)
			line.pack_start(icon, expand=False, fill=True, padding=1)

			index = 1 + self.windows.buffers.index(window)
			WINDOW_COLUMN = buffer_columns - 19
			window_name = window.get_name()
			window_name = window_name.ljust(WINDOW_COLUMN)[:WINDOW_COLUMN]
			flags = ''
			if window is top:
				flags += 'a'
			elif window is below:
				flags = '#'
			name = '{:>2} {:2} {} {:12}'.format(index, flags, window_name, window.get_workspace().get_name().lower())

			label = Gtk.Label(name)
			label.set_valign(Gtk.Align.END)
			label.set_max_width_chars(buffer_columns)
			label.get_layout().set_ellipsize(Pango.EllipsizeMode.END)
			label.set_ellipsize(Pango.EllipsizeMode.END)
			label.get_style_context().add_class('buffer-description')
			if self.windows.active == window:
				label.get_style_context().add_class('active-buffer-description')
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
		self.connect("clicked", self.on_clicked)

	def on_clicked(self, btn):
		self.window.activate_transient(self.controller.get_current_event_time())

class StatusBox(Gtk.Box):

	def __init__(self):
		Gtk.Box.__init__(self, homogeneous=False, spacing=0)
		self.get_style_context().add_class('status-line')
		self.page_size = -1
		self.page_items = 0

	def clear_state(self):
		self.page_items = 0
		for c in self.get_children(): c.destroy()

	def add_status_text(self, text, highlight):
		if self.page_items + len(text) > self.page_size:
			return
		l = Gtk.Label(text)
		l.get_style_context().add_class('status-text')
		if highlight:
			l.get_style_context().add_class('hint-highlight')
		self.pack_start(l, expand=False, fill=False, padding=0)
		self.page_items += len(text)

	def add_status_icon(self, window, highlight):
		if self.page_items + 2 > self.page_size:
			return
		icon = Gtk.Image()
		icon.get_style_context().add_class('application-icon')
		icon.get_style_context().add_class('status-application-icon')
		icon.set_from_pixbuf( window.get_mini_icon() )
		if highlight:
			icon.get_style_context().add_class('hint-highlight')
		self.pack_start(icon, expand=False, fill=False, padding=0)
		self.page_items += 2

	def show(self, hints, higlight_index):
		self.clear_state()
		width = 0
		for hint in hints:
			truncated_hint = (hint[:50] + '..') if len(hint) > 75 else hint
			if width + len(hint) + 2 < self.page_size:
				self.add_status_text(truncated_hint, hints.index(hint) == higlight_index)
				self.add_status_text('  ', False)
				width += len(hint) + 2
			else:
				self.add_status_text('>', False)
				break
		self.show_all()

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
	transition-property: initial;
	transition-duration: initial;
	transition-timing-function: initial;
	transition-delay: initial;
	padding: 0;
	margin: 0;
	background: @fg_color;
	color: @bg_color;
	font-family: 'DroidSansMono Nerd Font Mono', monospace;
}
.application-icon{
	padding: 0 1px;
	border: none;
}
#vimwn-title {
	background: @bg_color;
	font-weight : bold;
	font-family: sans;
	font-size: 10px;
}

/* WINDOW BUTTON */
.window-relative-number {
	border: none;
	padding: 2px 0;
}
.window-btn{
	padding: 4px;
	border: 1px solid transparent;
	border-radius: 4px;
}

/* BUFFERS LIST */
.buffer-description{
}
.active-buffer-description{
}

/* STATUS LINE STYLE */
.status-line {
	border: none;
	background: lighter(@fg_color);
}
.status-text{
	border: none;
	padding: 2px 0;
	background: lighter(@fg_color);
}
.status-application-icon {
	background: lighter(@fg_color);
}
.hint-highlight {
	background: darker(@fg_color);
}

/* COMMAND LINE STYLE */
.command-input {
	border: none;
	padding: 2px;
}
.input-ready{
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
