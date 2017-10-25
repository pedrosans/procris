#!/usr/bin/env python

from distutils.core import setup

setup(name='vimwn',
	version='1.0',
	description='Window navigator that emulates Vim commands',
	author='Pedro Santos',
	author_email='pedrosans@gmail.com',
	url='https://github.com/pedrosans/vimwn',
	classifiers=['License :: GPL3'],
	packages=['vimwn'],
	scripts=['bin/vimwn'],
)
