#!/usr/bin/env python

from distutils.core import setup

setup(name='vimwn',
	version='1.0',
	description='Windows navigator using Vim commands',
	author='Pedro Santos',
	author_email='pedrosans@gmail.com',
	url='https://github.com/pedrosans/vimwn',
	lincense='GPL3',
	packages=['vimwn'],
	scripts=['bin/vimwn'],
	data_files = [
		('share/applications', ['data/vimwn.desktop']),
	]
)
