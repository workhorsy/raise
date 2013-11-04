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

import os
import platform
import multiprocessing
import re
import lib_raise_helpers as Helpers
import lib_raise_config as Config
import lib_raise_os as OS


arch = None
bits = None
mhz = None
name = None
vendor_name = None
# FIXME: Change flags to a list, so we do 'blah' in flags instead of 'in' and bool test
flags = {}
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
		if re.match('^i\d86$|^x86$|^x86_32$|^i86pc$', dirty_arch):
			arch = 'x86_32'
			bits = '32'
		elif re.match('^x86$|^x86_64$|^amd64$', dirty_arch):
			arch = 'x86_64'
			bits = '64'
		else:
			Config.early_exit('Unknown architecture {0}.'.format(dirty_arch))

	# For Windows get the CPU info from the register
	if OS.os_type._name == 'Windows':
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
			'reserved1' : is_set(20), # reserved
			'dts' : is_set(21), # Debug Trace Store
			'acpi' : is_set(22), # ACPI support
			'mmx' : is_set(23), # MultiMedia Extensions
			'xsr' : is_set(24), # FXSAVE and FXRSTOR instructions
			'sse' : is_set(25), # SSE instructions
			'sse2' : is_set(26), # SSE2 (WNI) instructions
			'ss' : is_set(27), # self snoop
			'reserved2' : is_set(28), # reserved
			'tm' : is_set(29), # Automatic clock control
			'ia64' : is_set(30), # IA64 instructions
			'3dnow' : is_set(31) # 3DNow! instructions available
		}
	# For everything else, use /proc/cpuinfo
	else:
		# Get the CPU arch and bits
		set_arch(platform.machine())

		# Get the CPU MHz
		cpuinfo = os.popen('cat /proc/cpuinfo').read()
		mhz = Helpers.between(cpuinfo, 'cpu MHz		: ', '\n')

		# Get the CPU name
		name = Helpers.between(cpuinfo, 'model name	: ', '\n')

		# Get the CPU vendor name
		vendor_name = Helpers.between(cpuinfo, 'vendor_id	: ', '\n')

		# Get the CPU features
		features = Helpers.between(cpuinfo, 'flags		: ', '\n').split()

		def is_set(name):
			return name in features

		# FIXME: Is there a definitive list of flags? I am getting more on Linux, and
		# some are different. Like sse2 on Linux is simd2 on windows xp.
		flags = {
			'fpu' : is_set('fpu'), # Floating Point Unit
			'vme' : is_set('vme'), # V86 Mode Extensions
			'de' : is_set('de'), # Debug Extensions - I/O breakpoints supported
			'pse' : is_set('pse'), # Page Size Extensions (4 MB pages supported)
			'tsc' : is_set('tsc'), # Time Stamp Counter and RDTSC instruction are available
			'msr' : is_set('msr'), # Model Specific Registers
			'pae' : is_set('pae'), # Physical Address Extensions (36 bit address, 2MB pages)
			'mce' : is_set('mce'), # Machine Check Exception supported
			'cx8' : is_set('cx8'), # Compare Exchange Eight Byte instruction available
			'apic' : is_set('apic'), # Local APIC present (multiprocessor operation support)
			'sepamd' : is_set('sepamd'), # Fast system calls (AMD only)
			'sep' : is_set('sep'), # Fast system calls
			'mtrr' : is_set('mtrr'), # Memory Type Range Registers
			'pge' : is_set('pge'), # Page Global Enable
			'mca' : is_set('mca'), # Machine Check Architecture
			'cmov' : is_set('cmov'), # Conditional MOVe instructions
			'pat' : is_set('pat'), # Page Attribute Table
			'pse36' : is_set('pse36'), # 36 bit Page Size Extensions
			'serial' : is_set('serial'), # Processor Serial Number
			'clflush' : is_set('clflush'), # Cache Flush
			'reserved1' : is_set('reserved1'), # reserved
			'dts' : is_set('dts'), # Debug Trace Store
			'acpi' : is_set('acpi'), # ACPI support
			'mmx' : is_set('mmx'), # MultiMedia Extensions
			'xsr' : is_set('xsr'), # FXSAVE and FXRSTOR instructions
			'sse' : is_set('sse'), # SSE instructions
			'sse2' : is_set('sse2'), # SSE2 (WNI) instructions
			'ss' : is_set('ss'), # self snoop
			'reserved2' : is_set('reserved2'), # reserved
			'tm' : is_set('tm'), # Automatic clock control
			'ia64' : is_set('ia64'), # IA64 instructions
			'3dnow' : is_set('3dnow') # 3DNow! instructions available
		}
		for feature in features.split():
			flags[feature] = True


		#print('mhz', mhz)
		#print('name', name)
		#print('vendor_name', vendor_name)
		#print('flags', flags)


	# Figure out how many cpus there are
	cpus_total = multiprocessing.cpu_count()
	cpus_free = cpus_total


setup()


