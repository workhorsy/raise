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

import subprocess
import time
from lib_raise_cpu import *
from lib_raise_os import *
from lib_raise_terminal import *


class Process(object):
	is_setup = False

	@classmethod
	def setup(cls):
		if cls.is_setup:
			return

		cls.is_setup = True

Process.setup()

class ProcessRunner(object):
	def __init__(self, command):
		if OS.os_type._name == 'Windows':
			# Remove starting ./
			if command.startswith('./'):
				command = command[2 :]
			# Replace ${BLAH} with %BLAH%
			command = command.replace('${', '%').replace('}', '%')

		self._command = command
		self._process = None
		self._return_code = None
		self._stdout = None
		self._stderr = None
		self._status = None

	def run(self):
		# Recursively expand all environmental variables
		env = {}
		for key, value in os.environ.items():
			env[key] = expand_envs(value)

		# Start the process and save the output
		self._process = subprocess.Popen(
			self._command, 
			stderr = subprocess.PIPE, 
			stdout = subprocess.PIPE, 
			shell = True, 
			env = env
		)

	def wait(self):
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

		# :( Failure
		if self._return_code:
			self._status = Emoticons.FROWN
		else:
			# :\ Warning
			if len(self._stderr):
				self._status = Emoticons.NORMAL
			# :) Success
			else:
				self._status = Emoticons.SMILE

	def get_is_done(self):
		# You have to poll a process to update the retval. Even if it has stopped already
		if self._process.returncode == None:
			self._process.poll()
		return self._process.returncode != None
	is_done = property(get_is_done)

	def get_is_success(self):
		self._require_wait()
		return self._status == Emoticons.SMILE
	is_success = property(get_is_success)

	def get_is_warning(self):
		self._require_wait()
		return self._status == Emoticons.NORMAL
	is_warning = property(get_is_warning)

	def get_is_failure(self):
		self._require_wait()
		return self._status == Emoticons.FROWN
	is_failure = property(get_is_failure)

	def get_stderr(self):
		self._require_wait()
		return self._stderr
	stderr = property(get_stderr)

	def get_stdout(self):
		self._require_wait()
		return self._stdout
	stdout = property(get_stdout)

	def get_stdall(self):
		self._require_wait()
		return self._stdout + '\n' + self._stderr
	stdall = property(get_stdall)

	def _require_wait(self):
		if self._return_code == None:
			raise Exception("Wait needs to be called before any info on the process can be gotten.")


class Event(object):
	is_parallel = False
	is_first_parallel = False
	events = []

	def __init__(self, task, result, plural, singular, command, setup_cb):
		self._status = 'ready'
		self._runner = None

		self._task = task
		self._result = result
		self._plural = plural
		self._singular = singular
		self._command = command
		self._setup_cb = setup_cb

	def get_is_done(self):
		return self._runner.is_done
	is_done = property(get_is_done)

	def run(self):
		# Show the parallel header
		if Event.is_parallel:
			if Event.is_first_parallel:
				Event.is_first_parallel = False
				sys.stdout.write("{0} {1} in parallel ...\n".format(self._task, self._plural))
				sys.stdout.flush()
				Terminal.message_length = 0

		# Run the setup function
		if not self._setup_cb():
			return False

		# Show the serial message
		if not Event.is_parallel:
			print_status("{0} {1} '{2}'".format(self._task, self._singular, self._result))

		# Start the process
		self._runner = ProcessRunner(self._command)
		self._status = 'running'
		self._runner.run()
		return True

	def wait(self):
		# Wait for the process to complete
		self._runner.wait()

		# Display the message
		if Event.is_parallel:
			print_status("   '{0}'".format(self._result))

		# Success or failure
		if self._runner.is_success:
			print_ok()
			self._status = 'success'
		elif self._runner.is_warning:
			print_warning(self._runner.stderr)
			self._status = 'success'
		else:
			print_fail(self._runner.stdall)
			print_exit("{0} failed. Try again.".format(self._task))
			self._status = 'failure'

def add_event(event):
	Event.events.append(event)

	# If not parallel, run the event now
	if not Event.is_parallel:
		parallel_end()

def parallel_start():
	Event.is_parallel = True
	Event.is_first_parallel = True

def parallel_end():
	ready_events = Event.events
	running_events = []

	while len(ready_events) or len(running_events):
		# Check for events that are done
		for event in running_events[:]:
			# Check if it is done
			if event.is_done:
				event.wait()

			# Success. Keep going
			if event._status == 'success':
				running_events.remove(event)
				CPU.cpus_free += 1
			# Failure. Stop events and exit
			elif event._status == 'failure':
				print_exit("Event failed.")

		# Check for events that need to start
		while CPU.cpus_free > 0 and len(ready_events):
			event = ready_events.pop()
			if event.run():
				CPU.cpus_free -= 1
				running_events.insert(0, event)

		# Sleep if all the cpu cores are busy, or have already started
		if CPU.cpus_free == 0 or len(ready_events) == 0:
			time.sleep(0.1)

	# Clear all the events
	CPU.cpus_free = CPU.cpus_total
	Event.events = []
	Event.is_parallel = False
	Event.is_first_parallel = False

# FIXME: Rename to run_print
def run_say(command):
	print_status("Running command")

	runner = ProcessRunner(command)
	runner.run()
	runner.wait()

	if runner.is_success or runner.is_warning:
		print_ok()
		print(command)
		print(runner.stdall)
	elif runner.is_failure:
		print_fail()
		print(command)
		print(runner.stdall)
		print_exit('Failed to run command.')

def run_and_get_stdout(command):
	runner = ProcessRunner(command)
	runner.run()
	runner.wait()
	if runner.is_failure:
		return None
	else:
		return runner.stdout

def _do_on_fail_exit(start_message, fail_message, cb):
	print_status(start_message)

	# Run it if it is a function
	if hasattr(cb, '__call__'):
		try:
			cb()
			print_ok()
		except Exception as e:
			print_fail()
			print_exit(fail_message)
	# Or run it as a process if a string
	elif type(cb) == str:
		runner = ProcessRunner(cb)
		runner.run()
		runner.wait()
		if runner.is_success or runner.is_warning:
			print_ok()
		elif runner.is_failure:
			print_fail()
			print_exit(fail_message)

def _do_on_fail_pass(start_message, cb):
	print_status(start_message)
	try:
		cb()
	except Exception as e:
		pass
	print_ok()


