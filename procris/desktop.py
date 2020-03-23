import gi
import xdg.IconTheme
import procris.state as state
gi.require_version('Notify', '0.7')
from gi.repository import Notify, GLib,  GdkPixbuf
from procris.status import StatusIcon
from procris.wm import Monitor, get_active_workspace

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

status_icon: StatusIcon = None
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
    if not state.is_desktop_notifications():
        return
    html = ''
    count = 0
    while monitor:
        html += '<b>{}</b>: <b>{}</b> <i>nmaster</i>: <b>{}</b> <i>nservant</i>: <b>{}</b>'.format(
            1 if monitor.primary else 2, monitor.function_key, monitor.nmaster, monitor.nservant)
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


