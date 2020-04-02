from pocoy.keyboard import Key
from pocoy.names import Name
import pocoy

service = pocoy.service
reading = service.reading
windows = pocoy.model.windows
active_window = pocoy.model.active_window
active_monitor = pocoy.model.active_monitor
terminal = pocoy.terminal
decoration = pocoy.decoration
scratchpads = pocoy.scratchpads
applications = pocoy.applications


KEYS = [
	Key('<ctrl>Return',          active_window.zoom),
	Key('<ctrl>KP_Enter',        active_window.zoom),
	Key('<ctrl><shift>Return',   applications.spawn,            parameters=['x-terminal-emulator']),
	Key('<ctrl><shift>KP_Enter', applications.spawn,            parameters=['x-terminal-emulator']),
	Key('<ctrl>j',               active_window.focusstack,      parameters=[1]),
	Key('<ctrl>k',               active_window.focusstack,      parameters=[-1]),
	Key('<ctrl><shift>j',        active_window.pushstack,       parameters=[1]),
	Key('<ctrl><shift>k',        active_window.pushstack,       parameters=[-1]),
	Key('<ctrl>i',               active_monitor.incnmaster,     parameters=[1]),
	Key('<ctrl>d',               active_monitor.incnmaster,     parameters=[-1]),
	Key('<ctrl>l',               active_monitor.setmfact,       parameters=[0.05]),
	Key('<ctrl>h',               active_monitor.setmfact,       parameters=[-0.05]),
	Key('<ctrl>t',               active_monitor.setlayout,      parameters=['T']),
	Key('<ctrl>m',               active_monitor.setlayout,      parameters=['M']),
	Key('<ctrl>f',               active_monitor.setlayout,      parameters=[None]),
	Key('<ctrl>space',           active_monitor.setlayout),
	Key('<ctrl>q', None, combinations=[
		Key('Escape',       reading.escape),
		Key('<shift>colon', reading.show_prompt),
		Key('<ctrl>w',      active_window.focus_next),
		Key('<shift>w',     active_window.focus_next),
		Key('w',            active_window.focus_next),
		Key('q',            active_window.minimize),
		Key('o',            active_window.only),
		Key('<ctrl>o',      active_window.only),
		Key('l',            active_window.focus_right),
		Key('p',            active_window.focus_previous),
		Key('<ctrl>l',      active_window.focus_right),
		Key('j',            active_window.focus_down),
		Key('<ctrl>j',      active_window.focus_down),
		Key('h',            active_window.focus_left),
		Key('<ctrl>h',      active_window.focus_left),
		Key('k',            active_window.focus_up),
		Key('<ctrl>k',      active_window.focus_up),
	])
]
NAMES = [
	Name('edit',        applications.launch, alias='e', complete=applications.complete),
	Name('!',           terminal.bang, complete=terminal.complete),
	Name('buffers',     windows.list, alias='ls'),
	Name('bdelete',     windows.delete, alias='bd'),
	Name('buffer',      windows.activate, alias='b', complete=windows.complete),
	Name('centralize',  active_window.centralize, alias='ce'),
	Name('maximize',    active_window.maximize, alias='ma'),
	Name('reload',      service.reload),
	Name('decorate',    active_window.decorate, complete=decoration.complete),
	Name('read',        service.read_screen),
	Name('quit',        active_window.minimize, alias='q'),
	Name('only',        active_window.only, alias='on'),
	Name('gap',         active_monitor.gap, complete=active_monitor.complete_gap_options),
]
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
pocoy.state.force_defaults()
