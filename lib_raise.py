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

import os, sys, platform
import tempfile, shutil, filecmp
import multiprocessing, subprocess
import signal, atexit
import re
import time
import traceback, inspect
from collections import namedtuple

lib_file_cache = {}

def early_exit(message):
	sys.stdout.write('{0} Exiting ...\n'.format(message))
	sys.stdout.flush()
	exit()

# Make sure we are in at least python 2.6
if sys.version_info < (2, 6):
	early_exit("Python 2.6 or greater is required.")

def before(s, n):
	i = s.find(n)
	if i == -1:
		return s
	else:
		return s[0 : i]

def after(s, n):
	i = s.find(n)
	if i == -1:
		return s
	else:
		return s[i+len(n) : ]

def between(s, l, r):
	return before(after(s, l), r)

def version_string_to_tuple(version_string):
	# Get the version number
	Version = namedtuple('Version', 'major minor micro')
	major, minor, micro = 0, 0, 0
	try:
		version = version_string.split('.')
		major = int(version[0])
		minor = int(version[1])
		micro = int(version[2])
	except Exception as e:
		pass
	return Version(major, minor, micro)

def expand_envs(string):
	while True:
		before = string
		string = os.path.expandvars(string)
		if before == string:
			return string

# FIXME: Update so config does not know about any module specific information
class Config(object):
	modules = []
	target_name = None
	message_length = None
	c_compilers = {}
	linkers = {}
	cxx_compilers = {}
	d_compilers = {}
	cs_compilers = {}
	_cc = None
	_cxx = None
	_dc = None
	_csc = None
	_linker = None

	@classmethod
	def init(cls):
		# Get the path of the rscript file
		cls.pwd = os.sys.path[0]

		# Get the name of the current running python program
		cls.python = sys.executable
		if not cls.python:
			early_exit('Could not find python to run child processes with.')

		# Figure out the CPU architecture
		if re.match('^i\d86$|^x86$|^x86_32$|^i86pc$', platform.machine()):
			cls._arch = 'x86_32'
			cls._bits = '32'
		elif re.match('^x86$|^x86_64$|^amd64$', platform.machine()):
			cls._arch = 'x86_64'
			cls._bits = '64'
		else:
			early_exit('Unknown architecture {0}.'.format(platform.machine()))

		# Figure out how many cpus there are
		cls._cpus_total = multiprocessing.cpu_count()
		cls._cpus_free = cls._cpus_total

		# Figure out the general OS type
		if 'cygwin' in platform.system().lower():
			cls._os_type = OSType(
				name =                 'Cygwin', 
				exe_extension =        '', 
				object_extension =     '.o', 
				shared_lib_extension = '.so', 
				static_lib_extension = '.a'
			)
		elif 'windows' in platform.system().lower():
			cls._os_type = OSType(
				name =                 'Windows', 
				exe_extension =        '.exe', 
				object_extension =     '.obj', 
				shared_lib_extension = '.dll', 
				static_lib_extension = '.lib'
			)
		else:
			cls._os_type = OSType(
				name =                 'Unix', 
				exe_extension =        '', 
				object_extension =     '.o', 
				shared_lib_extension = '.so', 
				static_lib_extension = '.a'
			)

		# Figure out how to clear the terminal
		if cls._os_type._name == 'Windows':
			cls._terminal_clear = 'cls'
		else:
			cls._terminal_clear = 'clear'

		# FIXME: Have this look for stty first then try the registry
		# Figure out the terminal width
		if cls._os_type._name == 'Windows':
			import _winreg
			key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, r"Console")
			val = _winreg.QueryValueEx(key, "ScreenBufferSize")
			_winreg.CloseKey(key)
			size = hex(val[0])
			cls._terminal_width = int('0x' + size[-4 : len(size)], 16)
		else:
			cls._terminal_width = int(os.popen('stty size', 'r').read().split()[1])

		# Make sure Windows SDK tools are found
		if cls._os_type._name == 'Windows':
			if not 'WINDOWSSDKDIR' in os.environ and not 'WINDOWSSDKVERSIONOVERRIDE' in os.environ:
				early_exit('Windows SDK not found. Must be run from Windows SDK Command Prompt.')

