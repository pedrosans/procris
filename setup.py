#!/usr/bin/env python3

from distutils.core import setup

setup(name='vimwn',
	version='1.6',
	description='Maps Vim window commands to Libwnck functions to move and navigate around X windows',
	author='Pedro Santos',
	author_email='pedrosans@gmail.com',
	url='https://github.com/pedrosans/vimwn',
	classifiers=['License :: GPL3'],
	packages=['vimwn'],
	scripts=['bin/vimwn'],
	data_files=[
		('/usr/share/bash-completion/completions/', ['data/completion/vimwn']),
		('/usr/share/applications/', ['data/vimwn.desktop']),
		('/usr/share/icons/hicolor/48x48/apps', ['data/icon/48x48/vimwn.png']),
		('/usr/share/icons/hicolor/256x256/apps', ['data/icon/256x256/vimwn.png']),
		('/usr/share/icons/hicolor/256x256/apps', ['data/icon/256x256/vimwn-light.png']),
		('/usr/share/icons/hicolor/256x256/apps', ['data/icon/256x256/vimwn-dark.png']),
	],
)
