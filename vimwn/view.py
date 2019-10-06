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
from gi.repository import Gtk, Gdk, Pango, GLib
from vimwn.message import BufferName


# TODO show 'no name' active buffer if no active window at the buffers list
class NavigatorWindow(Gtk.Window):

	def show_warning(self, error):
		error_dialog = Gtk.MessageDialog(
			self, Gtk.DialogFlags.MODAL, Gtk.MessageType.WARNING,
			Gtk.ButtonsType.CLOSE, error, title="vimwn - warning")
		error_dialog.run()
		error_dialog.destroy()

	def show_error(self, error):
		error_dialog = Gtk.MessageDialog(
			self, Gtk.DialogFlags.MODAL, Gtk.MessageType.ERROR,
			Gtk.ButtonsType.CLOSE, error, title="vimwn error")
		error_dialog.run()
		error_dialog.destroy()

	def __init__(self, controller, windows, messages):
		Gtk.Window.__init__(self, title="vimwn")

		self.columns = 100

		self.controller = controller
		self.windows = windows
		self.messages = messages
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

		self.messages_box = Gtk.VBox(homogeneous=False, spacing=0)
		self.v_box.pack_start(self.messages_box, expand=True, fill=True, padding=0)

		self.hint_line = HintLine(self)
		self.v_box.pack_start(self.hint_line, expand=True, fill=True, padding=0)

		self.entry = Gtk.Entry()
		self.entry.get_style_context().add_class('command-input')
		self.entry.set_overwrite_mode(True)
		self.v_box.pack_start(self.entry, expand=True, fill=True, padding=0)

		self.connect("realize", self._on_window_realize)
		self.connect("size-allocate", self._move_to_preferred_position)
		self.set_size_request(0, 0)

	def hint(self, hints, highlight_index, auto_select_first_hint):
		"""
		Show hints of a command or paramter based on the
		hints array, plus auto complete the current input
		if any comple command
		"""
		self._calculate_width()
		self.hint_line.show(hints, highlight_index, auto_select_first_hint)

	def clean_hints(self):
		"""
		Clean the status line and render it again
		"""
		self.hint_line.clear_status_line()
		if not self.messages.list:
			self.hint_line.add_status_text(' ', False)
		self.hint_line.show_all()

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
		self.set_gravity(Gdk.Gravity.NORTH_WEST)
		for c in self.output_box.get_children(): c.destroy()
		for c in self.messages_box.get_children(): c.destroy()

		self._calculate_width()
		self.clean_hints()

		self.show_messages(event_time)

		self._render_command_line()

		if self.windows.active:
			if self.single_line_view:
				if not self.messages.list and not self.controller.in_command_mode():
					self.list_navigation_windows()
			else:
				self.populate_navigation_options()

		self.v_box.show_all()

	def list_navigation_windows(self):
		for c in self.hint_line.get_children(): c.destroy()
		for window in self.windows.line:
			name = window.get_name()
			name = ' ' + ((name[:8] + '..') if len(name) > 10 else name)
			position = self._navigation_index(window)
			if window is not self.windows.active:
				position = ' ' + position
			active = window is self.windows.active
			self.hint_line.add_status_icon(window, active)
			self.hint_line.add_status_text(position, active)
			self.hint_line.add_status_text(name, active)
			self.hint_line.add_status_text(' ', False)

	def populate_navigation_options(self):
		line = Gtk.HBox(homogeneous=False, spacing=0);
		line.set_halign(Gtk.Align.CENTER)
		self.output_box.pack_start(line, expand=True, fill=True, padding=0)

		for window in self.windows.line:
			column_box = Gtk.VBox(homogeneous=False, spacing=0)
			column_box.set_valign(Gtk.Align.CENTER)
			column_box.pack_start(WindowBtn(self.controller, window), expand=False, fill=False, padding=2)

			navigation_hint = Gtk.Label(self._navigation_index(window))
			navigation_hint.get_style_context().add_class('window-relative-number')
			column_box.pack_start(navigation_hint, expand=False, fill=False, padding=0)

			line.pack_start(column_box, expand=False, fill=False, padding=4)

	def show_messages(self, time):
		for message in self.messages.list:
			line = Gtk.HBox(homogeneous=False)
			self.messages_box.pack_start(line, expand=False, fill=True, padding=0)

			if isinstance(message, BufferName):
				icon = self.create_icon_image(message.get_window())
				line.pack_start(icon, expand=False, fill=True, padding=0)

			label = Gtk.Label(message.get_content(self.columns))
			label.set_valign(Gtk.Align.END)
			label.set_max_width_chars(self.columns)
			label.get_layout().set_ellipsize(Pango.EllipsizeMode.END)
			label.set_ellipsize(Pango.EllipsizeMode.END)
			if message.level is 'error':
				label.get_style_context().add_class('error-message')
			line.pack_start(label, expand=False, fill=False, padding=0)

	def _render_command_line(self):
		if self.controller.in_command_mode():
			self.entry.set_can_focus(True)
			self.entry.grab_focus()
			self.entry.set_text('')
			self.entry.set_position(0)
		else:
			self.entry.set_text(self.messages.command_placeholder)
			# self.entry.set_position(-1)
			self.entry.hide()
			self.entry.show()  # cause entry to lose focus
			self.entry.set_can_focus(False)

	def _navigation_index(self, window):
		length = len(self.windows.line)
		start_position = self.windows.line.index(self.windows.active)
		multiplier = (length + self.windows.line.index(window) - start_position) % len(self.windows.line)
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
		self.char_size = layout.get_pixel_extents().logical_rect.width
		self.columns = int(self.window_width / self.char_size)
		self.hint_line.page_size = self.columns

	def _move_to_preferred_position(self, allocation, data):
		geo = self.get_monitor_geometry()
		wid, hei = self.get_size()
		midx = geo.x + geo.width / 2 - wid / 2
		if self.controller.configurations.get_position() == 'top':
			midy = geo.y
		elif self.controller.configurations.get_position() == 'middle':
			midy = geo.y + geo.height / 2 - hei
		else:
			midy = geo.y + geo.height - hei

		if self.get_gravity() == Gdk.Gravity.SOUTH_WEST:
			midy += hei
		#print('m1: h {} y {} hei {}'.format(geo.height, geo.y, hei))
		self.move(midx, midy)

	def _on_window_realize(self, widget):
		try:
			self.apply_css(GTK_3_18_CSS)
		except GLib.GError as exc:
			self.apply_css(GTK_3_18_CSS.decode().replace('theme_fg_color', 'fg_color').encode())
		if Gtk.get_major_version() >= 3 and Gtk.get_minor_version() >= 20:
			self.apply_css(GTK_3_20_CSS)

		css_file_path = self.controller.configurations.get_css_file_path()
		try:
			with open(css_file_path, 'r') as custom_css:
				s = custom_css.read()
				self.apply_css(bytes(s, 'utf-8'))
		except FileNotFoundError:
			print('info: to customize the interface, create and edit the file {}'.format(css_file_path))

	def apply_css(self, css):
		provider = Gtk.CssProvider()
		provider.load_from_data(css)
		Gtk.StyleContext.add_provider_for_screen(self.get_screen(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

	def create_icon_image(self, window):
		icon = Gtk.Image()
		icon.set_from_pixbuf(window.get_mini_icon() if self.char_size < 14 else window.get_icon())
		icon.get_style_context().add_class('application-icon')
		return icon


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


class HintLine(Gtk.Box):

	def __init__(self, view):
		self.view = view
		Gtk.Box.__init__(self, homogeneous=False, spacing=0)
		self.get_style_context().add_class('status-line')
		self.page_size = -1
		self.page_items = 0

	def clear_status_line(self):
		self.page_items = 0
		for c in self.get_children(): c.destroy()

	def add_status_text(self, text, highlight, selected=False):
		if self.page_items + len(text) > self.page_size:
			return
		l = Gtk.Label(text)
		l.get_style_context().add_class('status-text')
		if highlight:
			l.get_style_context().add_class('hint-highlight')
		if selected:
			l.get_style_context().add_class('hint-selection')
		self.pack_start(l, expand=False, fill=False, padding=0)
		self.page_items += len(text)

	def add_status_icon(self, window, highlight):
		if self.page_items + 2 > self.page_size:
			return
		icon = self.view.create_icon_image(window)
		icon.get_style_context().add_class('status-application-icon')
		if highlight:
			icon.get_style_context().add_class('hint-highlight')
		self.pack_start(icon, expand=False, fill=False, padding=0)
		self.page_items += 2

	def show(self, hints, highlight_index, auto_select_first_hint):
		self.clear_status_line()
		for hint in hints:
			index = hints.index(hint)
			highlighted = index == highlight_index
			selected = index == 0 and auto_select_first_hint
			shown = highlight_index < index

			if self.page_items + len(hint) + 3 > self.page_size:
				if shown:
					if highlight_index == -1:
						self.add_status_text(' ' * (self.page_size - 1), False)
					self.add_status_text('>', False)
					break
				else:
					self.clear_status_line()
					self.add_status_text('< ' if highlight_index > 0 else '  ', False)

			if self.page_items + len(hint) + 3 <= self.page_size:
				self.add_status_text(hint, highlighted, selected=selected)
				self.add_status_text('  ', False)
			elif highlighted:
				self.add_status_text(' ' * (self.page_size - 3), False)

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
	background: @theme_fg_color;
	color: @theme_bg_color;
	font-family: monospace;
}
.application-icon{
	padding: 0 1px;
	border: none;
}
.error-message{
	background: red;
	color: white;
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

/* STATUS LINE STYLE */
.status-line {
	border: none;
	background: lighter(@theme_fg_color);
}
.status-text{
	border: none;
	padding: 2px 0;
	background: lighter(@theme_fg_color);
}
.status-application-icon {
	background: lighter(@theme_fg_color);
}
.hint-highlight {
	background: darker(@theme_fg_color);
}
.hint-selection {
	color: @theme_fg_color;
	background: @theme_bg_color;
}

/* COMMAND LINE STYLE */
.command-input {
	border: none;
	padding: 2px;
}
"""
GTK_3_20_CSS = b"""
* {
	min-height: initial;
}
"""
