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

import sys, os
import shutil
import stat
import lib_raise_config as Config
import lib_raise_terminal as Print
import lib_raise_os as OS
import lib_raise_libraries as Libraries
import lib_raise_process as Process
import lib_raise_helpers as Helpers


cs_compilers = {}
cs_runtimes = {}
csc = None
runtime = None

def setup():
	global cs_compilers
	global cs_runtimes

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
		paths = Libraries.program_paths(name)
		if len(paths) == 0:
			continue

		if name in ['dmcs']:
			comp = Config.Compiler(
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
			cs_compilers[comp._name] = comp
			cs_runtimes[comp._name] = 'mono'
		elif name in ['csc']:
			comp = Config.Compiler(
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
			cs_compilers[comp._name] = comp
			cs_runtimes[comp._name] = ''

	# Make sure there is at least one C# compiler installed
	if len(cs_compilers) == 0:
		Print.status("Setting up C# module")
		Print.fail()
		Print.exit("No C# compiler found. Install one and try again.")


def get_default_compiler():
	global cs_compilers

	comp = None
	for name in ['dmcs', 'csc']:
		if name in cs_compilers:
			comp = cs_compilers[name]
			break

	return comp

def save_compiler(compiler):
	global cs_runtimes
	global csc
	global runtime

	# CSC
	csc = compiler
	runtime = cs_runtimes[csc._name]
	os.environ['CSC'] = csc._name

	# CSFLAGS
	opts = []
	if csc.debug: opts.append(csc._opt_debug)
	if csc.warnings_all: opts.append(csc._opt_warnings_all)
	if csc.warnings_as_errors: opts.append(csc._opt_warnings_as_errors)
	if csc.optimize: opts.append(csc._opt_optimize)
	for compile_time_flag in csc.compile_time_flags:
		opts.append(csc._opt_compile_time_flags + compile_time_flag)

	os.environ['CSFLAGS'] = str.join(' ', opts)

def build_program(out_file, inc_files, link_files=[]):
	global csc

	# Make sure the extension is valid
	if not out_file.endswith('.exe'):
		Print.exit("Out file extension should be '.exe' not '.{0}'.".format(out_file.split('.')[-1]))

	# Setup the messages
	task = 'Building'
	result = out_file
	plural = 'C# programs'
	singular = 'C# program'
	command = "${CSC} ${CSFLAGS} " + \
	csc._opt_out_file + out_file + ' ' + \
	str.join(' ', inc_files) + " " + str.join(' ', link_files)
	command = csc.to_native(command)

	def setup():
		if not 'CSC' in os.environ:
			Print.fail()
			Print.exit("Set the env variable 'CSC' to the C# compiler, and try again.")

		return True

	# Create the event
	event = Process.Event(task, result, plural, singular, command, setup)
	Process.add_event(event)

def build_shared_library(out_file, inc_files, link_files=[]):
	global csc

	# Make sure the extension is valid
	if not out_file.endswith('.dll'):
		Print.exit("Out file extension should be '.dll' not '.{0}'.".format(out_file.split('.')[-1]))

	# Setup the messages
	task = 'Building'
	result = out_file
	plural = 'C# shared libraries'
	singular = 'C# shared library'
	command = "${CSC} ${CSFLAGS} -target:library " + \
	csc._opt_out_file + out_file + ' ' + \
	str.join(' ', inc_files) + " " + str.join(' ', link_files)
	command = csc.to_native(command)

	def setup():
		if not 'CSC' in os.environ:
			Print.fail()
			Print.exit("Set the env variable 'CSC' to the C# compiler, and try again.")

		return True

	# Create the event
	event = Process.Event(task, result, plural, singular, command, setup)
	Process.add_event(event)

def run_say(command):
	global csc
	global runtime
	Print.status("Running C# program")

	native_command = '{0} {1}'.format(runtime, command)
	native_command = csc.to_native(native_command)
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

def install_program(name, dir_name):
	global csc

	# Make sure the extension is valid
	Helpers.require_file_extension(name, '.exe')

	# Get the location programs are stored in
	prog_root = None
	if OS.os_type._name == 'Windows':
		prog_root = os.environ.get('programfiles', 'C:\Program Files')
	else:
		prog_root = '/usr/lib/'

	# Get the native install source and dest
	source = csc.to_native(name)
	install_dir = os.path.join(prog_root, dir_name or '')
	dest = os.path.join(install_dir, source)

	# Install
	def fn():
		# Make the dir if needed
		if dir_name and not os.path.isdir(install_dir):
			os.mkdir(install_dir)

		# Copy the file
		shutil.copy2(source, dest)

		if OS.os_type._name != 'Windows':
			script_name = Helpers.before(name, '.')
			script_path = '/usr/bin/' + script_name
			with open(script_path, 'wb') as f:
				f.write("#!/usr/bin/env bash\n")
				f.write("\n")
				f.write("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib/{0}\n".format(script_name))
				f.write("THIS_EXE=\"/usr/lib/{0}/{0}.exe\"\n".format(script_name))
				f.write("exec mono $THIS_EXE \"$@\"\n")
				f.write("\n")
			st = os.stat(script_path)
			os.chmod(script_path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

	Process.do_on_fail_exit("Installing the program '{0}'".format(name),
					"Failed to install the program '{0}'.".format(name),
				lambda: fn())

def uninstall_program(name, dir_name):
	global csc

	# Make sure the extension is valid
	Helpers.require_file_extension(name, '.exe')

	# Get the location programs are stored in
	prog_root = None
	if OS.os_type._name == 'Windows':
		prog_root = os.environ.get('programfiles', 'C:\Program Files')
	else:
		prog_root = '/usr/lib/'

	# Get the native install source and dest
	source = csc.to_native(name)
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

		if OS.os_type._name != 'Windows':
			script_name = Helpers.before(name, '.')
			if os.path.isfile('/usr/bin/' + script_name):
				os.remove('/usr/bin/' + script_name)

	Process.do_on_fail_exit("Uninstalling the program '{0}'".format(name),
					"Failed to uninstall the program '{0}'.".format(name),
				lambda: fn())

def install_library(name, dir_name=None):
	global csc

	# Make sure the extension is valid
	Helpers.require_file_extension(name, '.dll')

	# Get the location programs are stored in
	prog_root = None
	if OS.os_type._name == 'Windows':
		prog_root = os.environ.get('programfiles', 'C:\Program Files')
	else:
		prog_root = '/usr/lib/'

	# Get the native install source and dest
	source = csc.to_native(name)
	install_dir = os.path.join(prog_root, dir_name or '')
	dest = os.path.join(install_dir, source)

	# Install
	def fn():
		# Make the dir if needed
		if dir_name and not os.path.isdir(install_dir):
			os.mkdir(install_dir)

		# Copy the file
		shutil.copy2(source, dest)

	Process.do_on_fail_exit("Installing the library '{0}'".format(name),
					"Failed to install the library '{0}'.".format(name),
				lambda: fn())

def uninstall_library(name, dir_name=None):
	global csc

	# Make sure the extension is valid
	Helpers.require_file_extension(name, '.dll')

	# Get the location programs are stored in
	prog_root = None
	if OS.os_type._name == 'Windows':
		prog_root = os.environ.get('programfiles', 'C:\Program Files')
	else:
		prog_root = '/usr/lib/'

	# Get the native install source and dest
	source = csc.to_native(name)
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

	Process.do_on_fail_exit("Uninstalling the library '{0}'".format(name),
					"Failed to uninstall the library '{0}'.".format(name),
				lambda: fn())

setup()

