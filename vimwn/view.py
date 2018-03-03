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
import gi, io
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango

#TODO show 'no name' active buffer if no active window at the buffers list
class NavigatorWindow(Gtk.Window):

	def __init__(self, controller, windows):
		Gtk.Window.__init__(self, title="vimwn")

		self.columns = 100

		self.controller = controller
		self.windows = windows
		self.single_line_view = self.controller.configurations.is_compact_interface()
		self.show_app_name = False

		self.set_keep_above(True)
		self.set_skip_taskbar_hint(True)
		self.set_decorated(False)
		self.set_redraw_on_allocate(True)
		self.set_resizable(False)
		self.set_type_hint(Gdk.WindowTypeHint.UTILITY)

		self.v_box = Gtk.VBox()
		self.add(self.v_box)

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
		self.set_gravity(Gdk.Gravity.NORTH_WEST)
		self.set_size_request(0, 0)

	def hint(self, hints, higlight_index, comple_command):
		"""
		Show hints of a command or paramter based on the
		hints array, plus auto complete the current input
		if any comple command
		"""
		self.status_box.show(hints, higlight_index)
		if comple_command:
			self.set_command(comple_command)

	def clear_hints_state(self):
		"""
		Clear the status line and renders it again, so
		any change in the hints listing can be shown
		"""
		self.status_box.clear_status_line()
		if not self.controller.listing_windows:
			self.status_box.add_status_text(' ', False)
		self.status_box.show_all()

	def get_command(self):
		return self.entry.get_text()[1:]

	def set_command(self, cmd):
		self.entry.set_text(':'+cmd)
		self.entry.set_position(len(self.entry.get_text()))

	def get_monitor_geometry(self):
		display = self.get_display()
		screen, x, y, modifiers = display.get_pointer()
		monitor_nr = screen.get_monitor_at_point(x, y)
		return screen.get_monitor_workarea(monitor_nr)

	def show(self, event_time ):
		for c in self.output_box.get_children(): c.destroy()
		for c in self.windows_list_box.get_children(): c.destroy()

		self.present_with_time(event_time)
		self._calculate_width()
		self.clear_hints_state()

		if self.controller.listing_windows:
			self.list_windows(event_time)

		self._render_command_line()

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
		for window in self.windows.x_line:
			name = window.get_name()
			name = ' ' + ((name[:8] + '..') if len(name) > 10 else name)
			position = self._navigation_index(window)
			if window is not self.windows.active:
				position = ' ' + position
			active = window is self.windows.active
			self.status_box.add_status_icon(window, active)
			self.status_box.add_status_text(position, active)
			self.status_box.add_status_text(name, active)
			self.status_box.add_status_text(' ', False)

	def populate_navigation_options(self):
		line = Gtk.HBox(homogeneous=False, spacing=0);
		line.set_halign(Gtk.Align.CENTER)
		self.output_box.pack_start(line, expand=True, fill=True, padding=0)

		for window in self.windows.x_line:
			column_box = Gtk.VBox(homogeneous=False, spacing=0)
			column_box.set_valign(Gtk.Align.CENTER)
			column_box.pack_start(WindowBtn(self.controller, window), expand=False, fill=False, padding=2)

			navigation_hint = Gtk.Label(self._navigation_index(window))
			navigation_hint.get_style_context().add_class('window-relative-number')
			column_box.pack_start(navigation_hint, expand=False, fill=False, padding=0)

			line.pack_start(column_box, expand=False, fill=False, padding=4)

	def list_windows(self, time):
		buffer_columns = min(100, self.columns - 3)
		lines = Gtk.VBox();
		self.windows_list_box.pack_start(lines, expand=True, fill=True, padding=0)
		top, below = self.windows.get_top_two_windows()
		for window in self.windows.buffers:
			line = Gtk.HBox(homogeneous=False, spacing=0)
			lines.pack_start(line, expand=False, fill=True, padding=0)

			icon = Gtk.Image()
			icon.set_from_pixbuf( window.get_mini_icon() )
			icon.get_style_context().add_class('application-icon')
			line.pack_start(icon, expand=False, fill=True, padding=0)

			flags = ''
			if window is top:
				flags += '%a'
			elif window is below:
				flags = '#'
			index = 1 + self.windows.buffers.index(window)
			description_columns = buffer_columns - 19
			window_name = window.get_name().ljust(description_columns)[:description_columns]
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

	def _navigation_index(self, window):
		length = len(self.windows.x_line)
		start_position = self.windows.x_line.index(self.windows.active)
		multiplier = (length + self.windows.x_line.index(window) - start_position) % len(self.windows.x_line)
		if multiplier == 0:
			return ''
		if multiplier == 1:
			return 'w'
		else:
			return str(multiplier) + 'w'

	def _calculate_width(self):
		width_config = self.controller.configurations.get_width()
		if '100%' == width_config:
			self.window_width = self.get_monitor_geometry().width
		else:
			self.window_width = int(width_config)
		self.set_size_request(self.window_width, -1)

		layout = self.entry.create_pango_layout("W")
		layout.set_font_description(self.entry.get_style_context().get_font(Gtk.StateFlags.NORMAL))
		char_size = layout.get_pixel_extents().logical_rect.width
		self.columns = int(self.window_width / char_size)
		self.status_box.page_size = self.columns

	def _move_to_preferred_position(self, allocation, data):
		geo = self.get_monitor_geometry()
		wid, hei = self.get_size()
		midx = geo.x + geo.width / 2 - wid / 2
		if self.controller.configurations.get_position() == 'top':
			midy = geo.y
		elif self.controller.configurations.get_position() == 'center':
			midy = geo.y + geo.height / 2 - hei
		else:
			midy = geo.y + geo.height - hei
		#print('m1: h {} y {} hei {}'.format(geo.height, geo.y, hei))
		self.move(midx, midy)

	def _on_window_realize(self, widget):
		css_file = self.controller.configurations.get_css_file()
		try:
			f = open(css_file, 'r')
		except:
			f = None
		if css_file and f:
			s = f.read()
			self.apply_css(bytes(s, 'utf-8'))
			f.close()
		else:
			self.apply_css(GTK_3_18_CSS)
			if Gtk.get_major_version() >= 3 and Gtk.get_minor_version() >= 20:
				self.apply_css(GTK_3_20_CSS)

	def apply_css(self, css):
		provider = Gtk.CssProvider()
		provider.load_from_data(css)
		Gtk.StyleContext.add_provider_for_screen(self.get_screen(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

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

#TODO rename to status line
class StatusBox(Gtk.Box):

	def __init__(self):
		Gtk.Box.__init__(self, homogeneous=False, spacing=0)
		self.get_style_context().add_class('status-line')
		self.page_size = -1
		self.page_items = 0

	def clear_status_line(self):
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
		self.clear_status_line()
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
	font-family: monospace;
}
.application-icon{
	padding: 0 1px;
	border: none;
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
