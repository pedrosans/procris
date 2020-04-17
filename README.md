# ![logo](data/icon/pocoy.svg "pocoy logo") pocoy

<div align="center">
<a href="https://github.com/pedrosans/pocoy-media/raw/master/tile-example-01.png">
<img src="https://github.com/pedrosans/pocoy-media/raw/master/preview.png" />
</a>
</div>

pocoy is a window management tool to add tiling and navigation features
from dwm and Vim to the window manager of choice.
It adds the prefix key + command key combinations in addition to dwm keys,
thus enabling a standard set of commands to navigate inside Vim, Tmux and the WM
on top of windows tiled in master and stack areas.

### Usage

Commands are bound to names and keys in the config module.
Keys can be combined of
[prefix key](https://manpages.debian.org/buster/tmux/tmux.1.en.html#KEY_BINDINGS)
+
[command key](https://manpages.debian.org/buster/tmux/tmux.1.en.html#KEY_BINDINGS),
which are by default bound to a set of
Vim [window commands](http://vimdoc.sourceforge.net/htmldoc/vimindex.html#CTRL-W).


Example:

1. open the colon prompt <kbd>prefix key</kbd> + <kbd>:</kbd>
2. list windows by entering `buffers`
3. pass window numbers (as listed by `:buffers`) as parameters to `:bdelete` to close a set of windows

or:

1. <kbd>prefix key</kbd> + <kbd>o</kbd> to quit all visible windows but the active one.


The prefix key is <kbd>Ctrl</kbd> + <kbd>q</kbd> by default. A custom config module can
be defined at `~/.config/pocoy/config.py`, being the default
[one](pocoy/config.py) meant to be a starting point. For all keys and names:

```shell
groff -mman pocoy.1 -T utf8 | less
```

### dwm stuff

The usual dwm keys are bound by default.
The layout can be selected by their option in the status icon on the DE panel (if running on a DE)
or via a bound key or name.

Each layout is visually indicated by a custom icon in the DE panel. Main layouts are bound by default:

||none|monocle|tile|[centeredmaster](https://dwm.suckless.org/patches/centeredmaster/)|centeredfloatingmaster|[spiral](https://dwm.suckless.org/patches/fibonacci/)|dwindle|
|---|--|---|---|---|---|---|---|
|Icon| ![floating](data/icon/48x48/pocoy-dark.png "pocoy logo") | ![floating](data/icon/48x48/pocoy-M-dark.png "pocoy logo") | ![floating](data/icon/48x48/pocoy-T-dark.png "pocoy logo") | ![floating](data/icon/48x48/pocoy-C-dark.png "pocoy logo") | ![floating](data/icon/48x48/pocoy->-dark.png "pocoy logo") | ![floating](data/icon/48x48/pocoy-@-dark.png "pocoy logo") | ![floating](data/icon/48x48/pocoy-\\-dark.png "pocoy logo")
|Default key|ctrl+f|ctrl+m|ctrl+t|||||


### Vim stuff

The set of Vim names and keys to manipulate buffers, which translates to
both application and windows inside pocoy, works like:

`:ls` lists current windows.

`:b4` change the focus to the window number 4.

`:buffer term` activate the window containing `term` in the title if any.

`:bd` closes the current window.

`:edit calc` launches an application containing `calc` in the name like a calculator.

### Installation

1. From PPA, for Ubuntu distributions
	```bash
	sudo add-apt-repository ppa:pedrosans/pocoy
	sudo apt-get update
	sudo apt-get install pocoy
	```
2. Make file

	```bash
	sudo make install
	```

	To uninstall:

	```bash
	sudo make uninstall
	```

3. Manually

	1. Install pocoy's dependencies

		`python3 gir1.2-gtk-3.0 python3-gi-cairo` python + gtk  
		`python3-xdg` free desktop standards used to configure and launch pocoy  
		`gir1.2-wnck-3.0 libwnck-3-0` functions to navigate X windows  
		`gir1.2-appindicator3-0.1` used to indicate pocoy running on the statur bar  
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

	2. Install pocoy
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

### Start pocoy

Via DE:

`/usr/share/applications/pocoy.desktop`

Via command line:

`pocoy`: start pocoy

#### Configuration

##### config module

The config module has 3 variables: parameters, keys, names.

- keys and names: list of `Key` and `Name` objects binding keys and names to functions.
- parameters: optional dictionary of optional parameters and their values:

Property|Description|Default
-|-|-
`list_workspaces`| if buffers command should list windows from all workspaces. |`true`
`position`| colon prompt positon on the monitor `top`, `middle`, `bottom` | `bottom`
`width`| colon prompt width in pixels or `100%` if it should span the entire screen. | 800
`auto_hint` | show hints for the command as it is being typed. | `true`
`auto_select_first_hint` | if the fist option offered in the hint bar should be selected automatically. | `true`


##### interface

Font size: create and add to `~/.config/pocoy/pocoy.css` ( more properties in [view](pocoy/view.py) module)

```css
* {
	font-size: 14pt;
}
```

Border around active window: create and add to `~/.config/gtk-3.0/gtk.cs`

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
