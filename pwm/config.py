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
	Key('<ctrl>Return', layout.move_to_master),
	Key('<ctrl>KP_Enter', layout.move_to_master),
	Key('<ctrl>i', layout.increment_master, parameters=[1]),
	Key('<ctrl>d', layout.increment_master, parameters=[-1]),
	Key('<ctrl>l', layout.increase_master_area, parameters=[0.05]),
	Key('<ctrl>h', layout.increase_master_area, parameters=[-0.05]),
	Key('<ctrl>j', layout.move_focus, parameters=[1]),
	Key('<ctrl>k', layout.move_focus, parameters=[-1]),
	Key('<ctrl><shift>j', layout.swap_focused_with, parameters=[1]),
	Key('<ctrl><shift>k', layout.swap_focused_with, parameters=[-1]),
	Key('<ctrl>u', layout.change_function, parameters=['C']),
	Key('<ctrl>t', layout.change_function, parameters=['T']),
	Key('<ctrl>m', layout.change_function, parameters=['M']),
	Key('<ctrl>f', layout.change_function, parameters=[None]),
	Key('<ctrl>space', layout.cycle_function, parameters=[None]),
	Key('<ctrl>q', None, plexes=[
		Key('Escape', pwm.service.escape_reading),
		Key('<shift>colon', pwm.service.show_prompt),
		Key('<ctrl>e', windows.active.focus.cycle),
		Key('<ctrl>w', windows.active.focus.cycle),
		Key('<shift>w', windows.active.focus.cycle),
		Key('w', windows.active.focus.cycle),
		Key('q', windows.active.minimize),
		Key('o', windows.active.only),
		Key('<ctrl>o', windows.active.only),
		Key('l', windows.active.focus.move_right),
		Key('p', windows.active.focus.move_to_previous),
		Key('<ctrl>l', windows.active.focus.move_right),
		Key('j', windows.active.focus.move_down),
		Key('<ctrl>j', windows.active.focus.move_down),
		Key('h', windows.active.focus.move_left),
		Key('<ctrl>h', windows.active.focus.move_left),
		Key('k', windows.active.focus.move_up),
		Key('<ctrl>k', windows.active.focus.move_up),
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