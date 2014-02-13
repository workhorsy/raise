#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2014, Matthew Brennan Jones <mattjones@workhorsy.org>
# Py-cpuinfo is a Python module to show the cpuinfo of a processor
# It uses a MIT style license
# It is hosted at: https://github.com/workhorsy/py-cpuinfo
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

# FIXME: Figure out how /proc/cpuinfo simulates cpuinfo on non x86 cpus
# FIXME: See if running this in a multiprocessing process will stop it from segfaulting when it breaks
# FIXME: Check how this compares to numpy. How does numpy get MHz and sse3 detection when the registry
# does not have this info, and there is no /proc/cpuinfo ? Does it use win32 __cpuinfo ?

# Assembly code can be assembled and disassembled like this:
'''
; cpuid.asm
; clear && nasm -o out -f bin cpuid.asm && ndisasm out
BITS 32
section .data
section .text
global main

main:
	mov ax, 1
	cpuid
	mov ax, bx
	ret
'''

import os
import re
import time
import platform
import multiprocessing
import ctypes

bits = platform.architecture()[0]
is_windows = platform.system().lower() == 'windows'
has_checked_for_selinux = False
has_selinux = False


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

def is_bit_set(reg, bit):
	mask = 1 << bit
	is_set = reg & mask > 0
	return is_set

def asm_func(restype=None, argtypes=(), byte_code=[]):
	global has_checked_for_selinux
	global has_selinux
	byte_code = bytes.join(b'', byte_code)

	# Check for SE Linux
	if not has_checked_for_selinux:
		can_selinux_exec_heap, can_selinux_exec_memory = True, True
		if program_paths('sestatus'):
			can_selinux_exec_heap = os.popen("sestatus -b | grep -i \"allow_execheap\"").read().strip().lower().endswith('on')
			can_selinux_exec_memory = os.popen("sestatus -b | grep -i \"allow_execmem\"").read().strip().lower().endswith('on')

		has_selinux = (not can_selinux_exec_heap or not can_selinux_exec_memory)
		has_checked_for_selinux = True

	address = None
		
	if is_windows:
		# Allocate a memory segment the size of the byte code, and make it executable
		size = len(byte_code)
		MEM_COMMIT = ctypes.c_ulong(0x1000)
		PAGE_EXECUTE_READWRITE = ctypes.c_ulong(0x40)
		address = ctypes.windll.kernel32.VirtualAlloc(ctypes.c_int(0), ctypes.c_size_t(size), MEM_COMMIT, PAGE_EXECUTE_READWRITE)
		if not address:
			raise Exception("Failed to VirtualAlloc")
				
		# Copy the byte code into the memory segment
		memmove = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t)(ctypes._memmove_addr)
		if memmove(address, byte_code, size) < 0:
			raise Exception("Failed to memmove")
	else:
		# Allocate a memory segment the size of the byte code
		size = len(byte_code)
		address = ctypes.pythonapi.valloc(size)
		if not address:
			raise Exception("Failed to valloc")

		# Mark the memory segment as safe for code execution
		if not has_selinux:
			READ_WRITE_EXECUTE = 0x1 | 0x2 | 0x4
			if ctypes.pythonapi.mprotect(address, size, READ_WRITE_EXECUTE) < 0:
				raise Exception("Failed to mprotect")
				
		# Copy the byte code into the memory segment
		if ctypes.pythonapi.memmove(address, byte_code, size) < 0:
			raise Exception("Failed to memmove")

	# Cast the memory segment into a function
	functype = ctypes.CFUNCTYPE(restype, *argtypes)
	fun = functype(address)
	return fun, address

def run_asm(*byte_code):
	# Convert the byte code into a function that returns an int
	restype = None
	if bits == '64bit':
		restype = ctypes.c_uint64
	else:
		restype = ctypes.c_uint32
	argtypes = ()
	func, address = asm_func(restype, argtypes, byte_code)

	# Call the byte code like a function
	retval = func()

	# Free the function memory segment
	# FIXME: This should set the memory as non executable before freeing
	if is_windows:
		size = ctypes.c_size_t(len(byte_code))
		MEM_RELEASE = ctypes.c_ulong(0x8000)
		ctypes.windll.kernel32.VirtualFree(address, size, MEM_RELEASE)
	else:
		ctypes.pythonapi.free(address)

	return retval