class OSType(object):
	def __init__(self, name, exe_extension, object_extension, 
				shared_lib_extension, static_lib_extension):

		self._name = name
		self._exe_extension = exe_extension
		self._object_extension = object_extension
		self._shared_lib_extension = shared_lib_extension
		self._static_lib_extension = static_lib_extension


def get_normal_user_name():
	# Get the name from the environmental variable
	user_name = \
		os.getenv('SUDO_USER') or \
		os.getenv('USER') or \
		os.getenv('LOGNAME')

	# Make sure we got a name
	if not user_name:
		print_exit('Failed to get the normal user name.')

	return user_name

def get_normal_user_id():
	user_name = get_normal_user_name()
	return int(os.popen('id -u {0}'.format(user_name)).read())


def do_as_normal_user(cb):
	prev_id = -1

	# Change the user to the normal user
	if not Config._os_type._name in ['Windows', 'Cygwin']:
		prev_id = os.geteuid()
		user_id = get_normal_user_id()
		os.setegid(user_id)
		os.seteuid(user_id)

	# Run the cb as the normal user
	exception = False
	is_exiting = False
	try:
		cb()
	except SystemExit as err:
		# Don't save any exit() exceptions. Just exit
		is_exiting = True
	except Exception as err:
		exception = traceback.format_exc()
	except StandardError as err:
		exception = traceback.format_exc()
	except BaseException as err:
		exception = traceback.format_exc()
	finally:
		# Return the user to normal
		if not Config._os_type._name in ['Windows', 'Cygwin']:
			os.setegid(prev_id)
			os.seteuid(prev_id)

	if is_exiting:
		exit()
	if exception:
		print_exit(exception)

class Emoticons:
	SMILE = ':)'
	NORMAL = ':\\'
	FROWN = ':('

class BGColors:
	MESSAGE = '\033[44m\033[37m'
	OK = '\033[42m\033[37m'
	WARNING = '\033[43m\033[30m'
	FAIL = '\033[41m\033[37m'
	ENDC = '\033[0m'

def terminal_pad(length, pad_char=' '):
	width = Config._terminal_width

	if length > (width-3):
		i = int(width * (int(length / width) + 1)) - 3
	else:
		i = width - 3
	return ''.ljust(i-length, pad_char)

def print_info(message):
	sys.stdout.write('{0}{1}{2}\n'.format(BGColors.MESSAGE, message, BGColors.ENDC))
	sys.stdout.flush()

def print_status(message):
	message = '{0} ...'.format(message)
	Config.message_length = len(message)

	sys.stdout.write(message)
	sys.stdout.flush()

def print_ok():
	padding = terminal_pad(Config.message_length)
	message = "{0}{1}{2}{3}\n".format(padding, BGColors.OK, Emoticons.SMILE, BGColors.ENDC)
	Config.message_length = 0

	sys.stdout.write(message)
	sys.stdout.flush()

def print_warning(post_message=None):
	padding = terminal_pad(Config.message_length, '.')
	message = "{0}{1}{2}{3}\n".format(padding, BGColors.WARNING, Emoticons.NORMAL, BGColors.ENDC)
	if post_message:
		message += post_message + "\n"
	Config.message_length = 0

	sys.stdout.write(message)
	sys.stdout.flush()

def print_fail(post_fail_message=None):
	padding = terminal_pad(Config.message_length, '.')
	message = "{0}{1}{2}{3}\n".format(padding, BGColors.FAIL, Emoticons.FROWN, BGColors.ENDC)
	if post_fail_message:
		message += post_fail_message + "\n"
	Config.message_length = 0

	sys.stdout.write(message)
	sys.stdout.flush()

def print_exit(message):
	message = '{0}{1} Exiting ...{2}\n'.format(BGColors.FAIL, message, BGColors.ENDC)

	sys.stdout.write(message)
	sys.stdout.flush()
	exit()


