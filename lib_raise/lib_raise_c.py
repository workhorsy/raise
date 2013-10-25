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

import shutil
from lib_raise_config import *
from lib_raise_os import *
from lib_raise_libraries import *
from lib_raise_fs import *
from lib_raise_linker import *


class C(RaiseModule):
	c_compilers = {}
	cc = None

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
					link =                 '-Wl,-as-needed', 
					extension_map = extension_map
				)
				C.c_compilers[comp._name] = comp
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
					link =                 '-Wl,-as-needed', 
					extension_map = extension_map
				)
				C.c_compilers[comp._name] = comp
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
					link =                 '-Wl,-as-needed', 
					extension_map = extension_map
				)
				C.c_compilers[comp._name] = comp

		# Make sure there is at least one C compiler installed
		if len(C.c_compilers) == 0:
			print_status("Setting up C module")
			print_fail()
			print_exit("No C compiler found. Install one and try again.")


def c_get_default_compiler():
	comp = None

	if OS.os_type._name == 'Windows':
		comp = C.c_compilers['cl.exe']
	else:
		if 'gcc' in C.c_compilers:
			comp = C.c_compilers['gcc']
		elif 'clang' in C.c_compilers:
			comp = C.c_compilers['clang']

	return comp

def c_save_compiler(compiler):
	# CC
	C.cc = compiler
	os.environ['CC'] = C.cc._name

	# CFLAGS
	opts = []
	opts.append(C.cc._opt_setup)
	if C.cc.debug: opts.append(C.cc._opt_debug)
	if C.cc.warnings_all: opts.append(C.cc._opt_warnings_all)
	if C.cc.warnings_as_errors: opts.append(C.cc._opt_warnings_as_errors)
	if C.cc.optimize: opts.append(C.cc._opt_optimize)
	for compile_time_flag in C.cc.compile_time_flags:
		opts.append(C.cc._opt_compile_time_flags + compile_time_flag)

	os.environ['CFLAGS'] = str.join(' ', opts)

def c_link_program(out_file, obj_files, i_files=[]):
	# Make sure the extension is valid
	require_file_extension(out_file, '.exe')

	# Setup the messages
	task = 'Linking'
	result = out_file
	plural = 'C programs'
	singular = 'C program'
	command = '${CC} ${CFLAGS} ' + \
				C.cc._opt_link + ' ' + \
				str.join(' ', obj_files) + ' ' + \
				str.join(' ', i_files) + ' ' + \
				C.cc._opt_out_file + out_file
	command = C.cc.to_native(command)

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
	# Make sure the extension is valid
	require_file_extension(o_file, '.o')

	# Setup the messages
	task = 'Building'
	result = o_file
	plural = 'C objects'
	singular = 'C object'
	command = "${CC} ${CFLAGS} " + \
				C.cc._opt_no_link + ' ' +  \
				C.cc._opt_out_file + \
				o_file + ' ' + \
				str.join(' ', c_files) + ' ' + \
				str.join(' ', i_files)
	command = C.cc.to_native(command)

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
	# Make sure the extension is valid
	require_file_extension(o_file, '.exe')

	# Setup the messages
	task = 'Building'
	result = o_file
	plural = 'C programs'
	singular = 'C program'
	command = '${CC} ${CFLAGS} ' + \
				str.join(' ', c_files) + ' ' + \
				str.join(' ', i_files) + ' ' + \
				C.cc._opt_out_file + o_file
	command = C.cc.to_native(command)

	def setup():
		# Make sure the environmental variable is set
		if not 'CC' in os.environ:
			print_fail()
			print_exit("Set the env variable 'CC' to the C compiler, and try again.")

		return True

	# Create the event
	event = Event(task, result, plural, singular, command, setup)
	add_event(event)

# FIXME: Change to use the linker through the compiler
def c_build_shared_library(so_file, o_files):
	# Make sure the extension is valid
	require_file_extension(so_file, '.so')

	# Setup the messages
	task = 'Building'
	result = so_file
	plural = 'shared libraries'
	singular = 'shared library'
	command = "{0} {1} {2} {3} {4}{5}".format(
				LinkerModule.linker._name, 
				LinkerModule.linker._opt_setup, 
				LinkerModule.linker._opt_shared, 
				str.join(' ', o_files), 
				LinkerModule.linker._opt_out_file, 
				so_file)
	command = LinkerModule.linker.to_native(command)

	def setup():
		# Skip if the files have not changed since last build
		if not is_outdated(to_update = [so_file], triggers = o_files):
			return False
		return True

	# Create the event
	event = Event(task, result, plural, singular, command, setup)
	add_event(event)

def c_run_say(command):
	print_status("Running C program")

	native_command = C.cc.to_native(command)
	runner = ProcessRunner(native_command)
	runner.run()
	runner.is_done
	runner.wait()

	if runner.is_success or runner.is_warning:
		print_ok()
		sys.stdout.write(command + '\n')
		sys.stdout.write(runner.stdall)
	elif runner.is_failure:
		print_fail()
		sys.stdout.write(command + '\n')
		sys.stdout.write(runner.stdall)
		print_exit('Failed to run command.')

