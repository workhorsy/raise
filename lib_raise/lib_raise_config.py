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

import os, sys
import lib_raise_terminal as Print


target_name = None
pwd = os.sys.path[0]
python = sys.executable
is_plain = False
is_inspect = False


def early_exit(message):
	sys.stdout.write('{0} Exiting ...\n'.format(message))
	sys.stdout.flush()
	sys.exit(1)

def import_rscript(globals_var, locals_var):
	# Make sure there is an rscript file
	if not os.path.isfile('rscript'):
		return None

	# Load the rscript file into this namespace
	# Get a list of all the things in the script
	names = []
	with open('rscript', 'rb') as f:
		code = None
		try:
			code = compile(f.read(), 'rscript', 'exec')
			names = [name for name in code.co_names]
		except Exception as e:
			Print.exit(e)

		exec(code, globals_var, locals_var)

	# Get just the target functions
	targets = {}
	for name in names:
		if name in globals_var and not name.startswith('_'):
			if hasattr(globals_var[name], '__call__'):
				targets[name] = globals_var[name]

	return targets


# FIXME: This should be in the C module?
# Other C compilers: Clang, DMC, Dingus, Elsa, PCC
# http://en.wikipedia.org/wiki/List_of_compilers#C_compilers
class Compiler(object):
	def __init__(self, name, path, setup, out_file, no_link, 
				debug, warnings_all, warnings_as_errors, optimize, 
				compile_time_flags, link, extension_map):

		self._name = name
		self._path = path

		# Save text for all the options
		self._opt_setup = setup
		self._opt_out_file = out_file
		self._opt_no_link = no_link
		self._opt_debug = debug
		self._opt_warnings_all = warnings_all
		self._opt_warnings_as_errors = warnings_as_errors
		self._opt_optimize = optimize
		self._opt_compile_time_flags = compile_time_flags
		self._opt_link = link

		# Set the default values of the flags
		self.debug = False
		self.warnings_all = False
		self.warnings_as_errors = False
		self.optimize = False
		self.compile_time_flags = []

		self.extension_map = extension_map

	def to_native(self, command):
		for before, after in self.extension_map.items():
			command = command.replace(before, after)

		return command



