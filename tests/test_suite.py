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

import os, sys
import subprocess
import difflib
import inspect
import time
import multiprocessing
import shutil


def program_paths(program_name):
	paths = []
	exts = filter(None, os.environ.get('PATHEXT', '').split(os.pathsep))
	path = os.environ['PATH']
	for p in os.environ['PATH'].split(os.pathsep):
		p = os.path.join(p, program_name)
		# Save the path if it is executable
		if os.access(p, os.X_OK) and not os.path.isdir(p):
			paths.append(p)
		# Save the path if we found one with a common extension like .exe
		for e in exts:
			pext = p + e
			if os.access(pext, os.X_OK) and not os.path.isdir(pext):
				paths.append(pext)
	return paths

def chomp(s):
	for sep in ['\r\n', '\n', '\r']:
		if s.endswith(sep):
			return s[:-len(sep)]

	return s

class TestCase(object):
	@classmethod
	def has_prerequisites(cls):
		raise NotImplementedError("The has_prerequisites class method should be overridden on any child classes.")

	def set_up(self, id):
		pass

	def init(self, test_dir, id):
		self.id = id

		# Change to the test directory
		self.pwd = os.getcwd()
		self.build_dir = 'build_{0}'.format(self.id)
		shutil.copytree(test_dir, self.build_dir)
		os.chdir(self.build_dir)

	def tear_down(self):
		# Change back to the original directory
		os.chdir(self.pwd)
		shutil.rmtree(self.build_dir)

	def assert_not_diff(self, expected, actual):
		if expected == actual:
			return

		diff_lines = difflib.ndiff(expected.splitlines(1), actual.splitlines(1))
		diff = '\n' + str.join('', diff_lines)
		raise AssertionError(diff)

	def assert_process_output(self, command, expected, is_success = True):
		# Run the process and wait for it to complete
		process = TestProcessRunner(command)
		process.run()

		# Convert the line endings to the native style
		actual = process.stdall.replace(os.linesep, '\n')

		# Make sure the text returned is as expected
		self.assert_not_diff(expected, actual)

		# Make sure the return code is as expected
		if process.is_success == is_success:
			return

		if is_success:
			raise AssertionError("Process return code expected to be 0 but was {0}.".format(process._return_code))
		else:
			raise AssertionError("Process return code expected to NOT be 0 but was {0}.".format(process._return_code))


def test_runner(conn, test_case, member, id):
	try:
		test_case.set_up(id)
		member()
		conn.send('ok')
	except Exception as err:
		conn.send(str(err))
	finally:
		conn.close()
		test_case.tear_down()


