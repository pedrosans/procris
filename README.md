# vimwn
Maps Vim window commands to Libwnck functions to move and navigate around X windows.

## Usage
X windows may be controlled by using a combination of a prefix key, <kbd>ctrl+q</kbd> by default, followed by:

### Navigation key combinations

<kbd>prefix key</kbd> + <kbd>w</kbd> Move focus to the window below/right of the current one

<kbd>prefix key</kbd> + <kbd>o</kbd> Make the current window the only one on the screen.  All other windows are minimized.

<kbd>prefix key</kbd> + <kbd>h</kbd> Move to the window on the left

<kbd>prefix key</kbd> + <kbd>j</kbd> Move to the window below

<kbd>prefix key</kbd> + <kbd>k</kbd> Move to the window above

<kbd>prefix key</kbd> + <kbd>l</kbd> Move to the window on the right

<kbd>prefix key</kbd> + <kbd>h</kbd> Move the current window to be at the far left

<kbd>prefix key</kbd> + <kbd>j</kbd> Move the current window to be at the very bottom

<kbd>prefix key</kbd> + <kbd>k</kbd> Move the current window to be at the very top

<kbd>prefix key</kbd> + <kbd>l</kbd> Move the current window to be at the far right

<kbd>prefix key</kbd> + <kbd><</kbd> Decrease current window width

<kbd>prefix key</kbd> + <kbd>></kbd> Increase current window width

<kbd>prefix key</kbd> + <kbd>=</kbd> Make top 2 windows equally high and wide

### Navigation commands

`:buffers` `:ls` List windows

`:only` `:on` Make the current window the only one on the screen

`:b[uffer] {bufname}` Open window for {bufname}

`:b[uffer] [N]` Open window [N] from the window list

`:bd[elete] {bufname}` Close window for {bufname} (default: corrent buffer) and delete it from the window list

`:bd[elete] [N]` Close window [N] (default: corrent buffer) and delete it from the window list

### Specific commands

`:maximizes` Maximize active window

`:centralize` Centralize active window

## Installation

vimwn uses Libwnck to manipulate windows so it works only on X11

### Dependencies

`python3 gir1.2-gtk-3.0 python3-gi-cairo` python + gtk  
`python3-xdg` free desktop standards used to configure and launch vimwn  
`gir1.2-wnck-3.0 libwnck-3-0` functions to navigate X windows  
`gir1.2-appindicator3-0.1` used to indicate vimwn running on the statur bar  
`gir1.2-keybinder-3.0 python3-dbus` to bind navigation functions to keyboard prefix + shortcuts  
`python3-setproctitle` used to name the running process

### From source code

1) Install vimwn's dependencies, on Unbuntu

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

`vimwn start`: start vimwn

`vimwn status`: show vimwn process status

`vimwn stop`: stop vimwn process

`vimwn --help`: show command line interface help

## Customization

Configuration file is located at `$HOME/.config/vimwn/vimwn.cfg` and enables:

Section `[interface]` | Customization options
-|-
`prefix_key`| comma separated list of prefix keybindings, defauld is <kbd>ctrl+q</kbd>
`command_prefix_key`| <kbd>prefix key</kbd> for opening vimwn in command line mode
`list_workspaces`| if buffers command should list windows from all workspaces, default is `true`
`auto_hint`| automatic command hints in the status line, default is `true`
`position`| `top`, `center` and `bottom`. Default is `bottom`
`width`| interface width in pixels or `100%` if the it should span the entire screen

Example:

```
[interface]
prefix_key = <ctrl>q,<ctrl>w
auto_hint = true
list_workspaces = true
position = midle
width = 800
```
