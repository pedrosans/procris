from poco.keyboard import Key
from poco.commands import Command
import poco

applications = poco.applications
windows = poco.service.windows
reading = poco.service.reading
layout = poco.service.layout

termkey = '<Primary>e'

keys = [
	Key(['<Ctrl>Return'], layout.move_to_master),
	Key(['<Ctrl>KP_Enter'], layout.move_to_master),
	Key(['<Ctrl>i'], layout.increment_master, [1]),
	Key(['<Ctrl>d'], layout.increment_master, [-1]),
	Key(['<Ctrl>l'], layout.increase_master_area, [0.05]),
	Key(['<Ctrl>h'], layout.increase_master_area, [-0.05]),
	Key([termkey], reading.start),
	Key([termkey, 'q'],         windows.active.minimize),
	Key([termkey, 'o'],         windows.active.only),
	Key([termkey, 'Right'],     windows.focus.move_right),
	Key([termkey, 'l'],         windows.focus.move_right),
	Key([termkey, '<Ctrl>l'],   windows.focus.move_right),
	Key([termkey, 'L'],         windows.active.move_right),
	Key([termkey, 'Down'],      windows.focus.move_down),
	Key([termkey, 'j'],         windows.focus.move_down),
	Key([termkey, '<Ctrl>j'],   windows.focus.move_down),
	Key([termkey, 'J'],         windows.active.move_down),
	Key([termkey, 'Left'],      windows.focus.move_left),
	Key([termkey, 'h'],         windows.focus.move_left),
	Key([termkey, '<Ctrl>h'],   windows.focus.move_left),
	Key([termkey, 'H'],         windows.active.move_left),
	Key([termkey, 'Up'],        windows.focus.move_up),
	Key([termkey, 'k'],         windows.focus.move_up),
	Key([termkey, '<Ctrl>k'],   windows.focus.move_up),
	Key([termkey, 'K'],         windows.active.move_up),
	Key([termkey, 'w'],         windows.focus.cycle),
	Key([termkey, '<Ctrl>w'],   windows.focus.cycle),
	Key([termkey, 'W'],         windows.focus.cycle),
	Key([termkey, 'p'],         windows.focus.move_to_previous),
]
commands = [
	Command('edit'			,'e'			,applications.launch			),
	Command('!'				, None			,reading.bang					),
	Command('buffers'		,'ls'			,windows.list					),
	Command('bdelete'		,'bd'			,reading.delete_buffer			),
	Command('buffer'		,'b'			,reading.buffer					),
	Command('centralize'	,'ce'			,windows.active.centralize				),
	Command('maximize'		,'ma'			,windows.active.maximize		),
	Command('reload'		, None			,reading.reload					),
	Command('decorate'		, None			,windows.active.decorate				),
	Command('report'		, None	    	,reading.debug					),
	Command('move'			, None			,windows.active.move					),
	Command('quit'			,'q'			,windows.active.minimize		),
	Command('only'			,'on'			,windows.active.only	   		),
]