class ConcurrentTestRunner(object):
	def __init__(self):
		self.test_cases = []
		self.fails = []
		self.next_id = 0

	def add_test_case(self, test_case):
		self.test_cases.append(test_case)

	def run(self):
		# Get the number of CPU cores
		cpus_total = multiprocessing.cpu_count()
		cpus_free = cpus_total
		ready_members = []
		total = 0
		successful = 0

		# Get each test instance and method
		for test_case_cls in self.test_cases:
			# Skip this test suite if it does not have the prerequisites
			if not test_case_cls.has_prerequisites():
				print('Skipping test suite "{0}"'.format(test_case_cls.__name__))
				continue

			# Find all the tests in the suite
			test_case = test_case_cls()
			members = inspect.getmembers(test_case, predicate=inspect.ismethod)

			for name, member in members:
				if not name.startswith('test_'):
					continue

				data = (test_case, member, test_case_cls.__name__ + '.' + name)
				ready_members.append(data)
				total += 1

		# Run one process per CPU core, until all the processes are done
		running_processes = {}
		while True:
			# Start the next processes
			while cpus_free and ready_members:
				test_case, member, name = ready_members.pop()

				self.next_id += 1
				parent_conn, child_conn = multiprocessing.Pipe()
				args = (child_conn, test_case, member, self.next_id)
				process = multiprocessing.Process(target=test_runner, args=args)
				process.start()
				process.test_function_name = name
				running_processes[process] = parent_conn
				cpus_free -= 1

			# Check all the running processes and stop any that are done
			for process in list(running_processes.keys()):
				#print(cpus_free, len(ready_members), len(running_processes))
				if process.is_alive():
					continue

				cpus_free += 1
				parent_conn = running_processes[process]
				process.join()
				message = parent_conn.recv()
				if message == 'ok':
					successful += 1
					sys.stdout.write('.')
				else:
					self.fails.append(process.test_function_name + '\n' + message)
					sys.stdout.write('F')
				sys.stdout.flush()

				del running_processes[process]

			# Break if there are no more processes
			if not ready_members and not running_processes:
				break

			# Sleep for a bit if there are more processes to run
			time.sleep(0.2)

		# Print the results
		print('')
		for fail in self.fails:
			print(fail)
		print('Unit Test Results:')
		print('{0} total, {1} successful, {2} failed'.format(total, successful, len(self.fails)))


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

		self._stdout = b''
		self._stderr = b''

		while True:
			sout, serr = self._process.communicate()
			self._stdout += sout
			self._stderr += serr

			self._process.poll()
			if self._process.returncode != None:
				break

			time.sleep(0.2)

		# Wait for the process to exit
		self._process.wait()

		# Get the return code
		rc = self._process.returncode
		if hasattr(os, 'WIFEXITED') and os.WIFEXITED(rc):
			rc = os.WEXITSTATUS(rc)
		self._return_code = rc

		# Get the standard out and error text
		try:
			self._stderr = str(self._stderr, 'UTF-8')
		except Exception as err:
			pass
		try:
			self._stdout = str(self._stdout, 'UTF-8')
		except Exception as err:
			pass

		# Chomp the terminating newline off the ends of output
		self._stdout = chomp(self._stdout)
		self._stderr = chomp(self._stderr)

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


class TestBasics(TestCase):
	@classmethod
	def has_prerequisites(cls):
		return True

	def set_up(self, id):
		self.init('Basics', id)

	def test_nothing(self):
		command = '{0} raise -plain simple_nothing'.format(sys.executable)

		expected = \
"Running target 'simple_nothing'"

		self.assert_process_output(command, expected)

	def test_status(self):
		command = '{0} raise -plain simple_status'.format(sys.executable)

		expected = \
'''Running target 'simple_status'
Simple status ...'''

		self.assert_process_output(command, expected)

	def test_ok(self):
		command = '{0} raise -plain simple_ok'.format(sys.executable)

		expected = \
'''Running target 'simple_ok'
Simple ok ...                                                               :)'''

		self.assert_process_output(command, expected)

	def test_fail(self):
		command = '{0} raise -plain simple_fail'.format(sys.executable)

		expected = \
'''Running target 'simple_fail'
Simple fail ................................................................:('''

		self.assert_process_output(command, expected)

	def test_warning(self):
		command = '{0} raise -plain simple_warning'.format(sys.executable)

		expected = \
'''Running target 'simple_warning'
Simple warning .............................................................:\\'''

		self.assert_process_output(command, expected)

	def test_require_program(self):
		command = '{0} raise -plain simple_require_program'.format(sys.executable)

		expected = \
'''Running target 'simple_require_program'
Checking for program 'python' ...                                           :)'''

		self.assert_process_output(command, expected)

	def test_require_program_failure(self):
		command = '{0} raise -plain simple_require_program_failure'.format(sys.executable)

		expected = \
'''Running target 'simple_require_program_failure'
Checking for program 'no_such_program' .....................................:(
Install the program 'no_such_program' and try again. Exiting ...'''

		self.assert_process_output(command, expected, is_success = False)

	def test_require_not_root(self):
		command = '{0} raise -plain simple_require_not_root'.format(sys.executable)

		expected = \
"Running target 'simple_require_not_root'"

		self.assert_process_output(command, expected)

	def test_require_root_failure(self):
		command = '{0} raise -plain simple_require_root_failure'.format(sys.executable)

		expected = \
'''Running target 'simple_require_root_failure'
Must be run as root. Exiting ...'''

		self.assert_process_output(command, expected, is_success = False)


