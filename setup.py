#!/usr/bin/env python3
from distutils.core import setup

from pwm.desktop import ICON_STYLES_MAP
from pwm.layout import FUNCTIONS_MAP

FUNCTION_KEYS = FUNCTIONS_MAP
ICON_STYLE_KEYS = ICON_STYLES_MAP

icons = [
	('/usr/share/icons/hicolor/symbolic', ['data/icon/pwm.svg']),
	('/usr/share/icons/hicolor/scalable/apps', ['data/icon/pwm.svg']),
]

for size in (16, 48, 96, 256):
	for name in ICON_STYLE_KEYS:
		for layout_key in FUNCTION_KEYS:
			function_segment = '-{}'.format(layout_key) if layout_key else ''
			name_segment = '-{}'.format(name)
			icons.append((
				'/usr/share/icons/hicolor/{}x{}/apps'.format(size, size),
				['data/icon/{}x{}/pwm{}{}.png'.format(size, size, function_segment, name_segment)]))

setup(
	name='pwm',
	version='0.3',
	description='Plugable window management',
	author='Pedro Santos',
	author_email='pedrosans@gmail.com',
	url='https://github.com/pedrosans/pwm',
	classifiers=['License :: GPL3'],
	packages=['pwm'],
	scripts=['bin/pwm', 'bin/pwm-msg'],
	data_files=
	[
		('/usr/share/bash-completion/completions/', ['data/completion/pwm']),
		('/usr/share/applications/', ['data/pwm.desktop']),
		('/usr/share/man/man1/', ['pwm.1.gz']),
	] + icons,
)
