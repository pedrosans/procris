# Poco

Poco is a service that keeps windows in the workspace organized as a stack and maps commands to window operations on focus, position and state inside three (Normal, Command, Operator-Pending) different modes.

### Rationale

POCO is an attempt to bring the most comfortable mappings and logic to work with windows inside dwm and Vim to a desktop environment of your choice.

### Usage

Commands and keys are mapped to a function inside Poco mappings module. The default mapping is a mix of dwm and xmodad keys to manipulate the windows stack and select a layout, plus vim keys and commands to navigate, move, launch, close, minimize.

By default Poco is in normal state and besides of the status icon, there is no UI. Key binds to operate on the window stack and their layout can be used in this and any state.

Similar to Vim's [termwenkey](https://vimhelp.org/options.txt.html#%27termwinkey%27), Poco enters in operator-pending and is followed by a window command by using a combination of a prefix key, <kbd>ctrl+q</kbd> by default, plus a command key.

When in operator-pending mode, colon <kbd>:</kbd> will cause Poco to enter in command mode. A Gtk interface will show a input field to receive a command already mapped to a Poco funciton. Exemples:

`:ls` lists current windows

`:b4` bring the focus to the window number 4

`:buffer term` brings the focus to the the window containing `term` in the title, if any.

`:bd` closes the current window.

`:e text` launchs an application containing `text` in the name, if any.


#### Functions

* `focus.cycle` <kbd>prefix key</kbd> + <kbd>w</kbd>


	Move focus to the window below/right of the current one

* `focus.move_left` <kbd>prefix key</kbd> + <kbd>h</kbd>
* `focus.move_down` <kbd>prefix key</kbd> + <kbd>j</kbd>
* `focus.move_up` <kbd>prefix key</kbd> + <kbd>k</kbd>
* `focus.move_right` <kbd>prefix key</kbd> + <kbd>l</kbd>

	Change the focust to the window on the left/down/up/right side.

* `window.move_left` <kbd>prefix key</kbd> + <kbd>H</kbd>
* `window.move_down` <kbd>prefix key</kbd> + <kbd>J</kbd>
* `window.move_up` <kbd>prefix key</kbd> + <kbd>K</kbd>
* `window.move_right` <kbd>prefix key</kbd> + <kbd>L</kbd>

	Move the current window to the far left/down/up/right part of the screen.

* `commands.delte_buffer` `:bd[elete] {winname}` `:bd[elete] [N]`

	Close window {winname} (default: current buffer)

	Close window [N] (default: current buffer) and delete it from the window list

* `commands.buffer` `:b[uffer] {winname}` `:b[uffer] [N]`

	Open window {winname}

	Open window [N] from the window list

* `commands.buffers` `:buffers` `:ls`

	List windows

* `window.centralize` `:centralize` `:ce`

	Centralize the active window

* `window.only` `:only` `:on` <kbd>prefix key</kbd> + <kbd>o</kbd>

	Make the active window the only one on the screen.  All other windows are minimized.

* `window.maximize` `:maximize` `:ma`

	Maximize the active window

* `window.minimize` `:q[uit]` <kbd>prefix key</kbd> + <kbd>q</kbd>

	Minimize the active window

* `window.launch` `:e[dit] {appname}`

	Launch {appname}

* `commands.bang` `:!{cmd}`

	Execute {cmd} with the shell

* `poco.quit` <kbd>prefix key</kbd> + <kbd>esq</kbd> or <kbd>prefix key</kbd> + <kbd>ctrl + [</kbd>

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

		on Unbuntu:

		```bash
		sudo apt-get install python3-distutils gir1.2-gtk-3.0 gir1.2-wnck-3.0 \
		gir1.2-appindicator3-0.1 gir1.2-keybinder-3.0 libwnck-3-0             \
		python3-gi-cairo python3-xdg python3-dbus python3-setproctitle
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
`prefix_key`| comma separated list of prefix keybindings. Defauld is <kbd>ctrl+q</kbd>
`list_workspaces`| if buffers command should list windows from all workspaces. Default is `true`
`position`| `top`, `middle` and `bottom`. Default is `bottom`
`width`| interface width in pixels or `100%` if the it should span the entire screen. Default is 800
`auto_hint` | show hints for the command as it is being typed. Default is `true`
`auto_select_first_hint` | if the fist option offered in the hint bar should be selected automatically. Default is `true`

`poco.cfg` example:

```
[interface]
prefix_key = <ctrl>q,<ctrl>w
auto_hint = true
list_workspaces = true
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
