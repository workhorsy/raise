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
from lib_raise_config import *
from lib_raise_os import *
from lib_raise_fs import *
from lib_raise_libraries import *

class D(RaiseModule):
	d_compilers = {}
	dc = None

	@classmethod
	def setup(cls):
		extension_map = {}
		# Figure out the extensions for this OS
		if OS.os_type._name == 'Cygwin':
			extension_map = {
				'.exe' : '.exe',
				'.o' : '.o',
				'.so' : '.so',
				'.a' : '.a'
			}
		elif OS.os_type._name == 'Windows':
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

		# Get the names and paths for know D compilers
		names = ['dmd', 'dmd2', 'ldc2']
		for name in names:
			paths = program_paths(name)
			if len(paths) == 0:
				continue

			if name in ['dmd', 'dmd2']:
				comp = Compiler(
					name =                 name, 
					path =                 paths[0], 
					setup =                '', 
					out_file =             '-of', 
					no_link =              '-c', 
					debug =                '-g', 
					warnings_all =         '-w', 
					warnings_as_errors =   '', 
					optimize =             '-O', 
					compile_time_flags =   '-version=', 
					link =                 '-Wl,-as-needed', 
					extension_map = extension_map
				)
				D.d_compilers[comp._name] = comp
			elif name == 'ldc2':
				comp = Compiler(
					name =                 'ldc2', 
					path =                 paths[0], 
					setup =                '', 
					out_file =             '-of', 
					no_link =              '-c', 
					debug =                '-g', 
					warnings_all =         '-w', 
					warnings_as_errors =   '', 
					optimize =             '-O2',
					compile_time_flags =   '-version=', 
					link =                 '-Wl,-as-needed', 
					extension_map = extension_map
				)
				D.d_compilers[comp._name] = comp

		# Make sure there is at least one D compiler installed
		if len(D.d_compilers) == 0:
			print_status("Setting up D module")
			print_fail()
			print_exit("No D compiler found. Install one and try again.")


def d_get_default_compiler():
	comp = None
	for name in ['dmd', 'dmd2', 'ldc2']:
		if name in D.d_compilers:
			comp = D.d_compilers[name]
			break

	return comp

def d_save_compiler(compiler):
	# DC
	D.dc = compiler
	os.environ['DC'] = D.dc._name

	# DFLAGS
	opts = []
	if D.dc.debug: opts.append(D.dc._opt_debug)
	if D.dc.warnings_all: opts.append(D.dc._opt_warnings_all)
	if D.dc.warnings_as_errors: opts.append(D.dc._opt_warnings_as_errors)
	if D.dc.optimize: opts.append(D.dc._opt_optimize)
	for compile_time_flag in D.dc.compile_time_flags:
		opts.append(D.dc._opt_compile_time_flags + compile_time_flag)

	os.environ['DFLAGS'] = str.join(' ', opts)

def d_build_interface(d_file, i_files=[]):
	# Setup the messages
	task = 'Building'
	result = d_file + 'i'
	plural = 'D interfaces'
	singular = 'D interface'

	f = self_deleting_named_temporary_file()
	command = "${DC} ${DFLAGS} -c " + d_file + " " + str.join(' ', i_files) + " -Hf" + d_file + "i " + D.dc._opt_out_file + f.name
	command = D.dc.to_native(command)

	def setup():
		if not is_outdated(to_update = [d_file+'i'], triggers = [d_file]):
			return False

		if not 'DC' in os.environ:
			print_fail()
			print_exit("Set the env variable 'DC' to the D compiler, and try again.")

		return True

	# Create the event
	event = Event(task, result, plural, singular, command, setup)
	add_event(event)

def d_build_object(o_file, d_files, i_files=[], l_files=[], h_files=[]):
	# Make sure the extension is valid
	require_file_extension(o_file, '.o')

	# Setup the messages
	task = 'Building'
	result = o_file
	plural = 'D objects'
	singular = 'D object'

	command = "${DC} ${DFLAGS} -c " + D.dc._opt_out_file + o_file + " " + str.join(' ', d_files) + " " + str.join(' ', i_files) + " " + str.join(' ', l_files)
	if h_files:
		command += " -H -Hdimport -Hf" + str.join(' ', h_files)
	command = D.dc.to_native(command)

	def setup():
		if not is_outdated(to_update = [o_file], triggers = d_files):
			return False

		if not 'DC' in os.environ:
			print_fail()
			print_exit("Set the env variable 'DC' to the D compiler, and try again.")

		return True

	# Create the event
	event = Event(task, result, plural, singular, command, setup)
	add_event(event)

# FIXME: Remove this, as there are no shared libraries in D
def d_build_shared_library(o_file, d_files, i_files=[], l_files=[], generate_headers=False):
	# Make sure the extension is valid
	require_file_extension(o_file, '.so')

	# Setup the messages
	task = 'Building'
	result = o_file
	plural = 'D shared libraries'
	singular = 'D shared library'

	command = "${DC} ${DFLAGS} -shared " + D.dc._opt_out_file + o_file + " " + str.join(' ', d_files) + " " + str.join(' ', i_files) + " " + str.join(' ', l_files)
	if generate_headers:
		command += "  -Hdimport -H"
	command = D.dc.to_native(command)

	def setup():
		if not is_outdated(to_update = [o_file], triggers = d_files):
			return False

		if not 'DC' in os.environ:
			print_fail()
			print_exit("Set the env variable 'DC' to the D compiler, and try again.")

		return True

	# Create the event
	event = Event(task, result, plural, singular, command, setup)
	add_event(event)

def d_build_static_library(o_file, d_files, i_files=[], l_files=[], generate_headers=False):
	# Make sure the extension is valid
	require_file_extension(o_file, '.a')

	# Setup the messages
	task = 'Building'
	result = o_file
	plural = 'D static libraries'
	singular = 'D static library'

	command = "${DC} ${DFLAGS} -lib " + D.dc._opt_out_file + o_file + " " + str.join(' ', d_files) + " " + str.join(' ', i_files) + " " + str.join(' ', l_files)
	if generate_headers:
		command += "  -Hdimport -H"
	command = D.dc.to_native(command)

	def setup():
		if not 'DC' in os.environ:
			print_fail()
			print_exit("Set the env variable 'DC' to the D compiler, and try again.")

		return True

	# Create the event
	event = Event(task, result, plural, singular, command, setup)
	add_event(event)

def d_build_program(out_file, inc_files, link_files=[]):
	# Make sure the extension is valid
	require_file_extension(out_file, '.exe')

	# Setup the messages
	task = 'Building'
	result = out_file
	plural = 'D programs'
	singular = 'D program'
	command = "${DC} ${DFLAGS} " + D.dc._opt_out_file + out_file + ' ' + str.join(' ', inc_files) + " " + str.join(' ', link_files)
	command = D.dc.to_native(command)

	def setup():
		if not 'DC' in os.environ:
			print_fail()
			print_exit("Set the env variable 'DC' to the D compiler, and try again.")

		return True

	# Create the event
	event = Event(task, result, plural, singular, command, setup)
	add_event(event)

def d_run_say(command):
	print_status("Running D program")

	native_command = D.dc.to_native(command)
	runner = ProcessRunner(native_command)
	runner.run()
	runner.wait()

	if runner.is_success or runner.is_warning:
		print_ok()
		print(command)
		print(runner.stdall)
	elif runner.is_failure:
		print_fail()
		print(command)
		print(runner.stdall)
		print_exit('Failed to run command.')


D.call_setup()

