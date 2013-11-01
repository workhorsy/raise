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


def program_paths(program_name):
	paths = []
	exts = filter(None, os.environ.get('PATHEXT', '').split(os.pathsep))
	path = os.environ['PATH']
	for p in os.environ['PATH'].split(os.pathsep):
		p = os.path.join(p, program_name)
		if os.access(p, os.X_OK):
			paths.append(p)
		for e in exts:
			pext = p + e
			if os.access(pext, os.X_OK):
				paths.append(pext)
	return paths

def chomp(s):
	for sep in ['\r\n', '\n', '\r']:
		if s.endswith(sep):
			return s[:-len(sep)]

	return s

def chown_r(dir_name, uid, gid):
	# Just return if this OS does not support chown
	if not hasattr(os, 'chown'):
		return

	# Chown the root directory
	os.chown(dir_name, uid, gid)

	# Loop through all entries in the root directory
	for root, dirs, files in os.walk(dir_name):
		for entry in dirs + files:
			# Get the whole name
			absolute_entry = os.path.join(root, entry)

			# Chown the entry
			os.chown(absolute_entry, uid, gid)

class TestCase(object):
	@classmethod
	def has_prerequisites(cls):
		raise NotImplementedError("The has_prerequisites class method should be overridden on any child classes.")

	def set_up(self, id):
		pass

	def init(self, test_dir, id):
		self.id = id

		# Copy the files to a build dir
		self.pwd = os.getcwd()
		self.build_dir = 'build_{0}'.format(self.id)
		shutil.copytree(test_dir, self.build_dir)

		# Make the normal user the owner of all the files in the build dir
		status = os.stat(test_dir)
		chown_r(self.build_dir, status.st_uid, status.st_gid)

		# Change to the build dir
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
		cpus_total = 1
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

	def test_require_root(self):
		command = '{0} raise -plain simple_require_root'.format(sys.executable)

		expected = \
"Running target 'simple_require_root'"

		self.assert_process_output(command, expected)

	def test_require_not_root_failure(self):
		command = '{0} raise -plain simple_require_not_root_failure'.format(sys.executable)

		expected = \
'''Running target 'simple_require_not_root_failure'
Must not be run as root. Exiting ...'''

		self.assert_process_output(command, expected, is_success = False)


class TestC(TestCase):
	@classmethod
	def has_prerequisites(cls):
		return True

	def set_up(self, id):
		self.init('C', id)

	def test_install_and_uninstall_program(self):
		command = '{0} raise -plain install_and_uninstall_program'.format(sys.executable)

		expected = \
'''Running target 'install_and_uninstall_program'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building C program 'raise_example.exe' ...                                  :)
Uninstalling the program 'raise_example.exe' ...                            :)
Installing the program 'raise_example.exe' ...                              :)
Running C program ...                                                       :)
raise_example.exe
7 * 12 = 84
Uninstalling the program 'raise_example.exe' ...                            :)'''

		self.assert_process_output(command, expected)

	def test_install_and_uninstall_shared_library(self):
		command = '{0} raise -plain install_and_uninstall_shared_library'.format(sys.executable)

		expected = \
'''Running target 'install_and_uninstall_shared_library'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building C object 'lib_math.o' ...                                          :)
Building shared library 'lib_math.so' ...                                   :)
Building C program 'raise_example.exe' ...                                  :)
Uninstalling the program 'raise_example.exe' ...                            :)
Uninstalling the library 'lib_math.so' ...                                  :)
Installing the program 'raise_example.exe' ...                              :)
Installing the library 'lib_math.so' ...                                    :)
Running C program ...                                                       :)
raise_example.exe
7 * 12 = 84
Uninstalling the program 'raise_example.exe' ...                            :)
Uninstalling the library 'lib_math.so' ...                                  :)'''

		self.assert_process_output(command, expected)

	def test_install_and_uninstall_static_library(self):
		command = '{0} raise -plain install_and_uninstall_static_library'.format(sys.executable)

		expected = \
