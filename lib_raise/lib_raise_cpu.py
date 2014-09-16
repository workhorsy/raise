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

import lib_raise_helpers as Helpers
import lib_raise_config as Config
import lib_raise_users as Users

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


def get_utilization():
	global cpu_utilization
	return cpu_utilization

def start_get_utilization_thread():
	global utilization_thread

	def real_get_utilization():
		global cpu_utilization
		command = 'top -b -n 2 -d 1'

		while True:
			# Get the cpu percentages
			out = findlib.run_and_get_stdout(command)
			out = out.split("%Cpu(s):")[2]
			out = out.split('\n')[0]
			out = out.split(',')

			# Add the percentages to get the real cpu usage
			speed = \
			float(out[0].split('us')[0]) + \
			float(out[1].split('sy')[0]) + \
			float(out[2].split('ni')[0])

			cpu_utilization = speed

	utilization_thread = threading.Thread(target=real_get_utilization, args=())
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
	mhz = info['hz']

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

setup()


