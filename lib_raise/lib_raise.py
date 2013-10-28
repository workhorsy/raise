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
import signal


# Make sure we are in at least python 2.6
if sys.version_info < (2, 6):
	print("Python 2.6 or greater is required. Exiting ...")
	sys.exit(1)

# Load the default modules
import lib_raise_config as Config
import lib_raise_helpers as Helpers
import lib_raise_cpu as CPU
import lib_raise_os as OS
import lib_raise_terminal as Print
import lib_raise_fs as FS
import lib_raise_process as Process
import lib_raise_libraries as Libraries


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
		Print.exit('Exit called by the keyboard.')
		sys.exit(1)
	signal.signal(signal.SIGINT, signal_handler)

	# Set the terminal to plain or fancy
	if Config.is_plain:
		Print.set_plain()
	else:
		Print.set_fancy()

	# Clear the terminal if desired
	if Print.clear:
		os.system(Print.clear)

	# Get the target function name
	Config.target_name = str(str.join(' ', args))

	# Load the rscript
	targets = Config.import_rscript(globals(), locals())

	# Get a friendly list of all the targets
	target_list = []
	if targets:
		keys = list(targets.keys())
		keys.sort()
		target_list = "'" + str.join("', '", keys) + "'"

	# Exit if there is no target
	if not Config.target_name:
		print("Raise build automation tool (Version 0.3.0 - October 27 2013) http://launchpad.net/raise")
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
			Print.exit("No target specified. Found targets are {0}.".format(target_list))

	if not targets:
		Print.exit("No 'rscript' file found.")

	# Exit if there is no target with that name
	if not Config.target_name in targets:
		Print.exit("No target named '{0}'. Found targets are {1}.".format(Config.target_name, target_list))

	# Try running the target in the rscript
	target = targets[Config.target_name]
	Print.info("Running target '{0}'".format(Config.target_name))
	target()