'''Running target 'install_and_uninstall_static_library'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building C object 'lib_math.o' ...                                          :)
Building static library 'lib_math.a' ...                                    :)
Building C program 'raise_example.exe' ...                                  :)
Uninstalling the program 'raise_example.exe' ...                            :)
Uninstalling the library 'lib_math.a' ...                                   :)
Installing the program 'raise_example.exe' ...                              :)
Installing the library 'lib_math.a' ...                                     :)
Running C program ...                                                       :)
raise_example.exe
7 * 12 = 84
Uninstalling the program 'raise_example.exe' ...                            :)
Uninstalling the library 'lib_math.a' ...                                   :)'''

		self.assert_process_output(command, expected)


class TestCXX(TestCase):
	@classmethod
	def has_prerequisites(cls):
		return True

	def set_up(self, id):
		self.init('CXX', id)

	def test_install_and_uninstall_program(self):
		command = '{0} raise -plain install_and_uninstall_program'.format(sys.executable)

		expected = \
'''Running target 'install_and_uninstall_program'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building C++ program 'raise_example.exe' ...                                :)
Uninstalling the program 'raise_example.exe' ...                            :)
Installing the program 'raise_example.exe' ...                              :)
Running C++ program ...                                                     :)
raise_example.exe
7 + 9 = 16
Uninstalling the program 'raise_example.exe' ...                            :)'''

		self.assert_process_output(command, expected)

	def test_install_and_uninstall_shared_library(self):
		command = '{0} raise -plain install_and_uninstall_shared_library'.format(sys.executable)

		expected = \
'''Running target 'install_and_uninstall_shared_library'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building C++ object 'lib_math.o' ...                                        :)
Building shared library 'lib_math.so' ...                                   :)
Building C++ program 'raise_example.exe' ...                                :)
Uninstalling the program 'raise_example.exe' ...                            :)
Uninstalling the library 'lib_math.so' ...                                  :)
Installing the program 'raise_example.exe' ...                              :)
Installing the library 'lib_math.so' ...                                    :)
Running C++ program ...                                                     :)
raise_example.exe
7 + 9 = 16
Uninstalling the program 'raise_example.exe' ...                            :)
Uninstalling the library 'lib_math.so' ...                                  :)'''

		self.assert_process_output(command, expected)

	def test_install_and_uninstall_static_library(self):
		command = '{0} raise -plain install_and_uninstall_static_library'.format(sys.executable)

		expected = \
'''Running target 'install_and_uninstall_static_library'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building C++ object 'lib_math.o' ...                                        :)
Building static library 'lib_math.a' ...                                    :)
Building C++ program 'raise_example.exe' ...                                :)
Uninstalling the program 'raise_example.exe' ...                            :)
Uninstalling the library 'lib_math.a' ...                                   :)
Installing the program 'raise_example.exe' ...                              :)
Installing the library 'lib_math.a' ...                                     :)
Running C++ program ...                                                     :)
raise_example.exe
7 + 9 = 16
Uninstalling the program 'raise_example.exe' ...                            :)
Uninstalling the library 'lib_math.a' ...                                   :)'''

		self.assert_process_output(command, expected)


class TestD(TestCase):
	@classmethod
	def has_prerequisites(cls):
		return True

	def set_up(self, id):
		self.init('D', id)

	def test_install_and_uninstall_program(self):
		command = '{0} raise -plain install_and_uninstall_program'.format(sys.executable)

		expected = \
'''Running target 'install_and_uninstall_program'
Removing the file 'lib_math.di' ...                                         :)
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building D program 'raise_example.exe' ...                                  :)
Uninstalling the program 'raise_example.exe' ...                            :)
Installing the program 'raise_example.exe' ...                              :)
Running D program ...                                                       :)
raise_example.exe
9 * 12 = 108
Uninstalling the program 'raise_example.exe' ...                            :)'''

		self.assert_process_output(command, expected)


	def test_install_and_uninstall_static_library(self):
		command = '{0} raise -plain install_and_uninstall_static_library'.format(sys.executable)

		expected = \
