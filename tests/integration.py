
import os
import sys
import subprocess
import procris.names
import procris.applications as applications
import procris.terminal as terminal
from subprocess import Popen

p = os.path.realpath(__file__)
sys.path.append(p + "/..")


def list_application_names():

	applications.load()

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


run_command()
print('done')
# launch_app()

sys.stdin.readline()
