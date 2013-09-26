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

import os, sys, platform
import tempfile, shutil, filecmp
import multiprocessing, subprocess
import signal, atexit
import re
import time
import traceback, inspect
from collections import namedtuple

# FIXME: 
# Add a module class that has a setup method that mods use
# Move os type to modules
# Move cpu code to module
# Move stty to module
# Move registry stuff to windows os type


def early_exit(message):
	sys.stdout.write('{0} Exiting ...\n'.format(message))
	sys.stdout.flush()
	exit()

# Make sure we are in at least python 2.6
if sys.version_info < (2, 6):
	early_exit("Python 2.6 or greater is required.")

class Config(object):
	modules = {}
	modules_to_load = []
	target_name = None
	message_length = None

	@classmethod
	def init(cls):
		# Get the path of the rscript file
		cls.pwd = os.sys.path[0]

		# Get the name of the current running python program
		cls.python = sys.executable
		if not cls.python:
			early_exit('Could not find python to run child processes with.')

		# Figure out the CPU architecture
		if re.match('^i\d86$|^x86$|^x86_32$|^i86pc$', platform.machine()):
			cls._arch = 'x86_32'
			cls._bits = '32'
		elif re.match('^x86$|^x86_64$|^amd64$', platform.machine()):
			cls._arch = 'x86_64'
			cls._bits = '64'
		else:
			early_exit('Unknown architecture {0}.'.format(platform.machine()))

		# Figure out how many cpus there are
		cls._cpus_total = multiprocessing.cpu_count()
		cls._cpus_free = cls._cpus_total

		# Load the default modules
		load_module('OS')
		load_module('PROCESS')
		load_module('HELPERS')
		load_module('TERMINAL')
		load_module('FS')
		load_module('LIBRARIES')

		# Figure out the general OS type
		if 'cygwin' in platform.system().lower():
			cls._os_type = OSType(
				name =                 'Cygwin', 
				exe_extension =        '', 
				object_extension =     '.o', 
				shared_lib_extension = '.so', 
				static_lib_extension = '.a'
			)
		elif 'windows' in platform.system().lower():
			cls._os_type = OSType(
				name =                 'Windows', 
				exe_extension =        '.exe', 
				object_extension =     '.obj', 
				shared_lib_extension = '.dll', 
				static_lib_extension = '.lib'
			)
		else:
			cls._os_type = OSType(
				name =                 'Unix', 
				exe_extension =        '', 
				object_extension =     '.o', 
				shared_lib_extension = '.so', 
				static_lib_extension = '.a'
			)

		# Figure out how to clear the terminal
		if cls._os_type._name == 'Windows':
			cls._terminal_clear = 'cls'
		else:
			cls._terminal_clear = 'clear'

		# FIXME: Have this look for stty first then try the registry
		# Figure out the terminal width
		if cls._os_type._name == 'Windows':
			import _winreg
			key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, r"Console")
			val = _winreg.QueryValueEx(key, "ScreenBufferSize")
			_winreg.CloseKey(key)
			size = hex(val[0])
			cls._terminal_width = int('0x' + size[-4 : len(size)], 16)
		else:
			cls._terminal_width = int(os.popen('stty size', 'r').read().split()[1])

		# Make sure Windows SDK tools are found
		if cls._os_type._name == 'Windows':
			if not 'WINDOWSSDKDIR' in os.environ and not 'WINDOWSSDKVERSIONOVERRIDE' in os.environ:
				early_exit('Windows SDK not found. Must be run from Windows SDK Command Prompt.')

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
		raise NotImplementedError( "This method should setup the module, then set self.is_setup = True." )

	def _require_setup(self):
		# Just return if setup
		if self.is_setup:
			return

		# Print a message showing the user that they should setup the module
		print_status("{0} module check".format(self.name))
		print_fail()
		print_exit("Call import_module('{0}') before using any {0} functions.".format(self.name))


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

# FIXME: Should this just load the module right away?
def import_module(name):
	Config.modules_to_load.append(name)

def load_module(module_name, g=globals(), l=locals()):
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
	for module in RaiseModule.__subclasses__():
		if not module in existing_modules:
			mod = module()
			mod.setup()
			Config.modules[mod.name] = mod

def load_rscript(g=globals(), l=locals()):
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
	# Figure out everything we need to know about the system
	Config.init()

	# Have all KeyboardInterrupt exceptions quit with a clean message
	def signal_handler(signal, frame):
		print_exit('Exit called by the keyboard.')
		exit()
	signal.signal(signal.SIGINT, signal_handler)

	# Clear the terminal
	os.system(Config._terminal_clear)

	# Load the rscript
	targets = load_rscript()

	# Get the target function name
	Config.target_name = str(str.join(' ', sys.argv[1:]))

	# Get a friendly list of all the targets
	target_list = []
	if targets:
		keys = list(targets.keys())
		keys.sort()
		target_list = "'" + str.join("', '", keys) + "'"

	# Exit if there is no target
	if not Config.target_name:
		print("Raise software build tool (Version 0.3 - September 26 2013) http://launchpad.net/raise")
		print("")
		print("COMMANDS:")
		print("    ./raise update - Downloads the newest version of Raise. It will be stored in a file named \".lib_raise\" or \"lib_raise\".")
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

	# Setup any modules
	for module in Config.modules_to_load:
		load_module(module)

	# Try running the target
	target = targets[Config.target_name]
	print_info("Running target '{0}'".format(Config.target_name))
	target()


