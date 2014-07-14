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

import os, sys
import shutil
import lib_raise_config as Config
import lib_raise_terminal as Print
import lib_raise_users as Users
import lib_raise_find as Find
import lib_raise_fs as FS
import lib_raise_process as Process
import lib_raise_helpers as Helpers


cxx_compilers = {}

class Standard(object):
	std1998 = 1
	std2003 = 2
	std2011 = 3
	std201x = 4
	gnu1998 = 5
	gnu2003 = 6
	gnu2011 = 7
	gnu201x = 8

def setup():
	global cxx_compilers

	# Get the names and paths for know C++ compilers
	names = ['g++', 'clang++', 'cl.exe']
	for name in names:
		paths = Find.program_paths(name)
		if len(paths) == 0:
			continue

		standards = {
			Standard.std1998 : '-std=c++98', 
			Standard.std2003 : '-std=c++03', 
			Standard.std2011 : '-std=c++11', 
			Standard.std201x : '-std=c++1x', 
			Standard.gnu1998 : '-std=gnu++98', 
			Standard.gnu2003 : '-std=gnu++03', 
			Standard.gnu2011 : '-std=gnu++11', 
			Standard.gnu201x : '-std=gnu++1x'
		}

		if name == 'g++':
			comp = CXXCompiler(
				name =                 'g++', 
				path =                 paths[0], 
				standards =             standards, 
				setup =                '', 
				out_file =             '-o ', 
				no_link =              '-c', 
				debug =                '-g', 
				position_independent_code = '-fPIC', 
				warnings_all =         '-Wall', 
				warnings_as_errors =   '-Werror', 
				warnings_extra =       '-Wextra', 
				optimize_zero =        '-O0',
				optimize_one =         '-O1',
				optimize_two =         '-O2',
				optimize_three =       '-O3',
				optimize_size =        '-Os',
				compile_time_flags =   '-D', 
				link =                 '-shared -Wl,-as-needed'
			)
			cxx_compilers[comp._name] = comp
		elif name == 'clang++':
			comp = CXXCompiler(
				name =                 'clang++', 
				path =                 paths[0], 
				standards =             standards, 
				setup =                '', 
				out_file =             '-o ', 
				no_link =              '-c', 
				debug =                '-g', 
				position_independent_code = '-fPIC', 
				warnings_all =         '-Wall', 
				warnings_as_errors =   '-Werror', 
				warnings_extra =       '-Wextra', 
				optimize_zero =        '-O0',
				optimize_one =         '-O1',
				optimize_two =         '-O2',
				optimize_three =       '-O3',
				optimize_size =        '-Os',
				compile_time_flags =   '-D', 
				link =                 '-shared -Wl,-as-needed'
			)
			cxx_compilers[comp._name] = comp
		elif name == 'cl.exe':
			# http://msdn.microsoft.com/en-us/library/19z1t1wy.aspx
			comp = CXXCompiler(
				name =                 'cl.exe', 
				path =                 paths[0], 
				standards =             None, 
				setup =                '/nologo /EHsc', 
				out_file =             '/Fe', 
				no_link =              '/c', 
				debug =                '/Zi', 
				position_independent_code = '', 
				warnings_all =         '/Wall', 
				warnings_as_errors =   '/WX', 
				warnings_extra =       None, 
				optimize_zero =        '/Od',
				optimize_one =         '/O1',
				optimize_two =         '/O2',
				optimize_three =       '/Ox',
				optimize_size =        '/Os',
				compile_time_flags =   '/D', 
				link =                 '/LDd'
			)
			cxx_compilers[comp._name] = comp

	# Make sure there is at least one C++ compiler installed
	if len(cxx_compilers) == 0:
		Print.status("Setting up C++ module")
		Print.fail()
		Print.exit("No C++ compiler found. Install one and try again.")


