#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# This file is part of Raise.
# Raise is a small build automation tool that ships with your software.
# Raise uses a MIT style license, and is hosted at https://github.com/workhorsy/raise .
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
import atexit
import platform
import inspect
import lib_raise_config as Config
import lib_raise_terminal as Print



def chomp(s):
	for sep in ['\r\n', '\n', '\r']:
		if s.endswith(sep):
			return s[:-len(sep)]

	return s

def before(s, n):
	i = s.find(n)
	if i == -1:
		return s
	else:
		return s[0 : i]

def before_last(s, n):
	i = s.rfind(n)
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

def between_last(s, l, r):
	return before_last(after(s, l), r)

def require_file_extension(file_name, *required_extensions):
	extension = os.path.splitext(file_name)[-1].lower()
	if not extension in required_extensions:
		Print.exit("File extension should be '{0}' on '{1}'.".format(str.join(', ', required_extensions), file_name))

def call_on_exit(cb):
	# Set a cleanup function to run on exit
	if cb:
		atexit.register(cb)

def expand_envs(string):
	while True:
		before = string
		string = os.path.expandvars(string)
		if before == string:
			return string

def get_rscript_line():
	frame = inspect.currentframe()
	info, file, line = None, None, None
	while frame:
		info = inspect.getframeinfo(frame)
		file = os.path.abspath(info[0])
		line = info[1]
		frame = frame.f_back
		#print(file, line)
		if file.endswith('rscript'):
			return '{0} Ln {1}'.format(file, line)

	return '?'




