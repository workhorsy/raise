#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# This file is part of Raise.
# Raise is a small build automation tool that ships with your software.
# Raise uses a MIT style license, and is hosted at http://launchpad.net/raise .
# Copyright (c) 2014, Matthew Brennan Jones <matthew.brennan.jones@gmail.com>
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
import lib_raise_config as Config
import lib_raise_terminal as Print
import lib_raise_users as Users
import lib_raise_fs as FS
import lib_raise_find as Find
import lib_raise_process as Process
import lib_raise_helpers as Helpers


d_compilers = {}


def setup():
	global d_compilers

	# Get the names and paths for know D compilers
	names = ['dmd2', 'dmd', 'ldc2', 'ldc', 'gdc']
	for name in names:
		paths = Find.program_paths(name)
		if len(paths) == 0:
			continue

		if name in ['dmd2', 'dmd']:
			comp = DCompiler(
				name =                 name, 
				path =                 paths[0], 
				setup =                '', 
				out_file =             '-of', 
				no_link =              '-c', 
				debug =                '-g', 
				warnings_all =         '-w', 
				optimize =             '-O', 
				compile_time_flags =   '-version=', 
				link =                 '-Wl,-as-needed', 
				interface =            '-H', 
				interface_file =       '-Hf', 
				interface_dir =        '-Hd', 
				unittest =             '-unittest'
			)
			d_compilers[comp._name] = comp
		elif name in ['ldc2', 'ldc']:
			comp = DCompiler(
				name =                 name, 
				path =                 paths[0], 
				setup =                '', 
				out_file =             '-of', 
				no_link =              '-c', 
				debug =                '-g', 
				warnings_all =         '-w', 
				optimize =             '-O2',
				compile_time_flags =   '-version=', 
				link =                 '-Wl,-as-needed', 
				interface =            '-H', 
				interface_file =       '-Hf', 
				interface_dir =        '-Hd', 
				unittest =             '-unittest'
			)
			d_compilers[comp._name] = comp
		elif name in ['gdc']:
			comp = DCompiler(
				name =                 name, 
				path =                 paths[0], 
				setup =                '', 
				out_file =             '-o ', 
				no_link =              '-c', 
				debug =                '-g', 
				warnings_all =         '-Werror', 
				optimize =             '-O2', 
				compile_time_flags =   '-version=', 
				link =                 '-Wl,-as-needed', 
				interface =            '-fintfc=', 
				interface_file =       '-fintfc-file=', 
				interface_dir =        '-fintfc-dir=', 
				unittest =             '-unittest'
			)
			d_compilers[comp._name] = comp

	# Make sure there is at least one D compiler installed
	if len(d_compilers) == 0:
		Print.status("Setting up D module")
		Print.fail()
		Print.exit("No D compiler found. Install one and try again.")


