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

import os
import platform
import multiprocessing
import re
import lib_raise_helpers as Helpers
import lib_raise_config as Config
import lib_raise_users as Users
import cpuinfo


arch = None
bits = None
mhz = None
name = None
vendor_name = None
flags = []
cpus_total = None
cpus_free = None


def setup():
	global arch
	global bits
	global mhz
	global name
	global vendor_name
	global flags
	global cpus_total
	global cpus_free

	def set_arch(dirty_arch):
		global arch
		global bits
		if re.match('^i\d86$|^x86$|^x86_32$|^i86pc$', dirty_arch):
			arch = 'x86_32'
			bits = '32'
		elif re.match('^x86$|^x86_64$|^amd64$', dirty_arch):
			arch = 'x86_64'
			bits = '64'
		else:
			Config.early_exit('Unknown architecture {0}.'.format(dirty_arch))

	# FIXME: Move all this into the cpuinfo.py library as a fallback for Windows
	# For Windows get the CPU info from the register
	if Helpers.os_type._name == 'Windows':
		import _winreg

		# Get the CPU arch and bits
		key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment")
		dirty_arch = _winreg.QueryValueEx(key, "PROCESSOR_ARCHITECTURE")[0]
		_winreg.CloseKey(key)
		set_arch(dirty_arch)

		# Get the CPU MHz
		key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, r"Hardware\Description\System\CentralProcessor\0")
		mhz = _winreg.QueryValueEx(key, "~Mhz")[0]
		_winreg.CloseKey(key)

		# Get the CPU name
		key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, r"Hardware\Description\System\CentralProcessor\0")
		name = _winreg.QueryValueEx(key, "ProcessorNameString")[0]
		_winreg.CloseKey(key)

		# Get the CPU vendor name
		key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, r"Hardware\Description\System\CentralProcessor\0")
		vendor_name = _winreg.QueryValueEx(key, "VendorIdentifier")[0]
		_winreg.CloseKey(key)

		# Get the CPU features
		key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, r"Hardware\Description\System\CentralProcessor\0")
		feature_bits = _winreg.QueryValueEx(key, "FeatureSet")[0]
		_winreg.CloseKey(key)

		def is_set(bit):
			mask = 0x80000000 >> bit
			retval = mask & feature_bits > 0
			return retval

		# http://en.wikipedia.org/wiki/CPUID
		# http://unix.stackexchange.com/questions/43539/what-do-the-flags-in-proc-cpuinfo-mean
		# http://www.lohninger.com/helpcsuite/public_constants_cpuid.htm
		flags = {
			'fpu' : is_set(0), # Floating Point Unit
			'vme' : is_set(1), # V86 Mode Extensions
			'de' : is_set(2), # Debug Extensions - I/O breakpoints supported
			'pse' : is_set(3), # Page Size Extensions (4 MB pages supported)
			'tsc' : is_set(4), # Time Stamp Counter and RDTSC instruction are available
			'msr' : is_set(5), # Model Specific Registers
			'pae' : is_set(6), # Physical Address Extensions (36 bit address, 2MB pages)
			'mce' : is_set(7), # Machine Check Exception supported
			'cx8' : is_set(8), # Compare Exchange Eight Byte instruction available
			'apic' : is_set(9), # Local APIC present (multiprocessor operation support)
			'sepamd' : is_set(10), # Fast system calls (AMD only)
			'sep' : is_set(11), # Fast system calls
			'mtrr' : is_set(12), # Memory Type Range Registers
			'pge' : is_set(13), # Page Global Enable
			'mca' : is_set(14), # Machine Check Architecture
			'cmov' : is_set(15), # Conditional MOVe instructions
			'pat' : is_set(16), # Page Attribute Table
			'pse36' : is_set(17), # 36 bit Page Size Extensions
			'serial' : is_set(18), # Processor Serial Number
			'clflush' : is_set(19), # Cache Flush
			#'reserved1' : is_set(20), # reserved
			'dts' : is_set(21), # Debug Trace Store
			'acpi' : is_set(22), # ACPI support
			'mmx' : is_set(23), # MultiMedia Extensions
			'fxsr' : is_set(24), # FXSAVE and FXRSTOR instructions
			'sse' : is_set(25), # SSE instructions
			'sse2' : is_set(26), # SSE2 (WNI) instructions
			'ss' : is_set(27), # self snoop
			#'reserved2' : is_set(28), # reserved
			'tm' : is_set(29), # Automatic clock control
			'ia64' : is_set(30), # IA64 instructions
			'3dnow' : is_set(31) # 3DNow! instructions available
		}

		# Get a list of only the flags that are true
		flags = [k for k, v in flags.items() if v]
		flags.sort()
	# For everything else, assume unix/linux
	else:
		# First try /proc/cpuinfo
		info = cpuinfo.get_cpu_info_from_proc_cpuinfo()

		# If not, try querying the CPU cpuid register
		if not info:
			info = cpuinfo.get_cpu_info_from_cpuid()
		if not info:
			raise Exception('Failed to get CPU info.')

		# Get the CPU arch and bits
		set_arch(platform.machine())

		# Get the CPU MHz
		mhz = info['processor_hz']

		# Get the CPU name
		name = info['processor_brand']

		# Get the CPU vendor name
		vendor_name = info['vendor_id']

		# Get the CPU features
		flags = info['flags']

	# Figure out how many cpus there are
	cpus_total = multiprocessing.cpu_count()
	cpus_free = cpus_total

setup()


