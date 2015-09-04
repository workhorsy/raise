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

import sys, os, re
import subprocess
import threading
import atexit

import lib_raise_helpers as Helpers
import lib_raise_config as Config
import lib_raise_users as Users

import osinfo
import cpuinfo
import findlib


arch = None
bits = None
mhz = None
name = None
vendor_name = None
flags = []
cpus_total = None
cpus_free = None
cpu_utilization = 0.0
utilization_thread = None
is_utilization_thread_running = False


def _get_utilization_thread():
	global cpu_utilization
	global is_utilization_thread_running

	is_utilization_thread_running = True
	while is_utilization_thread_running:
		# Get the cpu percentages
		speed = 0
		out = None

		if Config.os_type in osinfo.OSType.Linux or Config.os_type in osinfo.OSType.Cygwin:
			command = 'top -b -n 2 -d 1'
			out = findlib.run_and_get_stdout(command)

			# Get the cpu percentages
			out = out.split("%Cpu(s):")[2]
			out = out.split('\n')[0]
			out = out.split(',')

			# Add the percentages to get the real cpu usage
			speed = \
			float(out[0].split('us')[0]) + \
			float(out[1].split('sy')[0]) + \
			float(out[2].split('ni')[0])
		elif Config.os_type in osinfo.OSType.BSD:
			command = 'top -b -P -s 2 -d 2'
			out = findlib.run_and_get_stdout(command)

			# Get the cpu percentages
			out = out.split("CPU:")[1]
			out = out.split('\n')[0]
			out = out.split(',')
		
			# Add the percentages to get the real cpu usage
			speed = \
			float(out[0].split('% user')[0]) + \
			float(out[1].split('% nice')[0]) + \
			float(out[2].split('% system')[0])
		elif Config.os_type in osinfo.OSType.MacOS:
			command = 'top -F -l 2 -i 2 -n 0'
			out = findlib.run_and_get_stdout(command)

			# Get the cpu percentages
			out = out.split("CPU usage:")[2]
			out = out.split('\n')[0]
			out = out.split(',')

			# Add the percentages to get the real cpu usage
			speed = \
			float(out[0].split('% user')[0]) + \
			float(out[1].split('% sys')[0])
		elif Config.os_type in osinfo.OSType.Solaris:
			command = 'top -b -s 2 -d 2'
			out = findlib.run_and_get_stdout(command)

			# Get the cpu percentages
			out = out.split("CPU states: ")[2]
			out = out.split('\n')[0]
			out = out.split(',')

			# Add the percentages to get the real cpu usage
			speed = \
			float(out[0].split('% user')[0]) + \
			float(out[1].split('% nice')[0]) + \
			float(out[2].split('% kernel')[0])
		elif Config.os_type in osinfo.OSType.BeOS:
			command = 'top -d -i 2 -n 2'
			out = findlib.run_and_get_stdout(command)

			# Get the cpu percentages
			out = out.split("------")[1]
			out = out.split('% TOTAL')[0]
			out = out.split()

			# Add the percentages to get the real cpu usage
			speed = float(out[-1])
		elif Config.os_type in osinfo.OSType.Windows:
			command = 'wmic cpu get loadpercentage'
			out = findlib.run_and_get_stdout(command)

			# Get the cpu percentages
			out = out.split()[-1]

			# Add the percentages to get the real cpu usage
			speed = float(out)

		cpu_utilization = speed


def get_utilization():
	global cpu_utilization
	return cpu_utilization

def start_get_utilization_thread():
	global utilization_thread

	utilization_thread = threading.Thread(target=_get_utilization_thread, args=())
	utilization_thread.daemon = True
	utilization_thread.start()

def setup():
	global arch
	global bits
	global mhz
	global name
	global vendor_name
	global flags
	global cpus_total
	global cpus_free

	info = cpuinfo.get_cpu_info()

	# Make sure to show an error if we can't get any CPU info
	if not info:
		Config.early_exit('Failed to get CPU info.')

	# Make sure to show an error if we could not get the CPU arch or bits
	if not info['arch'] or not info['bits']:
		Config.early_exit('Unknown CPU architecture "{0}".'.format(info['raw_arch_string']))

	# Get the CPU arch
	arch = info['arch']

	# Get the CPU bits
	bits = info['bits']

	# Get the CPU MHz
	mhz = info['hz_advertised']

	# Get the CPU name
	name = info['brand']

	# Get the CPU vendor name
	vendor_name = info['vendor_id']

	# Get the CPU features
	flags = info['flags']

	# Figure out how many cpus there are
	cpus_total = info['count']
	cpus_free = cpus_total

	start_get_utilization_thread()

def exit_module():
	global utilization_thread
	global is_utilization_thread_running

	if is_utilization_thread_running and utilization_thread:
		is_utilization_thread_running = False
		utilization_thread.join()
		utilization_thread = None

setup()
atexit.register(exit_module)