# FIXME: We should not have to use different instructions to 
# set eax to 0 or 1, on 32bit and 64bit machines.
def _zero_eax():
	if bits == '64bit':
		return (
			b"\x66\xB8\x00\x00" # mov eax,0x0"
		)
	else:
		return (
			b"\x31\xC0"         # xor ax,ax
		)

def _one_eax():
	if bits == '64bit':
		return (
			b"\x66\xB8\x01\x00" # mov eax,0x1"
		)
	else:
		return (
			b"\x31\xC0"         # xor ax,ax
			b"\x40"             # inc ax
		)

# http://en.wikipedia.org/wiki/CPUID#EAX.3D0:_Get_vendor_ID
def get_vendor_id():
	# EBX
	ebx = run_asm(
		_zero_eax(),
		b"\x0F\xA2"         # cpuid
		b"\x89\xD8"         # mov ax,bx
		b"\xC3"             # ret
	)

	# ECX
	ecx = run_asm(
		_zero_eax(),
		b"\x0f\xa2"         # cpuid
		b"\x89\xC8"         # mov ax,cx
		b"\xC3"             # ret
	)

	# EDX
	edx = run_asm(
		_zero_eax(),
		b"\x0f\xa2"         # cpuid
		b"\x89\xD0"         # mov ax,dx
		b"\xC3"             # ret
	)

	# Each 4bits is a ascii letter in the name
	vendor_id = []
	for reg in [ebx, edx, ecx]:
		for n in [0, 8, 16, 24]:
			vendor_id.append(chr((reg >> n) & 0xFF))
	vendor_id = str.join('', vendor_id)

	return vendor_id

# http://en.wikipedia.org/wiki/CPUID#EAX.3D1:_Processor_Info_and_Feature_Bits
def get_info():
	# EAX
	eax = run_asm(
		_one_eax(),
		b"\x0f\xa2"         # cpuid
		b"\xC3"             # ret
	)

	# Get the CPU info
	stepping = (eax >> 0) & 0xF # 4 bits
	model = (eax >> 4) & 0xF # 4 bits
	family = (eax >> 8) & 0xF # 4 bits
	processor_type = (eax >> 12) & 0x3 # 2 bits
	extended_model = (eax >> 16) & 0xF # 4 bits
	extended_family = (eax >> 20) & 0xFF # 8 bits

	return {
		'stepping' : stepping, 
		'model' : model, 
		'family' : family,
		'processor_type' : processor_type,
		'extended_model' : extended_model,
		'extended_family' : extended_family
	}

def get_max_extension_support():
	# Check for extension support
	max_extension_support = run_asm(
		b"\xB8\x00\x00\x00\x80" # mov ax,0x80000000
		b"\x0f\xa2"             # cpuid
		b"\xC3"                 # ret
	)

	return max_extension_support

