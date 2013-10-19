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

import os
import atexit
import platform
import traceback
from lib_raise_config import *


class OS(RaiseModule):
	os_type = None

	@classmethod
	def setup(cls):
		# Figure out the general OS type
		if 'cygwin' in platform.system().lower():
			cls.os_type = OSType(
				name =                 'Cygwin'
			)
		elif 'windows' in platform.system().lower():
			cls.os_type = OSType(
				name =                 'Windows'
			)
		else:
			cls.os_type = OSType(
				name =                 'Unix'
			)

		# Make sure Windows SDK tools are found
		if cls.os_type._name == 'Windows':
			if not 'WINDOWSSDKDIR' in os.environ and not 'WINDOWSSDKVERSIONOVERRIDE' in os.environ:
				early_exit('Windows SDK not found. Must be run from Windows SDK Command Prompt.')


class OSType(object):
	def __init__(self, name):

		self._name = name

def expand_envs(string):
	while True:
		before = string
		string = os.path.expandvars(string)
		if before == string:
			return string

def get_normal_user_name():
	# Get the name from the environmental variable
	user_name = \
		os.getenv('SUDO_USER') or \
		os.getenv('USER') or \
		os.getenv('LOGNAME')

	# Make sure we got a name
	if not user_name:
		print_exit('Failed to get the normal user name.')

	return user_name

def get_normal_user_id():
	user_name = get_normal_user_name()
	return int(os.popen('id -u {0}'.format(user_name)).read())

def do_as_normal_user(cb):
	prev_id = -1

	# Change the user to the normal user
	if not OS.os_type._name in ['Windows', 'Cygwin']:
		prev_id = os.geteuid()
		user_id = get_normal_user_id()
		os.setegid(user_id)
		os.seteuid(user_id)

	# Run the cb as the normal user
	exception = False
	is_exiting = False
	try:
		cb()
	except SystemExit as err:
		# Don't save any exit() exceptions. Just exit
		is_exiting = True
	except Exception as err:
		exception = traceback.format_exc()
	except StandardError as err:
		exception = traceback.format_exc()
	except BaseException as err:
		exception = traceback.format_exc()
	finally:
		# Return the user to normal
		if not OS.os_type._name in ['Windows', 'Cygwin']:
			os.setegid(prev_id)
			os.seteuid(prev_id)

	if is_exiting:
		exit(1)
	if exception:
		print_exit(exception)

def require_root():
	is_root = False

	# Cygwin
	if OS.os_type._name == 'Cygwin':
		# Cygwin has no root user
		is_root = True
	# Windows
	elif OS.os_type._name == 'Windows':
		try:
			# Only Admin can read the C:\windows\temp
			sys_root = os.environ.get('SystemRoot', 'C:\windows')
			temp = os.listdir(os.path.join(sys_root, 'temp'))
			is_root = True
		except:
			pass
	# Linux / Unix
	elif os.getuid() == 0:
		is_root = True

	# Make sure we are root
	if not is_root:
		print_exit("Must be run as root.")

def require_not_root():
	# On Windows/Cygwin it does not matter if we are root. So just return
	if OS.os_type._name in ['Windows', 'Cygwin']:
		return

	# Make sure we are NOT root
	if os.getuid() == 0:
		print_exit("Must not be run as root.")

def call_on_exit(cb):
	# Set a cleanup function to run on exit
	if cb:
		atexit.register(cb)


OS.call_setup()

