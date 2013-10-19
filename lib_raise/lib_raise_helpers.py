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

import os
from collections import namedtuple

class Helpers(object):
	is_setup = False

	@classmethod
	def setup(cls):
		if cls.is_setup:
			return

		cls.is_setup = True


def before(s, n):
	i = s.find(n)
	if i == -1:
		return s
	else:
		return s[0 : i]

def after(s, n):
	i = s.find(n)
	if i == -1:
		return s
	else:
		return s[i+len(n) : ]

def between(s, l, r):
	return before(after(s, l), r)

def version_string_to_tuple(version_string):
	# Get the version number
	Version = namedtuple('Version', 'major minor micro')
	major, minor, micro = 0, 0, 0
	try:
		version = version_string.split('.')
		major = int(version[0])
		minor = int(version[1])
		micro = int(version[2])
	except Exception as e:
		pass
	return Version(major, minor, micro)

def require_file_extension(file_name, required_extension):
	extension = os.path.splitext(file_name)[-1].lower()
	if extension != required_extension:
		print_exit("File extension should be '{0}' on '{1}'.".format(required_extension, file_name))


Helpers.setup()
