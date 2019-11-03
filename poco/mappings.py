from poco.keyboard import Key
from poco.names import Name
import poco

applications = poco.applications
windows = poco.service.windows
reading = poco.service.reading
layout = poco.service.layout
terminal = poco.terminal

termkey = '<Primary>e'

keys = [

	# tile window managers bindings
	Key(['<Ctrl>Return'], layout.move_to_master),
	Key(['<Ctrl>KP_Enter'], layout.move_to_master),
	Key(['<Ctrl>i'], layout.increment_master, [1]),
	Key(['<Ctrl>d'], layout.increment_master, [-1]),
	Key(['<Ctrl>l'], layout.increase_master_area, [0.05]),
	Key(['<Ctrl>h'], layout.increase_master_area, [-0.05]),
	Key(['<Ctrl>u'], layout.change_function, ['C']),
	Key(['<Ctrl>t'], layout.change_function, ['T']),

	# xmonad bindings https://xmonad.org/manpage.html
	Key(['<Ctrl><Shift>j'], layout.swap_focused_with, [1]),
	Key(['<Ctrl><Shift>k'], layout.swap_focused_with, [-1]),

	# poco reading binding
	Key([termkey], reading.start),

	# Vim bindings
	Key([termkey, 'q'],         windows.active.minimize),
	Key([termkey, 'o'],         windows.active.only),
	Key([termkey, 'Right'],     windows.focus.move_right),
	Key([termkey, 'l'],         windows.focus.move_right),
	Key([termkey, '<Ctrl>l'],   windows.focus.move_right),
	Key([termkey, '<Shift>l'],  windows.active.move_right),
	Key([termkey, 'Down'],      windows.focus.move_down),
	Key([termkey, 'j'],         windows.focus.move_down),
	Key([termkey, '<Ctrl>j'],   windows.focus.move_down),
	Key([termkey, '<Shift>j'],  windows.active.move_down),
	Key([termkey, 'Left'],      windows.focus.move_left),
	Key([termkey, 'h'],         windows.focus.move_left),
	Key([termkey, '<Ctrl>h'],   windows.focus.move_left),
	Key([termkey, '<Shift>h'],  windows.active.move_left),
	Key([termkey, 'Up'],        windows.focus.move_up),
	Key([termkey, 'k'],         windows.focus.move_up),
	Key([termkey, '<Ctrl>k'],   windows.focus.move_up),
	Key([termkey, '<Shift>k'],  windows.active.move_up),
	Key([termkey, 'w'],         windows.focus.cycle),
	Key([termkey, '<Ctrl>w'],   windows.focus.cycle),
	Key([termkey, '<Shift>w'],  windows.focus.cycle),
	Key([termkey, 'p'],         windows.focus.move_to_previous),
]
names = [
	Name('edit', 'e', applications.launch),
	Name('!', None, terminal.bang),
	Name('buffers', 'ls', windows.list),
	Name('bdelete', 'bd', windows.delete),
	Name('buffer', 'b', windows.activate),
	Name('centralize', 'ce', windows.active.centralize),
	Name('maximize', 'ma', windows.active.maximize),
	Name('reload', None, poco.service.reload),
	Name('decorate', None, windows.active.decorate),
	Name('report', None, poco.service.debug),
	Name('move', None, windows.active.move),
	Name('quit', 'q', windows.active.minimize),
	Name('only', 'on', windows.active.only),
]
