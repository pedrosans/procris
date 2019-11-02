#!/usr/bin/env python3

import poco.layout
from distutils.core import setup

icons = [
	('/usr/share/icons/hicolor/symbolic', ['data/icon/poco.svg']),
	('/usr/share/icons/hicolor/scalable/apps', ['data/icon/poco.svg']),
]

for size in (16, 48, 256):
	for name_diff in ('', '-light'):
		for layout_key in [''] + list(poco.layout.FUNCTIONS_MAP.keys()):
			key_func_name_diff = ''
			if layout_key:
				key_func_name_diff = key_func_name_diff + '-' + layout_key
			icons.append((
				'/usr/share/icons/hicolor/{}x{}/apps'.format(size, size),
				['data/icon/{}x{}/poco{}{}.png'.format(size, size, key_func_name_diff, name_diff)]))

setup(
	name='poco',
	version='0.7',
	description='Maps Vim window commands to Libwnck functions to move and navigate around X windows',
	author='Pedro Santos',
	author_email='pedrosans@gmail.com',
	url='https://github.com/pedrosans/poco',
	classifiers=['License :: GPL3'],
	packages=['poco'],
	scripts=['bin/poco'],
	data_files=
	[
		('/usr/share/bash-completion/completions/', ['data/completion/poco']),
		('/usr/share/applications/', ['data/poco.desktop']),
	] + icons,
)
