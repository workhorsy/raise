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

import platform
import traceback

class OSModule(RaiseModule):
	def __init__(self):
		super(OSModule, self).__init__("OS")
		self._os_type = None
		self._file_map = {}

	def setup(self):
		# Figure out the general OS type
		if 'cygwin' in platform.system().lower():
			self._os_type = OSType(
				name =                 'Cygwin', 
				exe_extension =        '', 
				object_extension =     '.o', 
				shared_lib_extension = '.so', 
				static_lib_extension = '.a'
			)
		elif 'windows' in platform.system().lower():
			self._os_type = OSType(
				name =                 'Windows', 
				exe_extension =        '.exe', 
				object_extension =     '.obj', 
				shared_lib_extension = '.dll', 
				static_lib_extension = '.lib'
			)
		else:
			self._os_type = OSType(
				name =                 'Unix', 
				exe_extension =        '', 
				object_extension =     '.o', 
				shared_lib_extension = '.so', 
				static_lib_extension = '.a'
			)

		# Make sure Windows SDK tools are found
		if self._os_type._name == 'Windows':
			if not 'WINDOWSSDKDIR' in os.environ and not 'WINDOWSSDKVERSIONOVERRIDE' in os.environ:
				early_exit('Windows SDK not found. Must be run from Windows SDK Command Prompt.')


		self.is_setup = True

class OSType(object):
	def __init__(self, name, exe_extension, object_extension, 
				shared_lib_extension, static_lib_extension):

		self._name = name
		self._exe_extension = exe_extension
		self._object_extension = object_extension
		self._shared_lib_extension = shared_lib_extension
		self._static_lib_extension = static_lib_extension

def _rename_to_native(string, before, after):
	module = Config.require_module("OS")

	for word in string.split():
		if before in word and not word in module._file_map:
			module._file_map[word] = word.replace(before, after)

	return string.replace(before, after)

def save_native(thing):
	module = Config.require_module("OS")

	# Get a dict of the standard extensions and their other os counterparts
	replaces = {
		'.exe' : module._os_type._exe_extension,
		'.o'   : module._os_type._object_extension,
		'.so'  : module._os_type._shared_lib_extension,
		'.a'   : module._os_type._static_lib_extension
	}

	# Replace the extension
	if type(thing) == list:
		for before, after in replaces.items():
			thing = [_rename_to_native(o, before, after) for o in thing]
	else:
		for before, after in replaces.items():
			thing = _rename_to_native(thing, before, after)

	return thing

def to_native(command):
	module = Config.require_module("OS")

	for before, after in module._file_map.items():
		command = command.replace(before, after)

	return command

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
	module = Config.require_module("OS")
	prev_id = -1

	# Change the user to the normal user
	if not module._os_type._name in ['Windows', 'Cygwin']:
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
		if not module._os_type._name in ['Windows', 'Cygwin']:
			os.setegid(prev_id)
			os.seteuid(prev_id)

	if is_exiting:
		exit(1)
	if exception:
		print_exit(exception)

def require_root():
	module = Config.require_module("OS")
	is_root = False

	# Cygwin
	if module._os_type._name == 'Cygwin':
		# Cygwin has no root user
		is_root = True
	# Windows
	elif module._os_type._name == 'Windows':
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
	module = Config.require_module("OS")

	# On Windows/Cygwin it does not matter if we are root. So just return
	if module._os_type._name in ['Windows', 'Cygwin']:
		return

	# Make sure we are NOT root
	if os.getuid() == 0:
		print_exit("Must not be run as root.")

def call_on_exit(cb):
	# Set a cleanup function to run on exit
	if cb:
		atexit.register(cb)

