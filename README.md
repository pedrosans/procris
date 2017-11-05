# vimwn
Emulates Vim commands to move and navigate around windows.

## Usage
Windows may be controlled by using a combination of a prefix key, ‘C-q’ (Ctrl-q) by default, followed by:

### Emulated commands

`:buffers` `:ls` Show all windows

`:only` `:on` Make the current window the only one on the screen.  All other windows are minimized.

`:b[uffer] {bufname}` Open window for {bufname}

`:b[uffer] [N]` Open window [N] from the window list.

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

## Installation

vimwn uses Libwnck API so it only works on X11

### From source code

1) Install vimwn's dependencies, on Unbuntu 16.04 or 17.10:

```
sudo apt-get install python gir1.2-gtk-3.0 gir1.2-wnck-3.0 gir1.2-keybinder-3.0 libwnck-3-0 python-gi python-xdg python-dbus python-setproctitle
```
2) Install vimwn as a python package and command:
```
sudo python setup.py install
```

Instalation alternative:

To track the list of installed files so vimwn can be uninstalled:

```
sudo python setup.py install --record installed_files.txt
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

The prefix keybind can be customized at:
```
"$HOME"/.config/vimwn/vimwn.cfg
```

Example of vimwn configured to mimic vim's Ctrl-w mapping:

```
[interface]
hotkey = <ctrl>w
```
