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
from lib_raise_os import *
from lib_raise_libraries import *


class CSharp(RaiseModule):
	cs_compilers = {}
	cs_runtimes = {}
	csc = None
	runtime = None

	@classmethod
	def setup(cls):
		extension_map = {}
		# Figure out the extensions for this OS
		if OS.os_type._name == 'Cygwin':
			extension_map = {
				'.exe' : '.exe',
				'.dll' : '.dll'
			}
		elif OS.os_type._name == 'Windows':
			extension_map = {
				'.exe' : '.exe',
				'.dll' : '.dll'
			}
		else:
			extension_map = {
				'.exe' : '.exe',
				'.dll' : '.dll'
			}

		# Get the names and paths for know C# compilers
		names = ['dmcs', 'csc']
		for name in names:
			paths = program_paths(name)
			if len(paths) == 0:
				continue

			if name in ['dmcs']:
				comp = Compiler(
					name =                 name, 
					path =                 paths[0], 
					setup =                '', 
					out_file =             '-out:', 
					no_link =              '', 
					debug =                '-debug', 
					warnings_all =         '-warn:4', 
					warnings_as_errors =   '-warnaserror', 
					optimize =             '-optimize', 
					compile_time_flags =   '', 
					link =                 '', 
					extension_map = extension_map
				)
				CSharp.cs_compilers[comp._name] = comp
				CSharp.cs_runtimes[comp._name] = 'mono'
			elif name in ['csc']:
				comp = Compiler(
					name =                 name, 
					path =                 paths[0], 
					setup =                '', 
					out_file =             '-out:', 
					no_link =              '', 
					debug =                '-debug', 
					warnings_all =         '-warn:4', 
					warnings_as_errors =   '-warnaserror', 
					optimize =             '-optimize', 
					compile_time_flags =   '', 
					link =                 '', 
					extension_map = extension_map
				)
				CSharp.cs_compilers[comp._name] = comp
				CSharp.cs_runtimes[comp._name] = ''

		# Make sure there is at least one C# compiler installed
		if len(cls.cs_compilers) == 0:
			print_status("Setting up C# module")
			print_fail()
			print_exit("No C# compiler found. Install one and try again.")


def csharp_get_default_compiler():
	comp = None
	for name in ['dmcs', 'csc']:
		if name in CSharp.cs_compilers:
			comp = CSharp.cs_compilers[name]
			break

	return comp

def csharp_save_compiler(compiler):
	# CSC
	CSharp.csc = compiler
	CSharp.runtime = CSharp.cs_runtimes[CSharp.csc._name]
	os.environ['CSC'] = CSharp.csc._name

	# CSFLAGS
	opts = []
	if CSharp.csc.debug: opts.append(CSharp.csc._opt_debug)
	if CSharp.csc.warnings_all: opts.append(CSharp.csc._opt_warnings_all)
	if CSharp.csc.warnings_as_errors: opts.append(CSharp.csc._opt_warnings_as_errors)
	if CSharp.csc.optimize: opts.append(CSharp.csc._opt_optimize)
	for compile_time_flag in CSharp.csc.compile_time_flags:
		opts.append(CSharp.csc._opt_compile_time_flags + compile_time_flag)

	os.environ['CSFLAGS'] = str.join(' ', opts)

def csharp_build_program(out_file, inc_files, link_files=[]):
	# Make sure the extension is valid
	if not out_file.endswith('.exe'):
		print_exit("Out file extension should be '.exe' not '.{0}'.".format(out_file.split('.')[-1]))

	# Setup the messages
	task = 'Building'
	result = out_file
	plural = 'C# programs'
	singular = 'C# program'
	command = "${CSC} ${CSFLAGS} " + \
	CSharp.csc._opt_out_file + out_file + ' ' + \
	str.join(' ', inc_files) + " " + str.join(' ', link_files)
	command = CSharp.csc.to_native(command)

	def setup():
		if not 'CSC' in os.environ:
			print_fail()
			print_exit("Set the env variable 'CSC' to the C# compiler, and try again.")

		return True

	# Create the event
	event = Event(task, result, plural, singular, command, setup)
	add_event(event)

def csharp_build_shared_library(out_file, inc_files, link_files=[]):
	# Make sure the extension is valid
	if not out_file.endswith('.dll'):
		print_exit("Out file extension should be '.dll' not '.{0}'.".format(out_file.split('.')[-1]))

	# Setup the messages
	task = 'Building'
	result = out_file
	plural = 'C# shared libraries'
	singular = 'C# shared library'
	command = "${CSC} ${CSFLAGS} -target:library " + \
	CSharp.csc._opt_out_file + out_file + ' ' + \
	str.join(' ', inc_files) + " " + str.join(' ', link_files)
	command = CSharp.csc.to_native(command)

	def setup():
		if not 'CSC' in os.environ:
			print_fail()
			print_exit("Set the env variable 'CSC' to the C# compiler, and try again.")

		return True

	# Create the event
	event = Event(task, result, plural, singular, command, setup)
	add_event(event)

def csharp_run_say(command):
	print_status("Running C# program")

	native_command = '{0} {1}'.format(CSharp.runtime, command)
	native_command = CSharp.csc.to_native(native_command)
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

def csharp_install_program(name, dir_name=None):
	# Make sure the extension is valid
	require_file_extension(name, '.exe')

	# Get the location programs are stored in
	prog_root = None
	if OS.os_type._name == 'Windows':
		prog_root = os.environ.get('programfiles', 'C:\Program Files')
	else:
		prog_root = '/usr/bin/'

	# Get the native install source and dest
	source = CSharp.csc.to_native(name)
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

def csharp_uninstall_program(name, dir_name=None):
	# Make sure the extension is valid
	require_file_extension(name, '.exe')

	# Get the location programs are stored in
	prog_root = None
	if OS.os_type._name == 'Windows':
		prog_root = os.environ.get('programfiles', 'C:\Program Files')
	else:
		prog_root = '/usr/bin/'

	# Get the native install source and dest
	source = CSharp.csc.to_native(name)
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

def csharp_install_library(name, dir_name=None):
	# Make sure the extension is valid
	require_file_extension(name, '.dll')

	# Get the location programs are stored in
	prog_root = None
	if OS.os_type._name == 'Windows':
		prog_root = os.environ.get('programfiles', 'C:\Program Files')
	else:
		prog_root = '/usr/lib/'

	# Get the native install source and dest
	source = CSharp.csc.to_native(name)
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

def csharp_uninstall_library(name, dir_name=None):
	# Make sure the extension is valid
	require_file_extension(name, '.dll')

	# Get the location programs are stored in
	prog_root = None
	if OS.os_type._name == 'Windows':
		prog_root = os.environ.get('programfiles', 'C:\Program Files')
	else:
		prog_root = '/usr/lib/'

	# Get the native install source and dest
	source = CSharp.csc.to_native(name)
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

CSharp.call_setup()