class ProcessRunner(object):
	def __init__(self, command):
		if Config._os_type._name == 'Windows':
			# Remove starting ./
			if command.startswith('./'):
				command = command[2 :]
			# Replace ${BLAH} with %BLAH%
			command = command.replace('${', '%').replace('}', '%')

		self._command = command
		self._process = None
		self._return_code = None
		self._stdout = None
		self._stderr = None
		self._status = None

	def run(self):
		# Recursively expand all environmental variables
		env = {}
		for key, value in os.environ.items():
			env[key] = expand_envs(value)

		# Start the process and save the output
		self._process = subprocess.Popen(
			self._command, 
			stderr = subprocess.PIPE, 
			stdout = subprocess.PIPE, 
			shell = True, 
			env = env
		)

	def wait(self):
		# Wait for the process to exit
		self._process.wait()

		# Get the return code
		self._return_code = self._process.returncode

		# Get the standard out and error text
		self._stderr  = self._process.stderr.read().rstrip()
		self._stdout = self._process.stdout.read().rstrip()
		try:
			self._stderr = str(self._stderr, 'UTF-8')
		except Exception as err:
			pass
		try:
			self._stdout = str(self._stdout, 'UTF-8')
		except Exception as err:
			pass

		# :( Failure
		if self._return_code:
			self._status = Emoticons.FROWN
		else:
			# :\ Warning
			if len(self._stderr):
				self._status = Emoticons.NORMAL
			# :) Success
			else:
				self._status = Emoticons.SMILE

	def get_is_done(self):
		# You have to poll a process to update the retval. Even if it has stopped already
		if self._process.returncode == None:
			self._process.poll()
		return self._process.returncode != None
	is_done = property(get_is_done)

	def get_is_success(self):
		self._require_wait()
		return self._status == Emoticons.SMILE
	is_success = property(get_is_success)

	def get_is_warning(self):
		self._require_wait()
		return self._status == Emoticons.NORMAL
	is_warning = property(get_is_warning)

	def get_is_failure(self):
		self._require_wait()
		return self._status == Emoticons.FROWN
	is_failure = property(get_is_failure)

	def get_stderr(self):
		self._require_wait()
		return self._stderr
	stderr = property(get_stderr)

	def get_stdout(self):
		self._require_wait()
		return self._stdout
	stdout = property(get_stdout)

	def get_stdall(self):
		self._require_wait()
		return self._stdout + '\n' + self._stderr
	stdall = property(get_stdall)

	def _require_wait(self):
		if self._return_code == None:
			raise Exception("Wait needs to be called before any info on the process can be gotten.")


class Event(object):
	is_parallel = False
	is_first_parallel = False
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
		# Show the parallel header
		if Event.is_parallel:
			if Event.is_first_parallel:
				Event.is_first_parallel = False
				sys.stdout.write("{0} {1} in parallel ...\n".format(self._task, self._plural))
				sys.stdout.flush()
				Config.message_length = 0

		# Run the setup function
		if not self._setup_cb():
			return False

		# Show the serial message
		if not Event.is_parallel:
			print_status("{0} {1} '{2}'".format(self._task, self._singular, self._result))

		# Start the process
		self._runner = ProcessRunner(self._command)
		self._status = 'running'
		self._runner.run()
		return True

	def wait(self):
		# Wait for the process to complete
		self._runner.wait()

		# Display the message
		if Event.is_parallel:
			print_status("   '{0}'".format(self._result))

		# Success or failure
		if self._runner.is_success:
			print_ok()
			self._status = 'success'
		elif self._runner.is_warning:
			print_warning(self._runner.stderr)
			self._status = 'success'
		else:
			print_fail(self._runner.stdall)
			print_exit("{0} failed. Try again.".format(self._task))
			self._status = 'failure'

def add_event(event):
	Event.events.append(event)

	# If not parallel, run the event now
	if not Event.is_parallel:
		parallel_end()

def parallel_start():
	Event.is_parallel = True
	Event.is_first_parallel = True

def parallel_end():
	ready_events = Event.events
	running_events = []

	while len(ready_events) or len(running_events):
		# Check for events that are done
		for event in running_events[:]:
			# Check if it is done
			if event.is_done:
				event.wait()

			# Success. Keep going
			if event._status == 'success':
				running_events.remove(event)
				Config._cpus_free += 1
			# Failure. Stop events and exit
			elif event._status == 'failure':
				print_exit("Event failed.")

		# Check for events that need to start
		while Config._cpus_free > 0 and len(ready_events):
			event = ready_events.pop()
			if event.run():
				Config._cpus_free -= 1
				running_events.insert(0, event)

		# Sleep if all the cpu cores are busy, or have already started
		if Config._cpus_free == 0 or len(ready_events) == 0:
			time.sleep(0.1)

	# Clear all the events
	Config._cpus_free = Config._cpus_total
	Event.events = []
	Event.is_parallel = False
	Event.is_first_parallel = False

