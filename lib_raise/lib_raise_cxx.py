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


class CXXModule(RaiseModule):
	def __init__(self):
		super(CXXModule, self).__init__("CXX")
		self.cxx_compilers = {}
		self._cxx = None

	def setup(self):
		os_module = Config.require_module("OS")
		extension_map = {}
		# Figure out the extensions for this OS
		if os_module._os_type._name == 'Cygwin':
			extension_map = {
				'.exe' : '.exe',
				'.o' : '.o',
				'.so' : '.so',
				'.a' : '.a'
			}
		elif os_module._os_type._name == 'Windows':
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
		names = ['g++']
		for name in names:
			paths = program_paths(name)
			if len(paths) == 0:
				continue

			if name == 'g++':
				comp = Compiler(
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
				self.cxx_compilers[comp._name] = comp

		# Make sure there is at least one C++ compiler installed
		if len(self.cxx_compilers) == 0:
			print_status("Setting up C++ module")
			print_fail()
			print_exit("No C++ compiler found. Install one and try again.")

		self.is_setup = True


def cxx_get_default_compiler():
	module = Config.require_module("CXX")
	os_module = Config.require_module("OS")

	comp = None

	if os_module._os_type._name == 'Windows':
		comp = module.cxx_compilers['cl.exe']
	else:
		if 'g++' in module.cxx_compilers:
			comp = module.cxx_compilers['g++']

	return comp

def cxx_save_compiler(compiler):
	module = Config.require_module("CXX")

	# CXX
	module._cxx = compiler
	os.environ['CXX'] = module._cxx._name

	# CXXFLAGS
	opts = []
	opts.append(module._cxx._opt_setup)
	if module._cxx.debug: opts.append(module._cxx._opt_debug)
	if module._cxx.warnings_all: opts.append(module._cxx._opt_warnings_all)
	if module._cxx.warnings_as_errors: opts.append(module._cxx._opt_warnings_as_errors)
	if module._cxx.optimize: opts.append(module._cxx._opt_optimize)
	for compile_time_flag in module._cxx.compile_time_flags:
		opts.append(module._cxx._opt_compile_time_flags + compile_time_flag)

	os.environ['CXXFLAGS'] = str.join(' ', opts)

def cxx_build_program(o_file, cxx_files, i_files=[]):
	module = Config.require_module("CXX")

	# Make sure the extension is valid
	require_file_extension(o_file, '.exe')

	# Setup the messages
	task = 'Building'
	result = o_file
	plural = 'C++ programs'
	singular = 'C++ program'
	command = '${CXX} ${CXXFLAGS} ' + \
				str.join(' ', cxx_files) + ' ' + \
				str.join(' ', i_files) + ' ' + \
				module._cxx._opt_out_file + o_file
	command = module._cxx.to_native(command)

	def setup():
		# Make sure the environmental variable is set
		if not 'CXX' in os.environ:
			print_fail()
			print_exit("Set the env variable 'CXX' to the C++ compiler, and try again.")

		return True

	# Create the event
	event = Event(task, result, plural, singular, command, setup)
	add_event(event)

def cxx_link_program(out_file, obj_files, i_files=[]):
	module = Config.require_module("CXX")

	# Make sure the extension is valid
	require_file_extension(out_file, '.exe')

	# Setup the messages
	task = 'Linking'
	result = out_file
	plural = 'C++ programs'
	singular = 'C++ program'
	command = '${CXX} ${CXXFLAGS} ' + \
				module._cxx._opt_link + ' ' + \
				str.join(' ', obj_files) + ' ' + \
				str.join(' ', i_files) + ' ' + \
				module._cxx._opt_out_file + out_file
	command = module._cxx.to_native(command)

	def setup():
		# Make sure the environmental variable is set
		if not 'CXX' in os.environ:
			print_fail()
			print_exit("Set the env variable 'CXX' to the C++ compiler, and try again.")

		return True

	# Create the event
	event = Event(task, result, plural, singular, command, setup)
	add_event(event)

def cxx_build_object(o_file, cxx_files, i_files=[]):
	module = Config.require_module("CXX")

	# Make sure the extension is valid
	require_file_extension(o_file, '.o')

	# Setup the messages
	task = 'Building'
	result = o_file
	plural = 'C++ objects'
	singular = 'C++ object'
	command = "${CXX} ${CXXFLAGS} " + \
				module._cxx._opt_no_link + ' ' +  \
				module._cxx._opt_out_file + \
				o_file + ' ' + \
				str.join(' ', cxx_files) + ' ' + \
				str.join(' ', i_files)
	command = module._cxx.to_native(command)

	def setup():
		# Skip if the files have not changed since last build
		if not is_outdated(to_update = [o_file], triggers = cxx_files):
			return False

		# Make sure the environmental variable is set
		if not 'CXX' in os.environ:
			print_fail()
			print_exit("Set the env variable 'CXX' to the C++ compiler, and try again.")

		return True

	# Create the event
	event = Event(task, result, plural, singular, command, setup)
	add_event(event)

def cxx_run_say(command):
	module = Config.require_module("CXX")

	print_status("Running C++ program")

	native_command = module._cxx.to_native(command)
	runner = ProcessRunner(native_command)
	runner.run()
	runner.wait()

	if runner.is_success or runner.is_warning:
		print_ok()
		print(command)
		print(runner.stdall)
	elif runner.is_failure:
		print_fail()
		print(command)
		print(runner.stdall)
		print_exit('Failed to run command.')