class CXXCompiler(object):
	def __init__(self, name, path, standards, setup, out_file, 
				no_link, debug, position_independent_code, 
				warnings_all, warnings_as_errors, warnings_extra, 
				optimize_zero, optimize_one, optimize_two,
				optimize_three, optimize_size, 
				compile_time_flags, link):

		self._name = name
		self._path = path

		# Save text for all the options
		self._opt_standards = standards
		self._opt_setup = setup
		self._opt_out_file = out_file
		self._opt_no_link = no_link
		self._opt_debug = debug
		self._opt_position_independent_code = position_independent_code
		self._opt_warnings_all = warnings_all
		self._opt_warnings_as_errors = warnings_as_errors
		self._opt_warnings_extra = warnings_extra
		self._opt_optimize_zero = optimize_zero
		self._opt_optimize_one = optimize_one
		self._opt_optimize_two = optimize_two
		self._opt_optimize_three = optimize_three
		self._opt_optimize_size = optimize_size

		self._opt_compile_time_flags = compile_time_flags
		self._opt_link = link

		# Set the default values of the flags
		self.debug = False
		self.standard = None
		self.position_independent_code = False
		self.warnings_all = False
		self.warnings_as_errors = False
		self.warnings_extra = False
		self.optimize_level = 1
		self.compile_time_flags = []

	def get_cxx(self):
		return self._name
	cxx = property(get_cxx)

	def get_cxxflags(self):
		opts = []
		opts.append(self._opt_setup)
		if self.debug: opts.append(self._opt_debug)
		if self.standard: opts.append(self._opt_standards[self.standard])
		if self.position_independent_code: opts.append(self._opt_position_independent_code)
		if self.warnings_all: opts.append(self._opt_warnings_all)
		if self.warnings_as_errors: opts.append(self._opt_warnings_as_errors)
		if self.warnings_extra: opts.append(self._opt_warnings_extra)
		if self.optimize_level == 0: opts.append(self._opt_optimize_zero)
		if self.optimize_level == 1: opts.append(self._opt_optimize_one)
		if self.optimize_level == 2: opts.append(self._opt_optimize_two)
		if self.optimize_level == 3: opts.append(self._opt_optimize_three)
		if self.optimize_level == 'small': opts.append(self._opt_optimize_size)
		for compile_time_flag in self.compile_time_flags:
			opts.append(self._opt_compile_time_flags + compile_time_flag)

		flags = str.join(' ', opts)
		return flags
	cxxflags = property(get_cxxflags)

	def build_program(self, o_file, cxx_files, i_files=[]):
		# Make sure the extension is valid
		Helpers.require_file_extension(o_file, '.exe')

		# Setup the messages
		task = 'Building'
		result = o_file
		plural = 'C++ programs'
		singular = 'C++ program'
		command = '{0} {1} {2} {3} {4}{5}'.format(
					self._path, 
					self.cxxflags, 
					str.join(' ', cxx_files), 
					str.join(' ', i_files), 
					self._opt_out_file, 
					o_file)
		command = to_native(command)

		def setup():
			# Skip if the files have not changed since last build
			to_update = [to_native(o_file)]
			triggers = [to_native(t) for t in cxx_files + i_files]
			if not FS.is_outdated(to_update, triggers):
				return False

			# Create the output directory if it does not exist
			FS.create_path_dirs(o_file)

			return True

		# Create the event
		event = Process.Event(task, result, plural, singular, command, setup)
		Process.add_event(event)

	def build_shared_library(self, o_file, cxx_files, i_files=[]):
		# Make sure the extension is valid
		Helpers.require_file_extension(o_file, '.so')

		# Setup the messages
		task = 'Building'
		result = o_file
		plural = 'C++ shared libraries'
		singular = 'C++ shared library'
		command = '{0} {1} {2} {3} {4} {5}{6}'.format(
					self._path, 
					self.cxxflags, 
					self._opt_link, 
					str.join(' ', cxx_files), 
					str.join(' ', i_files), 
					self._opt_out_file, 
					o_file)
		command = to_native(command)

		def setup():
			# Skip if the files have not changed since last build
			to_update = [to_native(o_file)]
			triggers = [to_native(t) for t in cxx_files + i_files]
			if not FS.is_outdated(to_update, triggers):
				return False

			# Create the output directory if it does not exist
			FS.create_path_dirs(o_file)

			return True

		# Create the event
		event = Process.Event(task, result, plural, singular, command, setup)
		Process.add_event(event)

	def link_program(self, out_file, obj_files, i_files=[]):
		# Make sure the extension is valid
		Helpers.require_file_extension(out_file, '.exe')

		# Setup the messages
		task = 'Linking'
		result = out_file
		plural = 'C++ programs'
		singular = 'C++ program'
		command = '{0} {1} {2} {3} {4} {5}{6}'.format(
					self._path, 
					self.cxxflags, 
					self._opt_link, 
					str.join(' ', obj_files), 
					str.join(' ', i_files), 
					self._opt_out_file, 
					out_file)
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

	def build_object(self, o_file, cxx_files, i_files=[]):
		# Make sure the extension is valid
		Helpers.require_file_extension(o_file, '.o')

		# Setup the messages
		task = 'Building'
		result = o_file
		plural = 'C++ objects'
		singular = 'C++ object'
		command = "{0} {1} {2} {3}{4} {5} {6}".format(
					self._path, 
					self.cxxflags, 
					self._opt_no_link, 
					self._opt_out_file, 
					o_file, 
					str.join(' ', cxx_files), 
					str.join(' ', i_files))
		command = to_native(command)

		def setup():
			# Skip if the files have not changed since last build
			to_update = [to_native(o_file)]
			triggers = [to_native(t) for t in cxx_files + i_files]
			if not FS.is_outdated(to_update, triggers):
				return False

			# Create the output directory if it does not exist
			FS.create_path_dirs(o_file)

			return True

		# Create the event
		event = Process.Event(task, result, plural, singular, command, setup)
		Process.add_event(event)


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

def get_default_compiler():
	global cxx_compilers
	comp = None

	if Helpers.os_type._name == 'Windows':
		comp = cxx_compilers['cl.exe']
	else:
		if 'g++' in cxx_compilers:
			comp = cxx_compilers['g++']
		elif 'clang++' in cxx_compilers:
			comp = cxx_compilers['clang++']

	return comp

def run_print(command):
	Print.status("Running C++ program")

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
	if Helpers.os_type._name == 'Windows':
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
	if Helpers.os_type._name == 'Windows':
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
	Helpers.require_file_extension(name, '.so', '.a')

	# Get the location programs are stored in
	prog_root = None
	if Helpers.os_type._name == 'Windows':
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
	Helpers.require_file_extension(name, '.so', '.a')

	# Get the location programs are stored in
	prog_root = None
	if Helpers.os_type._name == 'Windows':
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

def install_header(name, dir_name=None):
	# Make sure the extension is valid
	Helpers.require_file_extension(name, '.h')

	# Get the location headers are stored in
	prog_root = None
	if Helpers.os_type._name == 'Windows':
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

	Process.do_on_fail_exit("Installing the header '{0}'".format(name),
					"Failed to install the header '{0}'.".format(name),
				lambda: fn())

def uninstall_header(name, dir_name=None):
	# Make sure the extension is valid
	Helpers.require_file_extension(name, '.h')

	# Get the location header are stored in
	prog_root = None
	if Helpers.os_type._name == 'Windows':
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

	Process.do_on_fail_exit("Uninstalling the header '{0}'".format(name),
					"Failed to uninstall the header '{0}'.".format(name),
				lambda: fn())


setup()


