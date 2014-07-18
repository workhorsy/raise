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


import os
import re
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

def _get_best_match(names, desired):
	'''
	Will match files with this priority:
	1. Exact match
	2. Exact match different capitalization
	3. Matches start or end
	4. Matches start or end different capitalization
	'''

	# 1. Exact match
	for name in names:
		if name == desired:
			return name

	# 2. Exact match different capitalization
	for name in names:
		if name.lower() == desired.lower():
			return name

	# 3. Matches start or end
	for name in names:
		if name.startswith(desired) or name.endswith(desired):
			return name

	# 4. Matches start or end different capitalization
	for name in names:
		if name.lower().startswith(desired.lower()) or name.lower().endswith(desired.lower()):
			return name

	return None

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

	# Try finding with dpkg
	if not files:
		files = _get_library_files_from_dpkg(lib_name, version_cb)

	# Try finding with rpm
	if not files:
		files = _get_library_files_from_rpm(lib_name, version_cb)

	# Try finding with pacman
	if not files:
		files = _get_library_files_from_pacman(lib_name, version_cb)

	# Try finding with slackware
	if not files:
		files = _get_library_files_from_slackware(lib_name, version_cb)

	# Try finding with portage
	if not files:
		files = _get_library_files_from_portage(lib_name, version_cb)

	# Try finding with pkg_info
	if not files:
		files = _get_library_files_from_pkg_info(lib_name, version_cb)

	# Try finding with ports
	if not files:
		files = _get_library_files_from_ports(lib_name, version_cb)

	# Try finding with pkg-config
	if not files:
		files = _get_library_files_from_pkg_config(lib_name, version_cb)
	
	# Try finding with the file system. But only if there is no version requirement.
	if not version_cb and not files:
		files = _get_library_files_from_fs(lib_name)

	# Save the file names in the cache
	if files:
		lib_file_cache[search_param] = files

	return files

def _get_library_files_from_pkg_config(lib_name, version_cb = None):
	matching_files = []
	lib_name = lib_name.lstrip('lib')

	# Just return if there is no pkg-config
	if not program_paths('pkg-config'):
		return matching_files

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

def _get_library_files_from_ports(lib_name, version_cb = None):
	matching_files = []
	lib_name = lib_name.lstrip('lib')

	# Just return if there is no port
	if not program_paths('port'):
		return matching_files

	# Find all packages that contain the name
	result = Process.run_and_get_stdout("port list | grep -i {0}".format(lib_name))
	if not result:
		return matching_files

	# For each package
	for package in result.split("\n"):
		# Get the name
		name = package.split()[0]

		# Skip if the library name is not in the package name
		if not lib_name.lower() in name.lower():
			continue

		# Skip if not a devel package
		if not package.split()[2].startswith('devel/'):
			continue

		# Get the version
		version = package.split()[1].lstrip('@')
		if not version:
			continue
		version = Helpers.version_string_to_tuple(version)

		# Skip if the version does not match
		if version_cb and not version_cb(version):
			continue

		# Get the files and skip if there are none
		library_files = Process.run_and_get_stdout("port contents {0}".format(name))
		if not library_files:
			continue

		# Get the valid files
		for entry in library_files.split("\n"):
			entry = entry.strip()
			if os.path.isfile(entry):
				matching_files.append(entry)

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

def _get_library_files_from_pacman(lib_name, version_cb = None):
	matching_files = []
	lib_name = lib_name.lstrip('lib')

	# Just return if there is no pacman
	if not program_paths('pacman'):
		return matching_files

	# Find all packages that contain the name
	result = Process.run_and_get_stdout("pacman -Sl | grep -i {0}".format(lib_name))
	if not result:
		return matching_files

	# Get the best package name
	packages = [p.split()[1] for p in result.split("\n")]
	best_name = _get_best_match(packages, lib_name)
	if not best_name:
		return matching_files

	# For each package
	for package in result.split("\n"):
		# Get the name
		name = package.split()[1]

		# Skip this package if it is not the best name
		if not best_name == name:
			continue

		# Skip this package if the library name is not in the package name
		if not lib_name.lower() in name.lower():
			continue

		# Get the version
		version = package.split()[2]
		version = version.split('-')[0]
		version = Helpers.version_string_to_tuple(version)

		# Skip this package if the version does not match
		if version_cb and not version_cb(version):
			continue

		# Get the library files
		result = Process.run_and_get_stdout('pacman -Ql {0}'.format(name))
		if not result:
			continue

		# Save all the files
		for entry in result.split("\n"):
			entry = entry.split()[1]
			if os.path.isfile(entry):
				matching_files.append(entry)

	return matching_files

