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

from lib_raise_os import *
from lib_raise_libraries import *


class Java(RaiseModule):
	java_compilers = {}
	java_runtimes = {}
	java_jars = {}
	javac = None
	jar = None
	runtime = None

	@classmethod
	def setup(cls):
		extension_map = {}
		# Figure out the extensions for this OS
		extension_map = {
			'.class' : '.class',
			'.jar' : '.jar'
		}

		# Get the names and paths for know Java compilers
		names = ['javac']
		for name in names:
			paths = program_paths(name)
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
					extension_map = extension_map
				)
				Java.java_compilers[comp._name] = comp
				Java.java_runtimes[comp._name] = 'java'
				Java.java_jars[comp._name] = 'jar'

		# Make sure there is at least one Java compiler installed
		if len(cls.java_compilers) == 0:
			print_status("Setting up Java module")
			print_fail()
			print_exit("No Java compiler found. Install one and try again.")


class JavaCompiler(object):
	def __init__(self, name, path, debug, no_warnings, verbose, 
				deprecation, extension_map):

		self._name = name
		self._path = path

		# Save text for all the options
		self._opt_debug = debug
		self._opt_no_warnings = no_warnings
		self._opt_verbose = verbose
		self._opt_deprecation = deprecation
		self._opt_extension_map = extension_map

		# Set the default values of the flags
		self.debug = False
		self.warnings = True
		self.verbose = False
		self.deprecation = False

		self.extension_map = extension_map

	def to_native(self, command):
		for before, after in self.extension_map.items():
			command = command.replace(before, after)

		return command

def java_get_default_compiler():
	comp = None
	for name in ['javac']:
		if name in Java.java_compilers:
			comp = Java.java_compilers[name]
			break

	return comp

def java_save_compiler(compiler):
	# JAVAC
	Java.javac = compiler
	Java.runtime = Java.java_runtimes[Java.javac._name]
	Java.jar = Java.java_jars[Java.javac._name]
	os.environ['JAVAC'] = Java.javac._name
	os.environ['JAR'] = Java.jar
	os.environ['JAVA'] = Java.runtime

	# JAVAFLAGS
	opts = []
	if Java.javac.debug: opts.append(Java.javac._opt_debug)
	if not Java.javac.warnings: opts.append(Java.javac._opt_no_warnings)
	if Java.javac.verbose: opts.append(Java.javac._opt_verbose)
	if Java.javac.deprecation: opts.append(Java.javac._opt_deprecation)

	os.environ['JAVAFLAGS'] = str.join(' ', opts)

def java_build_program(out_file, inc_files, link_files=[]):
	# Make sure the extension is valid
	if not out_file.endswith('.class'):
		print_exit("Out file extension should be '.class' not '.{0}'.".format(out_file.split('.')[-1]))

	# Setup the messages
	task = 'Building'
	result = out_file
	plural = 'Java programs'
	singular = 'Java program'
	command = "${JAVAC} ${JAVAFLAGS} " + \
	str.join(' ', inc_files) + " " + str.join(' ', link_files)
	command = Java.javac.to_native(command)

	def setup():
		if not 'JAVAC' in os.environ:
			print_fail()
			print_exit("Set the env variable 'JAVAC' to the Java compiler, and try again.")

		return True

	# Create the event
	event = Event(task, result, plural, singular, command, setup)
	add_event(event)

def java_build_jar(out_file, inc_files, link_files=[]):
	# Make sure the extension is valid
	if not out_file.endswith('.jar'):
		print_exit("Out file extension should be '.jar' not '.{0}'.".format(out_file.split('.')[-1]))

	# Setup the messages
	task = 'Building'
	result = out_file
	plural = 'Java jars'
	singular = 'Java jar'
	command = "${JAR} " + \
	'-cf ' + out_file + ' ' + \
	str.join(' ', inc_files) + " " + str.join(' ', link_files)
	command = Java.javac.to_native(command)

	def setup():
		if not 'JAR' in os.environ:
			print_fail()
			print_exit("Set the env variable 'JAR' to Java jar, and try again.")

		return True

	# Create the event
	event = Event(task, result, plural, singular, command, setup)
	add_event(event)

def java_run_say(command):
	print_status("Running Java program")

	native_command = '{0} {1}'.format(Java.runtime, command)
	native_command = Java.javac.to_native(native_command)
	runner = ProcessRunner(native_command)
	runner.run()
	runner.wait()

	if runner.is_success or runner.is_warning:
		print_ok()
		print(native_command)
		print(runner.stdall)
	elif runner.is_failure:
		print_fail()
		print(native_command)
		print(runner.stdall)
		print_exit('Failed to run command.')


Java.call_setup()

