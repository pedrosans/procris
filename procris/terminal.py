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
import procris.messages as messages
from subprocess import PIPE
from procris.names import PromptInput

COMMANDS_GLOB = ["/usr/bin/*", "/snap/bin/*", os.path.expanduser('~/.local/bin')+'/*']
ALIAS_PATTERN = r'^\s*alias\s+.*$'
ALIAS_DEFINITION_GROUP = r'^\s*alias\s+(.*)$'
ALIASES_MAP = {}
NAME_MAP = {}


def load():
	_load_aliases()
	_load_commands()


def reload():
	ALIASES_MAP.clear()
	NAME_MAP.clear()
	load()


def _load_commands():
	for commands_glob in COMMANDS_GLOB:
		for path in glob.glob(commands_glob):
			name = path.split('/')[-1]
			NAME_MAP[name] = path


def _load_aliases():
	for stdout_line in get_sys_aliases().splitlines():
		if not re.match(ALIAS_PATTERN, stdout_line):
			continue
		aliases_definition = parse_alias_line(stdout_line)
		for alias_definition in aliases_definition:
			name, cmd = alias_definition
			ALIASES_MAP[name] = cmd


def get_sys_aliases():
	proc = subprocess.Popen(['bash', '-ic', 'alias'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
	return proc.communicate()[0].decode('utf-8')


def parse_alias_line(line):
	aliases_definition = re.search(ALIAS_DEFINITION_GROUP, line).group(1)
	aliases = re.split(r'(?<=\')\s+(?=[^\']+=\$?\'.*\')', aliases_definition)
	result = []
	for alias in aliases:
		name = re.search(r'(.*?)=', alias).group(1)
		cmd = re.search(r'=\$?\'(.*)\'', alias).group(1)
		result.append([name, cmd])
	return result


def has_perfect_match(name):
	return name in NAME_MAP.keys()


def complete(c_in: PromptInput):
	if c_in.terminal_command_spacer:
		return query_command_parameters(c_in)
	else:
		return query_command_names(c_in.terminal_command)


def query_command_parameters(c_in):
	cmd = COMPLETIONS_FUNCTION + 'get_completions \'' + c_in.vim_command_parameter + '\''
	proc = subprocess.Popen(cmd, executable='bash', shell=True, stdin=PIPE, stdout=PIPE)
	completions = proc.communicate()[0].decode('utf-8')
	completions = map(lambda x: x.strip(), completions.splitlines())
	completions = filter(lambda x: x.startswith(c_in.terminal_command_parameter), completions)
	return sorted(list(set(completions)))


def query_command_names(name_filter):
	names = list(NAME_MAP.keys()) + list(ALIASES_MAP.keys())
	if name_filter:
		names = filter(lambda x: x.startswith(name_filter), names)
		names = filter(lambda x: x.strip() != name_filter, names)
	return sorted(list(set(names)))


def bang(c_in):
	cmd = c_in.vim_command_parameter
	if not cmd:
		return messages.Message('ERROR: empty command', 'error')
	stdout, stderr = execute(cmd)
	if stdout:
		return messages.Message(stdout, None)
	if stderr:
		return messages.Message(stderr, 'error')
	return messages.Message('Command executed successfully with no return.', None)


def execute(cmd):
	if cmd in ALIASES_MAP.keys():
		cmd = ALIASES_MAP[cmd]
	try:
		process = subprocess.Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)
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
"""
#
# Author: Brian Beffa <brbsix@gmail.com>
# Original source: https://brbsix.github.io/2015/11/29/accessing-tab-completion-programmatically-in-bash/
# License: LGPLv3 (http://www.gnu.org/licenses/lgpl-3.0.txt)
#
COMPLETIONS_FUNCTION = """
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
