from pwm.keyboard import Key
from pwm.names import Name
import pwm

service = pwm.service
windows = pwm.model.windows
active_window = pwm.model.active_window
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
	Key('<ctrl>Return',    active_window.zoom),
	Key('<ctrl>KP_Enter',  active_window.zoom),
	Key('<ctrl>j', active_window.focusstack, [1]),
	Key('<ctrl>k', active_window.focusstack, [-1]),
	Key('<ctrl><shift>j', active_window.pushstack, parameters=[1]),
	Key('<ctrl><shift>k', active_window.pushstack, parameters=[-1]),
	Key('<ctrl>i', monitors.incnmaster, parameters=[1]),
	Key('<ctrl>d', monitors.incnmaster, parameters=[-1]),
	Key('<ctrl>l', monitors.setmfact, parameters=[0.05]),
	Key('<ctrl>h', monitors.setmfact, parameters=[-0.05]),
	Key('<ctrl>t', monitors.setlayout, parameters=['T']),
	Key('<ctrl>m', monitors.setlayout, parameters=['M']),
	Key('<ctrl>f', monitors.setlayout, parameters=[None]),

	Key('<ctrl>space', monitors.cycle_function, parameters=[None]),
	Key('<ctrl>q', None, combinations=[
		Key('Escape', pwm.service.escape_reading),
		Key('<shift>colon', pwm.service.show_prompt),
		Key('<ctrl>w', active_window.focus_next),
		Key('<shift>w', active_window.focus_next),
		Key('w', active_window.focus_next),
		Key('q', active_window.minimize),
		Key('o', active_window.only),
		Key('<ctrl>o', active_window.only),
		Key('l', active_window.focus_right),
		Key('p', active_window.focus_previous),
		Key('<ctrl>l', active_window.focus_right),
		Key('j', active_window.move_down),
		Key('<ctrl>j', active_window.move_down),
		Key('h', active_window.focus_left),
		Key('<ctrl>h', active_window.focus_left),
		Key('k', active_window.focus_up),
		Key('<ctrl>k', active_window.focus_up),
	])
]
NAMES = [
	Name('edit', applications.launch, alias='e', complete=applications.complete),
	Name('!', terminal.bang, complete=terminal.complete),
	Name('buffers', windows.list, alias='ls'),
	Name('bdelete', windows.delete, alias='bd'),
	Name('buffer', windows.activate, alias='b', complete=windows.complete),
	Name('centralize', active_window.centralize, alias='ce'),
	Name('maximize', active_window.maximize, alias='ma'),
	Name('reload', service.reload),
	Name('decorate', active_window.decorate, complete=decoration.complete),
	Name('report', service.debug),
	Name('quit', active_window.minimize, alias='q'),
	Name('only', active_window.only, alias='on'),
	Name('gap', monitors.gap, complete=monitors.complete_gap_options),
]
