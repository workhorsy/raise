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
import osinfo
import lib_raise_terminal as Print


os_type = None
target_name = None
pwd = os.sys.path[0]
python = sys.executable
is_plain = False
is_inspect = False
is_nolineno = False
arg = []


def setup():
	global os_type

	# Figure out the general OS type
	os_type, os_brand, os_release = osinfo.get_os_info()


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


setup()



