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

from lib_raise_process import *
from lib_raise_fs import *

class AR(object):
	is_setup = False

	@classmethod
	def setup(cls):
		if cls.is_setup:
			return

		cls.is_setup = True


def ar_build_static_library(ar_file, o_files):
	# Make sure the extension is valid
	if not ar_file.endswith('.a'):
		print_exit("Out file extension should be '.a' not '.{0}'.".format(ar_file.split('.')[-1]))

	# Setup the messages
	task = 'Building'
	result = ar_file
	plural = 'static libraries'
	singular = 'static library'
	command = "ar rcs " + \
			ar_file + " " + \
			str.join(' ', o_files)

	def setup():
		# Skip if the files have not changed since last build
		if not is_outdated(to_update = [ar_file], triggers = o_files):
			return False
		return True

	# Create the event
	event = Event(task, result, plural, singular, command, setup)
	add_event(event)


AR.setup()

