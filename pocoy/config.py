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


inner_gap = 5
outer_gap = 5
workspaces = [
	{
		'monitors': [
			{'function': None, 'nmaster': 1, 'mfact': 0.55, 'strut': {'top': 0}},
			{'function': None, 'nmaster': 1, 'mfact': 0.55, 'strut': {'top': 0}}
		]
	}
]

keys = [
	Key(accelerator='<ctrl>Return',          function=active_window.zoom),
	Key(accelerator='<ctrl>KP_Enter',        function=active_window.zoom),
	Key(accelerator='<ctrl><shift>Return',   function=applications.spawn,  parameters=['x-terminal-emulator']),
	Key(accelerator='<ctrl><shift>KP_Enter', function=applications.spawn,  parameters=['x-terminal-emulator']),
	Key(accelerator='<ctrl><shift>c',        function=active_window.killclient),
	Key(accelerator='<ctrl>j',               function=active_window.focusstack,      parameters=[1]),
	Key(accelerator='<ctrl>k',               function=active_window.focusstack,      parameters=[-1]),
	Key(accelerator='<ctrl><shift>j',        function=active_window.pushstack,       parameters=[1]),
	Key(accelerator='<ctrl><shift>k',        function=active_window.pushstack,       parameters=[-1]),
	Key(accelerator='<ctrl>i',               function=active_monitor.incnmaster,     parameters=[1]),
	Key(accelerator='<ctrl>d',               function=active_monitor.incnmaster,     parameters=[-1]),
	Key(accelerator='<ctrl>l',               function=active_monitor.setmfact,       parameters=[0.05]),
	Key(accelerator='<ctrl>h',               function=active_monitor.setmfact,       parameters=[-0.05]),
	Key(accelerator='<ctrl>t',               function=active_monitor.setlayout,      parameters=['T']),
	Key(accelerator='<ctrl>m',               function=active_monitor.setlayout,      parameters=['M']),
	Key(accelerator='<ctrl>f',               function=active_monitor.setlayout,      parameters=[None]),
	Key(accelerator='<ctrl>space',           function=active_monitor.setlayout),
	Key(accelerator='<ctrl>q', combinations=[
		Key(accelerator='Escape',       function=reading.escape),
		Key(accelerator='<shift>colon', function=reading.show_prompt),
		Key(accelerator='<ctrl>w',      function=active_window.focus_next),
		Key(accelerator='<shift>w',     function=active_window.focus_next),
		Key(accelerator='w',            function=active_window.focus_next),
		Key(accelerator='q',            function=active_window.minimize),
		Key(accelerator='o',            function=active_window.only),
		Key(accelerator='<ctrl>o',      function=active_window.only),
		Key(accelerator='l',            function=active_window.focus_right),
		Key(accelerator='p',            function=active_window.focus_previous),
		Key(accelerator='<ctrl>l',      function=active_window.focus_right),
		Key(accelerator='j',            function=active_window.focus_down),
		Key(accelerator='<ctrl>j',      function=active_window.focus_down),
		Key(accelerator='h',            function=active_window.focus_left),
		Key(accelerator='<ctrl>h',      function=active_window.focus_left),
		Key(accelerator='k',            function=active_window.focus_up),
		Key(accelerator='<ctrl>k',      function=active_window.focus_up),
	])
]
names = [
	Name('edit',        applications.launch_from_name, alias='e', complete=applications.complete),
	Name('!',           terminal.bang, complete=terminal.complete),
	Name('buffers',     windows.list, alias='ls'),
	Name('bdelete',     windows.delete, alias='bd'),
	Name('buffer',      windows.activate, alias='b', complete=windows.complete),
	Name('maximize',    active_window.maximize, alias='ma'),
	Name('reload',      service.reload),
	Name('quit',        active_window.minimize, alias='q'),
	Name('only',        active_window.only, alias='on'),
	Name('gap',         active_monitor.gap, complete=active_monitor.complete_gap_options),
]
