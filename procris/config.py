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

procris.state.force_defaults()

DEFAULTS = {
	'position': 'bottom',
	'width': 800,
	'auto_hint': True,
	'auto_select_first_hint': False,
	'desktop_icon': 'light',
	'desktop_notifications': False,
	'window_manger_border': 0,
	'remove_decorations': False,
	'inner_gap': 5,
	'outer_gap': 5,
	'workspaces': [
		{
			'monitors': [
				{'nmaster': 1, 'mfact': 0.5, 'function': None},
				{'nmaster': 1, 'mfact': 0.5, 'function': None}
			]
		},
		{
			'monitors': [
				{'function': None},
				{'function': None}
			]
		}
	]
}
KEYS = [
	Key('<Ctrl>Return', layout.move_to_master),
	Key('<Ctrl>KP_Enter', layout.move_to_master),
	Key('<Ctrl>i', layout.increment_master, parameters=[1]),
	Key('<Ctrl>d', layout.increment_master, parameters=[-1]),
	Key('<Ctrl>j', layout.move_focus, parameters=[1]),
	Key('<Ctrl>k', layout.move_focus, parameters=[-1]),
	Key('<Ctrl>l', layout.increase_master_area, parameters=[0.05]),
	Key('<Ctrl>h', layout.increase_master_area, parameters=[-0.05]),
	Key('<Ctrl>u', layout.change_function, parameters=['C']),
	Key('<Ctrl>t', layout.change_function, parameters=['T']),
	Key('<Ctrl>m', layout.change_function, parameters=['M']),
	Key('<Ctrl>f', layout.change_function, parameters=[None]),
	Key('<Ctrl><Shift>j', layout.swap_focused_with, parameters=[1]),
	Key('<Ctrl><Shift>k', layout.swap_focused_with, parameters=[-1]),
	Key('<Ctrl>q', procris.service.read_command_key, plexes=[
		Key('Escape', procris.service.escape_reading),
		Key('<Ctrl>e', windows.active.focus.cycle),
		Key('<Ctrl>w', windows.active.focus.cycle),
		Key('<Shift>w', windows.active.focus.cycle),
		Key('w', windows.active.focus.cycle),
		Key('q', windows.active.minimize),
		Key('o', windows.active.only),
		Key('<Ctrl>o', windows.active.only),
		Key('l', windows.active.focus.move_right),
		Key('p', windows.active.focus.move_to_previous),
		Key('<Ctrl>l', windows.active.focus.move_right),
		Key('j', windows.active.focus.move_down),
		Key('<ctrl>j', windows.active.focus.move_down),
		Key('h', windows.active.focus.move_left),
		Key('<Ctrl>h', windows.active.focus.move_left),
		Key('k', windows.active.focus.move_up),
		Key('<Ctrl>k', windows.active.focus.move_up),
	])
]
NAMES = [
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
	Name('quit', windows.active.minimize, alias='q'),
	Name('only', windows.active.only, alias='on'),
	Name('gap', layout.gap, complete=layout.complete_gap_options),
]
