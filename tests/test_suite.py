#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# This file is part of Raise.
# Raise is a small build automation tool that ships with your software.
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
import time
import multiprocessing
import shutil


class TestCase(object):
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
		process = TestProcessRunner(command)
		process.run()

		# Make sure the text returned is as expected
		self.assert_not_diff(expected, process.stdall)

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

		# Wait for the process to exit
		self._process.wait()

		# Get the return code
		rc = self._process.returncode
		if hasattr(os, 'WIFEXITED') and os.WIFEXITED(rc):
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


class TestBasics(TestCase):
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


class TestC(TestCase):
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
Building shared library 'lib_math.so' ...                                   :)
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
Building shared library 'lib_math.so' ...                                   :)
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


class TestLibraries(TestCase):
	def set_up(self, id):
		self.init('Libraries', id)

	def test_find_installed_library(self):
		command = '{0} raise -plain find_installed_library'.format(sys.executable)

		expected = \
'''Running target 'find_installed_library'
Checking for shared library 'libSDL' ...                                    :)'''

		self.assert_process_output(command, expected)

	def test_find_missing_library(self):
		command = '{0} raise -plain find_missing_library'.format(sys.executable)

		expected = \
'''Running target 'find_missing_library'
Checking for shared library 'libDoesNotExist' ..............................:(
Shared library 'libDoesNotExist (Any version)' not installed. Install and try again. Exiting ...'''

		self.assert_process_output(command, expected, False)

	def test_find_installed_library_bad_version(self):
		command = '{0} raise -plain find_installed_library_bad_version'.format(sys.executable)

		expected = \
'''Running target 'find_installed_library_bad_version'
Checking for shared library 'libSDL' .......................................:(
Shared library 'libSDL ver >= (99, 0)' not installed. Install and try again. Exiting ...'''

		self.assert_process_output(command, expected, False)


if __name__ == '__main__':
	runner = ConcurrentTestRunner()
	for cls in TestCase.__subclasses__():
		runner.add_test_case(cls)
	runner.run()




