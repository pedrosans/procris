#!/usr/bin/env python3

from distutils.core import setup

setup(name='vimwn',
	version='1.3',
	last_version='1.2',
	description='Window navigator that emulates Vim commands',
	author='Pedro Santos',
	author_email='pedrosans@gmail.com',
	url='https://github.com/pedrosans/vimwn',
	classifiers=['License :: GPL3'],
	packages=['vimwn'],
	scripts=['bin/vimwn'],
	data_files=[
		('/usr/share/bash-completion/completions/', ['data/completion/vimwn']),
		('/usr/share/applications/', ['data/vimwn.desktop']),
	],
)