class DCompiler(object):
	def __init__(self, name, path, setup, out_file, no_link, 
				debug, warnings_all, optimize, 
				compile_time_flags, link, 
				interface, interface_file, interface_dir, 
				unittest):

		self._name = name
		self._path = path

		# Save text for all the options
		self._opt_setup = setup
		self._opt_out_file = out_file
		self._opt_no_link = no_link
		self._opt_debug = debug
		self._opt_warnings_all = warnings_all
		self._opt_optimize = optimize

		self._opt_compile_time_flags = compile_time_flags
		self._opt_link = link

		self._opt_interface = interface
		self._opt_interface_file = interface_file
		self._opt_interface_dir = interface_dir

		self._opt_unittest = unittest

		# Set the default values of the flags
		self.debug = False
		self.warnings_all = False
		self.optimize = True
		self.unittest = False
		self.compile_time_flags = []

	def get_dc(self):
		return self._name
	dc = property(get_dc)

	def get_dflags(self):
		opts = []
		if self.debug and self._opt_debug:
			opts.append(self._opt_debug)
		if self.warnings_all and self._opt_warnings_all:
			opts.append(self._opt_warnings_all)
		if self.optimize and self._opt_optimize:
			opts.append(self._opt_optimize)
		if self.unittest and self._opt_unittest:
			opts.append(self._opt_unittest)
		if self._opt_compile_time_flags:
			for compile_time_flag in self.compile_time_flags:
				opts.append(self._opt_compile_time_flags + compile_time_flag)

		return str.join(' ', opts)
	dflags = property(get_dflags)

	def build_interface(self, d_file, i_files=[]):
		# Setup the messages
		task = 'Building'
		result = d_file + 'i'
		plural = 'D interfaces'
		singular = 'D interface'

		f = FS.self_deleting_named_temporary_file()
		command = '"{0}" {1} {2} {3} {4} {5}{6}i {7}{8}'.format(
			self._path, 
			self.dflags, 
			self._opt_no_link, 
			d_file, 
			str.join(' ', i_files), 
			self._opt_interface_file, 
			d_file, 
			self._opt_out_file, 
			f.name
		)
		command = to_native(command)

		def setup():
			# Skip if the files have not changed since last build
			to_update = [d_file+'i']
			triggers = [to_native(t) for t in i_files]
			if not FS.is_outdated(to_update, triggers):
				return False

			return True

		# Create the event
		event = Process.Event(task, result, plural, singular, command, setup)
		Process.add_event(event)

	def build_object(self, o_file, d_files, i_files=[], l_files=[], h_file='', h_dir=''):
		# Make sure the extension is valid
		Helpers.require_file_extension(o_file, '.o')

		# Setup the messages
		task = 'Building'
		result = o_file
		plural = 'D objects'
		singular = 'D object'

		command = '"{0}" {1} {2} {3}{4} {5} {6} {7}'.format(
			self._path, 
			self.dflags, 
			self._opt_no_link, 
			self._opt_out_file, 
			o_file, 
			str.join(' ', d_files), 
			str.join(' ', i_files), 
			str.join(' ', l_files)
		)
		if h_file or h_dir:
			command += " {0}".format(self._opt_interface)

		if h_file:
			command += " {0}{1}".format(
				self._opt_interface_file, h_file
			)

		if h_dir:
			command += " {0}{1}".format(
				self._opt_interface_dir, h_dir
			)
		command = to_native(command)
		#print("!!! command: {0}".format(command))

		def setup():
			# Skip if the files have not changed since last build
			to_update = [to_native(o_file)]
			triggers = [to_native(t) for t in d_files + i_files + l_files]
			if h_file: triggers.append(h_file)
			if not FS.is_outdated(to_update, triggers):
				return False

			# Create the output directory if it does not exist
			FS.create_path_dirs(o_file)

			return True

		# Create the event
		event = Process.Event(task, result, plural, singular, command, setup)
		Process.add_event(event)

	def build_static_library(self, o_file, d_files, i_files=[], l_files=[], generate_headers=False):
		# Make sure the extension is valid
		Helpers.require_file_extension(o_file, '.a')

		# Setup the messages
		task = 'Building'
		result = o_file
		plural = 'D static libraries'
		singular = 'D static library'

		command = '"{0}" {1} -lib {2}{3} {4} {5} {6}'.format(
			self._path, 
			self.dflags, 
			self._opt_out_file, 
			o_file, 
			str.join(' ', d_files), 
			str.join(' ', i_files), 
			str.join(' ', l_files)
		)
		if generate_headers:
			command += "  {0}import {1}".format(
				self._opt_interface_dir, 
				self._opt_interface, 
			)
		command = to_native(command)

		def setup():
			# Skip if the files have not changed since last build
			to_update = [to_native(o_file)]
			triggers = [to_native(t) for t in d_files + i_files + l_files]
			if not FS.is_outdated(to_update, triggers):
				return False

			# Create the output directory if it does not exist
			FS.create_path_dirs(o_file)

			return True

		# Create the event
		event = Process.Event(task, result, plural, singular, command, setup)
		Process.add_event(event)

	def build_program(self, out_file, inc_files, link_files=[]):
		# Make sure the extension is valid
		Helpers.require_file_extension(out_file, '.exe')

		# Setup the messages
		task = 'Building'
		result = out_file
		plural = 'D programs'
		singular = 'D program'
		command = '"{0}" {1} {2}{3} {4} {5}'.format(
			self._path, 
			self.dflags, 
			self._opt_out_file, 
			out_file, 
			str.join(' ', inc_files), 
			str.join(' ', link_files)
		)
		command = to_native(command)

		def setup():
			# Skip if the files have not changed since last build
			to_update = [to_native(out_file)]
			triggers = [to_native(t) for t in inc_files + link_files]
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
	if Helpers.os_type == Helpers.OSType.cygwin:
		extension_map = {
			'.exe' : '.exe',
			'.o' : '.obj',
			'.so' : '.dll',
			'.a' : '.lib'
		}
	elif Helpers.os_type == Helpers.OSType.windows:
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

