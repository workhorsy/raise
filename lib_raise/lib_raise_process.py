#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# This file is part of Raise.
# Raise is a small build automation tool that ships with your software.
# Raise uses a MIT style license, and is hosted at https://github.com/workhorsy/raise .
# Copyright (c) 2012-2017 Matthew Brennan Jones <matthew.brennan.jones@gmail.com>
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
import time
from osinfo import *
import lib_raise_config as Config
import lib_raise_helpers as Helpers
import lib_raise_cpu as CPU
import lib_raise_users as Users
import lib_raise_terminal as Print

import findlib


class Event(object):
	is_concurrent = False
	is_first_concurrent = False
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
		# Show the concurrent header
		if Event.is_concurrent:
			if Event.is_first_concurrent:
				Event.is_first_concurrent = False
				sys.stdout.write("{0} {1} concurrently ...\n".format(self._task, self._plural))
				sys.stdout.flush()
				Print.message_length = 0

		# Run the setup function
		if not self._setup_cb():
			return False

		# Show the serial message
		if not Event.is_concurrent:
			Print.status("{0} {1} '{2}'".format(self._task, self._singular, self._result))

		# Start the process
		self._runner = findlib.ProcessRunner(self._command)
		self._status = 'running'
		self._runner.run()
		return True

	def wait(self):
		# Wait for the process to complete
		self._runner.wait()

		# Display the message
		if Event.is_concurrent:
			Print.status("   '{0}'".format(self._result))

		# Success or failure
		if self._runner.is_success:
			Print.ok()
			self._status = 'success'
		elif self._runner.is_warning:
			Print.warning(self._runner.stderr)
			self._status = 'success'
		else:
			Print.fail(self._runner.stdall)
			Print.exit("{0} failed. Try again.".format(self._task))
			self._status = 'failure'


def add_event(event):
	Event.events.append(event)

	# If not concurrent, run the event now
	if not Event.is_concurrent:
		concurrent_end()

def concurrent_start():
	Event.is_concurrent = True
	Event.is_first_concurrent = True

def concurrent_end():
	ready_events = Event.events
	running_events = []

	while len(ready_events) or len(running_events):
		#print(CPU.get_utilization(), CPU.cpus_free)

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
				Print.exit("Event failed.")

		# Check for events that need to start
		while CPU.cpus_free > 0 and CPU.get_utilization() < 90.0 and len(ready_events):
			event = ready_events.pop()
			if event.run():
				CPU.cpus_free -= 1
				running_events.insert(0, event)

		# Sleep if all the cpu cores are busy, or have already started
		if CPU.get_utilization() >= 90.0:
			time.sleep(0.1)

	# Clear all the events
	CPU.cpus_free = CPU.cpus_total * 10 # 10 jobs per core
	Event.events = []
	Event.is_concurrent = False
	Event.is_first_concurrent = False

def do_on_fail_exit(start_message, fail_message, cb):
	Print.status(start_message)

	# Run it if it is a function
	if hasattr(cb, '__call__'):
		try:
			cb()
			Print.ok()
		except Exception as e:
			Print.fail()
			Print.exit(fail_message)
	# Or run it as a process if a string
	elif type(cb) == str:
		runner = findlib.ProcessRunner(cb)
		runner.run()
		runner.is_done
		runner.wait()
		if runner.is_success or runner.is_warning:
			Print.ok()
		elif runner.is_failure:
			Print.fail()
			Print.exit(fail_message)

def do_on_fail_pass(start_message, cb):
	Print.status(start_message)
	try:
		cb()
	except Exception as e:
		pass
	Print.ok()
