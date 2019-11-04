#!/usr/bin/env python3
from distutils.core import setup

FUNCTION_KEYS = ['', 'C', 'T', 'M']

icons = [
	('/usr/share/icons/hicolor/symbolic', ['data/icon/poco.svg']),
	('/usr/share/icons/hicolor/scalable/apps', ['data/icon/poco.svg']),
]

for size in (16, 48, 256):
	for name_diff in ('', '-light'):
		for layout_key in FUNCTION_KEYS:
			key_func_name_diff = ''
			if layout_key:
				key_func_name_diff = key_func_name_diff + '-' + layout_key
			icons.append((
				'/usr/share/icons/hicolor/{}x{}/apps'.format(size, size),
				['data/icon/{}x{}/poco{}{}.png'.format(size, size, key_func_name_diff, name_diff)]))

setup(
	name='Poco',
	version='0.1',
	description='Desktop environment utility to organize windows',
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
		('/usr/share/man/man1/', ['poco.1.gz']),
	] + icons,
)