class TestC(TestCase):
	@classmethod
	def has_prerequisites(cls):
		for prog in ['gcc', 'clang', 'cl.exe']:
			if program_paths(prog):
				return True

		return False

	def set_up(self, id):
		self.init('C', id)

	def test_setup_failure(self):
		command = '{0} raise -plain setup_failure'.format(sys.executable)

		expected = \
'''Running target 'setup_failure'
Setting up C module ........................................................:(
No C compiler found. Install one and try again. Exiting ...'''

		self.assert_process_output(command, expected, is_success = False)

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

		self.assert_process_output(command, expected)

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

		self.assert_process_output(command, expected)

	def test_build_shared_library(self):
		command = '{0} raise -plain build_shared_library'.format(sys.executable)

		expected = \
'''Running target 'build_shared_library'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building C object 'lib_math.o' ...                                          :)
Building C shared library 'lib_math.so' ...                                 :)
Building C program 'main.exe' ...                                           :)
Running C program ...                                                       :)
./main.exe
7 * 12 = 84'''

		self.assert_process_output(command, expected)

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

		self.assert_process_output(command, expected)


class TestD(TestCase):
	@classmethod
	def has_prerequisites(cls):
		for prog in ['dmd', 'dmd2', 'ldc2']:
			if program_paths(prog):
				return True

		return False

	def set_up(self, id):
		self.init('D', id)

	def test_setup_failure(self):
		command = '{0} raise -plain setup_failure'.format(sys.executable)

		expected = \
'''Running target 'setup_failure'
Setting up D module ........................................................:(
No D compiler found. Install one and try again. Exiting ...'''

		self.assert_process_output(command, expected, is_success = False)

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

		self.assert_process_output(command, expected)

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

		self.assert_process_output(command, expected)

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

		self.assert_process_output(command, expected)

	def test_build_interface(self):
		command = '{0} raise -plain build_interface'.format(sys.executable)

		expected = \
'''Running target 'build_interface'
Removing the file 'lib_math.di' ...                                         :)
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building D interface 'lib_math.di' ...                                      :)'''

		self.assert_process_output(command, expected)


class TestCXX(TestCase):
	@classmethod
	def has_prerequisites(cls):
		for prog in ['g++', 'cl.exe']:
			if program_paths(prog):
				return True

		return False

	def set_up(self, id):
		self.init('CXX', id)

	def test_setup_failure(self):
		command = '{0} raise -plain setup_failure'.format(sys.executable)

		expected = \
'''Running target 'setup_failure'
Setting up C++ module ......................................................:(
No C++ compiler found. Install one and try again. Exiting ...'''

		self.assert_process_output(command, expected, is_success = False)

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

		self.assert_process_output(command, expected)

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

		self.assert_process_output(command, expected)

	def test_build_shared_library(self):
		command = '{0} raise -plain build_shared_library'.format(sys.executable)

		expected = \
'''Running target 'build_shared_library'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building C++ object 'lib_math.o' ...                                        :)
Building C++ shared library 'lib_math.so' ...                               :)
Building C++ program 'main.exe' ...                                         :)
Running C++ program ...                                                     :)
./main.exe
7 + 9 = 16'''

		self.assert_process_output(command, expected)

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

		self.assert_process_output(command, expected)


class TestCSharp(TestCase):
	@classmethod
	def has_prerequisites(cls):
		for prog in ['dmcs', 'csc']:
			if program_paths(prog):
				return True

		return False

	def set_up(self, id):
		self.init('CSharp', id)

	def test_setup_failure(self):
		command = '{0} raise -plain setup_failure'.format(sys.executable)

		expected = \
'''Running target 'setup_failure'
Setting up C# module .......................................................:(
No C# compiler found. Install one and try again. Exiting ...'''

		self.assert_process_output(command, expected, is_success = False)

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

		self.assert_process_output(command, expected)

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

		self.assert_process_output(command, expected)


class TestJava(TestCase):
	@classmethod
	def has_prerequisites(cls):
		for prog in ['javac']:
			if program_paths(prog):
				return True

		return False

	def set_up(self, id):
		self.init('Java', id)

	def test_setup_failure(self):
		command = '{0} raise -plain setup_failure'.format(sys.executable)

		expected = \