def _get_library_files_from_dpkg(lib_name, version_cb = None):
	matching_files = []

	# Just return if there is no dpkg
	if not program_paths('dpkg'):
		return matching_files

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

	# Just return if there is no rpm
	if not program_paths('rpm'):
		return matching_files

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
		name = Helpers.between(result, 'Name        : ', '\n')
		version = Helpers.between(result, 'Version     : ', '\n')
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

	# Just return if there is not pkg_info
	if not program_paths('pkg_info'):
		return matching_files

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

def _get_library_files_from_slackware(lib_name, version_cb = None):
	matching_files = []
	lib_name = lib_name.lstrip('lib')

	# Just return if there is no package info
	if not os.path.isdir('/var/log/packages'):
		return matching_files

	# Get a list of all the installed packages
	result = Process.run_and_get_stdout("ls /var/log/packages | grep -i {0}".format(lib_name))
	if not result:
		return matching_files

	# For each package
	for package in result.split("\n"):
		# Get the metadata for this package
		result = Process.run_and_get_stdout("cat /var/log/packages/{0}".format(package))

		# Get the name (Everything before the version number)
		name = []
		for n in package.split('-'):
			if re.match('^(\d|\.)+$', n):
				break
			name.append(n)
		name = str.join('-', name)

		# Get the version
		version = None
		for n in package.split('-'):
			if re.match('^(\d|\.)+$', n):
				version = n
				break
		version = Helpers.version_string_to_tuple(version)

		# Skip this package if the version does not match
		if version_cb and not version_cb(version):
			continue

		# Skip this package if the library name is not in the package name
		if not lib_name.lower() in name.lower():
			continue

		# Get the files
		for entry in Helpers.after(result, 'FILE LIST:').split("\n"):
			entry = '/' + entry
			if os.path.isfile(entry):
				matching_files.append(entry)

	return matching_files

def _get_library_files_from_portage(lib_name, version_cb = None):
	matching_files = []

	# Just return if there is not portage
	if not program_paths('qlist'):
		return matching_files

	# Find all the packages that contain the name
	result = Process.run_and_get_stdout("qlist -C -I -v | grep -i {0}".format(lib_name))
	if not result:
		return matching_files

	# For each package
	for package in result.split("\n"):
		# Get the name (Everything before the version number)
		name = []
		for n in package.split('-'):
			if re.match('^(\d|\.)+$', n):
				break
			name.append(n)
		name = str.join('-', name)
		name = Helpers.after(name, '/')

		# Get the version
		version = None
		for n in package.split('-'):
			if re.match('^(\d|\.)+$', n):
				version = n
				break
		version = Helpers.version_string_to_tuple(version)

		# Skip this package if the version does not match
		if version_cb and not version_cb(version):
			continue

		# Skip this package if the library name is not in the package name
		if not lib_name.lower() in name.lower():
			continue

		# Get the files
		result = Process.run_and_get_stdout("qlist -C {0}".format(name))
		if not result:
			continue

		for entry in result.split("\n"):
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
	exts = []
	if 'PATHEXT' in os.environ:
		exts = os.environ['PATHEXT'].split(os.pathsep)

	path = os.environ['PATH']
	for p in os.environ['PATH'].split(os.pathsep):
		full_name = os.path.join(p, program_name)

		# Save the path if it is executable
		if os.access(full_name, os.X_OK) and not os.path.isdir(full_name):
			paths.append(full_name)
		# Save the path if we found one with a common extension like .exe
		for e in exts:
			full_name_ext = full_name + e

			if os.access(full_name_ext, os.X_OK) and not os.path.isdir(full_name_ext):
				paths.append(full_name_ext)
	return paths

def require_environmental_variable(env_name, version_cb = None):
	Print.status("Checking for environmental variable '{0}'".format(env_name))

	if not os.environ.get(env_name):
		message = "The environmental variable '{0}' was not found. Set it and try again."
		Print.fail()
		Print.exit(message.format(env_name))
	else:
		Print.ok()

