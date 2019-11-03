# ![alt text](data/icon/poco.svg "Poco logo") Poco

Poco is a desktop environment utility to organize windows as a
stack and to operate on their focus, position, state and layout using
commands bound to keys and names.

### Rationale

Poco is an attempt to bring the most comfortable mappings and logic to work
with windows inside (mainly) dwm and Vim to the desktop environment of choice.

### Usage

Commands are bound to names and keys inside Poco mappings
module. A command can be called from both a bound key or from the colon prompt.

Unless a custom mapping module is defined at `~/.config/poco/mappgins.py`, Poco loads
the default on: [poco/mappings.py](poco/mappings.py).

Keys can be simple or combined.
Simple key straight cause the bound command to be called.
Combined key bindings are composed by a
[prefix key](https://manpages.debian.org/buster/tmux/tmux.1.en.html#KEY_BINDINGS)
followed by a
[command key](https://manpages.debian.org/buster/tmux/tmux.1.en.html#KEY_BINDINGS).
The prefix key starts a reading that waits for a command or colon key.
By default command keys are mapped to commands to change the window focus, position and state like 
[CTRL-W commands](http://vimdoc.sourceforge.net/htmldoc/windows.html#windows-intro)
or
[window commands](http://vimdoc.sourceforge.net/htmldoc/vimindex.html#CTRL-W)
in Vim.

### Reading

The prefix key causes Poco to start a reading, which is a process of to open a window
to capture the following key. The following key can both start the colon prompt
or, if a command key, to call a command.

While inside a reading,
commands can output messages which will be listed on top of the window.
The reading will continue until a command is successfuly called and returned
no message and the window will remain visible while the reading started.
This logic allow usages like to close a set of windows:

1. start a reading using the prefix key
2. list all windows in the workspace entering :buffers in the colon prompt
3. pass window numbers (as listed by :buffers) as parameters to :bdelete

### Terminology

While 'colon prompt' and 'prefix key' are terms from 
[GNU screen](https://www.gnu.org/software/screen/manual/html_node/Commands.html)
and
[tmux](https://manpages.debian.org/buster/tmux/tmux.1.en.html#KEY_BINDINGS),
similiar pieces are refered as 'command prompt' and 'termwinkey'
by also tmux and [Vim](https://vimhelp.org/options.txt.html#%27termwinkey%27)
documentations. They share the same logic and are refered as
'colon prompt' and 'prefix key' inside Poco documentation and source code.

### Layout

Poco default mappings are a mix of dwm and xmodad keys and commands to change the layout function,
increase/decrease the master area, promote/demote a window up, dwn or to the top of the stack.

### Vim

Poco borows Vim commands and keys to manipulate buffers. A buffer
means both an application and a window. So the bellow commands will:

`:ls` lists current windows

`:b4` change the focus to the window number 4

`:buffer term` brings the focus to the the window containing `term` in the title, if any.

`:bd` closes the current window.

`:edit calc` launchs an application containing `calc` in the name like a calculator app.


### Key grabbing

All simple key and prefix key are
[passively grabbed](https://www.x.org/wiki/Development/Documentation/GrabProcessing/)
by the display root window,
so the key won't be sent to the active window and cause side effects.
Meanwille, command keys are consumed by Poco window inside a reading,
which is opened and focused every time the the prefix key is issued.
For this reason, it is mandatory that the prefix key is mapped to the `reading.start` command.


#### Commands

	# tile window managers bindings
	Key(['<Ctrl>Return'], layout.move_to_master),
	Key(['<Ctrl>KP_Enter'], layout.move_to_master),
	Key(['<Ctrl>i'], layout.increment_master, [1]),
	Key(['<Ctrl>d'], layout.increment_master, [-1]),
	Key(['<Ctrl>l'], layout.increase_master_area, [0.05]),
	Key(['<Ctrl>h'], layout.increase_master_area, [-0.05]),
	Key(['<Ctrl>u'], layout.change_function, ['C']),
	Key(['<Ctrl>t'], layout.change_function, ['T']),

	# xmonad bindings https://xmonad.org/manpage.html
	Key(['<Ctrl><Shift>j'], layout.swap_focused_with, [1]),
	Key(['<Ctrl><Shift>k'], layout.swap_focused_with, [-1]),


* `windows.focus.cycle` <kbd>prefix key</kbd> + <kbd>w</kbd>

	Move focus to the window below/right of the current one

* `windows.focus.move_left` <kbd>prefix key</kbd> + <kbd>h</kbd>
* `windows.focus.move_down` <kbd>prefix key</kbd> + <kbd>j</kbd>
* `windows.focus.move_up` <kbd>prefix key</kbd> + <kbd>k</kbd>
* `windows.focus.move_right` <kbd>prefix key</kbd> + <kbd>l</kbd>

	Change the focus to the window on the left/down/up/right side.

* `windows.active.move_left` <kbd>prefix key</kbd> + <kbd>H</kbd>
* `windows.active.move_down` <kbd>prefix key</kbd> + <kbd>J</kbd>
* `windows.active.move_up` <kbd>prefix key</kbd> + <kbd>K</kbd>
* `windows.active.move_right` <kbd>prefix key</kbd> + <kbd>L</kbd>

	Move the current window to the far left/down/up/right part of the screen.

* `windows.delte` `:bd[elete] {winname}` `:bd[elete] [N]`

	Close window {winname} (default: current buffer)

	Close window [N] (default: current buffer) and delete it from the window list

* `windows.activate` `:b[uffer] {winname}` `:b[uffer] [N]`

	Open window {winname}

	Open window [N] from the window list

* `windows.list` `:buffers` `:ls`

	List windows

* `windows.active.centralize` `:centralize` `:ce`

	Centralize the active window

* `windows.active.only` `:only` `:on` <kbd>prefix key</kbd> + <kbd>o</kbd>

	Make the active window the only one on the screen.  All other windows are minimized.

* `windows.active.maximize` `:maximize` `:ma`

	Maximize the active window

* `windows.active.minimize` `:q[uit]` <kbd>prefix key</kbd> + <kbd>q</kbd>

	Minimize the active window

* `applications.launch` `:e[dit] {appname}`

	Launch {appname}

* `terminal.bang` `:!{cmd}`

	Execute {cmd} with the shell

* `window.active.minimize` <kbd>prefix key</kbd> + <kbd>esq</kbd> or <kbd>prefix key</kbd> + <kbd>ctrl + [</kbd>

	Quit poco operation and close its UI


## Installation

1. From PPA, for Ubuntu distributions
	```bash
	sudo add-apt-repository ppa:pedrosans/poco
	sudo apt-get update
	sudo apt-get install poco
	```
2. From source code

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

## Commmand line interface

`poco start`: start poco

`poco status`: show poco process status

`poco stop`: stop poco process

`poco --help`: show command line interface help

## Customization

##### Configuration file is located at `$HOME/.config/poco/poco.cfg` and enables:

Section `[interface]` | Customization options
-|-
`list_workspaces`| if buffers command should list windows from all workspaces. Default is `true`
`position`| `top`, `middle` and `bottom`. Default is `bottom`
`width`| interface width in pixels or `100%` if the it should span the entire screen. Default is 800
`auto_hint` | show hints for the command as it is being typed. Default is `true`
`auto_select_first_hint` | if the fist option offered in the hint bar should be selected automatically. Default is `true`

`poco.cfg` example:

```
[interface]
auto_hint = true
position = midle
width = 100%
```

##### The style can be customized by creating and editing `$HOME/.config/poco/poco.css`

The default CSS can be found and used as a reference at [poco/view.py](poco/view.py)

`poco.css` example:

```css
* {
	font-size: 14pt;
}
```
