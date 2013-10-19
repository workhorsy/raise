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
import signal


# Make sure we are in at least python 2.6
if sys.version_info < (2, 6):
	early_exit("Python 2.6 or greater is required.")

def import_rscript(g=globals(), l=locals()):
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
			print_exit(e)

		exec(code, g, l)

	# Get just the target functions
	targets = {}
	for name in names:
		if name in globals() and not name.startswith('_'):
			if hasattr(globals()[name], '__call__'):
				targets[name] = globals()[name]

	return targets

# Load the default modules
from lib_raise_config import *
from lib_raise_cpu import *
from lib_raise_os import *
from lib_raise_process import *
from lib_raise_helpers import *
from lib_raise_terminal import *
from lib_raise_fs import *
from lib_raise_libraries import *


if __name__ == '__main__':
	# Get the args and options
	args = []
	for arg in sys.argv[1:]:
		if arg.startswith('-'):
			if arg == '-plain': Config.is_plain = True
		else:
			args.append(arg)

	# Have all KeyboardInterrupt exceptions quit with a clean message
	def signal_handler(signal, frame):
		print_exit('Exit called by the keyboard.')
		exit(1)
	signal.signal(signal.SIGINT, signal_handler)

	# Set the terminal to plain or fancy
	if Config.is_plain:
		terminal_set_plain()
	else:
		terminal_set_fancy()

	# Clear the terminal if desired
	if Terminal.terminal_clear:
		os.system(Terminal.terminal_clear)

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
		print("Raise software build tool (Version 0.3.0 - October 18 2013) http://launchpad.net/raise")
		print("OPTIONS:")
		print("    -plain - Don't clear, don't use color, and fix the width to 79")
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

	# Try running the target in the rscript
	target = targets[Config.target_name]
	print_info("Running target '{0}'".format(Config.target_name))
	target()


