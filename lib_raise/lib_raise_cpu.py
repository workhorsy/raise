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

import platform
import multiprocessing
import re
from lib_raise_config import *


class CPU(RaiseModule):
	arch = None
	bits = None
	cpus_total = None
	cpus_free = None

	@classmethod
	def setup(cls):
		# Figure out the CPU architecture
		if re.match('^i\d86$|^x86$|^x86_32$|^i86pc$', platform.machine()):
			cls.arch = 'x86_32'
			cls.bits = '32'
		elif re.match('^x86$|^x86_64$|^amd64$', platform.machine()):
			cls.arch = 'x86_64'
			cls.bits = '64'
		else:
			early_exit('Unknown architecture {0}.'.format(platform.machine()))

		# Figure out how many cpus there are
		cls.cpus_total = multiprocessing.cpu_count()
		cls.cpus_free = cls.cpus_total


CPU.call_setup()

