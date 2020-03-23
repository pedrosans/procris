import gi
import xdg.IconTheme
from procris.wm import Monitor
gi.require_version('Notify', '0.7')
from gi.repository import Notify, GLib,  GdkPixbuf


# TODO: rename to desktop and move status icon to this module
# https://lazka.github.io/pgi-docs/Notify-0.7/classes/Notification.html
# https://developer.gnome.org/notification-spec
IMAGE_PATHS = {
    'procris':   xdg.IconTheme.getIconPath('procris', size=96),
    'procris-T': xdg.IconTheme.getIconPath('procris-T', size=96),
    'procris-B': xdg.IconTheme.getIconPath('procris-B', size=96),
}
IMAGES = {
    'procris':   GdkPixbuf.Pixbuf.new_from_file(IMAGE_PATHS['procris']),
    'procris-T': GdkPixbuf.Pixbuf.new_from_file(IMAGE_PATHS['procris-T']),
    'procris-B': GdkPixbuf.Pixbuf.new_from_file(IMAGE_PATHS['procris-B']),
}

Notify.init('procris')
notification = Notify.Notification.new('Procris')
# notification.set_timeout(-1)
notification.set_app_name('procris')
# notification.set_urgency(Notify.Urgency.CRITICAL)
notification.set_image_from_pixbuf(IMAGES['procris'])
notification.set_hint('resident', GLib.Variant.new_boolean(True))

# notification.set_hint('action-icons', GLib.Variant.new_boolean(True))
# notification.add_action("procris-t", "procris", lambda *args: None, None)
# notification.set_category('presence')
# notification.set_hint('desktop-entry', GLib.Variant.new_string('procris.desktop'))
# notification.set_hint('transient', GLib.Variant.new_boolean(False))
# notification.set_hint('category', GLib.Variant.new_string('presence'))
# notification.set_hint('x', GLib.Variant.new_int32(500))
# notification.set_hint('y', GLib.Variant.new_int32(500))
# notification.add_action("procris", "procris", my_callback_func, None)
# notification.clear_actions()


def show_monitor(monitor: Monitor):
    html = ''
    count = 0
    while monitor:
        html += '<b>{}</b>: <b>{}</b> <i>nmaster</i>: <b>{}</b> <i>nservant</i>: <b>{}</b>'.format(
            1 if monitor.primary else 2, monitor.function_key, monitor.nmaster, monitor.nservant)
        count += 1
        monitor = monitor.next()
        if monitor:
            html += '\r'
    show(summary='Procris - {} monitors'.format(count), body=html, icon='procris')


def show(summary: str = 'Procris', body: str = None, icon: str = 'procris'):
    notification.update(summary, body, icon)
    notification.show()


def close():
    notification.close()
