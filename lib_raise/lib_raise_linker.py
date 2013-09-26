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


def _linker_require_module():
	# Just return if setup
	if Config.linkers:
		return

	print_status("Linker module check")
	print_fail()
	print_exit("Call require_module('Linker') before using any Linker functions.")

def linker_module_setup():
	# Get the names and paths for know linkers
	names = ['ld', 'link.exe']
	for name in names:
		paths = program_paths(name)
		if len(paths) == 0:
			continue

		if name == 'link.exe':
			link = Linker(
				name            = 'link.exe',
				setup           = '/nologo', 
				out_file        = '/out:', 
				shared          = '/dll '
			)
			Config.linkers[link._name] = link
		elif name == 'ld':
			link = Linker(
				name            = 'ld',
				setup           = '', 
				out_file        = '-o ', 
				shared          = '-G'
			)
			Config.linkers[link._name] = link

	# Make sure there is at least one linker installed
	if len(Config.linkers) == 0:
		print_status("Setting up Linker module")
		print_fail()
		print_exit("No Linker found. Install one and try again.")

def linker_get_default_linker():
	_linker_require_module()

	if Config._os_type._name == 'Windows':
		return Config.linkers['link.exe']
	else:
		return Config.linkers['ld']

def linker_save_linker(linker):
	_linker_require_module()

	# LINKER
	Config._linker = linker
	os.environ['LINKER'] = Config._linker._name

def linker_link_program(out_file, obj_files, i_files=[]):
	_linker_require_module()

	# Change file extensions to os format
	out_file = to_native(out_file)
	obj_files = to_native(obj_files)
	i_files = to_native(i_files)

	# Setup the messages
	task = 'Linking'
	result = out_file
	plural = 'programs'
	singular = 'program'
	command = "${LINK} " + \
				Config._linker._opt_out_file + \
				out_file + ' ' + \
				str.join(' ', obj_files) + ' ' + \
				str.join(' ', i_files)

	def setup():
		# Skip if the files have not changed since last build
		if not is_outdated(to_update = [out_file], triggers = obj_files):
			return False

		# Make sure the environmental variable is set
		if not 'LINK' in os.environ:
			print_fail()
			print_exit("Set the env variable 'LINK' to the linker, and try again.")

		return True

	# Create the event
	event = Event(task, result, plural, singular, command, setup)
	add_event(event)

