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

import tempfile, shutil, filecmp
import atexit
from lib_raise_terminal import *


class FS(RaiseModule):
	@classmethod
	def setup(cls):
		pass


def change_dir(name):
	do_on_fail_exit("Changing to dir '{0}'".format(name),
					"Failed to change to the dir '{0}'.".format(name),
				lambda: os.chdir(name))

def move_file(source, dest):
	do_on_fail_exit("Moving the file '{0}' to '{1}'".format(source, dest),
					"Failed to move the file' {0}'.".format(source),
				lambda: shutil.move(source, dest))

def copy_file(source, dest):
	do_on_fail_exit("Copying the file '{0}' to '{1}'".format(source, dest),
					"Failed to copy the file '{0}' to '{1}'.".format(source, dest),
				lambda: shutil.copy2(source, dest))

def copy_new_file(source, dest):
	if not os.path.isfile(os.path.abspath(dest)):
		copy_file(source, dest)
	elif not filecmp.cmp(source, dest):
		copy_file(source, dest)

def copy_dir(source, dest, symlinks = False):
	do_on_fail_exit("Copying the dir '{0}' to '{1}'".format(source, dest),
					"Failed to copy the dir '{0}' to '{1}'.".format(source, dest),
				lambda: shutil.copytree(source, dest, symlinks = symlinks))

def make_dir(source, ignore_failure = False):
	if ignore_failure:
		do_on_fail_pass("Making the dir '{0}'".format(source),
					lambda: os.mkdir(source))
	else:
		do_on_fail_exit("Making the dir '{0}'".format(source),
						"Failed to make the dir '{0}'.".format(source),
					lambda: os.mkdir(source))

def remove_dir(name, and_children = False):
	print_status("Removing the dir '{0}'".format(name))
	success = False

	# Make sure we are not removing the current directory
	if name == os.getcwd():
		print_fail()
		print_exit("Can't remove the current directory '{0}'.".format(name))

	try:
		if os.path.islink(name):
			os.unlink(name)
		elif os.path.isdir(name):
			if and_children:
				shutil.rmtree(name)
			else:
				os.rmdir(name)
		success = True
	except OSError as e:
		if 'No such file or directory' in e:
			success = True

	if success:
		print_ok()
	else:
		print_fail()
		print_exit("Failed to remove the dir '{0}'.".format(name))

def remove_file(name, ignore_failure = False):
	print_status("Removing the file '{0}'".format(name))
	success = False

	try:
		if os.path.islink(name):
			os.unlink(name)
		elif os.path.isfile(name):
			os.remove(name)
		success = True
	except Exception as e:
		if ignore_failure:
			success = True

	if success:
		print_ok()
	else:
		print_fail()
		print_exit("Failed to remove the file '{0}'.".format(name))

def remove_binaries(name):
	print_status("Removing binaries '{0}'".format(name))

	extensions = ['.exe', '.o', '.obj', '.so', '.a', '.dll', '.lib', '.pyc',
				'.exe.mdb', '.dll.mdb', '.jar', '.class']

	for entry in os.listdir(os.getcwd()):
		if entry.startswith(name) and os.path.isfile(entry):
			extension = '.' + str.join('.', entry.lower().split('.')[1:])
			if extension in extensions or entry == name:
				os.remove(entry)

	print_ok()

def symlink(source, link_name):
	do_on_fail_exit("Symlinking '{0}' to '{1}'".format(source, link_name),
					"Failed linking '{0}' to '{1}'.".format(source, link_name),
				lambda: os.symlink(source, link_name))

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

def self_deleting_named_temporary_file():
	f = tempfile.NamedTemporaryFile(delete=False)
	f.close()

	def cb():
		if os.path.exists(f.name):
			os.unlink(f.name)

	atexit.register(cb)

	return f


FS.call_setup()

