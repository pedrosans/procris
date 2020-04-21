# ![logo](data/icon/pocoy.svg "pocoy logo") pocoy

<div align="center">
<a href="https://github.com/pedrosans/pocoy-media/raw/master/tile-example-01.png">
<img src="https://github.com/pedrosans/pocoy-media/raw/master/preview.png" />
</a>
</div>

pocoy is a window management tool to tile and navigate windows with layout, key and names from dwm and Vim, 
being the goal to enable a standard way to navigate inside Vim, Tmux and the WM.

## Overview

Commands are bound to names and keys in the config module.
Keys can be combined of
[prefix key](https://manpages.debian.org/buster/tmux/tmux.1.en.html#KEY_BINDINGS)
+
[command key](https://manpages.debian.org/buster/tmux/tmux.1.en.html#KEY_BINDINGS),
which are by default bound to
Vim's [window commands](http://vimdoc.sourceforge.net/htmldoc/vimindex.html#CTRL-W).


Examples:

Close a set of windows

1. open the colon prompt (<kbd>prefix key</kbd> + <kbd>:</kbd>)
2. list existing windows (`:buffers`)
3. list to close window numbers delete command (`:bdelete 3 5 6`)

Focus on a task

1. <kbd>prefix key</kbd> + <kbd>o</kbd> to quit all visible windows but the active one.


The prefix key is <kbd>Ctrl</kbd> + <kbd>q</kbd> by default. A custom config module can
be defined at `~/.config/pocoy/config.py`, being the default
one [pocoy/config.py](pocoy/config.py) meant to be a starting point. For keys and names documentation:

```shell
groff -mman pocoy.1 -T utf8 | less
```

### dwm stuff

Main dwm keys to set the layout and navigate are bound by default.
In addition, a layout can be selected by their option in the DE panel (if running on a DE).

Each layout is visually indicated by a custom icon, being the main one:

||none|monocle|tile|[centeredmaster](https://dwm.suckless.org/patches/centeredmaster/)|[spiral](https://dwm.suckless.org/patches/fibonacci/)|dwindle|
|---|---|---|---|---|---|---|
|Icon| ![floating](data/icon/48x48/pocoy-dark.png "pocoy logo") | ![floating](data/icon/48x48/pocoy-M-dark.png "pocoy logo") | ![floating](data/icon/48x48/pocoy-T-dark.png "pocoy logo") | ![floating](data/icon/48x48/pocoy-C-dark.png "pocoy logo") | ![floating](data/icon/48x48/pocoy-@-dark.png "pocoy logo") | ![floating](data/icon/48x48/pocoy-\\-dark.png "pocoy logo")
|Default key|ctrl+f|ctrl+m|ctrl+t||||


### Vim stuff

A set of Vim names and keys to manipulate buffers, which translates to
both application and windows inside pocoy, works like:

`:ls` list current windows.

`:b4` focus window number 4

`:buffer term` activate window containing `term` in the title if any

`:bd` close the current window

`:edit calc` launches an application containing `calc` in the name

## Installation

1. From PPA, for Ubuntu distributions
	```bash
	sudo add-apt-repository ppa:pedrosans/pocoy
	sudo apt-get update
	sudo apt-get install pocoy
	```

3. Manually

	1. Install pocoy's dependencies

		Unbuntu dependencies:

		```bash
		python3-distutils python3-xdg python3-dbus python3-setproctitle python3-xlib \
		gir1.2-gtk-3.0 gir1.2-wnck-3.0 gir1.2-appindicator3-0.1 gir1.2-notify-0.7 libx11-6
		```
		Arch dependencies:

		```bash
		python-pyxdg python-dbus python-setproctitle python-xlib \
		libwnck3 gobject-introspection-runtime libappindicator-gtk3 libx11
		```

	2. Install pocoy
		```
		./setup.py install --record installed_files.txt
		```
		to uninstall:
		```
		cat installed_files.txt | xargs rm -rf ; rm -f installed_files.txt
		```

	3. Update hicolor icons cache

		on Unbuntu: `update-icon-caches /usr/share/icons/hicolor`

		on Arch: `gtk-update-icon-cache -f --include-image-data /usr/share/icons/hicolor`

### Start pocoy

Via DE: `/usr/share/applications/pocoy.desktop`

Via command line: `pocoy`

## Configuration

### config module

The module defines a set of configuration variables that will be read when pocoy starts.
For customizations, new one needs to be place at `~/.config/pocoy/config.py`.

Default config module: [pocoy/config.py](pocoy/config.py)

Property|Description|Default
-|-|-
`keys` | list of keys and their correspondent command | [config.py](pocoy/config.py)
`names` | list of keys and their correspondent command | [config.py](pocoy/config.py)
`list_workspaces`| if buffers command should list windows from all workspaces. |`true`
`position`| colon prompt positon on the monitor `top`, `middle`, `bottom` | `bottom`
`width`| colon prompt width in pixels or `100%` if it should span the entire screen. | 800
`auto_hint` | show hints for the command as it is being typed. | `true`
`auto_select_first_hint` | if the fist option offered in the hint bar should be selected automatically. | `true`


### colon prompt window

Components in the window like the font size can be customized via a CSS file
by placing one at `~/.config/pocoy/pocoy.css`.

Default CSS at the bottom of [pocoy/view.py](pocoy/view.py)

Example:

```css
* {
	font-size: 14pt;
}
```

### window borders

pocoy does not add border around windows. For reference, one can define it
with a different color for the active window by placing `~/.config/gtk-3.0/gtk.css`
with:

```css
decoration {
	border-radius: 0;
}
.fullscreen decoration,
.tiled decoration {
	border-radius: 0; 
}
.popup decoration {
	border-radius: 0; 
}
.ssd decoration {
	border-radius: 0;
	box-shadow: 0 0 0 2px @theme_fg_color;
}
.ssd decoration:backdrop {
	box-shadow: 0 0 0 2px @theme_bg_color;
}
.csd decoration {
	border-radius: 0;
	box-shadow: 0 0 0 2px @theme_fg_color;
}
.csd decoration:backdrop {
	box-shadow: 0 0 0 2px @theme_bg_color;
}
.csd.popup decoration {
	border-radius: 0;
	box-shadow: 0 0 0 2px @theme_fg_color;
}
.csd.popup decoration:backdrop {
	box-shadow: 0 0 0 2px @theme_bg_color;
}
tooltip.csd decoration {
	border-radius: 0;
	box-shadow: 0 0 0 2px @theme_fg_color;
}
tooltip.csd decoration:backdrop {
	box-shadow: 0 0 0 2px @theme_bg_color;
}
```

Documentation note:

While 'colon prompt' and 'prefix key' are terms from 
[GNU screen](https://www.gnu.org/software/screen/manual/html_node/Commands.html)
and
[tmux](https://manpages.debian.org/buster/tmux/tmux.1.en.html#KEY_BINDINGS),
similar pieces are referred to as 'command prompt' and 'termwinkey'
by also tmux and [Vim](https://vimhelp.org/options.txt.html#%27termwinkey%27)
documentations.
They share the same logic and are 'colon prompt' and 'prefix key' on the documentation + source code.