# http://en.wikipedia.org/wiki/CPUID#EAX.3D1:_Processor_Info_and_Feature_Bits
def get_flags(max_extension_support):
	# EDX
	edx = run_asm(
		_one_eax(),
		b"\x0f\xa2"         # cpuid
		b"\x89\xD0"         # mov ax,dx
		b"\xC3"             # ret
	)

	# ECX
	ecx = run_asm(
		_one_eax(),
		b"\x0f\xa2"         # cpuid
		b"\x89\xC8"         # mov ax,cx
		b"\xC3"             # ret
	)

	# Get the CPU flags
	flags = {
		'fpu' : is_bit_set(edx, 0),
		'vme' : is_bit_set(edx, 1),
		'de' : is_bit_set(edx, 2),
		'pse' : is_bit_set(edx, 3),
		'tsc' : is_bit_set(edx, 4),
		'msr' : is_bit_set(edx, 5),
		'pae' : is_bit_set(edx, 6),
		'mce' : is_bit_set(edx, 7),
		'cx8' : is_bit_set(edx, 8),
		'apic' : is_bit_set(edx, 9),
		#'reserved1' : is_bit_set(edx, 10),
		'sep' : is_bit_set(edx, 11),
		'mtrr' : is_bit_set(edx, 12),
		'pge' : is_bit_set(edx, 13),
		'mca' : is_bit_set(edx, 14),
		'cmov' : is_bit_set(edx, 15),
		'pat' : is_bit_set(edx, 16),
		'pse36' : is_bit_set(edx, 17),
		'pn' : is_bit_set(edx, 18),
		'clflush' : is_bit_set(edx, 19),
		#'reserved2' : is_bit_set(edx, 20),
		'dts' : is_bit_set(edx, 21),
		'acpi' : is_bit_set(edx, 22),
		'mmx' : is_bit_set(edx, 23),
		'fxsr' : is_bit_set(edx, 24),
		'sse' : is_bit_set(edx, 25),
		'sse2' : is_bit_set(edx, 26),
		'ss' : is_bit_set(edx, 27),
		'ht' : is_bit_set(edx, 28),
		'tm' : is_bit_set(edx, 29),
		'ia64' : is_bit_set(edx, 30),
		'pbe' : is_bit_set(edx, 31),

		'pni' : is_bit_set(ecx, 0),
		'pclmulqdq' : is_bit_set(ecx, 1),
		'dtes64' : is_bit_set(ecx, 2),
		'monitor' : is_bit_set(ecx, 3),
		'ds_cpl' : is_bit_set(ecx, 4),
		'vmx' : is_bit_set(ecx, 5),
		'smx' : is_bit_set(ecx, 6),
		'est' : is_bit_set(ecx, 7),
		'tm2' : is_bit_set(ecx, 8),
		'ssse3' : is_bit_set(ecx, 9),
		'cid' : is_bit_set(ecx, 10),
		#'reserved3' : is_bit_set(ecx, 11),
		'fma' : is_bit_set(ecx, 12),
		'cx16' : is_bit_set(ecx, 13),
		'xtpr' : is_bit_set(ecx, 14),
		'pdcm' : is_bit_set(ecx, 15),
		#'reserved4' : is_bit_set(ecx, 16),
		'pcid' : is_bit_set(ecx, 17),
		'dca' : is_bit_set(ecx, 18),
		'sse4_1' : is_bit_set(ecx, 19),
		'sse4_2' : is_bit_set(ecx, 20),
		'x2apic' : is_bit_set(ecx, 21),
		'movbe' : is_bit_set(ecx, 22),
		'popcnt' : is_bit_set(ecx, 23),
		'tscdeadline' : is_bit_set(ecx, 24),
		'aes' : is_bit_set(ecx, 25),
		'xsave' : is_bit_set(ecx, 26),
		'osxsave' : is_bit_set(ecx, 27),
		'avx' : is_bit_set(ecx, 28),
		'f16c' : is_bit_set(ecx, 29),
		'rdrnd' : is_bit_set(ecx, 30),
		'hypervisor' : is_bit_set(ecx, 31)
	}

	# Get a list of only the flags that are true
	flags = [k for k, v in flags.items() if v]

	# Get the Extended CPU flags
	extended_flags = {}
	if max_extension_support >= 0x80000001:
		# EDX
		edx = run_asm(
			b"\xB8\x01\x00\x00\x80" # mov ax,0x80000001
			b"\x0f\xa2"         # cpuid
			b"\x89\xD0"         # mov ax,dx
			b"\xC3"             # ret
		)

		# ECX
		ecx = run_asm(
			b"\xB8\x01\x00\x00\x80" # mov ax,0x80000001
			b"\x0f\xa2"         # cpuid
			b"\x89\xC8"         # mov ax,cx
			b"\xC3"             # ret
		)

		# Get the extended CPU flags
		extended_flags = {
			'fpu' : is_bit_set(edx, 0),
			'vme' : is_bit_set(edx, 1),
			'de' : is_bit_set(edx, 2),
			'pse' : is_bit_set(edx, 3),
			'tsc' : is_bit_set(edx, 4),
			'msr' : is_bit_set(edx, 5),
			'pae' : is_bit_set(edx, 6),
			'mce' : is_bit_set(edx, 7),
			'cx8' : is_bit_set(edx, 8),
			'apic' : is_bit_set(edx, 9),
			#'reserved' : is_bit_set(edx, 10),
			'syscall' : is_bit_set(edx, 11),
			'mtrr' : is_bit_set(edx, 12),
			'pge' : is_bit_set(edx, 13),
			'mca' : is_bit_set(edx, 14),
			'cmov' : is_bit_set(edx, 15),
			'pat' : is_bit_set(edx, 16),
			'pse36' : is_bit_set(edx, 17),
			#'reserved' : is_bit_set(edx, 18),
			'mp' : is_bit_set(edx, 19),
			'nx' : is_bit_set(edx, 20),
			#'reserved' : is_bit_set(edx, 21),
			'mmxext' : is_bit_set(edx, 22),
			'mmx' : is_bit_set(edx, 23),
			'fxsr' : is_bit_set(edx, 24),
			'fxsr_opt' : is_bit_set(edx, 25),
			'pdpe1gp' : is_bit_set(edx, 26),
			'rdtscp' : is_bit_set(edx, 27),
			#'reserved' : is_bit_set(edx, 28),
			'lm' : is_bit_set(edx, 29),
			'3dnowext' : is_bit_set(edx, 30),
			'3dnow' : is_bit_set(edx, 31),

			'lahf_lm' : is_bit_set(ecx, 0),
			'cmp_legacy' : is_bit_set(ecx, 1),
			'svm' : is_bit_set(ecx, 2),
			'extapic' : is_bit_set(ecx, 3),
			'cr8_legacy' : is_bit_set(ecx, 4),
			'abm' : is_bit_set(ecx, 5),
			'sse4a' : is_bit_set(ecx, 6),
			'misalignsse' : is_bit_set(ecx, 7),
			'3dnowprefetch' : is_bit_set(ecx, 8),
			'osvw' : is_bit_set(ecx, 9),
			'ibs' : is_bit_set(ecx, 10),
			'xop' : is_bit_set(ecx, 11),
			'skinit' : is_bit_set(ecx, 12),
			'wdt' : is_bit_set(ecx, 13),
			#'reserved' : is_bit_set(ecx, 14),
			'lwp' : is_bit_set(ecx, 15),
			'fma4' : is_bit_set(ecx, 16),
			'tce' : is_bit_set(ecx, 17),
			#'reserved' : is_bit_set(ecx, 18),
			'nodeid_msr' : is_bit_set(ecx, 19),
			#'reserved' : is_bit_set(ecx, 20),
			'tbm' : is_bit_set(ecx, 21),
			'topoext' : is_bit_set(ecx, 22),
			'perfctr_core' : is_bit_set(ecx, 23),
			'perfctr_nb' : is_bit_set(ecx, 24),
			#'reserved' : is_bit_set(ecx, 25),
			#'reserved' : is_bit_set(ecx, 26),
			#'reserved' : is_bit_set(ecx, 27),
			#'reserved' : is_bit_set(ecx, 28),
			#'reserved' : is_bit_set(ecx, 29),
			#'reserved' : is_bit_set(ecx, 30),
			#'reserved' : is_bit_set(ecx, 31)
		}

	# Get a list of only the flags that are true
	extended_flags = [k for k, v in extended_flags.items() if v]
	flags += extended_flags

	flags.sort()
	return flags

