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

class CPUModule(RaiseModule):
	def __init__(self):
		super(CPUModule, self).__init__("CPU")
		self._arch = None
		self._bits = None
		self._cpus_total = None
		self._cpus_free = None

	def setup(self):
		# Figure out the CPU architecture
		if re.match('^i\d86$|^x86$|^x86_32$|^i86pc$', platform.machine()):
			self._arch = 'x86_32'
			self._bits = '32'
		elif re.match('^x86$|^x86_64$|^amd64$', platform.machine()):
			self._arch = 'x86_64'
			self._bits = '64'
		else:
			early_exit('Unknown architecture {0}.'.format(platform.machine()))

		# Figure out how many cpus there are
		self._cpus_total = multiprocessing.cpu_count()
		self._cpus_free = self._cpus_total

		self.is_setup = True

