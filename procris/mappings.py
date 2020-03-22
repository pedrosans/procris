from procris.keyboard import Key
from procris.names import Name
import procris

service = procris.service
applications = procris.applications
windows = procris.service.windows
layout = procris.service.layout
terminal = procris.terminal
reading = procris.service.reading
scratchpads = procris.scratchpads
decoration = procris.decoration

default_interface = {
	'position': 'bottom',
	'width': '800',
	'auto_hint': 'true',
	'auto_select_first_hint': 'true',
	'icon': 'default',
	'remove_decorations': 'false'
}

default_layout = {
	'workspaces': {
		'0': {
			'nmaster': 1,
			'mfact': 0.5,
			'function': 'B',
			'gap': 2,
			'border': 0
		},
		'1': {
			'nmaster': 1,
			'mfact': 0.5,
			'function': 'T',
			'gap': 0,
			'border': 0
		},
	}
}

prefix_key = '<Ctrl>q'

keys = [

	# tile window managers bindings
	Key(['<Ctrl>Return'], layout.move_to_master),
	Key(['<Ctrl>KP_Enter'], layout.move_to_master),
	Key(['<Ctrl>i'], layout.increment_master, 1),
	Key(['<Ctrl>d'], layout.increment_master, -1),
	Key(['<Ctrl>j'], layout.move_focus, 1),
	Key(['<Ctrl>k'], layout.move_focus, -1),
	Key(['<Ctrl>l'], layout.increase_master_area, 0.05),
	Key(['<Ctrl>h'], layout.increase_master_area, -0.05),
	Key(['<Ctrl>u'], layout.change_function, 'C'),
	Key(['<Ctrl>t'], layout.change_function, 'T'),
	Key(['<Ctrl>m'], layout.change_function, 'M'),
	Key(['<Ctrl>f'], layout.change_function, None),

	# xmonad bindings https://xmonad.org/manpage.html
	Key(['<Ctrl><Shift>j'], layout.swap_focused_with, 1),
	Key(['<Ctrl><Shift>k'], layout.swap_focused_with, -1),

	# procris reading binding
	Key([prefix_key], service.read_command_key),

	# Vim bindings
	Key([prefix_key, 'q'], windows.active.minimize),
	Key([prefix_key, 'o'], windows.active.only),
	Key([prefix_key, 'Right'], windows.active.focus.move_right),
	Key([prefix_key, 'l'], windows.active.focus.move_right),
	Key([prefix_key, '<Ctrl>l'], windows.active.focus.move_right),
	Key([prefix_key, '<Shift>l'], windows.active.move_right),
	Key([prefix_key, 'Down'], windows.active.focus.move_down),
	Key([prefix_key, 'j'], windows.active.focus.move_down),
	Key([prefix_key, '<Ctrl>j'], windows.active.focus.move_down),
	Key([prefix_key, '<Shift>j'], windows.active.move_down),
	Key([prefix_key, 'Left'], windows.active.focus.move_left),
	Key([prefix_key, 'h'], windows.active.focus.move_left),
	Key([prefix_key, '<Ctrl>h'], windows.active.focus.move_left),
	Key([prefix_key, '<Shift>h'], windows.active.move_left),
	Key([prefix_key, 'Up'], windows.active.focus.move_up),
	Key([prefix_key, 'k'], windows.active.focus.move_up),
	Key([prefix_key, '<Ctrl>k'], windows.active.focus.move_up),
	Key([prefix_key, '<Shift>k'], windows.active.move_up),
	Key([prefix_key, 'w'], windows.active.focus.cycle),
	Key([prefix_key, '<Ctrl>w'], windows.active.focus.cycle),
	Key([prefix_key, '<Shift>w'], windows.active.focus.cycle),
	Key([prefix_key, 'p'], windows.active.focus.move_to_previous),
]
names = [
	Name('edit', applications.launch, alias='e', complete=applications.complete),
	Name('!', terminal.bang, complete=terminal.complete),
	Name('buffers', windows.list, alias='ls'),
	Name('bdelete', windows.delete, alias='bd'),
	Name('buffer', windows.activate, alias='b', complete=windows.complete),
	Name('centralize', windows.active.centralize, alias='ce'),
	Name('maximize', windows.active.maximize, alias='ma'),
	Name('reload', service.reload),
	Name('decorate', windows.active.decorate, complete=decoration.complete),
	Name('report', service.debug),
	Name('stack', layout.move_stacked),
	Name('quit', windows.active.minimize, alias='q'),
	Name('only', windows.active.only, alias='on'),
	Name('gap', layout.set_gap),
	Name('border', layout.set_border),
]
