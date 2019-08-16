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
import os, glob, subprocess, shlex, re, traceback
from vimwn.command import Command

COMMANDS_GLOB = ["/usr/bin/*", "/snap/bin/*", os.path.expanduser('~/.local/bin')+'/*']


class Terminal:

	def __init__(self):
		self.aliases_map = {}
		self.name_map = {}
		self._read_aliases()
		self._read_commands()

	def reload(self):
		self.aliases_map.clear()
		self.name_map.clear()
		self._read_aliases()
		self._read_commands()

	def _read_aliases(self):
		proc = subprocess.Popen(LIST_ALIASE, executable='bash', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		result = proc.communicate()[0].decode('utf-8')
		for alias_line in result.splitlines():
			name, cmd = Terminal.parse_alias_line(alias_line)
			self.aliases_map[name] = cmd

	@staticmethod
	def parse_alias_line(line):
		aliases_definition = re.search(r'^\s*alias\s+(.*)$', line).group(1)
		aliases = re.compile(r'(?<=\')\s+(?=[^\']+=\$?\'.*\')').split(aliases_definition)
		result = []
		for alias in aliases:
			name = re.search(r'(.*?)=', alias).group(1)
			cmd = re.search(r'=\$?\'(.*)\'', alias).group(1)
			result.append([name, cmd])
		return result

	def _read_commands(self):
		for commands_glob in COMMANDS_GLOB:
			for path in glob.glob(commands_glob):
				name = path.split('/')[-1]
				self.name_map[name] = path

	def has_perfect_match(self, name):
		return name in self.name_map.keys()

	def list_completions(self, command_input):
		if command_input.terminal_command_parameter:
			return self.query_command_parameters(command_input)
		else:
			return self.query_command_names(command_input.terminal_command)

	def query_command_parameters(self, command_input):

		completions = self.list_bash_completions(command_input.vim_command_parameter)

		completions = filter(lambda x : x.startswith(command_input.terminal_command_parameter), completions)
		completions = filter(lambda x : x != command_input.terminal_command_parameter, completions)
		return sorted(list(set(completions)))

	def list_bash_completions(self, text):
		cmd = SOURCE + 'get_completions \'' + text + '\''
		proc = subprocess.Popen(cmd, executable='bash', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		result = proc.communicate()[0].decode('utf-8')
		return map(lambda x : x.strip(), result.splitlines())

	def query_command_names(self, name_filter):
		names = list(self.name_map.keys()) + list(self.aliases_map.keys())
		if name_filter:
			names = filter(lambda x: x.startswith(name_filter), names)
			names = filter(lambda x: x.strip() != name_filter, names)
		return sorted(list(set(names)))

	def execute(self, cmd):
		if cmd in self.aliases_map.keys:
			cmd = self.aliases_map[cmd]
		try:
			process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			stdout, stderr = process.communicate(timeout=3)
			if stdout:
				stdout = stdout.decode('utf-8')
			if stderr:
				stderr = stderr.decode('utf-8')
			return stdout, stderr
		except FileNotFoundError:
			return None, 'Cant run {}'.format(cmd)
		except Exception as e:
			print(traceback.format_exc())
			return None, 'Error ({}) running command: {}'.format(str(e), cmd)


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
