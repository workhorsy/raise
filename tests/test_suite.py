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
import inspect
import threading
import time
import multiprocessing


class TestCase(object):
	def setUp(self):
		pass

	def init(self, test_dir):
		# Change to the test directory
		self.pwd = os.getcwd()
		os.chdir(test_dir)

	def tearDown(self):
		# Change back to the original directory
		os.chdir(self.pwd)

	def assertEqual(self, a, b):
		if a == b:
			return
		raise AssertionError("{0} != {1}".format(a, b))

	def assertNotDiff(self, expected, actual):
		if expected == actual:
			return

		diff_lines = difflib.ndiff(expected.splitlines(1), actual.splitlines(1))
		diff = '\n' + str.join('', diff_lines)
		raise AssertionError(diff)

	def assertProcessOutput(self, command, expected, is_success = True):
		process = TestProcessRunner(command)
		process.run()

		self.assertNotDiff(expected, process.stdall)
		self.assertEqual(process.is_success, is_success)

class TestThread(threading.Thread):
	def __init__(self, test_case, test_member):
		threading.Thread.__init__(self)
		self.test_case = test_case
		self.test_member = test_member

	def run(self):
		self.err = None
		try:
			self.test_case.setUp()
			self.test_member()
		except Exception as err:
			self.err = err
		finally:
			self.test_case.tearDown()

class ConcurrentTestRunner(object):
	def __init__(self):
		self.test_cases = []
		self.fails = []

	def add(self, test_case):
		self.test_cases.append(test_case)

	def run(self):
		# Get the number of CPU cores
		cpus_total = 1 #multiprocessing.cpu_count() # FIXME
		cpus_free = cpus_total
		ready_members = []

		# Get each test instance and method
		for test_case_cls in self.test_cases:
			test_case = test_case_cls()
			members = inspect.getmembers(test_case, predicate=inspect.ismethod)

			for name, member in members:
				if not name.startswith('test_'):
					continue

				pair = (test_case, member)
				ready_members.append(pair)

		# Run one thread per CPU core, until all the threads are done
		running_threads = []
		while True:
			while cpus_free and ready_members:
				test_case, member = ready_members.pop()

				t = TestThread(test_case, member)
				t.start()
				running_threads.append(t)
				cpus_free -= 1

			for t in running_threads[:]:
				#print(cpus_free, len(ready_members), len(running_threads))
				if t.isAlive():
					continue

				cpus_free += 1
				running_threads.remove(t)
				t.join()
				if t.err:
					self.fails.append(t.err)
					sys.stdout.write('F')
				else:
					sys.stdout.write('.')
				sys.stdout.flush()

			if not ready_members and not running_threads:
				break

			time.sleep(0.2)

		sys.stdout.write('\n')
		for fail in self.fails:
			print(fail)

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

	def get_stdall(self):
		return self._stdout + self._stderr
	stdall = property(get_stdall)



class TestC(TestCase):
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

class TestD(TestCase):
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

class TestCXX(TestCase):
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

class TestCSharp(TestCase):
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

class TestLibraries(TestCase):
	def setUp(self):
		self.init('Libraries')

	def test_find_installed_library(self):
		command = '{0} raise -plain find_installed_library'.format(sys.executable)

		expected = \
'''Running target 'find_installed_library'
Checking for shared library 'libSDL' ...                                    :)'''

		self.assertProcessOutput(command, expected)

	def test_find_missing_library(self):
		command = '{0} raise -plain find_missing_library'.format(sys.executable)

		expected = \
'''Running target 'find_missing_library'
Checking for shared library 'libDoesNotExist' ..............................:(
Shared library 'libDoesNotExist (Any version)' not installed. Install and try again. Exiting ...'''

		self.assertProcessOutput(command, expected, False)

	def test_find_installed_library_bad_version(self):
		command = '{0} raise -plain find_installed_library_bad_version'.format(sys.executable)

		expected = \
'''Running target 'find_installed_library_bad_version'
Checking for shared library 'libSDL' ......................................:(
Shared library 'libSDL (ver >= (99))' not installed. Install and try again. Exiting ...'''

		self.assertProcessOutput(command, expected, False)

if __name__ == '__main__':
	runner = ConcurrentTestRunner()
	for cls in TestCase.__subclasses__():
		runner.add(cls)
	runner.run()



