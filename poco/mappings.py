from poco.keyboard import Key
from poco.commands import Command
import poco

applications = poco.applications
windows = poco.service.windows
reading = poco.service.reading
layout = poco.service.layout
terminal = poco.terminal

termkey = '<Primary>e'

keys = [

	# layout bindings
	Key(['<Ctrl>Return'], layout.move_to_master),
	Key(['<Ctrl>KP_Enter'], layout.move_to_master),
	Key(['<Ctrl>i'], layout.increment_master, [1]),
	Key(['<Ctrl>d'], layout.increment_master, [-1]),
	Key(['<Ctrl>l'], layout.increase_master_area, [0.05]),
	Key(['<Ctrl>h'], layout.increase_master_area, [-0.05]),
	Key(['<Ctrl>u'], layout.change_function, ['C']),
	Key(['<Ctrl>t'], layout.change_function, ['T']),

	# # xmonad bindings https://xmonad.org/manpage.html
	Key(['<Ctrl><Shift>j'], layout.swap_focused_with, [1]),
	Key(['<Ctrl><Shift>k'], layout.swap_focused_with, [-1]),

	# # Vim bindings
	Key([termkey], reading.start),
	Key([termkey, 'q'],         windows.active.minimize),
	Key([termkey, 'o'],         windows.active.only),
	Key([termkey, 'Right'],     windows.focus.move_right),
	Key([termkey, 'l'],         windows.focus.move_right),
	Key([termkey, '<Ctrl>l'],   windows.focus.move_right),
	Key([termkey, '<Shift>l'],  windows.active.move_right),
	Key([termkey, 'Down'],      windows.focus.move_down),
	Key([termkey, 'j'],         windows.focus.move_down),
	Key([termkey, '<Ctrl>j'],   windows.focus.move_down),
	Key([termkey, '<Shift>j'],  windows.active.move_down),
	Key([termkey, 'Left'],      windows.focus.move_left),
	Key([termkey, 'h'],         windows.focus.move_left),
	Key([termkey, '<Ctrl>h'],   windows.focus.move_left),
	Key([termkey, '<Shift>h'],  windows.active.move_left),
	Key([termkey, 'Up'],        windows.focus.move_up),
	Key([termkey, 'k'],         windows.focus.move_up),
	Key([termkey, '<Ctrl>k'],   windows.focus.move_up),
	Key([termkey, '<Shift>k'],  windows.active.move_up),
	Key([termkey, 'w'],         windows.focus.cycle),
	Key([termkey, '<Ctrl>w'],   windows.focus.cycle),
	Key([termkey, '<Shift>w'],  windows.focus.cycle),
	Key([termkey, 'p'],         windows.focus.move_to_previous),
]
commands = [
	Command('edit'			,'e'			,applications.launch			),
	Command('!'				, None			,terminal.bang					),
	Command('buffers'		,'ls'			,windows.list					),
	Command('bdelete'		,'bd'			,windows.delete					),
	Command('buffer'		,'b'			,windows.show					),
	Command('centralize'	,'ce'			,windows.active.centralize		),
	Command('maximize'		,'ma'			,windows.active.maximize		),
	Command('reload'		, None			,poco.service.reload			),
	Command('decorate'		, None			,windows.active.decorate		),
	Command('report'		, None	    	,poco.service.debug				),
	Command('move'			, None			,windows.active.move			),
	Command('quit'			,'q'			,windows.active.minimize		),
	Command('only'			,'on'			,windows.active.only	   		),
]
