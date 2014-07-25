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
from osinfo import *
import lib_raise_config as Config
import lib_raise_terminal as Print
import lib_raise_users as Users
import lib_raise_find as Find
import lib_raise_process as Process
import lib_raise_fs as FS
import lib_raise_helpers as Helpers


c_compilers = {}

class Standard(object):
	std1989 = 1
	std1990 = 2
	std1999 = 3
	std2011 = 4
	std201x = 5
	gnu1989 = 6
	gnu1990 = 7
	gnu1999 = 8
	gnu2011 = 9
	gnu201x = 10

def setup():
	global c_compilers

	# Get the names and paths for know C compilers
	names = ['gcc', 'clang', 'cl.exe']
	for name in names:
		paths = Find.program_paths(name)
		if len(paths) == 0:
			continue

		standards = {
			Standard.std1989 : '-std=c89', 
			Standard.std1990 : '-std=c90', 
			Standard.std1999 : '-std=c99', 
			Standard.std2011 : '-std=c11', 
			Standard.std201x : '-std=c1x', 
			Standard.gnu1989 : '-std=gnu89', 
			Standard.gnu1990 : '-std=gnu90', 
			Standard.gnu1999 : '-std=gnu99', 
			Standard.gnu2011 : '-std=gnu11', 
			Standard.gnu201x : '-std=gnu1x'
		}

		if name == 'gcc':
			comp = CCompiler(
				name =                 'gcc', 
				path =                 paths[0], 
				standards =             standards, 
				setup =                '', 
				out_file =             '-o ', 
				no_link =              '-c', 
				debug =                '-g', 
				position_independent_code = '-fPIC', 
				warnings_all =         '-Wall', 
				warnings_extra =       '-Wextra', 
				warnings_as_errors =   '-Werror', 
				optimize_zero =        '-O0',
				optimize_one =         '-O1',
				optimize_two =         '-O2',
				optimize_three =       '-O3',
				optimize_size =        '-Os',
				compile_time_flags =   '-D', 
				link =                 '-shared'
			)
			c_compilers[comp._name] = comp
		elif name == 'clang':
			comp = CCompiler(
				name =                 'clang', 
				path =                 paths[0], 
				standards =             standards, 
				setup =                '', 
				out_file =             '-o ', 
				no_link =              '-c', 
				debug =                '-g', 
				position_independent_code = '-fPIC', 
				warnings_all =         '-Wall', 
				warnings_extra =       '-Wextra', 
				warnings_as_errors =   '-Werror', 
				optimize_zero =        '-O0',
				optimize_one =         '-O1',
				optimize_two =         '-O2',
				optimize_three =       '-O3',
				optimize_size =        '-Os',
				compile_time_flags =   '-D', 
				link =                 '-shared'
			)
			c_compilers[comp._name] = comp
		elif name == 'cl.exe':
			# http://msdn.microsoft.com/en-us/library/19z1t1wy.aspx
			comp = CCompiler(
				name =                 'cl.exe', 
				path =                 paths[0], 
				standards =             None, 
				setup =                '/nologo', 
				out_file =             '/Fe', 
				no_link =              '/c', 
				debug =                '/Zi', 
				position_independent_code = '', 
				warnings_all =         '/Wall', 
				warnings_extra =       None, 
				warnings_as_errors =   '/WX', 
				optimize_zero =        '/Od',
				optimize_one =         '/O1',
				optimize_two =         '/O2',
				optimize_three =       '/Ox',
				optimize_size =        '/Os',
				compile_time_flags =   '/D', 
				link =                 '/LDd'
			)
			c_compilers[comp._name] = comp

	# Make sure there is at least one C compiler installed
	if len(c_compilers) == 0:
		Print.status("Setting up C module")
		Print.fail()
		Print.exit("No C compiler found. Install one and try again.")