'''Running target 'install_and_uninstall_static_library'
Removing the file 'lib_math.di' ...                                         :)
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building D object 'lib_math.o' ...                                          :)
Building static library 'lib_math.a' ...                                    :)
Building D program 'raise_example.exe' ...                                  :)
Uninstalling the program 'raise_example.exe' ...                            :)
Uninstalling the library 'lib_math.a' ...                                   :)
Installing the program 'raise_example.exe' ...                              :)
Installing the library 'lib_math.a' ...                                     :)
Running D program ...                                                       :)
raise_example.exe
9 * 12 = 108
Uninstalling the program 'raise_example.exe' ...                            :)
Uninstalling the library 'lib_math.a' ...                                   :)'''

		self.assert_process_output(command, expected)


class TestCSharp(TestCase):
	@classmethod
	def has_prerequisites(cls):
		return True

	def set_up(self, id):
		self.init('CSharp', id)

	def test_install_and_uninstall_program(self):
		command = '{0} raise -plain install_and_uninstall_program'.format(sys.executable)

		expected = \
'''Running target 'install_and_uninstall_program'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building C# program 'raise_example.exe' ...                                 :)
Uninstalling the program 'raise_example.exe' ...                            :)
Installing the program 'raise_example.exe' ...                              :)
Running C# program ...                                                      :)
raise_example.exe
10 - 4 = 6
Uninstalling the program 'raise_example.exe' ...                            :)'''

		self.assert_process_output(command, expected)


	def test_install_and_uninstall_shared_library(self):
		command = '{0} raise -plain install_and_uninstall_shared_library'.format(sys.executable)

		expected = \
'''Running target 'install_and_uninstall_shared_library'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building C# shared library 'lib_math.dll' ...                               :)
Building C# program 'raise_example.exe' ...                                 :)
Uninstalling the program 'raise_example.exe' ...                            :)
Uninstalling the library 'lib_math.dll' ...                                 :)
Installing the program 'raise_example.exe' ...                              :)
Installing the library 'lib_math.dll' ...                                   :)
Running C# program ...                                                      :)
raise_example.exe
10 - 4 = 6
Uninstalling the program 'raise_example.exe' ...                            :)
Uninstalling the library 'lib_math.dll' ...                                 :)'''

		self.assert_process_output(command, expected)


class TestJava(TestCase):
	@classmethod
	def has_prerequisites(cls):
		return True

	def set_up(self, id):
		self.init('Java', id)

	def test_install_and_uninstall_program(self):
		command = '{0} raise -plain install_and_uninstall_program'.format(sys.executable)

		expected = \
'''Running target 'install_and_uninstall_program'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building Java program 'main.class' ...                                      :)
Uninstalling the program 'main.class' ...                                   :)
Installing the program 'main.class' ...                                     :)
Running Java program ...                                                    :)
java main
8 - 1 = 7
Uninstalling the program 'main.class' ...                                   :)'''

		self.assert_process_output(command, expected)


	def test_install_and_uninstall_jar(self):
		command = '{0} raise -plain install_and_uninstall_jar'.format(sys.executable)

		expected = \
'''Running target 'install_and_uninstall_jar'
Removing binaries 'lib_math' ...                                            :)
Removing binaries 'main' ...                                                :)
Building Java jar 'lib_math.jar' ...                                        :)
Building Java program 'main.class' ...                                      :)
Uninstalling the program 'main.class' ...                                   :)
Uninstalling the jar 'lib_math.jar' ...                                     :)
Installing the program 'main.class' ...                                     :)
Installing the jar 'lib_math.jar' ...                                       :)
Running Java program ...                                                    :)
java main
8 - 1 = 7
Uninstalling the program 'main.class' ...                                   :)
Uninstalling the jar 'lib_math.jar' ...                                     :)'''

		self.assert_process_output(command, expected)


if __name__ == '__main__':
	runner = ConcurrentTestRunner()
	runner.add_test_case(TestBasics)
	runner.add_test_case(TestC)
	runner.add_test_case(TestCXX)
	runner.add_test_case(TestCSharp)
	runner.add_test_case(TestJava)
	runner.run()




