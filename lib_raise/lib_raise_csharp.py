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
import stat

import lib_raise_config as Config
import lib_raise_terminal as Print
import lib_raise_users as Users
import lib_raise_find as Find
import lib_raise_fs as FS
import lib_raise_process as Process
import lib_raise_helpers as Helpers

from osinfo import *

cs_compilers = {}
missing_compilers = []

def setup():
	global cs_compilers
	global missing_compilers

	# Get the names and paths for know C# compilers
	names = ['dmcs', 'csc']
	for name in names:
		paths = Find.program_paths(name)
		if len(paths) == 0:
			missing_compilers.append(name)
			continue

		if name in ['dmcs']:
			comp = CSCompiler(
				name =                 name, 
				path =                 paths[0], 
				out_file =             '-out:', 
				debug =                '-debug', 
				warnings_all =         '-warn:4', 
				warnings_as_errors =   '-warnaserror', 
				optimize =             '-optimize', 
				runtime =              'mono'
			)
			cs_compilers[comp._name] = comp
		elif name in ['csc']:
			comp = CSCompiler(
				name =                 name, 
				path =                 paths[0], 
				out_file =             '-out:', 
				debug =                '-debug', 
				warnings_all =         '-warn:4', 
				warnings_as_errors =   '-warnaserror', 
				optimize =             '-optimize', 
				runtime =              ''
			)
			cs_compilers[comp._name] = comp

	# Make sure there is at least one C# compiler installed
	if len(cs_compilers) == 0:
		Print.status("Setting up C# module")
		Print.fail()
		Print.exit("No C# compiler found. Install one and try again.")


class CSCompiler(object):
	def __init__(self, name, path, out_file, 
				debug, warnings_all, warnings_as_errors, 
				optimize, runtime):

		self._name = name
		self._path = path

		# Save text for all the options
		self._opt_setup = setup
		self._opt_out_file = out_file
		self._opt_debug = debug
		self._opt_warnings_all = warnings_all
		self._opt_warnings_as_errors = warnings_as_errors
		self._opt_optimize = optimize

		# Set the default values of the flags
		self.debug = False
		self.warnings_all = False
		self.warnings_as_errors = False
		self.optimize = True

		self._runtime = runtime

	def get_csc(self):
		return self._name
	csc = property(get_csc)

	def get_csflags(self):
		opts = []
		if self.debug and self._opt_debug:
			opts.append(self._opt_debug)
		if self.warnings_all and self._opt_warnings_all:
			opts.append(self._opt_warnings_all)
		if self.warnings_as_errors and self._opt_warnings_as_errors:
			opts.append(self._opt_warnings_as_errors)
		if self.optimize and self._opt_optimize:
			opts.append(self._opt_optimize)

		return str.join(' ', opts)
	csflags = property(get_csflags)

	def build_program(self, out_file, inc_files, link_files=[]):
		# Make sure the extension is valid
		if not out_file.endswith('.exe'):
			Print.exit("Out file extension should be '.exe' not '.{0}'.".format(out_file.split('.')[-1]))

		# Setup the messages
		task = 'Building'
		result = out_file
		plural = 'C# programs'
		singular = 'C# program'
		command = '"{0}" {1} {2}{3} {4} {5}'.format(
			self._path, 
			self.csflags, 
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

	def build_shared_library(self, out_file, inc_files, link_files=[]):
		# Make sure the extension is valid
		if not out_file.endswith('.dll'):
			Print.exit("Out file extension should be '.dll' not '.{0}'.".format(out_file.split('.')[-1]))

		# Setup the messages
		task = 'Building'
		result = out_file
		plural = 'C# shared libraries'
		singular = 'C# shared library'
		command = '"{0}" {1} -target:library {2}{3} {4} {5}'.format(
			self._path, 
			self.csflags, 
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

	def run_print(self, command):
		Print.status("Running C# program")

		native_command = '{0} {1}'.format(self._runtime, command)
		native_command = to_native(native_command)

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

def to_native(command):
	extension_map = {}
	# Figure out the extensions for this OS
	if Config.os_type in OSType.Cygwin:
		extension_map = {
			'.exe' : '.exe',
			'.dll' : '.dll'
		}
	elif Config.os_type in OSType.Windows:
		extension_map = {
			'.exe' : '.exe',
			'.dll' : '.dll'
		}
	else:
		extension_map = {
			'.exe' : '.exe',
			'.dll' : '.dll'
		}

	for before, after in extension_map.items():
		command = command.replace(before, after)

	return command

def get_default_compiler():
	global cs_compilers

	for name in ['dmcs', 'csc']:
		if name in cs_compilers:
			return cs_compilers[name]

	return None

def install_program(name, dir_name):
	# Make sure the extension is valid
	Helpers.require_file_extension(name, '.exe')

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

		if not Config.os_type in OSType.Windows:
			script_name = Helpers.before(name, '.')
			script_path = os.path.join('/usr/bin/', script_name)
			with open(script_path, 'w') as f:
				f.write("#!/usr/bin/env bash\n")
				f.write("\n")
				f.write("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib/{0}\n".format(dir_name))
				f.write("THIS_EXE=\"/usr/lib/{0}/{1}.exe\"\n".format(dir_name, script_name))
				f.write("exec mono $THIS_EXE \"$@\"\n")
				f.write("\n")
			st = os.stat(script_path)
			os.chmod(script_path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

	Process.do_on_fail_exit("Installing the program '{0}'".format(name),
					"Failed to install the program '{0}'.".format(name),
				lambda: fn())

def uninstall_program(name, dir_name):
	# Make sure the extension is valid
	Helpers.require_file_extension(name, '.exe')

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

		if not Config.os_type in OSType.Windows:
			script_name = Helpers.before(name, '.')
			if os.path.isfile('/usr/bin/' + script_name):
				os.remove('/usr/bin/' + script_name)

	Process.do_on_fail_exit("Uninstalling the program '{0}'".format(name),
					"Failed to uninstall the program '{0}'.".format(name),
				lambda: fn())

def install_library(name, dir_name):
	# Make sure the extension is valid
	Helpers.require_file_extension(name, '.dll')

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

def uninstall_library(name, dir_name):
	# Make sure the extension is valid
	Helpers.require_file_extension(name, '.dll')

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

setup()