'''Running target 'setup_failure'
Setting up Java module .....................................................:(
No Java compiler found. Install one and try again. Exiting ...'''

		self.assert_process_output(command, expected, is_success = False)

	def test_build_program(self):
		command = '{0} raise -plain build_program'.format(sys.executable)

		expected = \
'''Running target 'build_program'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building Java program 'main.class' ...                                      :)
Running Java program ...                                                    :)
java main
8 - 1 = 7'''

		self.assert_process_output(command, expected)

	def test_build_shared_library(self):
		command = '{0} raise -plain build_jar'.format(sys.executable)

		expected = \
'''Running target 'build_jar'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building Java jar 'lib_math.jar' ...                                        :)
Building Java program 'main.class' ...                                      :)
Running Java program ...                                                    :)
java main
8 - 1 = 7'''

		self.assert_process_output(command, expected)


class TestFind(TestCase):
	@classmethod
	def has_prerequisites(cls):
		return True

	def set_up(self, id):
		self.init('Find', id)

	def test_find_unparsable_version_code(self):
		command = '{0} raise -plain find_unparsable_version_code'.format(sys.executable)

		expected = \
'''Running target 'find_unparsable_version_code'
Building version string ....................................................:(
Version string unparsable. "@", invalid syntax (<unknown>, line 1)
Fix version string and try again. Exiting ...'''

		self.assert_process_output(command, expected, False)

	def test_find_black_listed_version_code(self):
		command = '{0} raise -plain find_black_listed_version_code'.format(sys.executable)

		expected = \
'''Running target 'find_black_listed_version_code'
Building version string ....................................................:(
Function call not allowed in version string. "eval("False")"
Fix version string and try again. Exiting ...'''

		self.assert_process_output(command, expected, False)

	def test_find_black_listed_version_code(self):
		command = '{0} raise -plain find_invalid_version_code'.format(sys.executable)

		expected = \
'''Running target 'find_invalid_version_code'
Building version string ....................................................:(
Invalid version string "a >= (1, 2)", global name 'a' is not defined
Fix version string and try again. Exiting ...'''

		self.assert_process_output(command, expected, False)



	def test_find_installed_shared_library(self):
		command = '{0} raise -plain find_installed_shared_library'.format(sys.executable)

		expected = \
'''Running target 'find_installed_shared_library'
Checking for shared library 'SDL' ...                                       :)
Checking for shared library 'sdl' ...                                       :)
Checking for shared library 'libSDL' ...                                    :)
Checking for shared library 'libsdl' ...                                    :)
Checking for shared library 'SDL' ...                                       :)
Checking for shared library 'sdl' ...                                       :)
Checking for shared library 'libSDL' ...                                    :)
Checking for shared library 'libsdl' ...                                    :)'''

		self.assert_process_output(command, expected)

	def test_find_missing_shared_library(self):
		command = '{0} raise -plain find_missing_shared_library'.format(sys.executable)

		expected = \
'''Running target 'find_missing_shared_library'
Checking for shared library 'libDoesNotExist' ..............................:(
Shared library 'libDoesNotExist (Any version)' not installed. Install and try again. Exiting ...'''

		self.assert_process_output(command, expected, False)

	def test_find_installed_shared_library_bad_version(self):
		command = '{0} raise -plain find_installed_shared_library_bad_version'.format(sys.executable)

		expected = \
'''Running target 'find_installed_shared_library_bad_version'
Checking for shared library 'libSDL' .......................................:(
Shared library 'libSDL ver >= (99, 0)' not installed. Install and try again. Exiting ...'''

		self.assert_process_output(command, expected, False)

	def test_find_installed_shared_library_cache(self):
		command = '{0} raise -plain find_installed_shared_library_cache'.format(sys.executable)

		expected = \
'''Running target 'find_installed_shared_library_cache'
Checking for shared library 'libSDL' ...                                    :)
Checking for shared library 'libSDL' .......................................:(
Shared library 'libSDL ver >= (99, 0)' not installed. Install and try again. Exiting ...'''

		self.assert_process_output(command, expected, False)

	def test_find_installed_static_library(self):
		command = '{0} raise -plain find_installed_static_library'.format(sys.executable)

		expected = \