def get_default_compiler():
	global d_compilers

	comp = None
	for name in ['dmd2', 'dmd', 'ldc2', 'ldc', 'gdc']:
		if name in d_compilers:
			comp = d_compilers[name]
			break

	return comp

def run_print(command):
	Print.status("Running D program")

	native_command = to_native(command)
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

def install_program(name, dir_name=None):
	# Make sure the extension is valid
	Helpers.require_file_extension(name, '.exe')

	# Get the location programs are stored in
	prog_root = None
	if Helpers.os_type == Helpers.OSType.windows:
		prog_root = os.environ.get('programfiles', 'C:\Program Files')
	else:
		prog_root = '/usr/bin/'

	# Get the native install source and dest
	source = to_native(name)
	install_dir = os.path.join(prog_root, dir_name or '')
	dest = os.path.join(install_dir, source)

	# Install
	def fn():
		# Make the dir if needed
		if dir_name and not os.path.isdir(install_dir):
			os.mkdir(install_dir)

		# Copy the file
		shutil.copy2(source, dest)

	Process.do_on_fail_exit("Installing the program '{0}'".format(name),
					"Failed to install the program '{0}'.".format(name),
				lambda: fn())

def uninstall_program(name, dir_name=None):
	# Make sure the extension is valid
	Helpers.require_file_extension(name, '.exe')

	# Get the location programs are stored in
	prog_root = None
	if Helpers.os_type == Helpers.OSType.windows:
		prog_root = os.environ.get('programfiles', 'C:\Program Files')
	else:
		prog_root = '/usr/bin/'

	# Get the native install source and dest
	source = to_native(name)
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

	Process.do_on_fail_exit("Uninstalling the program '{0}'".format(name),
					"Failed to uninstall the program '{0}'.".format(name),
				lambda: fn())

def install_library(name, dir_name=None):
	# Make sure the extension is valid
	Helpers.require_file_extension(name, '.a')

	# Get the location programs are stored in
	prog_root = None
	if Helpers.os_type == Helpers.OSType.windows:
		prog_root = os.environ.get('programfiles', 'C:\Program Files')
	else:
		prog_root = '/usr/lib/'

	# Get the native install source and dest
	source = to_native(name)
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
	# Make sure the extension is valid
	Helpers.require_file_extension(name, '.a')

	# Get the location programs are stored in
	prog_root = None
	if Helpers.os_type == Helpers.OSType.windows:
		prog_root = os.environ.get('programfiles', 'C:\Program Files')
	else:
		prog_root = '/usr/lib/'

	# Get the native install source and dest
	source = to_native(name)
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

def install_interface(name, dir_name=None):
	# Make sure the extension is valid
	Helpers.require_file_extension(name, '.di')

	# Get the location interfaces are stored in
	prog_root = None
	if Helpers.os_type == Helpers.OSType.windows:
		prog_root = os.environ.get('programfiles', 'C:\Program Files')
	else:
		prog_root = '/usr/include/'

	# Get the native install source and dest
	source = to_native(name)
	install_dir = os.path.join(prog_root, dir_name or '')
	dest = os.path.join(install_dir, source)

	# Install
	def fn():
		# Make the dir if needed
		if dir_name and not os.path.isdir(install_dir):
			os.mkdir(install_dir)

		# Copy the file
		shutil.copy2(source, dest)

	Process.do_on_fail_exit("Installing the interface '{0}'".format(name),
					"Failed to install the interface '{0}'.".format(name),
				lambda: fn())

def uninstall_interface(name, dir_name=None):
	# Make sure the extension is valid
	Helpers.require_file_extension(name, '.di')

	# Get the location interfaces are stored in
	prog_root = None
	if Helpers.os_type == Helpers.OSType.windows:
		prog_root = os.environ.get('programfiles', 'C:\Program Files')
	else:
		prog_root = '/usr/include/'

	# Get the native install source and dest
	source = to_native(name)
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

	Process.do_on_fail_exit("Uninstalling the interface '{0}'".format(name),
					"Failed to uninstall the interface '{0}'.".format(name),
				lambda: fn())

setup()

