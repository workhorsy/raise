#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# This file is part of Raise.
# Raise is a small build automation tool that ships with your software.
# Raise uses a MIT style license, and is hosted at https://github.com/workhorsy/raise .
# Copyright (c) 2012-2017 Matthew Brennan Jones <matthew.brennan.jones@gmail.com>
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

import lib_raise_config as Config
import lib_raise_users as Users
import lib_raise_fs as FS
import lib_raise_process as Process
import lib_raise_find as Find
import lib_raise_terminal as Print
import lib_raise_helpers as Helpers

from osinfo import *
import findlib


linkers = {}

def setup():
	global linkers

	# Get the names and paths for know linkers
	names = ['ld', 'link.exe']
	for name in names:
		paths = Find.program_paths(name)
		if len(paths) == 0:
			continue

		if name == 'link.exe':
			link = Linker(
				name            = 'link.exe',
				setup           = '/nologo',
				out_file        = '/out:',
				shared          = '/dll '
			)
			linkers[link._name] = link
		elif name == 'ld':
			link = Linker(
				name            = 'ld',
				setup           = '',
				out_file        = '-o ',
				shared          = '-G'
			)
			linkers[link._name] = link

	# Make sure there is at least one linker installed
	if len(linkers) == 0:
		Print.status("Setting up Linker module")
		Print.fail()
		Print.exit("No Linker found. Install one and try again.")


class Linker(object):
	def __init__(self, name, setup, out_file, shared):
		self._name = name

		self._opt_setup = setup
		self._opt_out_file = out_file
		self._opt_shared = shared

	def get_link(self):
		return self._name
	link = property(get_link)

	def link_program(self, out_file, obj_files, i_files=[]):
		# Setup the messages
		task = 'Linking'
		result = out_file
		plural = 'programs'
		singular = 'program'
		command = "{0} {1}{2} {3} {4}".format(
					self.link,
					linker._opt_out_file,
					out_file,
					str.join(' ', obj_files),
					str.join(' ', i_files)
		)
		command = to_native(command)

		def setup():
			# Skip if the files have not changed since last build
			to_update = [to_native(out_file)]
			triggers = [to_native(t) for t in obj_files + i_files]
			if not FS.is_outdated(to_update, triggers):
				return False

			# Create the output directory if it does not exist
			FS.create_path_dirs(out_file)

			return True

		# Create the event
		event = Process.Event(task, result, plural, singular, command, setup)
		Process.add_event(event)


def to_native(command):
	extension_map = {}
	# Figure out the extensions for this OS
	if Config.os_type in OSType.Cygwin:
		extension_map = {
			'.exe' : '.exe',
			'.o' : '.o',
			'.so' : '.so',
			'.a' : '.a'
		}
	elif Config.os_type in OSType.Windows:
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

def get_default_linker():
	global linkers

	if Config.os_type in OSType.Windows:
		return linkers['link.exe']
	else:
		return linkers['ld']

def ldconfig():
	# Setup the message
	Print.status("Running 'ldconfig'")

	# Skip ldconfig on Cygwin
	if Config.os_type in OSType.Cygwin:
		Print.ok()
		return

	# Find ldconfig
	prog = Find.program_paths('ldconfig')
	if not prog:
		Print.fail()
		Print.exit("Could not find 'ldconfig'.")

	# Run the process
	runner = findlib.ProcessRunner(prog[0])
	runner.run()
	runner.is_done
	runner.wait()

	# Success or failure
	if runner.is_failure:
		Print.fail(runner.stdall)
		Print.exit("Failed run 'ldconfig'.")
	elif runner.is_success or runner.is_warning:
		Print.ok()

def link_shared_path(lib_name):
	return '-L' + get_shared_library(lib_name)

def link_static_path(lib_name):
	return '-L' + get_static_library(lib_name)

def link_static_or_shared_path(lib_name):
	return '-L' + static_or_shared_library_path(lib_name)

def link_shared_paths(lib_names):
	paths = []
	for lib_name in lib_names:
		paths.append(link_shared_path(lib_name))
	return str.join(' ', paths)

def link_static_paths(lib_names):
	paths = []
	for lib_name in lib_names:
		paths.append(link_static_path(lib_name))
	return str.join(' ', paths)

def link_static_or_shared_paths(lib_names):
	paths = []
	for lib_name in lib_names:
		paths.append(link_static_or_shared_path(lib_name))
	return str.join(' ', paths)


setup()