'''Running target 'find_installed_static_library'
Checking for static library 'SDL' ...                                       :)
Checking for static library 'sdl' ...                                       :)
Checking for static library 'libSDL' ...                                    :)
Checking for static library 'libsdl' ...                                    :)
Checking for static library 'SDL' ...                                       :)
Checking for static library 'sdl' ...                                       :)
Checking for static library 'libSDL' ...                                    :)
Checking for static library 'libsdl' ...                                    :)'''

		self.assert_process_output(command, expected)

	def test_find_missing_static_library(self):
		command = '{0} raise -plain find_missing_static_library'.format(sys.executable)

		expected = \
'''Running target 'find_missing_static_library'
Checking for static library 'libDoesNotExist' ..............................:(
Static library 'libDoesNotExist (Any version)' not installed. Install and try again. Exiting ...'''

		self.assert_process_output(command, expected, False)

	def test_find_installed_static_library_bad_version(self):
		command = '{0} raise -plain find_installed_static_library_bad_version'.format(sys.executable)

		expected = \
'''Running target 'find_installed_static_library_bad_version'
Checking for static library 'libSDL' .......................................:(
Static library 'libSDL ver >= (99, 0)' not installed. Install and try again. Exiting ...'''

		self.assert_process_output(command, expected, False)

	def test_find_installed_static_library_cache(self):
		command = '{0} raise -plain find_installed_static_library_cache'.format(sys.executable)

		expected = \
'''Running target 'find_installed_static_library_cache'
Checking for static library 'libSDL' ...                                    :)
Checking for static library 'libSDL' .......................................:(
Static library 'libSDL ver >= (99, 0)' not installed. Install and try again. Exiting ...'''

		self.assert_process_output(command, expected, False)



	def test_find_installed_header_file(self):
		command = '{0} raise -plain find_installed_header_file'.format(sys.executable)

		expected = \
'''Running target 'find_installed_header_file'
Checking for header file 'SDL' ...                                          :)
Checking for header file 'sdl' ...                                          :)
Checking for header file 'libSDL' ...                                       :)
Checking for header file 'libsdl' ...                                       :)
Checking for header file 'SDL' ...                                          :)
Checking for header file 'sdl' ...                                          :)
Checking for header file 'libSDL' ...                                       :)
Checking for header file 'libsdl' ...                                       :)'''

		self.assert_process_output(command, expected)

	def test_find_missing_header_file(self):
		command = '{0} raise -plain find_missing_header_file'.format(sys.executable)

		expected = \
'''Running target 'find_missing_header_file'
Checking for header file 'libDoesNotExist' .................................:(
Header file 'libDoesNotExist (Any version)' not installed. Install and try again. Exiting ...'''

		self.assert_process_output(command, expected, False)

	def test_find_installed_header_file_bad_version(self):
		command = '{0} raise -plain find_installed_header_file_bad_version'.format(sys.executable)

		expected = \
'''Running target 'find_installed_header_file_bad_version'
Checking for header file 'libSDL' ..........................................:(
Header file 'libSDL ver >= (99, 0)' not installed. Install and try again. Exiting ...'''

		self.assert_process_output(command, expected, False)

	def test_find_installed_header_file_cache(self):
		command = '{0} raise -plain find_installed_header_file_cache'.format(sys.executable)

		expected = \
'''Running target 'find_installed_header_file_cache'
Checking for header file 'libSDL' ...                                       :)
Checking for header file 'libSDL' ..........................................:(
Header file 'libSDL ver >= (99, 0)' not installed. Install and try again. Exiting ...'''

		self.assert_process_output(command, expected, False)

if __name__ == '__main__':
	runner = ConcurrentTestRunner()
	runner.add_test_case(TestBasics)
	runner.add_test_case(TestFind)
	runner.add_test_case(TestC)
	runner.add_test_case(TestCXX)
	runner.add_test_case(TestD)
	runner.add_test_case(TestCSharp)
	runner.add_test_case(TestJava)
	runner.run()




