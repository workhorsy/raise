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
import lib_raise_config as Config
import lib_raise_terminal as Print
import lib_raise_process as Process
import lib_raise_helpers as Helpers


lib_file_cache = {}


# Returns all the paths that libraries are installed in
def _get_all_library_paths():
	paths = ['/usr/lib', '/usr/local/lib',
			'/usr/include', '/usr/local/include']
	if not os.path.exists('/etc/ld.so.conf.d/'):
		return paths

	for file_name in os.listdir('/etc/ld.so.conf.d/'):
		f = open('/etc/ld.so.conf.d/' + file_name, 'r')
		for path in f.readlines():
			path = path.strip()
			if os.path.exists(path) and not path in paths:
				paths.append(path)

	return paths

def _get_matched_file_from_library_files(library_name, extension, library_files):
	'''
	Will match files with this priority:
	1. Exact match after last path separator
	2. Exact match different capitalization after last path separator
	3. Matches ending
	4. Matches ending with different capitalization
	'''
	library_name = library_name.lstrip('lib')

	# 1. Exact match after last path separator
	desired_name = '{0}{1}'.format(library_name, extension)
	for entry in library_files:
		file_name = os.path.basename(entry)
		if file_name == desired_name:
			return entry

	# 2. Exact match different capitalization after last path separator
	desired_name = '{0}{1}'.format(library_name, extension).lower()
	for entry in library_files:
		file_name = os.path.basename(entry).lower()
		if file_name == desired_name:
			return entry

	# 3. Matches ending
	desired_name = '{0}{1}'.format(library_name, extension)
	for entry in library_files:
		file_name = os.path.basename(entry)
		if file_name.endswith(desired_name):
			return entry

	# 4. Matches ending with different capitalization
	desired_name = '{0}{1}'.format(library_name, extension).lower()
	for entry in library_files:
		file_name = os.path.basename(entry).lower()
		if file_name.endswith(desired_name):
			return entry

	return None

# FIXME: Make it work with other packaging systems:
# http://en.wikipedia.org/wiki/List_of_software_package_management_systems
# Returns the full path of a library file or None
def _get_library_files(lib_name, version_str = None):
	global lib_file_cache
	files = []

	# Create a version_cb from the string
	version_cb = None
	if version_str:
		version_cb = Helpers.to_version_cb(version_str)

	# Return the file names if already cached
	search_param = (version_str, lib_name)
	if search_param in lib_file_cache:
		return lib_file_cache[search_param]

	# Try finding the library with dpkg
	if not files and program_paths('dpkg'):
		files = _get_library_files_from_dpkg(lib_name, version_cb)

	# Try finding the library with rpm
	if not files and program_paths('rpm'):
		files = _get_library_files_from_rpm(lib_name, version_cb)

	# Try finding the library with pkg_info
	if not files and program_paths('pkg_info'):
		files = _get_library_files_from_pkg_info(lib_name, version_cb)

	# Try finding the library with pkg-config
	if not files and program_paths('pkg-config'):
		files = _get_library_files_from_pkg_config(lib_name, version_cb)

	# Try finding the library in the file system. But only if there is no version requirement.
	if not version_cb and not files:
		files = _get_library_files_from_fs(lib_name)

	# Save the file names in the cache
	if files:
		lib_file_cache[search_param] = files

	return files

def _get_library_files_from_pkg_config(lib_name, version_cb = None):
	matching_files = []
	lib_name = lib_name.lstrip('lib')

	# Find all packages that contain the name
	result = Process.run_and_get_stdout("pkg-config --list-all | grep -i {0}".format(lib_name))
	if not result:
		return matching_files

	# For each package
	for package in result.split("\n"):
		# Get the name
		name = package.split()[0]

		# Skip this package if the library name is not in the package name
		if not lib_name.lower() in name.lower():
			continue

		# Get the version, libdir, and includedir
		version = Process.run_and_get_stdout("pkg-config --modversion {0}".format(name))
		libdir = Process.run_and_get_stdout("pkg-config --variable=libdir {0}".format(name))
		includedir = Process.run_and_get_stdout("pkg-config --variable=includedir {0}".format(name))
		if not version or not libdir or not includedir:
			continue
		version = Helpers.version_string_to_tuple(version)

		# Skip this package if the version does not match
		if version_cb and not version_cb(version):
			continue

		# Get the library files in those directories
		for d in [libdir, includedir]:
			for root, dirs, files in os.walk(d):
				for entry in files:
					# Get the whole file name
					f = os.path.join(root, entry)

					# Save the file if the name is in the root
					if lib_name.lower() in root.lower():
						matching_files.append(f)
					# Save the file if the lib name is in the file
					elif 'lib' + lib_name.lower() in entry.lower():
						matching_files.append(f)

	return matching_files