def self_deleting_named_temporary_file():
	f = tempfile.NamedTemporaryFile(delete=False)
	f.close()

	def cb():
		if os.path.exists(f.name):
			os.unlink(f.name)

	atexit.register(cb)

	return f

def require_root():
	is_root = False

	# Cygwin
	if Config._os_type._name == 'Cygwin':
		# Cygwin has no root user
		is_root = True
	# Windows
	elif Config._os_type._name == 'Windows':
		try:
			# Only Admin can read the C:\windows\temp
			sys_root = os.environ.get('SystemRoot', 'C:\windows')
			temp = os.listdir(os.path.join(sys_root, 'temp'))
			is_root = True
		except:
			pass
	# Linux / Unix
	elif os.getuid() == 0:
		is_root = True

	# Make sure we are root
	if not is_root:
		print_exit("Must be run as root.")

def require_not_root():
	# On Windows/Cygwin it does not matter if we are root. So just return
	if Config._os_type._name in ['Windows', 'Cygwin']:
		return

	# Make sure we are NOT root
	if os.getuid() == 0:
		print_exit("Must not be run as root.")

def call_on_exit(cb):
	# Set a cleanup function to run on exit
	if cb:
		atexit.register(cb)

# FIXME: Rename to run_print
def run_say(command):
	print_status("Running command")

	runner = ProcessRunner(command)
	runner.run()
	runner.wait()

	if runner.is_success or runner.is_warning:
		print_ok()
		print(command)
		print(runner.stdall)
	elif runner.is_failure:
		print_fail()
		print(command)
		print(runner.stdall)
		print_exit('Failed to run command.')

def run_and_get_stdout(command):
	runner = ProcessRunner(command)
	runner.run()
	runner.wait()
	if runner.is_failure:
		return None
	else:
		return runner.stdout

def is_outdated(to_update, triggers):
	# Exit if any triggers don't exist
	for trigger in triggers:
		if not os.path.isfile(os.path.abspath(trigger)):
			print_fail()
			print_exit("The file '{0}' does not exist.".format(trigger))

	# Return true if any of the files to check do not exist
	for update in to_update:
		if not os.path.isfile(os.path.abspath(update)):
			return True

	# Get the modify date of the newest trigger file and file to check
	s, b = 0, 0
	for trigger in triggers:
		t = os.path.getmtime(trigger)
		if t > s:
			s = t
	for update in to_update:
		t = os.path.getmtime(update)
		if t > b:
			b = t

	# Rebuild if a trigger is newer than the newest file to check
	if s > b:
		return True
	else:
		return False

def _do_on_fail_exit(start_message, fail_message, cb):
	print_status(start_message)

	# Run it if it is a function
	if hasattr(cb, '__call__'):
		try:
			cb()
			print_ok()
		except Exception as e:
			print_fail()
			print_exit(fail_message)
	# Or run it as a process if a string
	elif type(cb) == str:
		runner = ProcessRunner(cb)
		runner.run()
		runner.wait()
		if runner.is_success or runner.is_warning:
			print_ok()
		elif runner.is_failure:
			print_fail()
			print_exit(fail_message)

def _do_on_fail_pass(start_message, cb):
	print_status(start_message)
	try:
		cb()
	except Exception as e:
		pass
	print_ok()

def cd(name):
	_do_on_fail_exit("Changing to dir '{0}'".format(name),
					"Failed to change to the dir '{0}'.".format(name),
				lambda: os.chdir(name))

def mvfile(source, dest):
	source = to_native(source)
	dest = to_native(dest)

	_do_on_fail_exit("Moving the file '{0}' to '{1}'".format(source, dest),
					"Failed to move the file' {0}'.".format(source),
				lambda: shutil.move(source, dest))

def cpfile(source, dest):
	source = to_native(source)
	dest = to_native(dest)
	_do_on_fail_exit("Copying the file '{0}' to '{1}'".format(source, dest),
					"Failed to copy the file '{0}' to '{1}'.".format(source, dest),
				lambda: shutil.copy2(source, dest))

def cp_new_file(source, dest):
	source = to_native(source)
	dest = to_native(dest)

	if not os.path.isfile(os.path.abspath(dest)):
		cpfile(source, dest)
	elif not filecmp.cmp(source, dest):
		cpfile(source, dest)

