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

import sys, os
from lib_raise_config import *
from lib_raise_os import *


class Terminal(RaiseModule):
	terminal_clear = None
	terminal_width = 79
	message_length = 0

	@classmethod
	def setup(cls):
		pass


class Emoticons:
	SMILE = ':)'
	NORMAL = ':\\'
	FROWN = ':('

class BGColors:
	MESSAGE = ''
	OK = ''
	WARNING = ''
	FAIL = ''
	ENDC = ''


# For plain mode, don't clear, don't use color, and fix the width to 79
def terminal_set_plain():
	Terminal.terminal_clear = None
	Terminal.terminal_width = 79

	BGColors.MESSAGE = ''
	BGColors.OK = ''
	BGColors.WARNING = ''
	BGColors.FAIL = ''
	BGColors.ENDC = ''

# For fancy mode, clear, use color, and use the real terminal width
def terminal_set_fancy():
	# Figure out how to clear the terminal
	if OS.os_type._name == 'Windows':
		Terminal.terminal_clear = 'cls'
	else:
		Terminal.terminal_clear = 'clear'

	# Figure out the terminal width
	if OS.os_type._name == 'Windows':
		import _winreg
		key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, r"Console")
		val = _winreg.QueryValueEx(key, "ScreenBufferSize")
		_winreg.CloseKey(key)
		size = hex(val[0])
		Terminal.terminal_width = int('0x' + size[-4 : len(size)], 16)
	else:
		Terminal.terminal_width = int(os.popen('stty size', 'r').read().split()[1])

	# Figure out the terminal colors
	if OS.os_type._name != 'Windows':
		BGColors.MESSAGE = '\033[44m\033[37m'
		BGColors.OK = '\033[42m\033[37m'
		BGColors.WARNING = '\033[43m\033[30m'
		BGColors.FAIL = '\033[41m\033[37m'
		BGColors.ENDC = '\033[0m'

def terminal_pad(length, pad_char=' '):
	width = Terminal.terminal_width

	if length > (width-3):
		i = int(width * (int(length / width) + 1)) - 3
	else:
		i = width - 3
	return ''.ljust(i-length, pad_char)

def print_info(message):
	sys.stdout.write('{0}{1}{2}\n'.format(BGColors.MESSAGE, message, BGColors.ENDC))
	sys.stdout.flush()

def print_status(message):
	message = '{0} ...'.format(message)
	Terminal.message_length = len(message)

	sys.stdout.write(message)
	sys.stdout.flush()

def print_ok():
	padding = terminal_pad(Terminal.message_length)
	message = "{0}{1}{2}{3}\n".format(padding, BGColors.OK, Emoticons.SMILE, BGColors.ENDC)
	Terminal.message_length = 0

	sys.stdout.write(message)
	sys.stdout.flush()

def print_warning(post_message=None):
	padding = terminal_pad(Terminal.message_length, '.')
	message = "{0}{1}{2}{3}\n".format(padding, BGColors.WARNING, Emoticons.NORMAL, BGColors.ENDC)
	if post_message:
		message += post_message + "\n"
	Terminal.message_length = 0

	sys.stdout.write(message)
	sys.stdout.flush()

def print_fail(post_fail_message=None):
	padding = terminal_pad(Terminal.message_length, '.')
	message = "{0}{1}{2}{3}\n".format(padding, BGColors.FAIL, Emoticons.FROWN, BGColors.ENDC)
	if post_fail_message:
		message += post_fail_message + "\n"
	Terminal.message_length = 0

	sys.stdout.write(message)
	sys.stdout.flush()

def print_exit(message):
	message = '{0}{1} Exiting ...{2}\n'.format(BGColors.FAIL, message, BGColors.ENDC)

	sys.stdout.write(message)
	sys.stdout.flush()
	exit(1)


Terminal.call_setup()

