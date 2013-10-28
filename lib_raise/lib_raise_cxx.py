#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# This file is part of Raise.
# Raise is a small build automation tool that ships with your software.
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

import os, sys
import lib_raise_config as Config
import lib_raise_terminal as Print
import lib_raise_os as OS
import lib_raise_libraries as Libraries
import lib_raise_fs as FS
import lib_raise_linker as Linker
import lib_raise_process as Process
import lib_raise_helpers as Helpers


cxx_compilers = {}
cxx = None

def setup():
	global cxx_compilers

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

	# Get the names and paths for know C++ compilers
	names = ['g++', 'cl.exe']
	for name in names:
		paths = Libraries.program_paths(name)
		if len(paths) == 0:
			continue

		if name == 'g++':
			comp = Config.Compiler(
				name =                 'g++', 
				path =                 paths[0], 
				setup =                '', 
				out_file =             '-o ', 
				no_link =              '-c', 
				debug =                '-g', 
				warnings_all =         '-Wall', 
				warnings_as_errors =   '-Werror', 
				optimize =             '-O2', 
				compile_time_flags =   '-D', 
				link =                 '-Wl,-as-needed', 
				extension_map = extension_map
			)
			cxx_compilers[comp._name] = comp
		elif name == 'cl.exe':
			# http://msdn.microsoft.com/en-us/library/19z1t1wy.aspx
			comp = Config.Compiler(
				name =                 'cl.exe', 
				path =                 paths[0], 
				setup =                '/nologo /EHsc', 
				out_file =             '/Fe', 
				no_link =              '/c', 
				debug =                '', 
				warnings_all =         '/Wall', 
				warnings_as_errors =   '', 
				optimize =             '/O2', 
				compile_time_flags =   '-D', 
				link =                 '-Wl,-as-needed', 
				extension_map = extension_map
			)
			cxx_compilers[comp._name] = comp

	# Make sure there is at least one C++ compiler installed
	if len(cxx_compilers) == 0:
		Print.status("Setting up C++ module")
		Print.fail()
		Print.exit("No C++ compiler found. Install one and try again.")


def get_default_compiler():
	global cxx_compilers
	comp = None

	if OS.os_type._name == 'Windows':
		comp = cxx_compilers['cl.exe']
	else:
		if 'g++' in cxx_compilers:
			comp = cxx_compilers['g++']

	return comp

def save_compiler(compiler):
	global cxx

	# CXX
	cxx = compiler
	os.environ['CXX'] = cxx._name

	# CXXFLAGS
	opts = []
	opts.append(cxx._opt_setup)
	if cxx.debug: opts.append(cxx._opt_debug)
	if cxx.warnings_all: opts.append(cxx._opt_warnings_all)
	if cxx.warnings_as_errors: opts.append(cxx._opt_warnings_as_errors)
	if cxx.optimize: opts.append(cxx._opt_optimize)
	for compile_time_flag in cxx.compile_time_flags:
		opts.append(cxx._opt_compile_time_flags + compile_time_flag)

	os.environ['CXXFLAGS'] = str.join(' ', opts)

def build_program(o_file, cxx_files, i_files=[]):
	global cxx

	# Make sure the extension is valid
	Helpers.require_file_extension(o_file, '.exe')

	# Setup the messages
	task = 'Building'
	result = o_file
	plural = 'C++ programs'
	singular = 'C++ program'
	command = '${CXX} ${CXXFLAGS} ' + \
				str.join(' ', cxx_files) + ' ' + \
				str.join(' ', i_files) + ' ' + \
				cxx._opt_out_file + o_file
	command = cxx.to_native(command)

	def setup():
		# Make sure the environmental variable is set
		if not 'CXX' in os.environ:
			Print.fail()
			Print.exit("Set the env variable 'CXX' to the C++ compiler, and try again.")

		return True

	# Create the event
	event = Process.Event(task, result, plural, singular, command, setup)
	Process.add_event(event)

def link_program(out_file, obj_files, i_files=[]):
	global cxx

	# Make sure the extension is valid
	Helpers.require_file_extension(out_file, '.exe')

	# Setup the messages
	task = 'Linking'
	result = out_file
	plural = 'C++ programs'
	singular = 'C++ program'
	command = '${CXX} ${CXXFLAGS} ' + \
				cxx._opt_link + ' ' + \
				str.join(' ', obj_files) + ' ' + \
				str.join(' ', i_files) + ' ' + \
				cxx._opt_out_file + out_file
	command = cxx.to_native(command)

	def setup():
		# Make sure the environmental variable is set
		if not 'CXX' in os.environ:
			Print.fail()
			Print.exit("Set the env variable 'CXX' to the C++ compiler, and try again.")

		return True

	# Create the event
	event = Event(task, result, plural, singular, command, setup)
	Process.add_event(event)

def build_object(o_file, cxx_files, i_files=[]):
	global cxx

	# Make sure the extension is valid
	Helpers.require_file_extension(o_file, '.o')

	# Setup the messages
	task = 'Building'
	result = o_file
	plural = 'C++ objects'
	singular = 'C++ object'
	command = "${CXX} ${CXXFLAGS} " + \
				cxx._opt_no_link + ' ' +  \
				cxx._opt_out_file + \
				o_file + ' ' + \
				str.join(' ', cxx_files) + ' ' + \
				str.join(' ', i_files)
	command = cxx.to_native(command)

	def setup():
		# Skip if the files have not changed since last build
		if not FS.is_outdated(to_update = [o_file], triggers = cxx_files):
			return False

		# Make sure the environmental variable is set
		if not 'CXX' in os.environ:
			Print.fail()
			Print.exit("Set the env variable 'CXX' to the C++ compiler, and try again.")

		return True

	# Create the event
	event = Process.Event(task, result, plural, singular, command, setup)
	Process.add_event(event)

def run_say(command):
	global cxx

	Print.status("Running C++ program")

	native_command = cxx.to_native(command)
	runner = Process.ProcessRunner(native_command)
	runner.run()
	runner.is_done
	runner.wait()

	if runner.is_success or runner.is_warning:
		Print.ok()
		sys.stdout.write(command + '\n')
		sys.stdout.write(runner.stdall)
	elif runner.is_failure:
		Print.fail()
		sys.stdout.write(command + '\n')
		sys.stdout.write(runner.stdall)
		Print.exit('Failed to run command.')


setup()


