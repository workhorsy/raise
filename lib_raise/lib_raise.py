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

import os, sys
import signal, atexit


def early_exit(message):
	sys.stdout.write('{0} Exiting ...\n'.format(message))
	sys.stdout.flush()
	exit(1)

# Make sure we are in at least python 2.6
if sys.version_info < (2, 6):
	early_exit("Python 2.6 or greater is required.")

class Config(object):
	modules = {}
	modules_to_import = []
	target_name = None
	pwd = os.sys.path[0]
	python = sys.executable
	is_bw = False

	@classmethod
	def require_module(cls, file_name):
		# Just return if exist and is setup
		if file_name in cls.modules and cls.modules[file_name].is_setup:
			return cls.modules[file_name]

		# Print a message showing the user that they should setup the module
		print_status("{0} module check".format(file_name))
		print_fail()
		print_exit("Call import_module('{0}') before using any {0} functions.".format(file_name))


class RaiseModule(object):
	def __init__(self, name):
		self.is_setup = False
		self.name = name

	def setup(self):
		raise NotImplementedError("This method should setup the module, then set self.is_setup = True.")

# Other C compilers: Clang, DMC, Dingus, Elsa, PCC
# http://en.wikipedia.org/wiki/List_of_compilers#C_compilers
class Compiler(object):
	def __init__(self, name, path, setup, out_file, no_link, 
				debug, warnings_all, warnings_as_errors, optimize, 
				compile_time_flags, link):

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

def import_module(name):
	Config.modules_to_import.append(name)

def import_module_immediate(module_name, g=globals(), l=locals()):
	# Skip if already loaded
	if module_name in Config.modules:
		return

	script_name = os.path.join(Config.pwd, 'lib_raise_{0}.py'.format(module_name.lower()))

	# Make sure there is an rscript file
	if not os.path.isfile(script_name):
		print_exit("No such module '{0}' ({1}).".format(module_name, script_name))

	# Get a list of all the modules
	existing_modules = [module for module in RaiseModule.__subclasses__()]

	# Load the module file into this namespace
	with open(script_name, 'rb') as f:
		code = compile(f.read(), script_name, 'exec')
		exec(code, g, l)

	# Get any new modules and set them up
	has_module = False
	for module in RaiseModule.__subclasses__():
		if not module in existing_modules:
			mod = module()
			mod.setup()
			Config.modules[mod.name] = mod
			has_module = True

	# Make sure the script actually has a module class in it
	if not has_module:
		print_exit("Script file does not contain a module ({0}).".format(script_name))

def import_rscript(g=globals(), l=locals()):
	# Make sure there is an rscript file
	if not os.path.isfile('rscript'):
		return None

	# Get a list of all the functions
	before = []
	for key in globals().keys():
		before.append(key)

	# Load the rscript file into this namespace
	with open('rscript', 'rb') as f:
		code = None
		try:
			code = compile(f.read(), 'rscript', 'exec')
		except Exception as e:
			print_exit(e)

		exec(code, g, l)

	# Get just the target functions
	targets = {}
	for key in globals().keys():
		if not key in before:
			if not key.startswith('_') and hasattr(globals()[key], '__call__'):
				targets[key] = globals()[key]

	return targets

if __name__ == '__main__':
	# Get the args and options
	args = []
	for arg in sys.argv[1:]:
		if arg.startswith('-'):
			if arg == '-bw': Config.is_bw = True
		else:
			args.append(arg)

	# Load the default modules
	import_module_immediate('CPU')
	import_module_immediate('OS')
	import_module_immediate('PROCESS')
	import_module_immediate('HELPERS')
	import_module_immediate('TERMINAL')
	import_module_immediate('FS')
	import_module_immediate('LIBRARIES')

	# Have all KeyboardInterrupt exceptions quit with a clean message
	def signal_handler(signal, frame):
		print_exit('Exit called by the keyboard.')
		exit(1)
	signal.signal(signal.SIGINT, signal_handler)

	# Clear the terminal
	terminal_mod = Config.require_module('TERMINAL')
	if terminal_mod._terminal_clear:
		os.system(terminal_mod._terminal_clear)

	# Get the target function name
	Config.target_name = str(str.join(' ', args))

	# Load the rscript
	targets = import_rscript()

	# Get a friendly list of all the targets
	target_list = []
	if targets:
		keys = list(targets.keys())
		keys.sort()
		target_list = "'" + str.join("', '", keys) + "'"

	# Exit if there is no target
	if not Config.target_name:
		print("Raise software build tool (Version 0.3 - October 1 2013) http://launchpad.net/raise")
		print("")
		print("COMMANDS:")
		print("    ./raise update - Downloads the Raise libraries into a directory named \".lib_raise\" or \"lib_raise\".")
		print("")

		# Print all the targets
		if targets:
			no_doc = "No docstring is provided for this target."
			print("TARGETS:")
			for t in targets:
				doc = targets[t].__doc__ or no_doc
				print("    ./raise {0} - {1}".format(t, doc))
				print("")
			print_exit("No target specified. Found targets are {0}.".format(target_list))

	if not targets:
		print_exit("No 'rscript' file found.")

	# Exit if there is no target with that name
	if not Config.target_name in targets:
		print_exit("No target named '{0}'. Found targets are {1}.".format(Config.target_name, target_list))

	# Setup any modules required in the rscript
	for module in Config.modules_to_import:
		import_module_immediate(module)

	# Try running the target in the rscript
	target = targets[Config.target_name]
	print_info("Running target '{0}'".format(Config.target_name))
	target()