def cpdir(source, dest, symlinks = False):
	_do_on_fail_exit("Copying the dir '{0}' to '{1}'".format(source, dest),
					"Failed to copy the dir '{0}' to '{1}'.".format(source, dest),
				lambda: shutil.copytree(source, dest, symlinks = symlinks))

def mkdir_f(source):
	_do_on_fail_pass("Making the dir '{0}'".format(source),
				lambda: os.mkdir(source))

def mkdir(source):
	_do_on_fail_exit("Making the dir '{0}'".format(source),
					"Failed to make the dir '{0}'.".format(source),
				lambda: os.mkdir(source))

def rmdir_and_children(name):
	print_status("Removing the dir '{0}'".format(name))

	# Make sure we are not removing the current directory
	if name == os.getcwd():
		print_fail()
		print_exit("Can't remove the current directory '{0}'.".format(name))

	try:
		if os.path.islink(name):
			os.unlink(name)
		elif os.path.isdir(name):
			shutil.rmtree(name)
		print_ok()
	except OSError as e:
		if 'No such file or directory' in e:
			print_ok()
			return
		print_fail()
		print_exit("Failed to remove the dir '{0}'.".format(name))

def rmdir(name):
	print_status("Removing the dir '{0}'".format(name))

	# Make sure we are not removing the current directory
	if name == os.getcwd():
		print_fail()
		print_exit("Can't remove the current directory '{0}'.".format(name))

	try:
		if os.path.islink(name):
			os.unlink(name)
		elif os.path.isdir(name):
			os.rmdir(name)
	except OSError as e:
		if 'Directory not empty' in e:
			pass
		elif 'No such file or directory' in e:
			pass
		else:
			print_fail()
			print_exit("Failed to remove the dir '{0}'.".format(name))

	print_ok()

def rmfile(name):
	name = to_native(name)

	print_status("Removing the file '{0}'".format(name))
	try:
		if os.path.islink(name):
			os.unlink(name)
		elif os.path.isfile(name):
			os.remove(name)
		print_ok()
	except Exception as e:
		print_fail()
		print_exit("Failed to remove the file '{0}'.".format(name))

def rmfile_f(name):
	name = to_native(name)

	print_status("Removing the file '{0}'".format(name))
	try:
		if os.path.islink(name):
			os.unlink(name)
		elif os.path.isfile(name):
			os.remove(name)
	except Exception as e:
		pass

	print_ok()

def symlink(source, link_name):
	source = to_native(source)
	link_name = to_native(link_name)

	_do_on_fail_exit("Symlinking '{0}' to '{1}'".format(source, link_name),
					"Failed linking '{0}' to '{1}'.".format(source, link_name),
				lambda: os.symlink(source, link_name))

def ldconfig():
	# Setup the message
	print_status("Running 'ldconfig'")

	# Skip ldconfig on Cygwin
	if Config._os_type._name == 'Cygwin':
		print_ok()
		return

	# Run the process
	runner = ProcessRunner("ldconfig")
	runner.run()
	runner.wait()

	# Success or failure
	if runner.is_failure:
		print_fail(runner.stdall)
		print_exit("Failed run 'ldconfig'.")
	elif runner.is_success or runner.is_warning:
		print_ok()

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

def _get_shared_library_from_library_files(library_name, entension, library_files):
	library_name = library_name.lstrip('lib')
	whole_name = library_name + entension

	for entry in library_files:
		if whole_name in entry:
			return entry

	return None

def _get_static_library_from_library_files(library_name, entension, library_files):
	library_name = library_name.lstrip('lib')
	whole_name = library_name + entension

	for entry in library_files:
		if whole_name in entry and entry.endswith(entension):
			return entry

	return None

def _get_header_from_library_files(library_name, library_files):
	library_name = library_name.lstrip('lib')
	for entry in library_files:
		if library_name in entry and entry.endswith('.h'):
			return entry

	return None

