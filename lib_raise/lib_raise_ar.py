#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# This file is part of Raise.
# Raise is a small build automation tool that ships with your software.
# Raise uses a MIT style license, and is hosted at http://launchpad.net/raise .
# Copyright (c) 2014, Matthew Brennan Jones <mattjones@workhorsy.org>
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

import lib_raise_config as Config
import lib_raise_users as Users
import lib_raise_fs as FS
import lib_raise_process as Process
import lib_raise_helpers as Helpers


def setup():
	pass

def to_native(command):
	extension_map = {}
	# Figure out the extensions for this OS
	if Helpers.os_type._name == 'Cygwin':
		extension_map = {
			'.exe' : '.exe',
			'.o' : '.o',
			'.so' : '.so',
			'.a' : '.a'
		}
	elif Helpers.os_type._name == 'Windows':
		extension_map = {
			'.exe' : '.exe',
			'.o' : '.obj',
			'.so' : '.dll',
			'.a' : '.lib'
		}
	else:
		extension_map = {
			'.exe' : '',
			'.o' : '.o',
			'.so' : '.so',
			'.a' : '.a'
		}

	for before, after in extension_map.items():
		command = command.replace(before, after)

	return command

def build_static_library(ar_file, o_files):
	# Make sure the extension is valid
	if not ar_file.endswith('.a'):
		Print.exit("Out file extension should be '.a' not '.{0}'.".format(ar_file.split('.')[-1]))

	# Setup the messages
	task = 'Building'
	result = ar_file
	plural = 'static libraries'
	singular = 'static library'
	command = "ar rcs " + \
			ar_file + " " + \
			str.join(' ', o_files)
	command = to_native(command)

	def setup():
		# Skip if the files have not changed since last build
		to_update = [to_native(ar_file)]
		triggers = [to_native(t) for t in o_files]
		if not FS.is_outdated(to_update, triggers):
			return False

		# Create the output directory if it does not exist
		FS.create_path_dirs(ar_file)

		return True

	# Create the event
	event = Process.Event(task, result, plural, singular, command, setup)
	Process.add_event(event)


setup()

