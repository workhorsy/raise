#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# This file is part of Raise.
# Raise is a small build automation tool that ships with your software.
# Raise uses a MIT style license, and is hosted at http://launchpad.net/raise .
# Copyright (c) 2014, Matthew Brennan Jones <mattjones@workhorsy.org>
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
import ast
from collections import namedtuple
import lib_raise_config as Config
import lib_raise_terminal as Print



os_type = None


def setup():
	global os_type

	# Figure out the general OS type
	if 'cygwin' in platform.system().lower():
		os_type = OSType(
			name =                 'Cygwin'
		)
	elif 'windows' in platform.system().lower():
		os_type = OSType(
			name =                 'Windows'
		)
	else:
		os_type = OSType(
			name =                 'Unix'
		)

	# Make sure Windows SDK tools are found
	if os_type._name == 'Windows':
		if not 'WINDOWSSDKDIR' in os.environ and not 'WINDOWSSDKVERSIONOVERRIDE' in os.environ:
			Config.early_exit('Windows SDK not found. Must be run from Windows SDK Command Prompt.')


class OSType(object):
	def __init__(self, name):

		self._name = name

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

def to_version_cb(version_str):
	code = "lambda ver: " + version_str
	try:
		version_cb = eval(code, {})
	except:
		Print.exit('\nInvalid version string:\n"{0}"'.format(version_str))
	return version_cb

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

def is_code_safe(source_code):
	safe_nodes = (
		ast.Module, ast.Load, ast.Expr, ast.Attribute, ast.Name, 
		ast.Lambda, ast.arguments, ast.Param, 
		ast.Str, ast.Num, ast.BoolOp, 
		ast.Dict, ast.List, ast.Tuple, 
		ast.Subscript, ast.Slice, 
		ast.BinOp, ast.UnaryOp, 
		ast.BitOr, ast.BitXor, ast.BitAnd, 
		ast.LShift, ast.RShift, 
		ast.Sub, ast.Add, ast.Div, ast.Mult, ast.Mod, 
		ast.Eq, ast.NotEq, ast.And, ast.Or, ast.Not, 
		ast.Is, ast.IsNot, ast.In, ast.NotIn, 
		ast.Compare, ast.Gt, ast.GtE, ast.Lt, ast.LtE
	)

	# Make sure the code can be parsed
	tree = None
	try:
		tree = ast.parse(source_code)
	except SyntaxError:
		raise False

	# Make sure each code node is in the white list
	for node in ast.walk(tree):
		if not isinstance(node, safe_nodes):
			print(type(node))
			return False

	return True


setup()