def _get_library_files_from_fs(lib_name):
	matching_files = []
	lib_name = lib_name.lstrip('lib')

	for path in _get_all_library_paths():
		for root, dirs, files in os.walk(path):
			for entry in files:
				# Get the whole file name
				f = os.path.join(root, entry)
				if lib_name in f and os.path.isfile(f):
					matching_files.append(f)

	return matching_files

def _get_library_files_from_dpkg(lib_name, version_cb = None):
	matching_files = []

	# Find all packages that contain the name
	result = Process.run_and_get_stdout("dpkg --list | grep -i {0}".format(lib_name))
	if not result:
		return matching_files

	# For each package
	for package in result.split("\n"):
		# Get the name and version
		name = Helpers.before(package.split()[1], ':')
		version = Helpers.between_last(package.split()[2], ':', '-')
		version = Helpers.version_string_to_tuple(version)

		# Skip this package if the library name is not in the package name
		if not lib_name.lower() in name.lower():
			continue

		# Skip this package if the version does not match
		if version_cb and not version_cb(version):
			continue

		# Get all the files and directories
		result = Process.run_and_get_stdout("dpkg -L {0}".format(name))
		if not result:
			continue

		# Save all the files
		library_entries = result.split("\n")
		for entry in library_entries:
			if os.path.isfile(entry):
				matching_files.append(entry)

	return matching_files

def _get_library_files_from_rpm(lib_name, version_cb = None):
	lib_name = lib_name.lstrip('lib')
	matching_files = []

	# Find all packages that contain the name
	result = Process.run_and_get_stdout("rpm -qa | grep -i {0}".format(lib_name))
	if not result:
		return matching_files

	# For each package
	for package in result.split("\n"):
		# Get the name and version
		result = Process.run_and_get_stdout("rpm -qi {0}".format(package))
		if not result:
			continue
		name = Helpers.between_last(result, 'Name        : ', '\n')
		version = Helpers.between_last(result, 'Version     : ', '\n')
		version = Helpers.version_string_to_tuple(version)

		# Skip this package if the library name is not in the package name
		if not lib_name.lower() in name.lower():
			continue

		# Skip this package if the version does not match
		if version_cb and not version_cb(version):
			continue

		# Get all the files and directories
		result = Process.run_and_get_stdout("rpm -ql {0}".format(package))
		if not result:
			continue

		# Save all the files
		library_entries = result.split("\n")
		for entry in library_entries:
			if os.path.isfile(entry):
				matching_files.append(entry)

	return matching_files

def _get_library_files_from_pkg_info(lib_name, version_cb = None):
	lib_name = lib_name.lstrip('lib')
	matching_files = []

	# Find all packages that contain the name
	result = Process.run_and_get_stdout("pkg_info | grep -i {0}".format(lib_name))
	if not result:
		return matching_files

	# For each package
	for package in result.split("\n"):
		# Get the name and version
		name = package.split()[0]
		version = Helpers.before(name.split('-')[-1], '_')
		version = Helpers.version_string_to_tuple(version)

		# Skip this package if the library name is not in the package name
		if not lib_name.lower() in name.lower():
			continue

		# Skip this package if the version does not match
		if version_cb and not version_cb(version):
			continue

		# Get all the files and directories
		result = Process.run_and_get_stdout("pkg_info -L {0}".format(name))
		if not result:
			continue

		# Save all the files
		library_entries = result.split("\n")
		for entry in library_entries:
			if os.path.isfile(entry):
				matching_files.append(entry)

	return matching_files

def get_header_file(header_name, version_str = None):
	library_files = _get_library_files(header_name, version_str)
	header_file = _get_matched_file_from_library_files(header_name, '.h', library_files)
	return header_file

def get_static_library(lib_name, version_str = None):
	library_files = _get_library_files(lib_name, version_str)
	static_file = _get_matched_file_from_library_files(lib_name, '.a', library_files)
	return static_file

def get_shared_library(lib_name, version_str = None):
	library_files = _get_library_files(lib_name, version_str)
	shared_file = _get_matched_file_from_library_files(lib_name, '.so', library_files)
	return shared_file

