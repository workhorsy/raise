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

import os, sys
import traceback
import lib_raise_config as Config
import lib_raise_terminal as Print
import lib_raise_helpers as Helpers


def get_normal_user_name():
	# Get the name from the environmental variable
	user_name = \
		os.getenv('SUDO_USER') or \
		os.getenv('USER') or \
		os.getenv('LOGNAME')

	# Make sure we got a name
	if not user_name:
		Print.exit('Failed to get the normal user name.')

	return user_name

def get_normal_user_id():
	user_name = get_normal_user_name()
	return int(os.popen('id -u {0}'.format(user_name)).read())

def do_as_normal_user(cb):
	prev_id = -1

	# Change the user to the normal user
	if not Helpers.os_type in Helpers.OSType.withoutRoot:
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
		if not Helpers.os_type in Helpers.OSType.withoutRoot:
			os.setegid(prev_id)
			os.seteuid(prev_id)

	if is_exiting:
		sys.exit(1)
	if exception:
		Print.exit(exception)

def require_root():
	is_root = False

	# Cygwin
	if Helpers.os_type in Helpers.OSType.cygwin:
		# Cygwin has no root user
		is_root = True
	# Windows
	elif Helpers.os_type in Helpers.OSType.windows:
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
		Print.exit("Must be run as root.")

def require_not_root():
	# On Windows/Cygwin it does not matter if we are root. So just return
	if Helpers.os_type in Helpers.OSType.withoutRoot:
		return

	# Make sure we are NOT root
	if os.getuid() == 0:
		Print.exit("Must not be run as root.")