# FIXME: Make it work with other packaging systems:
# http://en.wikipedia.org/wiki/List_of_software_package_management_systems
# Returns the full path of a library file or None
def _get_library_files(lib_name, version_cb = None):
	files = []

	# Return the file names if already cached
	if lib_name in lib_file_cache:
		return lib_file_cache[lib_name]

	# Try finding the library with pkg-config
	if not files and program_paths('pkg-config'):
		files = _get_library_files_from_pkg_config(lib_name, version_cb)

	# Try finding the library with dpkg
	if not files and program_paths('dpkg'):
		files = _get_library_files_from_dpkg(lib_name, version_cb)

	# Try finding the library with rpm
	if not files and program_paths('rpm'):
		files = _get_library_files_from_rpm(lib_name, version_cb)

	# Try finding the library with pkg_info
	if not files and program_paths('pkg_info'):
		files = _get_library_files_from_pkg_info(lib_name, version_cb)

	# Try finding the library in the file system
	if not files:
		files = _get_library_files_from_fs(lib_name)

	# Save the file names in the cache
	if files:
		lib_file_cache[lib_name] = files

	return files

def _get_library_files_from_pkg_config(lib_name, version_cb = None):
	matching_files = []
	lib_name = lib_name.lstrip('lib')

	# Find all packages that contain the name
	result = run_and_get_stdout("pkg-config --list-all | grep -i {0}".format(lib_name))
	if not result:
		return matching_files

	# For each package
	for package in result.split("\n"):
		# Get the name
		name = package.split()[0]
		if name.lower() != 'lib' + lib_name.lower():
			continue

		# Get the version, libdir, and includedir
		version = run_and_get_stdout("pkg-config --modversion {0}".format(name))
		libdir = run_and_get_stdout("pkg-config --variable=libdir {0}".format(name))
		includedir = run_and_get_stdout("pkg-config --variable=includedir {0}".format(name))
		if not version or not libdir or not includedir:
			continue
		version = version_string_to_tuple(version)

		# Skip this package if the version does not match
		if version_cb and not version_cb(version):
			continue

		# Get the library files in those directories
		for d in [libdir, includedir]:
			for root, dirs, files in os.walk(d):
				for entry in files:
					# Get the whole file name
					f = os.path.join(root, entry)
					if f.split('.')[0].endswith(lib_name) and os.path.isfile(f):
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
	result = run_and_get_stdout("dpkg --list | grep -i {0}".format(lib_name))
	if not result:
		return matching_files

	# For each package
	for package in result.split("\n"):
		# Get the name and version
		name = before(package.split()[1], ':')
		version = between(package.split()[2], ':', '-')
		version = version_string_to_tuple(version)

		# Skip this package if the version does not match
		if version_cb and not version_cb(version):
			continue

		# Get all the files and directories
		result = run_and_get_stdout("dpkg -L {0}".format(name))
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
	result = run_and_get_stdout("rpm -qa | grep -i {0}".format(lib_name))
	if not result:
		return matching_files

	# For each package
	for package in result.split("\n"):
		# Get the name and version
		result = run_and_get_stdout("rpm -qi {0}".format(package))
		if not result:
			continue
		name = between(result, 'Name        : ', '\n')
		version = between(result, 'Version     : ', '\n')
		version = version_string_to_tuple(version)

		# Skip this package if the version does not match
		if version_cb and not version_cb(version):
			continue

		# Get all the files and directories
		result = run_and_get_stdout("rpm -ql {0}".format(package))
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
	result = run_and_get_stdout("pkg_info -Ix {0}".format(lib_name))
	if not result:
		return matching_files

	# For each package
	for package in result.split("\n"):
		# Get the name and version
		name = package.split()[0]
		version = before(name.split('-')[-1], '_')
		version = version_string_to_tuple(version)

		# Skip this package if the version does not match
		if version_cb and not version_cb(version):
			continue

		# Get all the files and directories
		result = run_and_get_stdout("pkg_info -L {0}".format(name))
		if not result:
			continue

		# Save all the files
		library_entries = result.split("\n")
		for entry in library_entries:
			if os.path.isfile(entry):
				matching_files.append(entry)

	return matching_files

def get_header_file(header_name, version_cb = None):
	library_files = _get_library_files(header_name, version_cb)
	header_file = _get_header_from_library_files(header_name, library_files)
	return header_file

def get_static_library(lib_name, version_cb = None):
	library_files = _get_library_files(lib_name, version_cb)
	static_file = _get_static_library_from_library_files(lib_name, '.a', library_files)
	return static_file

def get_shared_library(lib_name, version_cb = None):
	library_files = _get_library_files(lib_name, version_cb)
	shared_file = _get_shared_library_from_library_files(lib_name, '.so', library_files)
	return shared_file

