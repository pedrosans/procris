"""
Copyright 2017 Pedro Santos

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import gi
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck
from typing import List
from pocoy import state
from pocoy.wm import set_geometry, resize, get_height, get_width
from pocoy.model import Monitor


#
# LAYOUTS
#
# https://git.suckless.org/dwm/file/dwm.c.html#l1674
# MIT/X Consortium License
#
# © 2006-2019 Anselm R Garbe <anselm@garbe.ca>
# © 2006-2009 Jukka Salmi <jukka at salmi dot ch>
# © 2006-2007 Sander van Dijk <a dot h dot vandijk at gmail dot com>
# © 2007-2011 Peter Hartlich <sgkkr at hartlich dot com>
# © 2007-2009 Szabolcs Nagy <nszabolcs at gmail dot com>
# © 2007-2009 Christof Musik <christof at sendfax dot de>
# © 2007-2009 Premysl Hruby <dfenze at gmail dot com>
# © 2007-2008 Enno Gottox Boland <gottox at s01 dot de>
# © 2008 Martin Hurton <martin dot hurton at gmail dot com>
# © 2008 Neale Pickett <neale dot woozle dot org>
# © 2009 Mate Nagy <mnagy at port70 dot net>
# © 2010-2016 Hiltjo Posthuma <hiltjo@codemadness.org>
# © 2010-2012 Connor Lane Smith <cls@lubutu.com>
# © 2011 Christoph Lohmann <20h@r-36.net>
# © 2015-2016 Quentin Rameau <quinq@fifth.space>
# © 2015-2016 Eric Pruitt <eric.pruitt@gmail.com>
# © 2016-2017 Markus Teich <markus.teich@stusta.mhn.de>
def tile(stack: List[Wnck.Window], m):
	n = len(stack)

	if n > m.nmaster:
		mw = m.ww * m.mfact if m.nmaster else 0
	else:
		mw = m.ww
	my = ty = 0
	padding = state.get_inner_gap()

	for i in range(len(stack)):
		window = stack[i]
		if i < m.nmaster:
			h = (m.wh - my) / (min(n, m.nmaster) - i) - padding * 2
			synchronized = set_geometry(
				window, synchronous=True, x=m.wx + padding, y=m.wy + my + ty + padding, w=mw - padding * 2, h=h)
			my += (get_height(window) if synchronized else h) + padding * 2
		else:
			h = (m.wh - ty) / (n - i) - padding * 2
			synchronized = set_geometry(
				window, synchronous=True, x=m.wx + mw + padding, y=m.wy + ty + padding, w=m.ww - mw - padding * 2, h=h)
			ty += (get_height(window) if synchronized else h) + padding * 2


# https://git.suckless.org/dwm/file/dwm.c.html#l1104
def monocle(stack, monitor):
	padding = state.get_inner_gap()
	for window in stack:
		set_geometry(
			window,
			x=monitor.wx + padding, y=monitor.wy + padding,
			w=monitor.ww - padding * 2, h=monitor.wh - padding * 2)


# https://dwm.suckless.org/patches/centeredmaster/
def centeredmaster(stack: List[Wnck.Window], m: Monitor):
	tw = mw = m.ww
	mx = my = 0
	oty = ety = 0
	n = len(stack)
	padding = state.get_inner_gap()

	if n > m.nmaster:
		mw = int(m.ww * m.mfact) if m.nmaster else 0
		tw = m.ww - mw

		if n - m.nmaster > 1:
			mx = int((m.ww - mw) / 2)
			tw = int((m.ww - mw) / 2)

	for i in range(len(stack)):
		window = stack[i]
		if i < m.nmaster:
			# nmaster clients are stacked vertically, in the center of the screen
			h = int((m.wh - my) / (min(n, m.nmaster) - i)) - padding * 2
			synchronized = set_geometry(
				window, synchronous=True, x=m.wx + mx + padding, y=m.wy + my + padding, w=mw - padding * 2, h=h)
			my += (get_height(window) if synchronized else h) + padding * 2
		else:
			# stack clients are stacked vertically
			if (i - m.nmaster) % 2:
				h = int((m.wh - ety) / int((1 + n - i) / 2)) - padding * 2
				synchronized = set_geometry(
					window, synchronous=True, x=m.wx + padding, y=m.wy + ety + padding, w=tw - padding * 2, h=h)
				ety += (get_height(window) if synchronized else h) + padding * 2
			else:
				h = int((m.wh - oty) / int((1 + n - i) / 2)) - padding * 2
				synchronized = set_geometry(
					window, synchronous=True, x=m.wx + mx + mw + padding, y=m.wy + oty + padding, w=tw - padding * 2, h=h)
				oty += (get_height(window) if synchronized else h) + padding * 2


def centeredfloatingmaster(stack: List[Wnck.Window], m: Monitor):
	padding = state.get_inner_gap()
	# i, n, w, mh, mw, mx, mxo, my, myo, tx = 0
	tx = mx = 0

	# count number of clients in the selected monitor
	n = len(stack)

	# initialize nmaster area
	if n > m.nmaster:
		# go mfact box in the center if more than nmaster clients
		if m.ww > m.wh:
			mw = m.ww * m.mfact if m.nmaster else 0
			mh = m.wh * 0.9 if m.nmaster else 0
		else:
			mh = m.wh * m.mfact if m.nmaster else 0
			mw = m.ww * 0.9 if m.nmaster else 0
		mx = mxo = (m.ww - mw) / 2
		my = myo = (m.wh - mh) / 2
	else:
		# go fullscreen if all clients are in the master area
		mh = m.wh
		mw = m.ww
		mx = mxo = 0
		my = myo = 0

	for i in range(len(stack)):
		c = stack[i]
		if i < m.nmaster:
			# nmaster clients are stacked horizontally, in the center of the screen
			w = (mw + mxo - mx) / (min(n, m.nmaster) - i)
			synchronized = set_geometry(
				c, synchronous=True,
				x=m.wx + mx + padding, y=m.wy + my + padding,
				w=w, h=mh - padding * 2)
			mx += get_width(c)
		else:
			# stack clients are stacked horizontally
			w = (m.ww - tx) / (n - i) - (padding * 2)
			synchronized = set_geometry(
				c, synchronous=True,
				x=m.wx + tx + padding, y=m.wy + padding,
				w=w, h=m.wh - padding * 2)
			tx += get_width(c) + padding * 2


# https://dwm.suckless.org/patches/fibonacci/
# Credit:
# Niki Yoshiuchi - aplusbi@gmail.com
# Joe Thornber
# Jan Christoph Ebersbach
def fibonacci(mon: Monitor, stack: List[int], s: int):
	n = len(stack)
	nx = mon.wx
	ny = 0
	nw = mon.ww
	nh = mon.wh
	padding = state.get_inner_gap()

	for i in range(n):
		c = stack[i]
		c.bw = 0
		if (i % 2 and nh / 2 > 2 * c.bw) or (not (i % 2) and nw / 2 > 2 * c.bw):
			if i < n - 1:
				if i % 2:
					nh /= 2
				else:
					nw /= 2
				if (i % 4) == 2 and not s:
					nx += nw
				elif (i % 4) == 3 and not s:
					ny += nh
			if (i % 4) == 0:
				if s:
					ny += nh
				else:
					ny -= nh
			elif (i % 4) == 1:
				nx += nw
			elif (i % 4) == 2:
				ny += nh
			elif (i % 4) == 3:
				if s:
					nx += nw
				else:
					nx -= nw
			if i == 0:
				if n != 1:
					nw = mon.ww * mon.mfact
				ny = mon.wy
			elif i == 1:
				nw = mon.ww - nw
		set_geometry(
			c,
			x=nx + padding, y=ny + padding,
			w=nw - padding * 2, h=nh - padding * 2)


def dwindle(stack: List[Wnck.Window], monitor: Monitor):
	fibonacci(monitor, stack, 1)


def spiral(stack: List[Wnck.Window], monitor: Monitor):
	fibonacci(monitor, stack, 0)


def biasedstack(stack: List[Wnck.Window], monitor: Monitor):
	n = len(stack)
	if n == 1:
		resize(stack[0], l=0.15, t=0.1, w=0.7, h=0.86)
		return
	oty = 0
	mw = int(monitor.ww * monitor.mfact) if monitor.nmaster else 0
	mx = tw = int((monitor.ww - mw) / 2)
	my = 0
	padding = state.get_inner_gap()

	for i in range(n):
		window: Wnck.Window = stack[i]
		if i < monitor.nmaster:
			# nmaster clients are stacked vertically, in the center of the screen
			h = int((monitor.wh - my) / (min(n, monitor.nmaster) - i))
			set_geometry(
				window,
				x=monitor.wx + mx + padding, y=monitor.wy + my + padding,
				w=mw - padding * 2, h=h - padding * 2)
			my += h
		else:
			# stack clients are stacked vertically
			if (i - monitor.nmaster) == 0:
				set_geometry(
					window,
					x=monitor.wx + padding, y=monitor.wy + padding,
					w=tw - padding * 2, h=monitor.wh - padding * 2)
			else:
				h = int((monitor.wh - oty) / (n - i))
				synchronized = set_geometry(
					window, synchronous=True,
					x=monitor.wx + mx + mw + padding, y=monitor.wy + oty + padding,
					w=tw - padding * 2, h=h - padding * 2)

				oty += ((get_height(window) + padding * 2) if synchronized else h)


FUNCTIONS_MAP = {
	None: None,
	'M': monocle, 'T': tile,
	'C': centeredmaster, '>': centeredfloatingmaster, 'B': biasedstack,
	'@': spiral, '\\': dwindle
}