def get_processor_brand(max_extension_support):
	processor_brand = ""

	# Processor brand string
	if max_extension_support >= 0x80000004:
		instructions = [
			b"\xB8\x02\x00\x00\x80", # mov ax,0x80000002
			b"\xB8\x03\x00\x00\x80", # mov ax,0x80000003
			b"\xB8\x04\x00\x00\x80"  # mov ax,0x80000004
		]
		for instruction in instructions:
			# EAX
			eax = run_asm(
				instruction,  # mov ax,0x8000000?
				b"\x0f\xa2"   # cpuid
				b"\x89\xC0"   # mov ax,ax
				b"\xC3"       # ret
			)

			# EBX
			ebx = run_asm(
				instruction,  # mov ax,0x8000000?
				b"\x0f\xa2"   # cpuid
				b"\x89\xD8"   # mov ax,bx
				b"\xC3"       # ret
			)

			# ECX
			ecx = run_asm(
				instruction,  # mov ax,0x8000000?
				b"\x0f\xa2"   # cpuid
				b"\x89\xC8"   # mov ax,cx
				b"\xC3"       # ret
			)

			# EDX
			edx = run_asm(
				instruction,  # mov ax,0x8000000?
				b"\x0f\xa2"   # cpuid
				b"\x89\xD0"   # mov ax,dx
				b"\xC3"       # ret
			)

			# Combine each of the 4 bytes in each register into the string
			for reg in [eax, ebx, ecx, edx]:
				for n in [0, 8, 16, 24]:
					processor_brand += chr((reg >> n) & 0xFF)

	return processor_brand[:-1]

def get_cache(max_extension_support):
	cache_info = {}

	# Just return if the cache feature is not supported
	if max_extension_support < 0x80000006:
		return cache_info

	# ECX
	ecx = run_asm(
		b"\xB8\x06\x00\x00\x80"  # mov ax,0x80000006
		b"\x0f\xa2"              # cpuid
		b"\x89\xC8"              # mov ax,cx
		b"\xC3"                   # ret
	)

	cache_info = {
		'size_kb' : ecx & 0xFF,
		'line_size_b' : (ecx >> 12) & 0xF,
		'associativity' : (ecx >> 16) & 0xFFFF
	}

	return cache_info

