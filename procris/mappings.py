from procris.keyboard import Key
from procris.names import Name
import procris

applications = procris.applications
windows = procris.service.windows
reading = procris.service.reading
layout = procris.service.layout
terminal = procris.terminal

prefix_key = '<Ctrl>q'

keys = [

	# tile window managers bindings
	Key(['<Ctrl>Return'], layout.move_to_master),
	Key(['<Ctrl>KP_Enter'], layout.move_to_master),
	Key(['<Ctrl>i'], layout.increment_master, [1]),
	Key(['<Ctrl>d'], layout.increment_master, [-1]),
	Key(['<Ctrl>j'], layout.move_focus, [1]),
	Key(['<Ctrl>k'], layout.move_focus, [-1]),
	Key(['<Ctrl>l'], layout.increase_master_area, [0.05]),
	Key(['<Ctrl>h'], layout.increase_master_area, [-0.05]),
	Key(['<Ctrl>u'], layout.change_function, ['C']),
	Key(['<Ctrl>t'], layout.change_function, ['T']),
	Key(['<Ctrl>m'], layout.change_function, ['M']),
	Key(['<Ctrl>f'], layout.change_function, [None]),

	# xmonad bindings https://xmonad.org/manpage.html
	Key(['<Ctrl><Shift>j'], layout.swap_focused_with, [1]),
	Key(['<Ctrl><Shift>k'], layout.swap_focused_with, [-1]),

	# procris reading binding
	Key([prefix_key], reading.begin),

	# Vim bindings
	Key([prefix_key, 'q'], windows.active.minimize),
	Key([prefix_key, 'o'], windows.active.only),
	Key([prefix_key, 'Right'], windows.focus.move_right),
	Key([prefix_key, 'l'], windows.focus.move_right),
	Key([prefix_key, '<Ctrl>l'], windows.focus.move_right),
	Key([prefix_key, '<Shift>l'], windows.active.move_right),
	Key([prefix_key, 'Down'], windows.focus.move_down),
	Key([prefix_key, 'j'], windows.focus.move_down),
	Key([prefix_key, '<Ctrl>j'], windows.focus.move_down),
	Key([prefix_key, '<Shift>j'], windows.active.move_down),
	Key([prefix_key, 'Left'], windows.focus.move_left),
	Key([prefix_key, 'h'], windows.focus.move_left),
	Key([prefix_key, '<Ctrl>h'], windows.focus.move_left),
	Key([prefix_key, '<Shift>h'], windows.active.move_left),
	Key([prefix_key, 'Up'], windows.focus.move_up),
	Key([prefix_key, 'k'], windows.focus.move_up),
	Key([prefix_key, '<Ctrl>k'], windows.focus.move_up),
	Key([prefix_key, '<Shift>k'], windows.active.move_up),
	Key([prefix_key, 'w'], windows.focus.cycle),
	Key([prefix_key, '<Ctrl>w'], windows.focus.cycle),
	Key([prefix_key, '<Shift>w'], windows.focus.cycle),
	Key([prefix_key, 'p'], windows.focus.move_to_previous),
]
names = [
	Name('edit', 'e', applications.launch),
	Name('!', None, terminal.bang),
	Name('buffers', 'ls', windows.list),
	Name('bdelete', 'bd', windows.delete),
	Name('buffer', 'b', windows.activate),
	Name('centralize', 'ce', windows.active.centralize),
	Name('maximize', 'ma', windows.active.maximize),
	Name('reload', None, procris.service.reload),
	Name('decorate', None, windows.active.decorate),
	Name('report', None, procris.service.debug),
	Name('move', None, windows.active.move),
	Name('stack', None, layout.move_stacked),
	Name('quit', 'q', windows.active.minimize),
	Name('only', 'on', windows.active.only),
]
