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
import atexit
import platform
import ast
import inspect
from collections import namedtuple
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
	black = {
		'AugAssign' : 'Operation with assignment', 
		'Assign' : 'Assignment', 
		'Lambda' : 'Lambda function', 
		'arguments' : 'Function argument', 
		'arg' : 'Argument', 
		'Param' : 'Function parameter', 
		'Call' : 'Function call', 
		'If' : 'If statement', 
		'While' : 'While loop', 
		'For' : 'For loop', 
		'Import' : 'Importing', 
		'ImportFrom' : 'Importing from', 
		'alias' : 'Aliase', 
		'ClassDef' : 'Class definition', 
		'Pass' : 'Pass statements', 
		'Assert' : 'Assert statement', 
		'Break' : 'Break statement', 
		'Continue' : 'Continue statement', 
		'Del' : 'Del statement', 
		'Delete' : 'Delete statement', 
		'ExceptHandler' : 'Exception handler', 
		'Raise' : 'Raise statement', 
		'Try' : 'Try block', 
		'TryExcept' : 'Try block', 
		'TryFinally' : 'Try finally block', 
		'Return' : 'Return statement', 
		'Yield' : 'Yield statement', 
		'With' : 'With statement', 
		'Global' : 'Global statement', 
		'Print' : 'Print statement', 
	}

	black_list = {}
	for k, v in black.items():
		if hasattr(ast, k):
			t = getattr(ast, k)
			black_list[t] = v

	# Make sure the code can be parsed
	tree = None
	parse_error = None
	try:
		tree = ast.parse(version_str)
	except SyntaxError as e:
		parse_error = str(e)
	if parse_error:
		Print.status('Building version string')
		Print.fail('Version string unparsable. "{0}", {1}'.format(version_str, parse_error))
		Print.exit('Fix version string and try again.')

	# Make sure each code node is not in the black list
	for node in ast.walk(tree):
		# Is in black list
		for k, v in black_list.items():
			if isinstance(node, k):
				Print.status('Building version string')
				Print.fail('{0} not allowed in version string. "{1}"'.format(v, version_str))
				Print.exit('Fix version string and try again.')

	code = "lambda ver: " + version_str
	version_cb = None
	# Make sure the code can be parsed into a lambda
	try:
		version_cb = eval(code, {})
		version_cb(version_string_to_tuple('(1, 9)'))
	except Exception as e:
		message = str(e).lstrip('global ')
		Print.status('Building version string')
		Print.fail('Invalid version string "{0}", {1}'.format(version_str, message))
		Print.exit('Fix version string and try again.')

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

def is_safe_code(source_code):
	safe_nodes = (
		ast.Module, ast.Load, ast.Expr, ast.Attribute, ast.Name, 
		ast.Str, ast.Num, ast.BoolOp, 
		ast.Dict, ast.List, ast.Tuple, 
		ast.Store, ast.ListComp, ast.comprehension, 
		ast.Subscript, ast.Slice, ast.Index, 
		ast.BinOp, ast.UnaryOp, 
		ast.BitOr, ast.BitXor, ast.BitAnd, 
		ast.LShift, ast.RShift, 
		ast.Sub, ast.Add, ast.Div, ast.Mult, ast.Mod, ast.Pow, 
		ast.Eq, ast.NotEq, ast.And, ast.Or, ast.Not, 
		ast.Is, ast.IsNot, ast.In, ast.NotIn, 
		ast.Compare, ast.Gt, ast.GtE, ast.Lt, ast.LtE
	)

	# Make sure the code can be parsed
	tree = None
	try:
		tree = ast.parse(source_code)
	except SyntaxError:
		return False

	# Make sure each code node is in the white list
	for node in ast.walk(tree):
		if not isinstance(node, safe_nodes):
			print(type(node))
			return False

	return True

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




