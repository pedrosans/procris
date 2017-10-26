# vimwn
Emulates Vim commands to move and navigate around windows. It works by using Libwnck API so it will work on window managers respecting Extended Window Manager Hints (EWMH)

## Usage
Windows may be controlled by using a key combination of a prefix key, ‘C-q’ (Ctrl-q) by default, followed by:

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

### From source code
```
sudo python setup.py install
```
To track the list of installed files so vimwn can be uninstalled:
```
sudo python setup.py install --record installed_files.txt
sudo cat installed_files.txt | sudo  xargs rm -rf ; rm -f installed_files.txt
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