def get_ticks():
	retval = None

	if bits == '32bit':
		# Works on x86_32
		restype = None
		argtypes = (ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint))
		get_ticks_x86_32, address = asm_func(restype, argtypes,
			[
			b"\x55",         # push bp
			b"\x89\xE5",     # mov bp,sp
			b"\x31\xC0",     # xor ax,ax
			b"\x0F\xA2",     # cpuid
			b"\x0F\x31",     # rdtsc
			b"\x8B\x5D\x08", # mov bx,[di+0x8]
			b"\x8B\x4D\x0C", # mov cx,[di+0xc]
			b"\x89\x13",     # mov [bp+di],dx
			b"\x89\x01",     # mov [bx+di],ax
			b"\x5D",         # pop bp
			b"\xC3"          # ret
			]
		)

		high = ctypes.c_uint32(0)
		low = ctypes.c_uint32(0)

		get_ticks_x86_32(ctypes.byref(high), ctypes.byref(low))
		retval = ((high.value << 32) & 0xFFFFFFFF00000000) | low.value
	elif bits == '64bit':
		# Works on x86_64
		restype = ctypes.c_uint64
		argtypes = ()
		get_ticks_x86_64, address = asm_func(restype, argtypes,
			[
			b"\x48",         # dec ax
			b"\x31\xC0",     # xor ax,ax
			b"\x0F\xA2",     # cpuid
			b"\x0F\x31",     # rdtsc
			b"\x48",         # dec ax
			b"\xC1\xE2\x20", # shl dx,byte 0x20
			b"\x48",         # dec ax
			b"\x09\xD0",     # or ax,dx
			b"\xC3",         # ret
			]
		)
		retval = get_ticks_x86_64()

	return retval

def get_ticks_hz():
	start = get_ticks()

	time.sleep(1)

	end = get_ticks()

	ticks = (end - start)

	return to_friendly_hz(ticks)

def to_friendly_hz(ticks):
	ticks = float(ticks)

	hz_map = [
		{'GHz' : 1000000000.0}, 
		{'MHz' : 1000000.0}, 
		{'KHz' : 1000.0}, 
		{'Hz' : 1.0}
	]

	for pair in hz_map:
		for symbol, place in pair.items():
			if ticks >= place:
				return '{0:.4f} {1}'.format(ticks / place, symbol)

def parse_arch(raw_arch_string):
	arch, bits = None, None

	if re.match('^i\d86$|^x86$|^x86_32$|^i86pc$', raw_arch_string):
		arch = 'x86_32'
		bits = '32'
	elif re.match('^x64$|^x86_64$|^amd64$', raw_arch_string):
		arch = 'x86_64'
		bits = '64'

	return (arch, bits)

def get_cpu_info_from_cpuid():
	'''
	Returns the CPU info gathered by querying the X86 cpuid register.
	Caution: Will only work on X86 CPUs.
	Caution: Will crash python if running under SELinux in enforcing mode.
	'''
	max_extension_support = get_max_extension_support()
	cache_info = get_cache(max_extension_support)
	info = get_info()

	# Get the CPU arch and bits
	raw_arch_string = platform.machine()
	arch, bits = parse_arch(raw_arch_string)

	return {
	'vendor_id' : get_vendor_id(), 
	'processor_brand' : get_processor_brand(max_extension_support), 
	'processor_hz' : get_ticks_hz(), 
	'processor_arch' : arch, 
	'processor_bits' : bits, 
	'processor_count' : multiprocessing.cpu_count(), 
	'processor_raw_arch_string' : raw_arch_string, 

	'l2_cache_size:' : cache_info['size_kb'], 
	'l2_cache_line_size' : cache_info['line_size_b'], 
	'l2_cache_associativity' : hex(cache_info['associativity']), 

	'stepping' : info['stepping'], 
	'model' : info['model'], 
	'family' : info['family'], 
	'processor_type' : info['processor_type'], 
	'extended_model' : info['extended_model'], 
	'extended_family' : info['extended_family'], 
	'flags' : get_flags(max_extension_support)
	}

