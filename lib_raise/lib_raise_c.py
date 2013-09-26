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



def _c_require_module():
	# Just return if setup
	if Config.c_compilers:
		return

	print_status("C module check")
	print_fail()
	print_exit("Call require_module('C') before using any C functions.")

def c_module_setup():
	# Get the names and paths for know C compilers
	names = ['gcc', 'clang', 'cl.exe']
	for name in names:
		paths = program_paths(name)
		if len(paths) == 0:
			continue

		if name == 'gcc':
			comp = Compiler(
				name =                 'gcc', 
				path =                 paths[0], 
				setup =                '', 
				out_file =             '-o ', 
				no_link =              '-c', 
				debug =                '-g', 
				warnings_all =         '-Wall', 
				warnings_as_errors =   '-Werror', 
				optimize =             '-O2', 
				compile_time_flags =   '-D', 
				link =                 '-Wl,-as-needed'
			)
			Config.c_compilers[comp._name] = comp
		elif name == 'clang':
			comp = Compiler(
				name =                 'clang', 
				path =                 paths[0], 
				setup =                '', 
				out_file =             '-o ', 
				no_link =              '-c', 
				debug =                '-g', 
				warnings_all =         '-Wall', 
				warnings_as_errors =   '-Werror', 
				optimize =             '-O2', 
				compile_time_flags =   '-D', 
				link =                 '-Wl,-as-needed'
			)
			Config.c_compilers[comp._name] = comp
		elif name == 'cl.exe':
			# http://msdn.microsoft.com/en-us/library/19z1t1wy.aspx
			comp = Compiler(
				name =                 'cl.exe', 
				path =                 paths[0], 
				setup =                '/nologo', 
				out_file =             '/Fe', 
				no_link =              '/c', 
				debug =                '', 
				warnings_all =         '/Wall', 
				warnings_as_errors =   '', 
				optimize =             '/O2', 
				compile_time_flags =   '-D', 
				link =                 '-Wl,-as-needed'
			)
			Config.c_compilers[comp._name] = comp

	# Make sure there is at least one C compiler installed
	if len(Config.c_compilers) == 0:
		print_status("Setting up C module")
		print_fail()
		print_exit("No C compiler found. Install one and try again.")

def c_get_default_compiler():
	_c_require_module()

	comp = None

	if Config._os_type._name == 'Windows':
		comp = Config.c_compilers['cl.exe']
	else:
		if 'gcc' in Config.c_compilers:
			comp = Config.c_compilers['gcc']
		elif 'clang' in Config.c_compilers:
			comp = Config.c_compilers['clang']

	return comp

def c_save_compiler(compiler):
	_c_require_module()

	# CC
	Config._cc = compiler
	os.environ['CC'] = Config._cc._name

	# CFLAGS
	opts = []
	opts.append(Config._cc._opt_setup)
	if Config._cc.debug: opts.append(Config._cc._opt_debug)
	if Config._cc.warnings_all: opts.append(Config._cc._opt_warnings_all)
	if Config._cc.warnings_as_errors: opts.append(Config._cc._opt_warnings_as_errors)
	if Config._cc.optimize: opts.append(Config._cc._opt_optimize)
	for compile_time_flag in Config._cc.compile_time_flags:
		opts.append(Config._cc._opt_compile_time_flags + compile_time_flag)

	os.environ['CFLAGS'] = str.join(' ', opts)

def c_link_program(out_file, obj_files, i_files=[]):
	_c_require_module()

	# Change file extensions to os format
	out_file = to_native(out_file)
	obj_files = to_native(obj_files)
	i_files = to_native(i_files)

	# Setup the messages
	task = 'Linking'
	result = out_file
	plural = 'C programs'
	singular = 'C program'
	command = '${CC} ${CFLAGS} ' + \
				Config._cc._opt_link + ' ' + \
				str.join(' ', obj_files) + ' ' + \
				str.join(' ', i_files) + ' ' + \
				Config._cc._opt_out_file + out_file

	def setup():
		# Make sure the environmental variable is set
		if not 'CC' in os.environ:
			print_fail()
			print_exit("Set the env variable 'CC' to the C compiler, and try again.")

		return True

	# Create the event
	event = Event(task, result, plural, singular, command, setup)
	add_event(event)

def c_build_object(o_file, c_files, i_files=[]):
	_c_require_module()

	# Change file extensions to os format
	o_file = to_native(o_file)
	c_files = to_native(c_files)
	i_files = to_native(i_files)

	# Setup the messages
	task = 'Building'
	result = o_file
	plural = 'C objects'
	singular = 'C object'
	command = "${CC} ${CFLAGS} " + \
				Config._cc._opt_no_link + ' ' +  \
				Config._cc._opt_out_file + \
				o_file + ' ' + \
				str.join(' ', c_files) + ' ' + \
				str.join(' ', i_files)

	def setup():
		# Skip if the files have not changed since last build
		if not is_outdated(to_update = [o_file], triggers = c_files):
			return False

		# Make sure the environmental variable is set
		if not 'CC' in os.environ:
			print_fail()
			print_exit("Set the env variable 'CC' to the C compiler, and try again.")

		return True

	# Create the event
	event = Event(task, result, plural, singular, command, setup)
	add_event(event)

def c_build_program(o_file, c_files, i_files=[]):
	_c_require_module()

	# Change file extensions to os format
	o_file = to_native(o_file)
	c_files = to_native(c_files)
	i_files = to_native(i_files)

	# Setup the messages
	task = 'Building'
	result = o_file
	plural = 'C programs'
	singular = 'C program'
	command = '${CC} ${CFLAGS} ' + \
				str.join(' ', c_files) + ' ' + \
				str.join(' ', i_files) + ' ' + \
				Config._cc._opt_out_file + o_file

	def setup():
		# Make sure the environmental variable is set
		if not 'CC' in os.environ:
			print_fail()
			print_exit("Set the env variable 'CC' to the C compiler, and try again.")

		return True

	# Create the event
	event = Event(task, result, plural, singular, command, setup)
	add_event(event)


# FIXME: Rename to c_build_static_library
def ar_build_static_library(ar_file, o_files):
	_c_require_module()

	# Change file extensions to os format
	ar_file = to_native(ar_file)
	o_files = to_native(o_files)

	# Setup the messages
	task = 'Building'
	result = ar_file
	plural = 'static libraries'
	singular = 'static library'
	command = "ar rcs " + \
			ar_file + " " + \
			str.join(' ', o_files)

	def setup():
		# Skip if the files have not changed since last build
		if not is_outdated(to_update = [ar_file], triggers = o_files):
			return False
		return True

	# Create the event
	event = Event(task, result, plural, singular, command, setup)
	add_event(event)

def c_build_shared_library(so_file, o_files):
	_c_require_module()

	# Change file extensions to os format
	so_file = to_native(so_file)
	o_files = to_native(o_files)

	# Setup the messages
	task = 'Building'
	result = so_file
	plural = 'shared libraries'
	singular = 'shared library'
	command = "{0} {1} {2} {3} {4}{5}".format(
				Config._linker._name, 
				Config._linker._opt_setup, 
				Config._linker._opt_shared, 
				str.join(' ', o_files), 
				Config._linker._opt_out_file, 
				so_file)

	def setup():
		# Skip if the files have not changed since last build
		if not is_outdated(to_update = [so_file], triggers = o_files):
			return False
		return True

	# Create the event
	event = Event(task, result, plural, singular, command, setup)
	add_event(event)

