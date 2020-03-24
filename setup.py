#!/usr/bin/env python3
from distutils.core import setup

from procris.desktop import ICON_STYLES_MAP
from procris.layout import FUNCTIONS_MAP

FUNCTION_KEYS = FUNCTIONS_MAP
ICON_STYLE_KEYS = ICON_STYLES_MAP

icons = [
	('/usr/share/icons/hicolor/symbolic', ['data/icon/procris.svg']),
	('/usr/share/icons/hicolor/scalable/apps', ['data/icon/procris.svg']),
]

for size in (16, 48, 96, 256):
	for name in ICON_STYLE_KEYS:
		for layout_key in FUNCTION_KEYS:
			function_segment = '-{}'.format(layout_key) if layout_key else ''
			name_segment = '-{}'.format(name)
			icons.append((
				'/usr/share/icons/hicolor/{}x{}/apps'.format(size, size),
				['data/icon/{}x{}/procris{}{}.png'.format(size, size, function_segment, name_segment)]))

setup(
	name='Procris',
	version='0.3',
	description='Tiling desktop environment plugin',
	author='Pedro Santos',
	author_email='pedrosans@gmail.com',
	url='https://github.com/pedrosans/procris',
	classifiers=['License :: GPL3'],
	packages=['procris'],
	scripts=['bin/procris', 'bin/procris-msg'],
	data_files=
	[
		('/usr/share/bash-completion/completions/', ['data/completion/procris']),
		('/usr/share/applications/', ['data/procris.desktop']),
		('/usr/share/man/man1/', ['procris.1.gz']),
	] + icons,
)
