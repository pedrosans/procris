import threading
import time
from datetime import datetime
import os
import sys
import subprocess

from procris.layout import Layout

from procris.windows import Windows

import procris.names
import procris.applications as applications
import procris.terminal as terminal
from subprocess import Popen
import gi
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, Gdk

p = os.path.realpath(__file__)
sys.path.append(p + "/..")
applications.load()


def list_application_names():
	for app_name in applications.NAME_MAP.keys():
		print('{}  ::: {}'.format(
			app_name, applications.NAME_MAP[app_name].getName()))


def launch_app():
	c_in = procris.names.PromptInput(text='e Firefox Web Browser').parse()
	applications.load()
	applications.launch(c_in)


def run_command():
	# terminal.execute('alacritty --title {} '.format('asdf'))
	os.system('nautilus')
	# os.system('nautilus &')
	# Popen(['alacritty', '--title',  'asdf'], start_new_session=True)
	# Popen(['nautilus'], close_fds=True, start_new_session=True)
	# Popen(['nautilus'], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
	# subprocess.run(['nautilus'], capture_output=False, start_new_session=True, close_fds=True)
	# Popen(['nautilus'])


def callback(*args):
	print('done')


def launch_setup_apps():
	applications.launch_name(name='Calculator', desktop=0, timestamp=datetime.now().microsecond, callback=callback)
	applications.launch_name(name='Logs', desktop=1, timestamp=datetime.now().microsecond, callback=callback)
	time.sleep(2)


def workspaces_setup():
	applications.load()
	x = threading.Thread(target=launch_setup_apps)
	x.start()
	x.join()

	windows = Windows()
	windows.read_screen()
	layout = Layout(windows=windows)
	layout.read_display()

	calculator_xid = None
	logs_xid = None
	for w in Wnck.Screen.get_default().get_windows():
		if w.get_name() in ['Calculator', 'Logs']:
			w.close(datetime.now().microsecond)
			calculator_xid = w.get_xid() if w.get_name() == 'Calculator' else calculator_xid
			logs_xid = w.get_xid() if w.get_name() == 'Logs' else logs_xid

	print('calc: {} should be in: {}'.format(calculator_xid, layout.stacks[0]))
	print('logs: {} should be in: {}'.format(logs_xid, layout.stacks[1]))
	print('REPORT:')
	for w in Wnck.Screen.get_default().get_windows():
		print('{} {}'.format(w.get_xid(), w.get_name()))


# run_command()
# launch_app()
workspaces_setup()
print('done')
# sys.stdin.readline()
