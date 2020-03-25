from pwm.keyboard import Key
from pwm.names import Name
import pwm

service = pwm.service
layout = service.layout
windows = service.windows
reading = service.reading
terminal = pwm.terminal
decoration = pwm.decoration
scratchpads = pwm.scratchpads
applications = pwm.applications

pwm.state.force_defaults()

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
				{'nmaster': 1, 'mfact': 0.55, 'function': None},
				{'nmaster': 1, 'mfact': 0.55, 'function': None}
			]
		},
		{
			'monitors': [
				{'nmaster': 1, 'mfact': 0.55, 'function': None},
				{'nmaster': 1, 'mfact': 0.55, 'function': None}
			]
		}
	]
}
KEYS = [
	Key('<CTRL>Return', layout.move_to_master),
	Key('<CTRL>KP_Enter', layout.move_to_master),
	Key('<CTRL>i', layout.increment_master, parameters=[1]),
	Key('<CTRL>d', layout.increment_master, parameters=[-1]),
	Key('<CTRL>l', layout.increase_master_area, parameters=[0.05]),
	Key('<CTRL>h', layout.increase_master_area, parameters=[-0.05]),
	Key('<CTRL>j', layout.move_focus, parameters=[1]),
	Key('<CTRL>k', layout.move_focus, parameters=[-1]),
	Key('<CTRL><SHIFT>j', layout.swap_focused_with, parameters=[1]),
	Key('<CTRL><SHIFT>k', layout.swap_focused_with, parameters=[-1]),
	Key('<CTRL>u', layout.change_function, parameters=['C']),
	Key('<CTRL>t', layout.change_function, parameters=['T']),
	Key('<CTRL>m', layout.change_function, parameters=['M']),
	Key('<CTRL>f', layout.change_function, parameters=[None]),
	Key('<CTRL>space', layout.cycle_function, parameters=[None]),
	Key('<CTRL>q', pwm.service.read_command_key, plexes=[
		Key('Escape', pwm.service.escape_reading),
		Key('<CTRL>e', windows.active.focus.cycle),
		Key('<CTRL>w', windows.active.focus.cycle),
		Key('<SHIFT>w', windows.active.focus.cycle),
		Key('w', windows.active.focus.cycle),
		Key('q', windows.active.minimize),
		Key('o', windows.active.only),
		Key('<CTRL>o', windows.active.only),
		Key('l', windows.active.focus.move_right),
		Key('p', windows.active.focus.move_to_previous),
		Key('<CTRL>l', windows.active.focus.move_right),
		Key('j', windows.active.focus.move_down),
		Key('<CTRL>j', windows.active.focus.move_down),
		Key('h', windows.active.focus.move_left),
		Key('<CTRL>h', windows.active.focus.move_left),
		Key('k', windows.active.focus.move_up),
		Key('<CTRL>k', windows.active.focus.move_up),
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
