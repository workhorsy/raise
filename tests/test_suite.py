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
import subprocess
import difflib
import unittest

class TestProcessRunner(object):
	def __init__(self, command):
		self._command = command
		self._process = None
		self._return_code = None
		self._stdout = None
		self._stderr = None

	def run(self):
		# Start the process and save the output
		self._process = subprocess.Popen(
			self._command, 
			stderr = subprocess.PIPE, 
			stdout = subprocess.PIPE, 
			shell = True
		)

		# Wait for the process to exit
		self._process.wait()

		# Get the return code
		rc = self._process.returncode
		if os.WIFEXITED(rc):
			rc = os.WEXITSTATUS(rc)
		self._return_code = rc

		# Get the standard out and error text
		self._stderr  = self._process.stderr.read().rstrip()
		self._stdout = self._process.stdout.read().rstrip()
		try:
			self._stderr = str(self._stderr, 'UTF-8')
		except Exception as err:
			pass
		try:
			self._stdout = str(self._stdout, 'UTF-8')
		except Exception as err:
			pass

	def get_is_success(self):
		return self._return_code == 0
	is_success = property(get_is_success)

	def get_is_failure(self):
		return self._return_code != 0
	is_failure = property(get_is_failure)

	def get_stderr(self):
		return self._stderr
	stderr = property(get_stderr)

	def get_stdout(self):
		return self._stdout
	stdout = property(get_stdout)

class TestRaise(unittest.TestCase):
	def init(self, test_dir):
		# Change to the test directory
		self.pwd = os.getcwd()
		os.chdir(test_dir)

	def tearDown(self):
		# Change back to the original directory
		os.chdir(self.pwd)

	def assertNotDiff(self, expected, actual):
		if expected == actual:
			return

		diff_lines = difflib.ndiff(expected.splitlines(1), actual.splitlines(1))
		diff = '\n' + str.join('', diff_lines)
		raise AssertionError(diff)

	def assertProcessOutput(self, command, expected):
		process = TestProcessRunner(command)
		process.run()

		self.assertNotDiff(expected, process.stdout)
		self.assertTrue(process.is_success)

class TestC(TestRaise):
	def setUp(self):
		self.init('C')

	def test_build_object(self):
		command = '{0} raise -plain build_object'.format(sys.executable)

		expected = \
'''Running target 'build_object'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building C object 'lib_math.o' ...                                          :)
Building C object 'main.o' ...                                              :)
Building C program 'main.exe' ...                                           :)
Running C program ...                                                       :)
./main.exe
7 * 12 = 84'''

		self.assertProcessOutput(command, expected)

	def test_build_program(self):
		command = '{0} raise -plain build_program'.format(sys.executable)

		expected = \
'''Running target 'build_program'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building C program 'main.exe' ...                                           :)
Running C program ...                                                       :)
./main.exe
7 * 12 = 84'''

		self.assertProcessOutput(command, expected)

	def test_build_shared_library(self):
		command = '{0} raise -plain build_shared_library'.format(sys.executable)

		expected = \
'''Running target 'build_shared_library'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building C object 'lib_math.o' ...                                          :)
Building shared library 'lib_math.so' ...                                   :)
Building C program 'main.exe' ...                                           :)
Running C program ...                                                       :)
./main.exe
7 * 12 = 84'''

		self.assertProcessOutput(command, expected)

	def test_build_static_library(self):
		command = '{0} raise -plain build_static_library'.format(sys.executable)

		expected = \
'''Running target 'build_static_library'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building C object 'lib_math.o' ...                                          :)
Building static library 'lib_math.a' ...                                    :)
Building C program 'main.exe' ...                                           :)
Running C program ...                                                       :)
./main.exe
7 * 12 = 84'''

		self.assertProcessOutput(command, expected)

class TestD(TestRaise):
	def setUp(self):
		self.init('D')

	def test_build_program(self):
		command = '{0} raise -plain build_program'.format(sys.executable)

		expected = \
'''Running target 'build_program'
Removing the file 'lib_math.di' ...                                         :)
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building D program 'main.exe' ...                                           :)
Running D program ...                                                       :)
./main.exe
9 * 12 = 108'''

		self.assertProcessOutput(command, expected)

	def test_build_object(self):
		command = '{0} raise -plain build_object'.format(sys.executable)

		expected = \
'''Running target 'build_object'
Removing the file 'lib_math.di' ...                                         :)
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building D object 'lib_math.o' ...                                          :)
Building D object 'main.o' ...                                              :)
Building D program 'main.exe' ...                                           :)
Running D program ...                                                       :)
./main.exe
9 * 12 = 108'''

		self.assertProcessOutput(command, expected)

	def test_build_static_library(self):
		command = '{0} raise -plain build_static_library'.format(sys.executable)

		expected = \
