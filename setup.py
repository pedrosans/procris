#!/usr/bin/env python3
from distutils.core import setup

FUNCTION_KEYS = ['', 'C', 'T', 'M']

icons = [
	('/usr/share/icons/hicolor/symbolic', ['data/icon/procris.svg']),
	('/usr/share/icons/hicolor/scalable/apps', ['data/icon/procris.svg']),
]

for size in (16, 48, 256):
	for name_diff in ('', '-light'):
		for layout_key in FUNCTION_KEYS:
			key_func_name_diff = ''
			if layout_key:
				key_func_name_diff = key_func_name_diff + '-' + layout_key
			icons.append((
				'/usr/share/icons/hicolor/{}x{}/apps'.format(size, size),
				['data/icon/{}x{}/procris{}{}.png'.format(size, size, key_func_name_diff, name_diff)]))

setup(
	name='Procris',
	version='0.2',
	description='Desktop environment utility to organize windows',
	author='Pedro Santos',
	author_email='pedrosans@gmail.com',
	url='https://github.com/pedrosans/procris',
	classifiers=['License :: GPL3'],
	packages=['procris'],
	scripts=['bin/procris'],
	data_files=
	[
		('/usr/share/bash-completion/completions/', ['data/completion/procris']),
		('/usr/share/applications/', ['data/procris.desktop']),
		('/usr/share/man/man1/', ['procris.1.gz']),
	] + icons,
)
