#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# This file is part of Raise.
# Raise is a small build automation tool that ships with your software.
# Raise uses a MIT style license, and is hosted at http://launchpad.net/raise .
# Copyright (c) 2014, Matthew Brennan Jones <matthew.brennan.jones@gmail.com>
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
import lib_raise_config as Config
import lib_raise_users as Users
import lib_raise_helpers as Helpers


clear = None
width = 79
message_length = 0


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
def set_plain():
	global clear
	global width

	clear = None
	width = 79

	BGColors.MESSAGE = ''
	BGColors.OK = ''
	BGColors.WARNING = ''
	BGColors.FAIL = ''
	BGColors.ENDC = ''

# For fancy mode, clear, use color, and use the real terminal width
def set_fancy():
	global clear
	global width

	# Figure out how to clear the terminal
	if Helpers.os_type._name == 'Windows':
		clear = 'cls'
	else:
		clear = 'clear'

	# Figure out the terminal width
	if Helpers.os_type._name == 'Windows':
		import _winreg
		key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, r"Console")
		val = _winreg.QueryValueEx(key, "ScreenBufferSize")
		_winreg.CloseKey(key)
		size = hex(val[0])
		width = int('0x' + size[-4 : len(size)], 16)
	else:
		width = int(os.popen('stty size', 'r').read().split()[1])

	# Figure out the terminal colors
	if Helpers.os_type._name != 'Windows':
		BGColors.MESSAGE = '\033[44m\033[37m'
		BGColors.OK = '\033[42m\033[37m'
		BGColors.WARNING = '\033[43m\033[30m'
		BGColors.FAIL = '\033[41m\033[37m'
		BGColors.ENDC = '\033[0m'

def pad(length, pad_char=' '):
	global width

	if length > (width-3):
		i = int(width * (int(length / width) + 1)) - 3
	else:
		i = width - 3
	return ''.ljust(i-length, pad_char)

def info(message):
	sys.stdout.write('{0}{1}{2}\n'.format(BGColors.MESSAGE, message, BGColors.ENDC))
	sys.stdout.flush()

def status(message):
	global message_length
	message = '{0} ...'.format(message)
	message_length = len(message)

	sys.stdout.write(message)
	sys.stdout.flush()

def ok():
	global message_length
	padding = pad(message_length)
	message = "{0}{1}{2}{3}\n".format(padding, BGColors.OK, Emoticons.SMILE, BGColors.ENDC)
	message_length = 0

	sys.stdout.write(message)
	sys.stdout.flush()

def warning(post_message=None):
	global message_length
	padding = pad(message_length, '.')
	message = "{0}{1}{2}{3}\n".format(padding, BGColors.WARNING, Emoticons.NORMAL, BGColors.ENDC)
	if post_message:
		message += post_message + "\n"
	message_length = 0

	sys.stdout.write(message)
	sys.stdout.flush()

def fail(post_fail_message=None):
	global message_length
	padding = pad(message_length, '.')
	message = "{0}{1}{2}{3}\n".format(padding, BGColors.FAIL, Emoticons.FROWN, BGColors.ENDC)
	if post_fail_message:
		message += post_fail_message + "\n"
	message_length = 0

	sys.stdout.write(message)
	sys.stdout.flush()

def exit(message):
	line = ''
	# Only print the line number in non plain mode
	if not Config.is_nolineno:
		no = Helpers.get_rscript_line()
		if no and no != '?':
			line = '\n(Called from {0})'.format(no)

	message = '{0}{1} Exiting ...{3}{2}\n'.format(
		BGColors.FAIL, 
		message, 
		BGColors.ENDC, 
		line
	)

	sys.stdout.write(message)
	sys.stdout.flush()
	sys.exit(1)



