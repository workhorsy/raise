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



class CModule(RaiseModule):
	def __init__(self):
		super(CModule, self).__init__("C")
		self.c_compilers = {}
		self._cc = None

	def setup(self):
		os_module = Config.require_module("OS")
		entension_map = {}
		# Figure out the extensions for this OS
		if os_module._os_type._name == 'Cygwin':
			entension_map = {
				'.exe' : '.exe',
				'.o' : '.o',
				'.so' : '.so',
				'.a' : '.a'
			}
		elif os_module._os_type._name == 'Windows':
			entension_map = {
				'.exe' : '.exe',
				'.o' : '.obj',
				'.so' : '.dll',
				'.a' : '.lib'
			}
		else:
			entension_map = {
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
					entension_map = entension_map
				)
				self.c_compilers[comp._name] = comp
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
					entension_map = entension_map
				)
				self.c_compilers[comp._name] = comp
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
					entension_map = entension_map
				)
				self.c_compilers[comp._name] = comp

		# Make sure there is at least one C compiler installed
		if len(self.c_compilers) == 0:
			print_status("Setting up C module")
			print_fail()
			print_exit("No C compiler found. Install one and try again.")

		self.is_setup = True

def c_get_default_compiler():
	module = Config.require_module("C")
	os_module = Config.require_module("OS")

	comp = None

	if os_module._os_type._name == 'Windows':
		comp = module.c_compilers['cl.exe']
	else:
		if 'gcc' in module.c_compilers:
			comp = module.c_compilers['gcc']
		elif 'clang' in module.c_compilers:
			comp = module.c_compilers['clang']

	return comp

def c_save_compiler(compiler):
	module = Config.require_module("C")

	# CC
	module._cc = compiler
	os.environ['CC'] = module._cc._name

	# CFLAGS
	opts = []
	opts.append(module._cc._opt_setup)
	if module._cc.debug: opts.append(module._cc._opt_debug)
	if module._cc.warnings_all: opts.append(module._cc._opt_warnings_all)
	if module._cc.warnings_as_errors: opts.append(module._cc._opt_warnings_as_errors)
	if module._cc.optimize: opts.append(module._cc._opt_optimize)
	for compile_time_flag in module._cc.compile_time_flags:
		opts.append(module._cc._opt_compile_time_flags + compile_time_flag)

	os.environ['CFLAGS'] = str.join(' ', opts)

def c_link_program(out_file, obj_files, i_files=[]):
	module = Config.require_module("C")

	# Make sure the extension is valid
	if not out_file.endswith('.exe'):
		print_exit("Out file extension should be '.exe' not '.{0}'.".format(out_file.split('.')[-1]))

	# Setup the messages
	task = 'Linking'
	result = out_file
	plural = 'C programs'
	singular = 'C program'
	command = '${CC} ${CFLAGS} ' + \
				module._cc._opt_link + ' ' + \
				str.join(' ', obj_files) + ' ' + \
				str.join(' ', i_files) + ' ' + \
				module._cc._opt_out_file + out_file
	command = module._cc.to_native(command)

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
	module = Config.require_module("C")

	# Make sure the extension is valid
	if not o_file.endswith('.o'):
		print_exit("Out file extension should be '.o' not '.{0}'.".format(o_file.split('.')[-1]))

	# Setup the messages
	task = 'Building'
	result = o_file
	plural = 'C objects'
	singular = 'C object'
	command = "${CC} ${CFLAGS} " + \
				module._cc._opt_no_link + ' ' +  \
				module._cc._opt_out_file + \
				o_file + ' ' + \
				str.join(' ', c_files) + ' ' + \
				str.join(' ', i_files)
	command = module._cc.to_native(command)

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
	module = Config.require_module("C")

	# Make sure the extension is valid
	if not o_file.endswith('.exe'):
		print_exit("Out file extension should be '.exe' not '.{0}'.".format(o_file.split('.')[-1]))

	# Setup the messages
	task = 'Building'
	result = o_file
	plural = 'C programs'
	singular = 'C program'
	command = '${CC} ${CFLAGS} ' + \
				str.join(' ', c_files) + ' ' + \
				str.join(' ', i_files) + ' ' + \
				module._cc._opt_out_file + o_file
	command = module._cc.to_native(command)

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
	module = Config.require_module("LINKER")

	# Make sure the extension is valid
	if not so_file.endswith('.so'):
		print_exit("Out file extension should be '.so' not '.{0}'.".format(so_file.split('.')[-1]))

	# Setup the messages
	task = 'Building'
	result = so_file
	plural = 'shared libraries'
	singular = 'shared library'
	command = "{0} {1} {2} {3} {4}{5}".format(
				module._linker._name, 
				module._linker._opt_setup, 
				module._linker._opt_shared, 
				str.join(' ', o_files), 
				module._linker._opt_out_file, 
				so_file)
	command = module._linker.to_native(command)

	def setup():
		# Skip if the files have not changed since last build
		if not is_outdated(to_update = [so_file], triggers = o_files):
			return False
		return True

	# Create the event
	event = Event(task, result, plural, singular, command, setup)
	add_event(event)

def c_run_say(command):
	module = Config.require_module("C")

	print_status("Running C program")

	native_command = module._cc.to_native(command)
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

