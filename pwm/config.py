from pwm.keyboard import Key
from pwm.names import Name
import pwm

service = pwm.service
windows = pwm.model.windows
monitors = pwm.model.monitors
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
	Key('<ctrl>Return',    windows.active.zoom),
	Key('<ctrl>KP_Enter',  windows.active.zoom),
	Key('<ctrl>j', windows.active.focusstack, [1]),
	Key('<ctrl>k', windows.active.focusstack, [-1]),
	Key('<ctrl><shift>j', windows.active.pushstack, parameters=[1]),
	Key('<ctrl><shift>k', windows.active.pushstack, parameters=[-1]),
	Key('<ctrl>i', monitors.incnmaster, parameters=[1]),
	Key('<ctrl>d', monitors.incnmaster, parameters=[-1]),
	Key('<ctrl>l', monitors.setmfact, parameters=[0.05]),
	Key('<ctrl>h', monitors.setmfact, parameters=[-0.05]),
	Key('<ctrl>t', monitors.setlayout, parameters=['T']),
	Key('<ctrl>m', monitors.setlayout, parameters=['M']),
	Key('<ctrl>f', monitors.setlayout, parameters=[None]),

	Key('<ctrl>space', monitors.cycle_function, parameters=[None]),
	Key('<ctrl>q', None, plexes=[
		Key('Escape', pwm.service.escape_reading),
		Key('<shift>colon', pwm.service.show_prompt),
		Key('<ctrl>e', windows.active.cycle),
		Key('<ctrl>w', windows.active.cycle),
		Key('<shift>w', windows.active.cycle),
		Key('w', windows.active.cycle),
		Key('q', windows.active.minimize),
		Key('o', windows.active.only),
		Key('<ctrl>o', windows.active.only),
		Key('l', windows.active.move_right),
		Key('p', windows.active.move_to_previous),
		Key('<ctrl>l', windows.active.move_right),
		Key('j', windows.active.move_down),
		Key('<ctrl>j', windows.active.move_down),
		Key('h', windows.active.move_left),
		Key('<ctrl>h', windows.active.move_left),
		Key('k', windows.active.move_up),
		Key('<ctrl>k', windows.active.move_up),
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
	Name('gap', monitors.gap, complete=monitors.complete_gap_options),
]
