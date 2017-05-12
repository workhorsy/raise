#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# This file is part of Raise.
# Raise is a small build automation tool that ships with your software.
# Raise uses a MIT style license, and is hosted at https://github.com/workhorsy/raise .
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
import sys
import glob
import tempfile, shutil, filecmp
import atexit
import lib_raise_config as Config
import lib_raise_process as Process
import lib_raise_terminal as Print

PY2 = sys.version_info[0] == 2

def is_string_like(thing):
	if PY2:
		return isinstance(thing, basestring)
	else:
		return isinstance(thing, str)

def change_dir(name):
	Process.do_on_fail_exit("Changing to dir '{0}'".format(name),
					"Failed to change to the dir '{0}'.".format(name),
				lambda: os.chdir(name))

def move_file(source, dest):
	Process.do_on_fail_exit("Moving the file '{0}' to '{1}'".format(source, dest),
					"Failed to move the file' {0}'.".format(source),
				lambda: shutil.move(source, dest))

def copy_file(source, dest):
	Process.do_on_fail_exit("Copying the file '{0}' to '{1}'".format(source, dest),
					"Failed to copy the file '{0}' to '{1}'.".format(source, dest),
				lambda: shutil.copy2(source, dest))

def copy_new_file(source, dest):
	if not os.path.isfile(os.path.abspath(dest)):
		copy_file(source, dest)
	elif not filecmp.cmp(source, dest):
		copy_file(source, dest)

def copy_dir(source, dest, symlinks = False):
	Process.do_on_fail_exit("Copying the dir '{0}' to '{1}'".format(source, dest),
					"Failed to copy the dir '{0}' to '{1}'.".format(source, dest),
				lambda: shutil.copytree(source, dest, symlinks = symlinks))

def make_dir(source, ignore_failure = False):
	if ignore_failure:
		Process.do_on_fail_pass("Making the dir '{0}'".format(source),
					lambda: os.mkdir(source))
	else:
		Process.do_on_fail_exit("Making the dir '{0}'".format(source),
						"Failed to make the dir '{0}'.".format(source),
					lambda: os.mkdir(source))

def remove_dir(name, and_children = False):
	Print.status("Removing the dir '{0}'".format(name))
	success = False

	# Make sure we are not removing the current directory
	if name == os.getcwd():
		Print.fail()
		Print.exit("Can't remove the current directory '{0}'.".format(name))

	try:
		for entry in glob_names(name):
			if os.path.islink(entry):
				os.unlink(entry)
			elif os.path.isdir(entry):
				if and_children:
					shutil.rmtree(entry)
				else:
					os.rmdir(entry)
		success = True
	except OSError as e:
		if 'No such file or directory' in e:
			success = True

	if success:
		Print.ok()
	else:
		Print.fail()
		Print.exit("Failed to remove the dir '{0}'.".format(name))

def remove_file(name, ignore_failure = False):
	Print.status("Removing the file '{0}'".format(name))
	success = False

	try:
		for entry in glob_names(name):
			if os.path.islink(entry):
				os.unlink(entry)
			elif os.path.isfile(entry):
				os.remove(entry)
		success = True
	except Exception as e:
		if ignore_failure:
			success = True

	if success:
		Print.ok()
	else:
		Print.fail()
		Print.exit("Failed to remove the file '{0}'.".format(name))

def remove_binaries(name):
	Print.status("Removing binaries '{0}'".format(name))

	extensions = ['.exe', '.o', '.obj', '.so', '.a', '.dll', '.lib', '.pyc',
				'.exe.mdb', '.dll.mdb', '.jar', '.class']

	for entry in os.listdir(os.getcwd()):
		if entry.startswith(name) and os.path.isfile(entry):
			extension = '.' + str.join('.', entry.lower().split('.')[1:])
			if extension in extensions or entry == name:
				os.remove(entry)

	Print.ok()

def symlink(source, link_name):
	Process.do_on_fail_exit("Symlinking '{0}' to '{1}'".format(source, link_name),
					"Failed linking '{0}' to '{1}'.".format(source, link_name),
				lambda: os.symlink(source, link_name))

def glob_name(name):
	entries = []
	globs = glob.glob(name)

	# No matches, so just return the original string
	if len(globs) == 0:
		entries.append(name)
	# Matches, so return all the matches
	else:
		for entry in globs:
			entries.append(entry)

	return entries

def glob_names(names):
	import types

	if names is None:
		return None

	# Is a string
	if is_string_like(names):
		return glob_name(names)

	# Is a list
	entries = []
	for name in names:
		for entry in glob_name(name):
			entries.append(entry)
	return entries

def is_outdated(to_update, triggers):
	to_update = glob_names(to_update)
	triggers = glob_names(triggers)

	# Return true if any of the files to check do not exist
	for update in to_update:
		if not os.path.isfile(os.path.abspath(update)):
			return True

	# Drop any entries that are not files
	to_update = [entry for entry in to_update if os.path.isfile(os.path.abspath(entry))]
	triggers = [entry for entry in triggers if os.path.isfile(os.path.abspath(entry))]

	# Get the modify date of the newest trigger file and file to check
	newest_trigger, newest_update = 0, 0
	for trigger in triggers:
		t = os.path.getmtime(trigger)
		if t > newest_trigger:
			newest_trigger = t
	for update in to_update:
		t = os.path.getmtime(update)
		if t > newest_update:
			newest_update = t

	# Rebuild if a trigger is newer than the newest file to check
	if newest_trigger > newest_update:
		return True
	else:
		return False

def create_path_dirs(path):
	out_dir = os.path.dirname(path)
	if out_dir and not os.path.isdir(out_dir):
		os.makedirs(out_dir)

def self_deleting_named_temporary_file():
	f = tempfile.NamedTemporaryFile(delete=False)
	f.close()

	def cb():
		if os.path.exists(f.name):
			os.unlink(f.name)

	atexit.register(cb)

	return f