def require_header_file(header_name, version_cb = None):
	print_status("Checking for header file '{0}'".format(header_name))

	# If the header is not installed, make them install it to continue
	if not get_header_file(header_name, version_cb):
		ver = "Any version"
		if version_cb:
			ver = between(inspect.getsource(version_cb), ': ', ')')

		message = "Header file '{0} ({1})' not installed. Install and try again."
		print_fail()
		print_exit(message.format(header_name, ver))
	else:
		print_ok()

def require_static_library(lib_name, version_cb = None):
	print_status("Checking for static library '{0}'".format(lib_name))

	# If the static library is not installed, make them install it to continue
	if not get_static_library(lib_name, version_cb):
		# Get the version requirement lambda as a printable string
		ver = "Any version"
		if version_cb:
			ver = between(inspect.getsource(version_cb), ': ', ')')

		message = "Static library '{0} ({1})' not installed. Install and try again."
		print_fail()
		print_exit(message.format(lib_name, ver))
	else:
		print_ok()

def require_shared_library(lib_name, version_cb = None):
	print_status("Checking for shared library '{0}'".format(lib_name))

	# If the shared library is not installed, make them install it to continue
	if not get_shared_library(lib_name, version_cb):
		# Get the version requirement lambda as a printable string
		ver = "Any version"
		if version_cb:
			ver = between(inspect.getsource(version_cb), ': ', ')')

		message = "Shared library '{0} ({1})' not installed. Install and try again."
		print_fail()
		print_exit(message.format(lib_name, ver))
	else:
		print_ok()

def require_static_or_shared_library(lib_name, version_cb = None):
	print_status("Checking for static/shared library '{0}'".format(lib_name))

	shared_file = get_shared_library(lib_name, version_cb)
	static_file = get_shared_library(lib_name, version_cb)

	# Make them install the lib if neither was found
	if not shared_file and not static_file:
		# Get the version requirement lambda as a printable string
		ver = "Any version"
		if version_cb:
			ver = between(inspect.getsource(version_cb), ': ', ')')

		message = "Shared/Static library '{0} ({1})' not installed. Install and try again."
		print_fail()
		print_exit(message.format(lib_name, ver))
	else:
		print_ok()

def require_programs(prog_names):
	for prog_name in prog_names:
		print_status("Checking for program '{0}'".format(prog_name))
		if len(program_paths(prog_name)):
			print_ok()
		else:
			print_fail()
			print_exit("Install the program '{0}' and try again.".format(prog_name))

def require_python_modules(mod_names):
	for mod_name in mod_names:
		_do_on_fail_exit(
			"Checking for python module '{0}'".format(mod_name),
			"Install the python module '{0}' and try again.".format(mod_name),
			'{0} -c "import {1}"'.format(Config.python, mod_name)
		)

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
		if 'lib' + Config._bits in path or Config._arch in path:
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

def link_shared_path(lib_name):
	return '-L' + get_shared_library(lib_name)

def link_static_path(lib_name):
	return '-L' + get_static_library(lib_name)

def link_static_or_shared_path(lib_name):
	return '-L' + static_or_shared_library_path(lib_name)

def link_shared_paths(lib_names):
	paths = []
	for lib_name in lib_names:
		paths.append(link_shared_path(lib_name))
	return str.join(' ', paths)

def link_static_paths(lib_names):
	paths = []
	for lib_name in lib_names:
		paths.append(link_static_path(lib_name))
	return str.join(' ', paths)

def link_static_or_shared_paths(lib_names):
	paths = []
	for lib_name in lib_names:
		paths.append(link_static_or_shared_path(lib_name))
	return str.join(' ', paths)


# Other C compilers: Clang, DMC, Dingus, Elsa, PCC
# http://en.wikipedia.org/wiki/List_of_compilers#C_compilers
class Compiler(object):
	def __init__(self, name, path, setup, out_file, no_link, 
				debug, warnings_all, warnings_as_errors, optimize, 
				compile_time_flags, link):

		self._name = name
		self._path = path

		# Save text for all the options
		self._opt_setup = setup
		self._opt_out_file = out_file
		self._opt_no_link = no_link
		self._opt_debug = debug
		self._opt_warnings_all = warnings_all
		self._opt_warnings_as_errors = warnings_as_errors
		self._opt_optimize = optimize
		self._opt_compile_time_flags = compile_time_flags
		self._opt_link = link

		# Set the default values of the flags
		self.debug = False
		self.warnings_all = False
		self.warnings_as_errors = False
		self.optimize = False
		self.compile_time_flags = []