'''Running target 'build_static_library'
Removing the file 'lib_math.di' ...                                         :)
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building D object 'lib_math.o' ...                                          :)
Building D static library 'lib_math.a' ...                                  :)
Building D program 'main.exe' ...                                           :)
Running D program ...                                                       :)
./main.exe
9 * 12 = 108'''

		self.assertProcessOutput(command, expected)

	def test_build_interface(self):
		command = '{0} raise -plain build_interface'.format(sys.executable)

		expected = \
'''Running target 'build_interface'
Removing the file 'lib_math.di' ...                                         :)
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building D interface 'lib_math.di' ...                                      :)'''

		self.assertProcessOutput(command, expected)

class TestCXX(TestRaise):
	def setUp(self):
		self.init('CXX')

	def test_build_program(self):
		command = '{0} raise -plain build_program'.format(sys.executable)

		expected = \
'''Running target 'build_program'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building C++ program 'main.exe' ...                                         :)
Running C++ program ...                                                     :)
./main.exe
7 + 9 = 16'''

		self.assertProcessOutput(command, expected)

	def test_build_object(self):
		command = '{0} raise -plain build_object'.format(sys.executable)

		expected = \
'''Running target 'build_object'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building C++ object 'lib_math.o' ...                                        :)
Building C++ object 'main.o' ...                                            :)
Building C++ program 'main.exe' ...                                         :)
Running C++ program ...                                                     :)
./main.exe
7 + 9 = 16'''

		self.assertProcessOutput(command, expected)

	def test_build_shared_library(self):
		command = '{0} raise -plain build_shared_library'.format(sys.executable)

		expected = \
'''Running target 'build_shared_library'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building C++ object 'lib_math.o' ...                                        :)
Building shared library 'lib_math.so' ...                                   :)
Building C++ program 'main.exe' ...                                         :)
Running C++ program ...                                                     :)
./main.exe
7 + 9 = 16'''

		self.assertProcessOutput(command, expected)

	def test_build_static_library(self):
		command = '{0} raise -plain build_static_library'.format(sys.executable)

		expected = \
'''Running target 'build_static_library'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building C++ object 'lib_math.o' ...                                        :)
Building static library 'lib_math.a' ...                                    :)
Building C++ program 'main.exe' ...                                         :)
Running C++ program ...                                                     :)
./main.exe
7 + 9 = 16'''

		self.assertProcessOutput(command, expected)

class TestCSharp(TestRaise):
	def setUp(self):
		self.init('CSharp')

	def test_build_program(self):
		command = '{0} raise -plain build_program'.format(sys.executable)

		expected = \
'''Running target 'build_program'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building C# program 'main.exe' ...                                          :)
Running C# program ...                                                      :)
main.exe
10 - 4 = 6'''

		self.assertProcessOutput(command, expected)

	def test_build_shared_library(self):
		command = '{0} raise -plain build_shared_library'.format(sys.executable)

		expected = \
'''Running target 'build_shared_library'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building C# shared library 'lib_math.dll' ...                               :)
Building C# program 'main.exe' ...                                          :)
Running C# program ...                                                      :)
main.exe
10 - 4 = 6'''

		self.assertProcessOutput(command, expected)

class TestLibraries(TestRaise):
	def setUp(self):
		self.init('Libraries')

	def test_find_installed_library(self):
		command = '{0} raise -plain find_installed_library'.format(sys.executable)

		expected = \
'''Running target 'find_installed_library'
Removing binaries 'main' ...                                                :)
Checking for shared library 'libSDL' ...                                    :)'''

		self.assertProcessOutput(command, expected)

	def test_find_missing_library(self):
		command = '{0} raise -plain find_missing_library'.format(sys.executable)

		expected = \
'''Running target 'find_missing_library'
Checking for shared library 'libDoesNotExist' ..............................:(
Shared library 'libDoesNotExist (Any version)' not installed. Install and try 
again. Exiting ...
'''

		self.assertProcessOutput(command, expected)

	def test_find_installed_library_bad_version(self):
		command = '{0} raise -plain find_installed_library_bad_version'.format(sys.executable)

		expected = \
'''Running target 'find_installed_library_bad_version'
Checking for shared library 'libSDL' ......................................:(
Shared library 'libSDL (ver >= (99))' not installed. Install and try again. E
xiting ...
'''

		self.assertProcessOutput(command, expected)

if __name__ == '__main__':
	unittest.main()