# Other C compilers: DMC, Dingus, Elsa, PCC
# http://en.wikipedia.org/wiki/List_of_compilers#C_compilers
class CCompiler(object):
	def __init__(self, name, path, standards, setup, out_file, 
				no_link, debug, position_independent_code, 
				warnings_all, warnings_extra, warnings_as_errors, 
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
		self._opt_warnings_extra = warnings_extra
		self._opt_warnings_as_errors = warnings_as_errors
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
		self.warnings_extra = False
		self.warnings_as_errors = False
		self.optimize_level = 1
		self.compile_time_flags = []

	def get_cc(self):
		return self._name
	cc = property(get_cc)

	def get_cflags(self):
		opts = []
		if self._opt_setup:
			opts.append(self._opt_setup)
		if self.debug and self._opt_debug:
			opts.append(self._opt_debug)
		if self.standard and self._opt_standards:
			opts.append(self._opt_standards[self.standard])
		if self.position_independent_code and self._opt_position_independent_code:
			opts.append(self._opt_position_independent_code)
		if self.warnings_all and self._opt_warnings_all:
			opts.append(self._opt_warnings_all)
		if self.warnings_extra and self._opt_warnings_extra:
			opts.append(self._opt_warnings_extra)
		if self.warnings_as_errors and self._opt_warnings_as_errors:
			opts.append(self._opt_warnings_as_errors)
		if self.optimize_level == 0 and self._opt_optimize_zero:
			opts.append(self._opt_optimize_zero)
		if self.optimize_level == 1 and self._opt_optimize_one:
			opts.append(self._opt_optimize_one)
		if self.optimize_level == 2 and self._opt_optimize_two:
			opts.append(self._opt_optimize_two)
		if self.optimize_level == 3 and self._opt_optimize_three:
			opts.append(self._opt_optimize_three)
		if self.optimize_level == 'small' and self._opt_optimize_size:
			opts.append(self._opt_optimize_size)
		if self._opt_compile_time_flags:
			for compile_time_flag in self.compile_time_flags:
				opts.append(self._opt_compile_time_flags + compile_time_flag)

		flags = str.join(' ', opts)
		return flags
	cflags = property(get_cflags)

	def link_program(self, out_file, obj_files, i_files=[]):
		# Make sure the extension is valid
		Helpers.require_file_extension(out_file, '.exe')

		# Setup the messages
		task = 'Linking'
		result = out_file
		plural = 'C programs'
		singular = 'C program'
		command = '"{0}" {1} {2} {3} {4} {5}{6}'.format(
					self._path, 
					self.cflags, 
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

	def build_object(self, o_file, c_files, i_files=[]):
		# Make sure the extension is valid
		Helpers.require_file_extension(o_file, '.o')

		# Setup the messages
		task = 'Building'
		result = o_file
		plural = 'C objects'
		singular = 'C object'
		command = '"{0}" {1} {2} {3}{4} {5} {6}'.format(
					self._path, 
					self.cflags, 
					self._opt_no_link, 
					self._opt_out_file, 
					o_file, 
					str.join(' ', c_files),
					str.join(' ', i_files))
		command = to_native(command)

		def setup():
			# Skip if the files have not changed since last build
			to_update = [to_native(o_file)]
			triggers = [to_native(t) for t in c_files + i_files]
			if not FS.is_outdated(to_update, triggers):
				return False

			# Create the output directory if it does not exist
			FS.create_path_dirs(o_file)

			return True

		# Create the event
		event = Process.Event(task, result, plural, singular, command, setup)
		Process.add_event(event)

	def build_program(self, o_file, c_files, i_files=[]):
		# Make sure the extension is valid
		Helpers.require_file_extension(o_file, '.exe')

		# Setup the messages
		task = 'Building'
		result = o_file
		plural = 'C programs'
		singular = 'C program'
		command = '"{0}" {1} {2} {3} {4}{5}'.format(
					self._path, 
					self.cflags, 
					str.join(' ', c_files), 
					str.join(' ', i_files), 
					self._opt_out_file, 
					o_file)
		command = to_native(command)

		def setup():
			# Skip if the files have not changed since last build
			to_update = [to_native(o_file)]
			triggers = [to_native(t) for t in c_files + i_files]
			if not FS.is_outdated(to_update, triggers):
				return False

			# Create the output directory if it does not exist
			FS.create_path_dirs(o_file)

			return True

		# Create the event
		event = Process.Event(task, result, plural, singular, command, setup)
		Process.add_event(event)

	def build_shared_library(self, so_file, o_files):
		# Make sure the extension is valid
		Helpers.require_file_extension(so_file, '.so')

		# Setup the messages
		task = 'Building'
		result = so_file
		plural = 'C shared libraries'
		singular = 'C shared library'
		command = "{0} {1} {2} {3} {4}{5}".format(
					self._name, 
					self._opt_setup, 
					self._opt_link, 
					str.join(' ', o_files), 
					self._opt_out_file, 
					so_file)
		command = to_native(command)

		def setup():
			# Skip if the files have not changed since last build
			to_update = [to_native(so_file)]
			triggers = [to_native(t) for t in o_files]
			if not FS.is_outdated(to_update, triggers):
				return False

			# Create the output directory if it does not exist
			FS.create_path_dirs(so_file)

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
	elif Config.os_type in OSType.MacOS:
		extension_map = {
			'.exe' : '',
			'.o' : '.o',
			'.so' : '.dylib',
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

def get_default_compiler():
	global c_compilers

	if Config.os_type in OSType.Windows:
		# Make sure Windows SDK tools are found
		if not 'WINDOWSSDKDIR' in os.environ and not 'WINDOWSSDKVERSIONOVERRIDE' in os.environ:
			Print.status("Setting up cl.exe")
			Print.fail()
			Print.exit('Windows SDK not found. Must be run from Windows SDK Command Prompt.')

		return c_compilers.get('cl.exe')
	elif Config.os_type in OSType.Unix:
		return c_compilers.get('clang') or c_compilers.get('gcc')
	else:
		return c_compilers.get('gcc') or c_compilers.get('clang')

	return None

def run_print(command):
	Print.status("Running C program")

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
	if Config.os_type in OSType.Windows:
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
	if Config.os_type in OSType.Windows:
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
	if Config.os_type in OSType.Windows:
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
	if Config.os_type in OSType.Windows:
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
	if Config.os_type in OSType.Windows:
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
	if Config.os_type in OSType.Windows:
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