def get_cpu_info_from_proc_cpuinfo():
	'''
	Returns the CPU info gathered from /proc/cpuinfo. Will return None if
	/proc/cpuinfo is not found.
	'''
	# Just return None if there is no cpuinfo
	if not os.path.exists('/proc/cpuinfo'):
		return None

	output = os.popen('cat /proc/cpuinfo').read()

	flags = output.split('flags		: ')[1].split('\n')[0].split()
	flags.sort()

	vendor_id = output.split('vendor_id	: ')[1].split('\n')[0]
	processor_brand = output.split('model name	: ')[1].split('\n')[0]
	cache_size = output.split('cache size	: ')[1].split('\n')[0]
	stepping = output.split('stepping	: ')[1].split('\n')[0]
	model = output.split('model		: ')[1].split('\n')[0]
	family = output.split('cpu family	: ')[1].split('\n')[0]

	# Convert from MHz string to Hz
	processor_hz = output.split('cpu MHz		: ')[1].split('\n')[0]
	processor_hz = float(processor_hz) * 1000000.0
	processor_hz = to_friendly_hz(processor_hz)

	# Get the CPU arch and bits
	raw_arch_string = platform.machine()
	arch, bits = parse_arch(raw_arch_string)

	return {
	'vendor_id' : vendor_id, 
	'processor_brand' : processor_brand, 
	'processor_hz' : processor_hz, 
	'processor_arch' : arch, 
	'processor_bits' : bits, 
	'processor_count' : multiprocessing.cpu_count(), 
	'processor_raw_arch_string' : raw_arch_string, 

	'l2_cache_size:' : cache_size, 
	'l2_cache_line_size' : 0, 
	'l2_cache_associativity' : 0, 

	'stepping' : stepping, 
	'model' : model, 
	'family' : family, 
	'processor_type' : 0, 
	'extended_model' : 0, 
	'extended_family' : 0, 
	'flags' : flags
	}

def get_cpu_info_from_registry():
	'''
	FIXME: Is missing many of the newer CPU flags like sse3
	Returns the CPU info gathered from the Windows Registry. Will return None if
	not on Windows.
	'''
	# Just return None if not on Windows
	if not is_windows:
		return None

	import _winreg

	# Get the CPU arch and bits
	key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment")
	raw_arch_string = _winreg.QueryValueEx(key, "PROCESSOR_ARCHITECTURE")[0]
	_winreg.CloseKey(key)
	arch, bits = parse_arch(raw_arch_string)

	# Get the CPU MHz
	key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, r"Hardware\Description\System\CentralProcessor\0")
	processor_hz = _winreg.QueryValueEx(key, "~Mhz")[0]
	_winreg.CloseKey(key)

	# Get the CPU name
	key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, r"Hardware\Description\System\CentralProcessor\0")
	processor_brand = _winreg.QueryValueEx(key, "ProcessorNameString")[0]
	_winreg.CloseKey(key)

	# Get the CPU vendor id
	key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, r"Hardware\Description\System\CentralProcessor\0")
	vendor_id = _winreg.QueryValueEx(key, "VendorIdentifier")[0]
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

	return {
	'vendor_id' : vendor_id, 
	'processor_brand' : processor_brand, 
	'processor_hz' : processor_hz, 
	'processor_arch' : arch, 
	'processor_bits' : bits, 
	'processor_count' : multiprocessing.cpu_count(), 
	'processor_raw_arch_string' : raw_arch_string, 

	'l2_cache_size:' : 0, 
	'l2_cache_line_size' : 0, 
	'l2_cache_associativity' : 0, 

	'stepping' : 0, 
	'model' : 0, 
	'family' : 0, 
	'processor_type' : 0, 
	'extended_model' : 0, 
	'extended_family' : 0, 
	'flags' : flags
	}

def get_cpu_info():
	info = None

	# Try the Windows registry
	if is_windows:
		info = get_cpu_info_from_registry()
	# Try /proc/cpuinfo
	elif not info:
		info = get_cpu_info_from_proc_cpuinfo()
	# Try querying the CPU cpuid register
	elif not info:
		info = get_cpu_info_from_cpuid()

	return info
'''
info = get_cpu_info_from_proc_cpuinfo()
print(info['vendor_id'])
print(info['processor_brand'])
print(info['processor_hz'])
print(info['processor_arch'])
print(info['processor_bits'])
print(info['processor_count'])
print(info['processor_raw_arch_string'])


info = get_cpu_info_from_cpuid()
print(info['vendor_id'])
print(info['processor_brand'])
print(info['processor_hz'])
print(info['processor_arch'])
print(info['processor_bits'])
print(info['processor_count'])
print(info['processor_raw_arch_string'])
'''