class Linker(object):
	def __init__(self, name, setup, out_file, shared):
		self._name = name
		
		self._opt_setup = setup
		self._opt_out_file = out_file
		self._opt_shared = shared

def to_native(thing):
	# Get a dict of the standard extensions and their other os counterparts
	replaces = {
		'.o' : Config._os_type._object_extension,
		'.so': Config._os_type._shared_lib_extension,
		'.a' : Config._os_type._static_lib_extension
	}

	# Replace the extension
	if type(thing) == list:
		for before, after in replaces.items():
			thing = [o.replace(before, after) for o in thing]
	else:
		for before, after in replaces.items():
			thing = thing.replace(before, after)

	return thing

def require_module(name):
	Config.modules.append(name)

def load_module(module_name, g=globals(), l=locals()):
	script_name = os.path.join(Config.pwd, 'lib_raise_{0}.py'.format(module_name.lower()))

	# Make sure there is an rscript file
	if not os.path.isfile(script_name):
		print_exit("No such module '{0}' ({1}).".format(module_name, script_name))

	# Load the module file into this namespace
	with open(script_name, 'rb') as f:
		code = compile(f.read(), script_name, 'exec')
		exec(code, g, l)

def load_rscript(g=globals(), l=locals()):
	# Make sure there is an rscript file
	if not os.path.isfile('rscript'):
		return None

	# Get a list of all the functions
	before = []
	for key in globals().keys():
		before.append(key)

	# Load the rscript file into this namespace
	with open('rscript', 'rb') as f:
		code = None
		try:
			code = compile(f.read(), 'rscript', 'exec')
		except Exception as e:
			print_exit(e)

		exec(code, g, l)

	# Get just the target functions
	targets = {}
	for key in globals().keys():
		if not key in before:
			if not key.startswith('_') and hasattr(globals()[key], '__call__'):
				targets[key] = globals()[key]

	return targets

if __name__ == '__main__':
	# Figure out everything we need to know about the system
	Config.init()

	# Have all KeyboardInterrupt exceptions quit with a clean message
	def signal_handler(signal, frame):
		print_exit('Exit called by the keyboard.')
		exit()
	signal.signal(signal.SIGINT, signal_handler)

	# Clear the terminal
	os.system(Config._terminal_clear)

	# Load the rscript
	targets = load_rscript()

	# Get the target function name
	Config.target_name = str(str.join(' ', sys.argv[1:]))

	# Get a friendly list of all the targets
	target_list = []
	if targets:
		keys = list(targets.keys())
		keys.sort()
		target_list = "'" + str.join("', '", keys) + "'"

	# Exit if there is no target
	if not Config.target_name:
		print("Raise software build tool (Version 0.3 - September 24 2013) http://launchpad.net/raise")
		print("")
		print("COMMANDS:")
		print("    ./raise update - Downloads the newest version of Raise. It will be stored in a file named \".lib_raise\" or \"lib_raise\".")
		print("")

		# Print all the targets
		if targets:
			no_doc = "No docstring is provided for this target."
			print("TARGETS:")
			for t in targets:
				doc = targets[t].__doc__ or no_doc
				print("    ./raise {0} - {1}".format(t, doc))
				print("")
			print_exit("No target specified. Found targets are {0}.".format(target_list))

	if not targets:
		print_exit("No 'rscript' file found.")

	# Exit if there is no target with that name
	if not Config.target_name in targets:
		print_exit("No target named '{0}'. Found targets are {1}.".format(Config.target_name, target_list))

	# Setup any modules
	for module in Config.modules:
		load_module(module)

		# FIXME: This should be done inside the module loading
		if module == 'Linker':
			linker_module_setup()
		elif module == 'C':
			c_module_setup()
		elif module == 'CXX':
			cxx_module_setup()
		elif module == 'D':
			d_module_setup()
		elif module == 'CSHARP':
			csharp_module_setup()
		else:
			print_exit('Unknown module "{0}"'.format(module))

	# Try running the target
	target = targets[Config.target_name]
	print_info("Running target '{0}'".format(Config.target_name))
	target()


