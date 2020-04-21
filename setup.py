#!/usr/bin/env python3
from distutils.core import setup

ICON_STYLE_KEYS = ['dark', 'light']
FUNCTION_KEYS = [None, 'M', 'T', 'C', '>', '<', '@', '\\']
icons = [
	('/usr/share/icons/hicolor/symbolic', ['data/icon/pocoy.svg']),
	('/usr/share/icons/hicolor/scalable/apps', ['data/icon/pocoy.svg']),
]

for size in (16, 48, 96, 256):
	for name in ICON_STYLE_KEYS:
		for layout_key in FUNCTION_KEYS:
			function_segment = '-{}'.format(layout_key) if layout_key else ''
			name_segment = '-{}'.format(name)
			icons.append((
				'/usr/share/icons/hicolor/{}x{}/apps'.format(size, size),
				['data/icon/{}x{}/pocoy{}{}.png'.format(size, size, function_segment, name_segment)]))

setup(
	name='pocoy',
	version='0.3',
	description='plugable window management',
	author='Pedro Santos',
	author_email='pedrosans@gmail.com',
	url='https://github.com/pedrosans/pocoy',
	classifiers=['License :: GPL3'],
	packages=['pocoy'],
	scripts=['bin/pocoy', 'bin/pocoy-msg'],
	data_files=
	[
		('/usr/share/bash-completion/completions/', ['data/completion/pocoy']),
		('/usr/share/applications/', ['data/pocoy.desktop']),
		('/usr/share/man/man1/', ['data/pocoy.1.gz']),
	] + icons,
)

# eof
