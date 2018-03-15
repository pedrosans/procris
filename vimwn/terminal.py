#!/usr/bin/env python3
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
import os, glob, subprocess, shlex, re
from vimwn.command import Command

COMMANDS_GLOB = [ "/usr/bin/*", "/snap/bin/*", os.path.expanduser('~/.local/bin')+'/*' ]

class Terminal():

	def __init__(self):
		self.aliases_map = {}
		self.read_aliases()
		self.name_map= {}
		for commands_glob in COMMANDS_GLOB:
			for c in glob.glob(commands_glob):
				segs = c.split('/')
				name = segs[-1]
				self.name_map[name] = c

	def read_aliases(self):
		proc = subprocess.Popen(LIST_ALIASE, executable='bash', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		result = proc.communicate()[0].decode('utf-8')
		for alias_line in result.splitlines():
			name = re.search(r'^\s*alias\s(.*?)\s*=', alias_line).group(1)
			cmd = re.search(r'=\s*\'(.*?)\'', alias_line).group(1)
			self.aliases_map[name] = cmd

	def has_perfect_match(self, name):
		return name in self.name_map.keys()

	def list_completions(self, text):
		if ' ' in text:
			try:
				return self.query_command_parameters(text)
			except:
				print('Error trying to list completion options for a terminal command')
				return None
		else:
			return self.query_command_names(text)

	def query_command_parameters(self, vim_command_parameter):
		terminal_command = Command.extract_terminal_command(vim_command_parameter)
		parameter_text = vim_command_parameter.replace(terminal_command, '', 1)
		terminal_command_spacer = re.match(r'^\s*', parameter_text).group()
		terminal_command_parameter = parameter_text.replace(terminal_command_spacer, '', 1)

		completions = self.list_bash_completions(vim_command_parameter)

		completions = filter( lambda x : x.startswith(terminal_command_parameter), completions)
		completions = filter( lambda x : x != terminal_command_parameter, completions)
		return sorted(list(set(completions)))

	def list_bash_completions(self, text):
		cmd = SOURCE + 'get_completions \'' + text + '\''
		proc = subprocess.Popen(cmd, executable='bash', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		result = proc.communicate()[0].decode('utf-8')
		return map(lambda x : x.strip(), result.splitlines())

	def query_command_names(self, name_filter):
		names = self.name_map.keys()
		names = filter(lambda x : x.startswith(name_filter), names)
		names = filter(lambda x : x.strip() != name_filter, names)
		return sorted(list(set(names)))

	def execute(self, cmd):
		subprocess.Popen(shlex.split(cmd))

LIST_ALIASE = """
source $HOME/.bash_aliases 2>/dev/null
alias
"""
#
# Author: Brian Beffa <brbsix@gmail.com>
# Original source: https://brbsix.github.io/2015/11/29/accessing-tab-completion-programmatically-in-bash/
# License: LGPLv3 (http://www.gnu.org/licenses/lgpl-3.0.txt)
#
SOURCE = """
get_completions(){
	local completion COMP_CWORD COMP_LINE COMP_POINT COMP_WORDS COMPREPLY=()

	# load bash-completion if necessary
	declare -F _completion_loader &>/dev/null || {
		source /usr/share/bash-completion/bash_completion
	}

	COMP_LINE=$*
	COMP_POINT=${#COMP_LINE}

	eval set -- "$@"

	COMP_WORDS=("$@")

	# add '' to COMP_WORDS if the last character of the command line is a space
	[[ ${COMP_LINE[@]: -1} = ' ' ]] && COMP_WORDS+=('')

	# index of the last word
	COMP_CWORD=$(( ${#COMP_WORDS[@]} - 1 ))

	# determine completion function
	completion=$(complete -p "$1" 2>/dev/null | awk '{print $(NF-1)}')

	# run _completion_loader only if necessary
	[[ -n $completion ]] || {

		# load completion
		_completion_loader "$1"

		# detect completion
		completion=$(complete -p "$1" 2>/dev/null | awk '{print $(NF-1)}')

	}

	# ensure completion was detected
	[[ -n $completion ]] || return 1

	# execute completion function
	"$completion"

	# print completions to stdout
	printf '%s\\n' "${COMPREPLY[@]}" | LC_ALL=C sort
	}
"""