def c_install_program(name, dir_name=None):
	# Make sure the extension is valid
	require_file_extension(name, '.exe')

	# Get the location programs are stored in
	prog_root = None
	if OS.os_type._name == 'Windows':
		prog_root = os.environ.get('programfiles', 'C:\Program Files')
	else:
		prog_root = '/usr/bin/'

	# Get the native install source and dest
	source = C.cc.to_native(name)
	install_dir = os.path.join(prog_root, dir_name or '')
	dest = os.path.join(install_dir, source)

	# Install
	def fn():
		# Make the dir if needed
		if dir_name and not os.path.isdir(install_dir):
			os.mkdir(install_dir)

		# Copy the file
		shutil.copy2(source, dest)

	do_on_fail_exit("Installing the program '{0}'".format(name),
					"Failed to install the program '{0}'.".format(name),
				lambda: fn())

def c_uninstall_program(name, dir_name=None):
	# Make sure the extension is valid
	require_file_extension(name, '.exe')

	# Get the location programs are stored in
	prog_root = None
	if OS.os_type._name == 'Windows':
		prog_root = os.environ.get('programfiles', 'C:\Program Files')
	else:
		prog_root = '/usr/bin/'

	# Get the native install source and dest
	source = C.cc.to_native(name)
	install_dir = os.path.join(prog_root, dir_name or '')
	dest = os.path.join(install_dir, source)

	# Remove
	def fn():
		# Remove the file
		if os.path.isfile(dest):
			os.remove(dest)
		# Remove the dir if empty
		if dir_name and os.path.isdir(install_dir) and not os.listdir(install_dir):
			shutil.rmtree(install_dir)

	do_on_fail_exit("Uninstalling the program '{0}'".format(name),
					"Failed to uninstall the program '{0}'.".format(name),
				lambda: fn())

def c_install_library(name, dir_name=None):
	# Make sure the extension is valid
	require_file_extension(name, '.so', '.a')

	# Get the location programs are stored in
	prog_root = None
	if OS.os_type._name == 'Windows':
		prog_root = os.environ.get('programfiles', 'C:\Program Files')
	else:
		prog_root = '/usr/lib/'

	# Get the native install source and dest
	source = C.cc.to_native(name)
	install_dir = os.path.join(prog_root, dir_name or '')
	dest = os.path.join(install_dir, source)

	# Install
	def fn():
		# Make the dir if needed
		if dir_name and not os.path.isdir(install_dir):
			os.mkdir(install_dir)

		# Copy the file
		shutil.copy2(source, dest)

	do_on_fail_exit("Installing the library '{0}'".format(name),
					"Failed to install the library '{0}'.".format(name),
				lambda: fn())

def c_uninstall_library(name, dir_name=None):
	# Make sure the extension is valid
	require_file_extension(name, '.so', '.a')

	# Get the location programs are stored in
	prog_root = None
	if OS.os_type._name == 'Windows':
		prog_root = os.environ.get('programfiles', 'C:\Program Files')
	else:
		prog_root = '/usr/lib/'

	# Get the native install source and dest
	source = C.cc.to_native(name)
	install_dir = os.path.join(prog_root, dir_name or '')
	dest = os.path.join(install_dir, source)

	# Remove
	def fn():
		# Remove the file
		if os.path.isfile(dest):
			os.remove(dest)
		# Remove the dir if empty
		if dir_name and os.path.isdir(install_dir) and not os.listdir(install_dir):
			shutil.rmtree(install_dir)

	do_on_fail_exit("Uninstalling the library '{0}'".format(name),
					"Failed to uninstall the library '{0}'.".format(name),
				lambda: fn())

def c_install_header(name, dir_name=None):
	# Make sure the extension is valid
	require_file_extension(name, '.h')

	# Get the location headers are stored in
	prog_root = None
	if OS.os_type._name == 'Windows':
		prog_root = os.environ.get('programfiles', 'C:\Program Files')
	else:
		prog_root = '/usr/include/'

	# Get the native install source and dest
	source = C.cc.to_native(name)
	install_dir = os.path.join(prog_root, dir_name or '')
	dest = os.path.join(install_dir, source)

	# Install
	def fn():
		# Make the dir if needed
		if dir_name and not os.path.isdir(install_dir):
			os.mkdir(install_dir)

		# Copy the file
		shutil.copy2(source, dest)

	do_on_fail_exit("Installing the header '{0}'".format(name),
					"Failed to install the header '{0}'.".format(name),
				lambda: fn())

def c_uninstall_header(name, dir_name=None):
	# Make sure the extension is valid
	require_file_extension(name, '.h')

	# Get the location header are stored in
	prog_root = None
	if OS.os_type._name == 'Windows':
		prog_root = os.environ.get('programfiles', 'C:\Program Files')
	else:
		prog_root = '/usr/include/'

	# Get the native install source and dest
	source = C.cc.to_native(name)
	install_dir = os.path.join(prog_root, dir_name or '')
	dest = os.path.join(install_dir, source)

	# Remove
	def fn():
		# Remove the file
		if os.path.isfile(dest):
			os.remove(dest)
		# Remove the dir if empty
		if dir_name and os.path.isdir(install_dir) and not os.listdir(install_dir):
			shutil.rmtree(install_dir)

	do_on_fail_exit("Uninstalling the header '{0}'".format(name),
					"Failed to uninstall the header '{0}'.".format(name),
				lambda: fn())

C.call_setup()


