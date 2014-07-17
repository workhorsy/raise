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
import stat
import lib_raise_terminal as Print
import lib_raise_config as Config
import lib_raise_users as Users
import lib_raise_find as Find
import lib_raise_fs as FS
import lib_raise_process as Process
import lib_raise_helpers as Helpers


java_compilers = {}

def setup():
	global java_compilers

	# Get the names and paths for know Java compilers
	names = ['javac']
	for name in names:
		paths = Find.program_paths(name)
		if len(paths) == 0:
			continue

		if name in ['javac']:
			comp = JavaCompiler(
				name =                 name, 
				path =                 paths[0], 
				debug =                '-g', 
				no_warnings =          '-nowarn', 
				verbose =              '-verbose', 
				deprecation =          '-deprecation', 
				runtime =              'java', 
				jar =                  'jar'
			)
			java_compilers[comp._name] = comp

	# Make sure there is at least one Java compiler installed
	if len(java_compilers) == 0:
		Print.status("Setting up Java module")
		Print.fail()
		Print.exit("No Java compiler found. Install one and try again.")


class JavaCompiler(object):
	def __init__(self, name, path, debug, no_warnings, verbose, 
				deprecation, runtime, jar):

		self._name = name
		self._path = path

		# Save text for all the options
		self._opt_debug = debug
		self._opt_no_warnings = no_warnings
		self._opt_verbose = verbose
		self._opt_deprecation = deprecation

		# Set the default values of the flags
		self.debug = False
		self.warnings = True
		self.verbose = False
		self.deprecation = False

		self._runtime = runtime
		self._jar = jar

	def get_java(self):
		return self._runtime
	java = property(get_java)

	def get_javac(self):
		return self._name
	javac = property(get_javac)

	def get_runtime(self):
		return self._runtime
	runtime = property(get_runtime)

	def get_jar(self):
		return self._jar
	jar = property(get_jar)

	def get_javaflags(self):
		opts = []
		if self.debug and self._opt_debug:
			opts.append(self._opt_debug)
		if not self.warnings and self._opt_no_warnings:
			opts.append(self._opt_no_warnings)
		if self.verbose and self._opt_verbose:
			opts.append(self._opt_verbose)
		if self.deprecation and self._opt_deprecation:
			opts.append(self._opt_deprecation)

		return str.join(' ', opts)
	javaflags = property(get_javaflags)

	def build_program(self, out_file, inc_files, link_files=[]):
		# Make sure the extension is valid
		if not out_file.endswith('.class'):
			Print.exit("Out file extension should be '.class' not '.{0}'.".format(out_file.split('.')[-1]))

		# Setup the messages
		task = 'Building'
		result = out_file
		plural = 'Java programs'
		singular = 'Java program'
		command = '"{0}" {1} {2} {3}'.format(
			self._path, 
			self.javaflags, 
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

	def build_jar(self, out_file, inc_files, link_files=[]):
		# Make sure the extension is valid
		if not out_file.endswith('.jar'):
			Print.exit("Out file extension should be '.jar' not '.{0}'.".format(out_file.split('.')[-1]))

		# Setup the messages
		task = 'Building'
		result = out_file
		plural = 'Java jars'
		singular = 'Java jar'
		command = '"{0}" -cf {1} {2} {3}'.format(
			self.jar, 
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
		Print.status("Running Java program")

		native_command = '{0} {1}'.format(self._runtime, command)
		native_command = to_native(native_command)
		runner = Process.ProcessRunner(native_command)
		runner.run()
		runner.is_done
		runner.wait()

		if runner.is_success or runner.is_warning:
			Print.ok()
			sys.stdout.write(native_command + '\n')
			sys.stdout.write(runner.stdall)
		elif runner.is_failure:
			Print.fail()
			sys.stdout.write(native_command + '\n')
			sys.stdout.write(runner.stdall)
			Print.exit('Failed to run command.')


def to_native(command):
	extension_map = {}
	# Figure out the extensions for this OS
	extension_map = {
		'.class' : '.class',
		'.jar' : '.jar'
	}

	for before, after in extension_map.items():
		command = command.replace(before, after)

	return command

def get_default_compiler():
	global java_compilers

	for name in ['javac']:
		if name in java_compilers:
			return java_compilers[name]

	return None

def install_program(name, dir_name):
	# Make sure the extension is valid
	Helpers.require_file_extension(name, '.class')

	# Get the location programs are stored in
	prog_root = None
	if Helpers.os_type in Helpers.OSType.windows:
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

		if not Helpers.os_type in Helpers.OSType.windows:
			script_name = Helpers.before(name, '.')
			script_path = os.path.join('/usr/bin/', script_name)
			with open(script_path, 'w') as f:
				f.write("#!/usr/bin/env bash\n")
				f.write("\n")
				f.write("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib/{0}\n".format(dir_name))
				f.write("THIS_PATH=\"/usr/lib/{0}\"\n".format(dir_name))
				f.write("THIS_EXE=\"{0}\"\n".format(script_name))
				f.write("exec java -classpath $THIS_PATH $THIS_EXE \"$@\"\n")
				f.write("\n")
			st = os.stat(script_path)
			os.chmod(script_path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

	Process.do_on_fail_exit("Installing the program '{0}'".format(name),
					"Failed to install the program '{0}'.".format(name),
				lambda: fn())

def uninstall_program(name, dir_name):
	# Make sure the extension is valid
	Helpers.require_file_extension(name, '.class')

	# Get the location programs are stored in
	prog_root = None
	if Helpers.os_type in Helpers.OSType.windows:
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

		if not Helpers.os_type in Helpers.OSType.windows:
			script_name = Helpers.before(name, '.')
			if os.path.isfile('/usr/bin/' + script_name):
				os.remove('/usr/bin/' + script_name)

	Process.do_on_fail_exit("Uninstalling the program '{0}'".format(name),
					"Failed to uninstall the program '{0}'.".format(name),
				lambda: fn())

def install_jar(name, dir_name=None):
	# Make sure the extension is valid
	Helpers.require_file_extension(name, '.jar')

	# Get the location programs are stored in
	prog_root = None
	if Helpers.os_type in Helpers.OSType.windows:
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

	Process.do_on_fail_exit("Installing the jar '{0}'".format(name),
					"Failed to install the jar '{0}'.".format(name),
				lambda: fn())

def uninstall_jar(name, dir_name=None):
	# Make sure the extension is valid
	Helpers.require_file_extension(name, '.jar')

	# Get the location programs are stored in
	prog_root = None
	if Helpers.os_type in Helpers.OSType.windows:
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

	Process.do_on_fail_exit("Uninstalling the jar '{0}'".format(name),
					"Failed to uninstall the jar '{0}'.".format(name),
				lambda: fn())


setup()

