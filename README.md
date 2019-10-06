# vimwn
Maps Vim window commands to Libwnck functions to move and navigate around X windows. As vimwn uses Libwnck to manipulate windows, it only works on X11

## Usage
X windows may be controlled by using a combination of a prefix key, <kbd>ctrl+q</kbd> by default, followed by a command

### Commands

##### Windows


<kbd>prefix key</kbd> + <kbd>w</kbd> Move focus to the window below/right of the current one

<kbd>prefix key</kbd> + <kbd>prefix key</kbd> Also move focus to the window below/right of the current one to emulate the <kbd>ctrl + w</kbd> + <kbd>ctrl + w</kbd> sequence in Vim, even if the prefix key is not mapped to <kbd>ctrl + w</kbd>

<kbd>prefix key</kbd> + <kbd>h</kbd> Move to the window on the left

<kbd>prefix key</kbd> + <kbd>j</kbd> Move to the window below

<kbd>prefix key</kbd> + <kbd>k</kbd> Move to the window above

<kbd>prefix key</kbd> + <kbd>l</kbd> Move to the window on the right

<kbd>prefix key</kbd> + <kbd>H</kbd> Move the current window to be at the far left

<kbd>prefix key</kbd> + <kbd>J</kbd> Move the current window to be at the very bottom

<kbd>prefix key</kbd> + <kbd>K</kbd> Move the current window to be at the very top

<kbd>prefix key</kbd> + <kbd>L</kbd> Move the current window to be at the far right

<kbd>prefix key</kbd> + <kbd><</kbd> Decrease current window width

<kbd>prefix key</kbd> + <kbd>></kbd> Increase current window width

<kbd>prefix key</kbd> + <kbd>=</kbd> Make top 2 windows equally high and wide

`:bd[elete] {winname}` Close window {winname} (default: current buffer)

`:bd[elete] [N]` Close window [N] (default: current buffer) and delete it from the window list

`:b[uffer] {winname}` Open window {winname}

`:b[uffer] [N]` Open window [N] from the window list

`:buffers` `:ls` List windows

`:centralize` `:ce` Centralize the active window

`:only` `:on` 

<kbd>prefix key</kbd> + <kbd>o</kbd> Make the active window the only one on the screen.  All other windows are minimized.

`:maximize` `:ma` Maximize the active window

`:q[uit]` 

<kbd>prefix key</kbd> + <kbd>q</kbd> Minimize the active window

##### General

`:!{cmd}` Execute {cmd} with the shell

`:e[dit] {appname}` Launch {appname}

<kbd>prefix key</kbd> + <kbd>esq</kbd> or <kbd>prefix key</kbd> + <kbd>ctrl + [</kbd> Quit vimwn operation and close its UI


## Installation

1. From PPA, for Ubuntu distributions
	```bash
	sudo add-apt-repository ppa:pedrosans/vimwn
	sudo apt-get update
	sudo apt-get install vimwn
	```
2. From source code

	1. Install vimwn's dependencies

		`python3 gir1.2-gtk-3.0 python3-gi-cairo` python + gtk  
		`python3-xdg` free desktop standards used to configure and launch vimwn  
		`gir1.2-wnck-3.0 libwnck-3-0` functions to navigate X windows  
		`gir1.2-appindicator3-0.1` used to indicate vimwn running on the statur bar  
		`gir1.2-keybinder-3.0 python3-dbus` bind navigation functions to keyboard prefix + shortcuts  
		`python3-setproctitle` used to name the running process

		on Unbuntu:

		```bash
		sudo apt-get install python3-distutils gir1.2-gtk-3.0 gir1.2-wnck-3.0 \
		gir1.2-appindicator3-0.1 gir1.2-keybinder-3.0 libwnck-3-0             \
		python3-gi-cairo python3-xdg python3-dbus python3-setproctitle
		```
	2. Install vimwn
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

`vimwn start`: start vimwn

`vimwn status`: show vimwn process status

`vimwn stop`: stop vimwn process

`vimwn --help`: show command line interface help

## Customization

##### Configuration file is located at `$HOME/.config/vimwn/vimwn.cfg` and enables:

Section `[interface]` | Customization options
-|-
`prefix_key`| comma separated list of prefix keybindings. Defauld is <kbd>ctrl+q</kbd>
`list_workspaces`| if buffers command should list windows from all workspaces. Default is `true`
`position`| `top`, `middle` and `bottom`. Default is `bottom`
`width`| interface width in pixels or `100%` if the it should span the entire screen. Default is 800
`auto_hint` | show hints for the command as it is being typed. Default is `true`
`auto_select_first_hint` | if the fist option offered in the hint bar should be selected automatically. Default is `true`

`vimwn.cfg` example:

```
[interface]
prefix_key = <ctrl>q,<ctrl>w
auto_hint = true
list_workspaces = true
position = midle
width = 100%
```

##### The style can be customized by creating and editing `$HOME/.config/vimwn/vimwn.css`

The default CSS can be found and used as a reference at [vimwn/view.py](vimwn/view.py)

`vimwn.css` example:

```css
* {
	font-size: 14pt;
}
```
