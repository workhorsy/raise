#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# This file is part of Raise.
# Raise is a small software build tool that ships with your code.
# Raise uses a MIT style license, and is hosted at http://launchpad.net/raise .
# Copyright (c) 2013, Matthew Brennan Jones <mattjones@workhorsy.org>
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

class TerminalModule(RaiseModule):
	def __init__(self):
		super(TerminalModule, self).__init__("TERMINAL")
		self._terminal_clear = None
		self._terminal_width = None
		self.message_length = None

	def setup(self):
		os_module = Config.require_module("OS")

		# Figure out how to clear the terminal
		if os_module._os_type._name == 'Windows':
			self._terminal_clear = 'cls'
		else:
			self._terminal_clear = 'clear'

		# FIXME: Have this look for stty first then try the registry
		# Figure out the terminal width
		if os_module._os_type._name == 'Windows':
			import _winreg
			key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, r"Console")
			val = _winreg.QueryValueEx(key, "ScreenBufferSize")
			_winreg.CloseKey(key)
			size = hex(val[0])
			self._terminal_width = int('0x' + size[-4 : len(size)], 16)
		else:
			self._terminal_width = int(os.popen('stty size', 'r').read().split()[1])

		self.is_setup = True

class Emoticons:
	SMILE = ':)'
	NORMAL = ':\\'
	FROWN = ':('

class BGColors:
	MESSAGE = '\033[44m\033[37m'
	OK = '\033[42m\033[37m'
	WARNING = '\033[43m\033[30m'
	FAIL = '\033[41m\033[37m'
	ENDC = '\033[0m'

def terminal_pad(length, pad_char=' '):
	module = Config.require_module("TERMINAL")
	width = module._terminal_width

	if length > (width-3):
		i = int(width * (int(length / width) + 1)) - 3
	else:
		i = width - 3
	return ''.ljust(i-length, pad_char)

def print_info(message):
	sys.stdout.write('{0}{1}{2}\n'.format(BGColors.MESSAGE, message, BGColors.ENDC))
	sys.stdout.flush()

def print_status(message):
	module = Config.require_module("TERMINAL")
	message = '{0} ...'.format(message)
	module.message_length = len(message)

	sys.stdout.write(message)
	sys.stdout.flush()

def print_ok():
	module = Config.require_module("TERMINAL")
	padding = terminal_pad(module.message_length)
	message = "{0}{1}{2}{3}\n".format(padding, BGColors.OK, Emoticons.SMILE, BGColors.ENDC)
	module.message_length = 0

	sys.stdout.write(message)
	sys.stdout.flush()

def print_warning(post_message=None):
	module = Config.require_module("TERMINAL")
	padding = terminal_pad(module.message_length, '.')
	message = "{0}{1}{2}{3}\n".format(padding, BGColors.WARNING, Emoticons.NORMAL, BGColors.ENDC)
	if post_message:
		message += post_message + "\n"
	module.message_length = 0

	sys.stdout.write(message)
	sys.stdout.flush()

def print_fail(post_fail_message=None):
	module = Config.require_module("TERMINAL")
	padding = terminal_pad(module.message_length, '.')
	message = "{0}{1}{2}{3}\n".format(padding, BGColors.FAIL, Emoticons.FROWN, BGColors.ENDC)
	if post_fail_message:
		message += post_fail_message + "\n"
	module.message_length = 0

	sys.stdout.write(message)
	sys.stdout.flush()

def print_exit(message):
	message = '{0}{1} Exiting ...{2}\n'.format(BGColors.FAIL, message, BGColors.ENDC)

	sys.stdout.write(message)
	sys.stdout.flush()
	exit()

