# ![alt text](data/icon/poco.svg "Poco logo") Poco

Poco is a desktop environment utility to organize windows in a stack and to
operate on their focus, position, state, layout using commands bound to keys and
names.

### Rationale

Poco is an attempt to bring the most comfortable mappings and logic to work
with windows inside (mainly) dwm and Vim to the desktop environment of choice.

### Usage

Commands are bound to names and keys inside Poco mappings
module. A command can be called from both a bound key or from the colon prompt.

Keys can be simple or combined.
Simple key straight cause the bound command to be called.
Combined keys are composed of a
[prefix key](https://manpages.debian.org/buster/tmux/tmux.1.en.html#KEY_BINDINGS)
(<kbd>Ctrl</kbd> + <kbd>q</kbd> by default) followed by a
[command key](https://manpages.debian.org/buster/tmux/tmux.1.en.html#KEY_BINDINGS).
The prefix key starts a reading and waits for a command key or a colon key.
By default, command keys are mapped to commands to change window focus, position, and state like 
[CTRL-W commands](http://vimdoc.sourceforge.net/htmldoc/windows.html#windows-intro)
or
[window commands](http://vimdoc.sourceforge.net/htmldoc/vimindex.html#CTRL-W)
in Vim.

### Reading

The prefix key causes Poco to start a reading, which is the process of to open a window
to capture the following key. The following key can both start the colon prompt
or, if a command key, to call a command.

While inside a reading,
commands can output messages which will be listed on top of the window.
The reading will continue until a command is successfully called and returned
with no message. The window will remain visible while the reading is started.
This logic allows usages like to close a set of windows:

1. start a reading using the prefix key
2. list all windows in the workspace entering :buffers in the colon prompt
3. pass window numbers (as listed by :buffers) as parameters to :bdelete

### Layout

Poco default mappings are mainly dwm key bindings for commands to change the
layout function, increase/decrease the master area, promote/demote a window
up/down or to the top of the stack. By default, Poco uses 
[tiled](https://dwm.suckless.org/tutorial/) layout. The other 3 layouts:
floating, monocle, [centeredmaster](https://dwm.suckless.org/patches/centeredmaster/)
can be chosen either by selecting their option on the status icon on the DE
panel or by calling their command via a bound key.
Each layout is visually indicated by a custom icon in the DE panel:

![floating](data/icon/48x48/poco.png "Poco logo") | ![floating](data/icon/48x48/poco-M.png "Poco logo")
-|-
![floating](data/icon/48x48/poco-T.png "Poco logo") | ![floating](data/icon/48x48/poco-C.png "Poco logo")


### Vim

Poco borrows Vim commands and keys to manipulate buffers. A buffer
means both an application and a window. So the bellow commands will:

`:ls` lists current windows.

`:b4` change the focus to the window number 4.

`:buffer term` brings the focus to the window containing `term` in the title if any.

`:bd` closes the current window.

`:edit calc` launch an application containing `calc` in the name like a calculator app.


### Commands

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

		Quit Poco operation and close its UI


### Installation

1. From PPA, for Ubuntu distributions
	```bash
	sudo add-apt-repository ppa:pedrosans/poco
	sudo apt-get update
	sudo apt-get install poco
	```
2. Make file

	```bash
	sudo make install
	```

	Dependencies for debian/ubuntu:
	```bash
	sudo make dependencies
	```

	To uninstall:

	```bash
	sudo make uninstall
	```

3. Manually

	1. Install poco's dependencies

		`python3 gir1.2-gtk-3.0 python3-gi-cairo` python + gtk  
		`python3-xdg` free desktop standards used to configure and launch poco  
		`gir1.2-wnck-3.0 libwnck-3-0` functions to navigate X windows  
		`gir1.2-appindicator3-0.1` used to indicate poco running on the statur bar  
		`gir1.2-keybinder-3.0 python3-dbus` bind navigation functions to keyboard prefix + shortcuts  
		`python3-setproctitle` used to name the running process
		`python3-xlib,libx11-dev` used to listen the keyboard

		on Unbuntu:

		```bash
		sudo apt-get install python3-distutils gir1.2-gtk-3.0 gir1.2-wnck-3.0 \
		gir1.2-appindicator3-0.1 gir1.2-keybinder-3.0 libwnck-3-0             \
		python3-gi-cairo python3-xdg python3-dbus python3-setproctitle        \
		python3-xlib,libx11-dev
		```
	2. Install poco
		```
		sudo ./setup.py install --record installed_files.txt
		```
		to uninstall:
		```
		sudo cat installed_files.txt | sudo  xargs rm -rf ; rm -f installed_files.txt
		```

	3. Update icons cache

		on Unbuntu:

		```
		sudo update-icon-caches /usr/share/icons/*
		```

### Commmand line interface

`poco start`: start Poco

`poco status`: show Poco process status

`poco stop`: stop Poco process

`poco --help`: show command line interface help

### Customization

#### Mappings

A custom mappings module can be provided by placing its definition in `~/.config/poco/mappings.py`.
In the case of a custom module, it will be loaded instead of the default one. The default one at
[poco/mappings.py](poco/mappings.py) is meant to be a starting point.

#### Interface

Configuration file is located at `~/.config/poco/poco.cfg` and enables:

Section `[interface]` | Customization options
-|-
`list_workspaces`| if buffers command should list windows from all workspaces. Default is `true`
`position`| `top`, `middle`, `bottom`. Default is `bottom`
`width`| interface width in pixels or `100%` if it should span the entire screen. Default is 800
`auto_hint` | show hints for the command as it is being typed. Default is `true`
`auto_select_first_hint` | if the fist option offered in the hint bar should be selected automatically. Default is `true`

`poco.cfg` example:

```
[interface]
auto_hint = true
position = middle
width = 100%
```

The style can be customized by placing a custom css at `~/.config/poco/poco.css`.
The default CSS in the module [view](poco/view.py) is meant to be used as a reference.
A possible customization example is:

```css
* {
	font-size: 14pt;
}
```

### Key grabbing

All simple key and prefix key are
[passively grabbed](https://www.x.org/wiki/Development/Documentation/GrabProcessing/)
by the display root window,
so the key won't be sent to the active window and cause side effects.
Meanwhile, command keys are consumed by Poco's window inside a reading,
which is opened and focused every time the prefix key is issued.
For this reason, the prefix key must be mapped to `reading.start` command.

### Terminology

While 'colon prompt' and 'prefix key' are terms from 
[GNU screen](https://www.gnu.org/software/screen/manual/html_node/Commands.html)
and
[tmux](https://manpages.debian.org/buster/tmux/tmux.1.en.html#KEY_BINDINGS),
similar pieces are referred to as 'command prompt' and 'termwinkey'
by also tmux and [Vim](https://vimhelp.org/options.txt.html#%27termwinkey%27)
documentation. They share the same logic and are referred to as
'colon prompt' and 'prefix key' inside Poco documentation and source code.
