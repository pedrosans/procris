#!/usr/bin/env python3

from distutils.core import setup

setup(name='poco',
	version='0.7',
	description='Maps Vim window commands to Libwnck functions to move and navigate around X windows',
	author='Pedro Santos',
	author_email='pedrosans@gmail.com',
	url='https://github.com/pedrosans/poco',
	classifiers=['License :: GPL3'],
	packages=['poco'],
	scripts=['bin/poco'],
	data_files=[
		('/usr/share/bash-completion/completions/', ['data/completion/poco']),
		('/usr/share/applications/', ['data/poco.desktop']),
		('/usr/share/icons/hicolor/48x48/apps', ['data/icon/48x48/poco.png']),
		('/usr/share/icons/hicolor/256x256/apps', ['data/icon/256x256/poco.png']),
		('/usr/share/icons/hicolor/256x256/apps', ['data/icon/256x256/poco-light.png']),
		('/usr/share/icons/hicolor/256x256/apps', ['data/icon/256x256/poco-dark.png']),
	],
)
