from procris.keyboard import Key
from procris.names import Name
import procris

service = procris.service
layout = service.layout
windows = service.windows
reading = service.reading
terminal = procris.terminal
decoration = procris.decoration
scratchpads = procris.scratchpads
applications = procris.applications

PREFIX_KEY = '<Ctrl>q'
DEFAULTS = {
	'position': 'bottom',
	'width': 800,
	'auto_hint': True,
	'auto_select_first_hint': True,
	'desktop_icon': 'light',
	'desktop_notifications': True,
	'window_manger_border': 0,
	'remove_decorations': False,
	'inner_gap': 5,
	'outer_gap': 5,
	'workspaces': [
		{
			'monitors': [
				{'nmaster': 1, 'mfact': 0.5, 'function': 'B'},
				{'nmaster': 1, 'mfact': 0.5, 'function': 'T'}
			]
		},
		{
			'monitors': [
				{'function': 'M'},
				{'function': 'M'}
			]
		}
	]
}
KEYS = [
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
	Key(['<Ctrl><Shift>j'], layout.swap_focused_with, 1),
	Key(['<Ctrl><Shift>k'], layout.swap_focused_with, -1),
	Key([PREFIX_KEY], service.read_command_key),
	Key([PREFIX_KEY, 'q'], windows.active.minimize),
	Key([PREFIX_KEY, 'o'], windows.active.only),
	Key([PREFIX_KEY, 'Right'], windows.active.focus.move_right),
	Key([PREFIX_KEY, 'l'], windows.active.focus.move_right),
	Key([PREFIX_KEY, '<Ctrl>l'], windows.active.focus.move_right),
	Key([PREFIX_KEY, '<Shift>l'], windows.active.move_right),
	Key([PREFIX_KEY, 'Down'], windows.active.focus.move_down),
	Key([PREFIX_KEY, 'j'], windows.active.focus.move_down),
	Key([PREFIX_KEY, '<Ctrl>j'], windows.active.focus.move_down),
	Key([PREFIX_KEY, '<Shift>j'], windows.active.move_down),
	Key([PREFIX_KEY, 'Left'], windows.active.focus.move_left),
	Key([PREFIX_KEY, 'h'], windows.active.focus.move_left),
	Key([PREFIX_KEY, '<Ctrl>h'], windows.active.focus.move_left),
	Key([PREFIX_KEY, '<Shift>h'], windows.active.move_left),
	Key([PREFIX_KEY, 'Up'], windows.active.focus.move_up),
	Key([PREFIX_KEY, 'k'], windows.active.focus.move_up),
	Key([PREFIX_KEY, '<Ctrl>k'], windows.active.focus.move_up),
	Key([PREFIX_KEY, '<Shift>k'], windows.active.move_up),
	Key([PREFIX_KEY, 'w'], windows.active.focus.cycle),
	Key([PREFIX_KEY, '<Ctrl>w'], windows.active.focus.cycle),
	Key([PREFIX_KEY, '<Shift>w'], windows.active.focus.cycle),
	Key([PREFIX_KEY, 'p'], windows.active.focus.move_to_previous),
]
NAMES = [
	Name('edit', applications.launch, alias='e', complete=applications.complete),
	Name('!', terminal.bang, complete=terminal.complete),
	Name('buffers', windows.list, alias='ls'),
	Name('bdelete', windows.delete, alias='bd'),
	Name('buffer', windows.activate, alias='b', complete=windows.complete),
	Name('centralize', windows.active.centralize, alias='ce'),
	Name('maximize', windows.active.maximize, alias='ma'),
	Name('reload', service.update),
	Name('decorate', windows.active.decorate, complete=decoration.complete),
	Name('report', service.debug),
	Name('quit', windows.active.minimize, alias='q'),
	Name('only', windows.active.only, alias='on'),
	Name('gap', layout.gap, complete=layout.complete_gap_options),
]
