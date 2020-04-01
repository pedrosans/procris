
`reading.start` <kbd>Ctrl</kbd> + <kbd>q</kbd>

		Start a reading, the process of to open a window and waiting for the
		following key, which can either be a command key or colon to open the
		colon prompt.

`layout.move_to_master` <kbd>Ctrl</kbd> + <kbd>Return</kbd>

		Move focused window to the top of the stack.

`layout.increment_master` <kbd>Ctrl</kbd> + <kbd>i</kbd>

`layout.increment_master` <kbd>Ctrl</kbd> + <kbd>d</kbd>

		Increment/decrement the number of windows in the master area.

`layout.increase_master_area` <kbd>Ctrl</kbd> + <kbd>l</kbd>

`layout.increase_master_area` <kbd>Ctrl</kbd> + <kbd>h</kbd>

		Increment/decrement the master area.

`layout.change_function` <kbd>Ctrl</kbd> + <kbd>f</kbd>

		Select the floating layout.

`layout.change_function` <kbd>Ctrl</kbd> + <kbd>m</kbd>

		Select the monocle layout.

`layout.change_function` <kbd>Ctrl</kbd> + <kbd>u</kbd>

		Select the centeredmaster layout.

`layout.change_function` <kbd>Ctrl</kbd> + <kbd>t</kbd>

		Select the tile layout.

`layout.swap_focused_with` <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>j</kbd>

`layout.swap_focused_with` <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>k</kbd>

		Swap the focused window with the previous/next one in the stack.

`windows.focus.cycle` <kbd>prefix key</kbd> + <kbd>w</kbd>

		Move focus to the window below/right of the current one

`windows.focus.move_left` <kbd>prefix key</kbd> + <kbd>h</kbd>

`windows.focus.move_down` <kbd>prefix key</kbd> + <kbd>j</kbd>

`windows.focus.move_up` <kbd>prefix key</kbd> + <kbd>k</kbd>

`windows.focus.move_right` <kbd>prefix key</kbd> + <kbd>l</kbd>

		Change the focus to the window on the left/down/up/right side.

`windows.active.move_left` <kbd>prefix key</kbd> + <kbd>H</kbd>

`windows.active.move_down` <kbd>prefix key</kbd> + <kbd>J</kbd>

`windows.active.move_up` <kbd>prefix key</kbd> + <kbd>K</kbd>

`windows.active.move_right` <kbd>prefix key</kbd> + <kbd>L</kbd>

		Move the current window to the far left/down/up/right part of the screen.

`windows.delte` `:bd[elete] {winname}` `:bd[elete] [N]`

		Close window {winname} (default: current buffer)

		Close window [N] (default: current buffer) and delete it from the window list

`windows.activate` `:b[uffer] {winname}` `:b[uffer] [N]`

		Open window {winname}

		Open window [N] from the window list

`windows.list` `:buffers` `:ls`

		List windows

`windows.active.centralize` `:centralize` `:ce`

		Centralize the active window

`windows.active.only` `:only` `:on` <kbd>prefix key</kbd> + <kbd>o</kbd>

		Make the active window the only one on the screen.  All other windows are minimized.

`windows.active.maximize` `:maximize` `:ma`

		Maximize the active window

`windows.active.minimize` `:q[uit]` <kbd>prefix key</kbd> + <kbd>q</kbd>

		Minimize the active window

`applications.launch` `:e[dit] {appname}`

		Launch {appname}

`terminal.bang` `:!{cmd}`

		Execute {cmd} with the shell

`window.active.minimize` <kbd>prefix key</kbd> + <kbd>esq</kbd> or <kbd>prefix key</kbd> + <kbd>ctrl + [</kbd>

		Quit pwm operation and close its UI

