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


import os
import re
import lib_raise_config as Config
import lib_raise_terminal as Print
import lib_raise_process as Process
import lib_raise_helpers as Helpers
import lib_raise_terminal as Terminal

import findlib
import findlib_server
from osinfo import *

def program_paths(*program_names):
	return findlib.program_paths(*program_names)

def get_header_file(header_name, version_str = None):
	return findlib.get_header_file(header_name, version_str)

def get_static_library(lib_name, version_str = None):
	return findlib.get_static_library(lib_name, version_str)

def get_shared_library(lib_name, version_str = None):
	return findlib.get_shared_library(lib_name, version_str)

def require_header_file(header_name, version_str = None):
	Print.status("Checking for header file '{0}'".format(header_name))

	# If the header is not installed, make them install it to continue
	if not findlib.get_header_file(header_name, version_str):
		ver = "(Any version)"
		if version_str:
			ver = version_str

		message = "Header file '{0} {1}' not installed. Install and try again."
		Print.fail()
		Print.exit(message.format(header_name, ver))
	else:
		Print.ok()

def require_static_library(lib_name, version_str = None):
	Print.status("Checking for static library '{0}'".format(lib_name))

	# If the static library is not installed, make them install it to continue
	if not findlib.get_static_library(lib_name, version_str):
		# Get the version requirement lambda as a printable string
		ver = "(Any version)"
		if version_str:
			ver = version_str

		message = "Static library '{0} {1}' not installed. Install and try again."
		Print.fail()
		Print.exit(message.format(lib_name, ver))
	else:
		Print.ok()

def require_shared_library(lib_name, version_str = None):
	Print.status("Checking for shared library '{0}'".format(lib_name))

	# If the shared library is not installed, make them install it to continue
	if not findlib.get_shared_library(lib_name, version_str):
		# Get the version requirement lambda as a printable string
		ver = "(Any version)"
		if version_str:
			ver = version_str

		message = "Shared library '{0} {1}' not installed. Install and try again."
		Print.fail()
		Print.exit(message.format(lib_name, ver))
	else:
		Print.ok()

def require_static_or_shared_library(lib_name, version_str = None):
	Print.status("Checking for static/shared library '{0}'".format(lib_name))

	shared_file = get_shared_library(lib_name, version_str)
	static_file = get_shared_library(lib_name, version_str)

	# Make them install the lib if neither was found
	if not shared_file and not static_file:
		# Get the version requirement lambda as a printable string
		ver = "(Any version)"
		if version_str:
			ver = version_str

		message = "Shared/Static library '{0} {1}' not installed. Install and try again."
		Print.fail()
		Print.exit(message.format(lib_name, ver))
	else:
		Print.ok()

def require_programs(prog_names):
	for prog_name in prog_names:
		Print.status("Checking for program '{0}'".format(prog_name))
		if len(findlib.program_paths(prog_name)):
			Print.ok()
		else:
			Print.fail()
			Print.exit("Install the program '{0}' and try again.".format(prog_name))

def require_environmental_variable(env_name, version_cb = None):
	Print.status("Checking for environmental variable '{0}'".format(env_name))

	if not os.environ.get(env_name):
		message = "The environmental variable '{0}' was not found. Set it and try again."
		Print.fail()
		Print.exit(message.format(env_name))
	else:
		Print.ok()


def _on_ok():
	Terminal.ok()
findlib._on_ok = _on_ok

def _on_warn(message=None):
	Terminal.warning(message)
findlib._on_warn = _on_warn

def _on_fail(message=None):
	Terminal.fail(message)
findlib._on_fail = _on_fail

def _on_exit(message):
	Terminal.exit(message)
findlib._on_exit = _on_exit

def _on_status(message):
	Terminal.status(message)
findlib._on_status = _on_status

def _ok_symbol():
	return Terminal.Emoticons.SMILE
findlib._ok_symbol = _ok_symbol

def _warn_symbol():
	return Terminal.Emoticons.NORMAL
findlib._warn_symbol = _warn_symbol

def _fail_symbol():
	return Terminal.Emoticons.FROWN
findlib._fail_symbol = _fail_symbol




