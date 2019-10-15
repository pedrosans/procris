from poco.keyboard import Key
from poco.commands import Command
import poco

applications = poco.applications
windows = poco.service.windows
reading = poco.service.reading
layout_manager = poco.service.layout_manager

termkey = '<Primary>q'

keys = [
	Key(['<Ctrl>Return'],   layout_manager.move_to_master),
	Key(['<Ctrl>KP_Enter'], layout_manager.move_to_master),
	Key(['<Ctrl>i'],        layout_manager.increment_master, [1]),
	Key(['<Ctrl>d'],        layout_manager.increment_master, [-1]),
	Key(['<Ctrl>l'],        layout_manager.increase_master_area, [0.05]),
	Key(['<Ctrl>h'],        layout_manager.increase_master_area, [-0.05]),
	Key([termkey], reading.start),
	Key([termkey, 'q'],         windows.minimize_active_window),
	Key([termkey, 'o'],         windows.only),
	Key([termkey, 'Right'],     windows.navigate_right),
	Key([termkey, 'l'],         windows.navigate_right),
	Key([termkey, '<Ctrl>l'],   windows.navigate_right),
	Key([termkey, 'L'],         windows.move_right),
	Key([termkey, 'Down'],      windows.navigate_down),
	Key([termkey, 'j'],         windows.navigate_down),
	Key([termkey, '<Ctrl>j'],   windows.navigate_down),
	Key([termkey, 'J'],         windows.move_down),
	Key([termkey, 'Left'],      windows.navigate_left),
	Key([termkey, 'h'],         windows.navigate_left),
	Key([termkey, '<Ctrl>h'],   windows.navigate_left),
	Key([termkey, 'H'],         windows.move_left),
	Key([termkey, 'Up'],        windows.navigate_up),
	Key([termkey, 'k'],         windows.navigate_up),
	Key([termkey, '<Ctrl>k'],   windows.navigate_up),
	Key([termkey, 'K'],         windows.move_up),
	Key([termkey, 'w'],         windows.cycle),
	Key([termkey, '<Ctrl>w'],   windows.cycle),
	Key([termkey, 'W'],         windows.cycle),
	Key([termkey, 'p'],         windows.navigate_to_previous),
]
commands = [
	Command('edit'			,'e'			,reading.edit					),
	Command('!'				, None			,reading.bang					),
	Command('buffers'		,'ls'			,reading.buffers				),
	Command('bdelete'		,'bd'			,reading.delete_buffer	),
	Command('buffer'		,'b'			,reading.buffer					),
	Command('centralize'	,'ce'			,windows.centralize				),
	Command('maximize'		,'ma'			,windows.maximize				),
	Command('reload'		, None			,reading.reload					),
	Command('decorate'		, None			,windows.decorate				),
	Command('report'		, None	    	,reading.debug					),
	Command('move'			, None			,windows.move					),
	Command('quit'			,'q'			,windows.minimize_active_window	),
	Command('only'			,'on'			,windows.only		    		),
]
