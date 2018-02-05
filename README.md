# vimwn
Emulates Vim commands to move and navigate around windows.

## Usage
Windows may be controlled by using a combination of a prefix key, ‘C-q’ (Ctrl-q) by default, followed by:

### Emulated key combinations

<kbd>prefix</kbd> + <kbd>w</kbd> Move focus to window below/right of the current one

<kbd>prefix</kbd> + <kbd>o</kbd> Make the current window the only one on the screen.  All other windows are minimized.

<kbd>prefix</kbd> + <kbd>h</kbd> Move to the window on the left

<kbd>prefix</kbd> + <kbd>j</kbd> Move to the window below

<kbd>prefix</kbd> + <kbd>k</kbd> Move to the window above

<kbd>prefix</kbd> + <kbd>l</kbd> Move to the window on the right

<kbd>prefix</kbd> + <kbd>h</kbd> Move the current window to be at the far left

<kbd>prefix</kbd> + <kbd>j</kbd> Move the current window to be at the very bottom

<kbd>prefix</kbd> + <kbd>k</kbd> Move the current window to be at the very top

<kbd>prefix</kbd> + <kbd>l</kbd> Move the current window to be at the far right

<kbd>prefix</kbd> + <kbd><</kbd> Decrease current window width

<kbd>prefix</kbd> + <kbd>></kbd> Increase current window width

<kbd>prefix</kbd> + <kbd>=</kbd> Make top 2 windows equally high and wide

### Emulated commands

`:buffers` `:ls` Show all windows

`:only` `:on` Make the current window the only one on the screen.  All other windows are minimized.

`:b[uffer] {bufname}` Open window for {bufname}

`:b[uffer] [N]` Open window [N] from the window list.

`:bd[elete] {bufname}` Close window for {bufname} (default: corrent buffer) and delete it from the window list.

`:bd[elete] [N]` Close window [N] (default: corrent buffer) and delete it from the window list.

### Specific commands

`:maximizes` Maximize the active window

`:centralize` Centralize the active window

## Installation

vimwn uses Libwnck to manipulate windows so it works only on X11

### From source code

1) Install vimwn's dependencies, on Unbuntu 16.04 or 17.10:

```
sudo apt-get install python3 gir1.2-gtk-3.0 gir1.2-wnck-3.0 gir1.2-appindicator3-0.1 gir1.2-keybinder-3.0 libwnck-3-0 python3-gi-cairo python3-xdg python3-dbus python3-setproctitle

```
2) Install vimwn
```
sudo ./setup.py install --record installed_files.txt

```

To uninstall:

```
sudo cat installed_files.txt | sudo  xargs rm -rf ; rm -f installed_files.txt
```

### From PPA

```bash
sudo add-apt-repository ppa:pedrosans/vimwn
sudo apt-get update
sudo apt-get install vimwn
```

## Commmand line interface

`vimwn --start`: start vimwn as a daemon process

`vimwn --status`: show vimwn daemon process status

`vimwn --stop`: stop vimwn daemom process

`vimwn --help`: show command line interface help

## Customization

Vimwn's configuration file is located at:
```
"$HOME"/.config/vimwn/vimwn.cfg
```

And has the followin properties:

Section `[service]`:

`log_file`: Location were the standard and error output will be redirected for

Section `[interface]`:

`hotkeys`: Comma separated list for prefix keybindings

`list_workspaces`: Indicates that the `:buffers` command should output the listed window workspace

`position`: The vertical aligment of the interface, possible values are: `top`, `center` and `bottom`

`width`: The width of the interface

Example of vimwn configured to mimic vim's ctrl-w mapping:

```
[service]
log_file = /home/myuser/.vimwn/log

[interface]
hotkeys = <ctrl>q,<ctrl>w
list_workspaces = true
position = top
width = 700
```