def require_header_file(header_name, version_str = None):
	Print.status("Checking for header file '{0}'".format(header_name))

	# If the header is not installed, make them install it to continue
	if not get_header_file(header_name, version_str):
		ver = "(Any version)"
		if version_str:
			ver = version_str

		message = "Header file '{0} {1}' not installed. Install and try again."
		Print.fail()
		Print.exit(message.format(header_name, ver))
	else:
		Print.ok()

def require_static_library(lib_name, version_str = None):
	Print.status("Checking for static library '{0}'".format(lib_name))

	# If the static library is not installed, make them install it to continue
	if not get_static_library(lib_name, version_str):
		# Get the version requirement lambda as a printable string
		ver = "(Any version)"
		if version_str:
			ver = version_str

		message = "Static library '{0} {1}' not installed. Install and try again."
		Print.fail()
		Print.exit(message.format(lib_name, ver))
	else:
		Print.ok()

def require_shared_library(lib_name, version_str = None):
	Print.status("Checking for shared library '{0}'".format(lib_name))

	# If the shared library is not installed, make them install it to continue
	if not get_shared_library(lib_name, version_str):
		# Get the version requirement lambda as a printable string
		ver = "(Any version)"
		if version_str:
			ver = version_str

		message = "Shared library '{0} {1}' not installed. Install and try again."
		Print.fail()
		Print.exit(message.format(lib_name, ver))
	else:
		Print.ok()

def require_static_or_shared_library(lib_name, version_str = None):
	Print.status("Checking for static/shared library '{0}'".format(lib_name))

	shared_file = get_shared_library(lib_name, version_str)
	static_file = get_shared_library(lib_name, version_str)

	# Make them install the lib if neither was found
	if not shared_file and not static_file:
		# Get the version requirement lambda as a printable string
		ver = "(Any version)"
		if version_str:
			ver = version_str

		message = "Shared/Static library '{0} {1}' not installed. Install and try again."
		Print.fail()
		Print.exit(message.format(lib_name, ver))
	else:
		Print.ok()

def header_path(header_name):
	retval = None

	# Get any paths that contain the library name
	paths = []
	include_paths = [
		"/usr/include", 
		"/usr/local/include"
	]
	for include_path in include_paths:
		for root, dirs, files in os.walk(include_path):
			for file_name in files:
				complete_name = os.path.join(root, file_name)
				if complete_name.endswith(header_name):
					paths.append(complete_name)

	# Of those paths, get the ones that match the architecture
	for path in paths:
		if 'lib' + CPU.bits in path or CPU.arch in path:
			retval = path

	# If none were matched specifically from the architecture
	# Use the first
	if retval == None and paths:
		retval = paths[0]

	# Make sure a header file was found
	if not retval or not os.path.exists(retval):
		raise Exception("Header file not found: '" + header_name + "'")

	i = retval.rfind('/') + 1
	return retval[:i]

def header_paths(header_names):
	paths = []
	for header_name in header_names:
		paths.append(header_path(header_name))

	return paths

def include_path(header_name):
	return '-I' + header_path(header_name)

def include_paths(header_names):
	paths = []
	for header_name in header_names:
		paths.append(include_path(header_name))
	return str.join(' ', paths)

def static_or_shared_library_path(lib_name):
	path = get_static_library(lib_name)
	if path:
		return path

	path = get_shared_library(lib_name)
	if path:
		return path

	raise Exception("Static/Shared library not found: '" + lib_name + "'")

def require_programs(prog_names):
	for prog_name in prog_names:
		Print.status("Checking for program '{0}'".format(prog_name))
		if len(program_paths(prog_name)):
			Print.ok()
		else:
			Print.fail()
			Print.exit("Install the program '{0}' and try again.".format(prog_name))

def program_paths(program_name):
	paths = []
	exts = filter(None, os.environ.get('PATHEXT', '').split(os.pathsep))
	path = os.environ['PATH']
	for p in os.environ['PATH'].split(os.pathsep):
		p = os.path.join(p, program_name)
		# Save the path if it is executable
		if os.access(p, os.X_OK) and not os.path.isdir(p):
			paths.append(p)
		# Save the path if we found one with a common extension like .exe
		for e in exts:
			pext = p + e
			if os.access(pext, os.X_OK) and not os.path.isdir(pext):
				paths.append(pext)
	return paths



