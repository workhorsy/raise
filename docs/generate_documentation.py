#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''
	Running this script will generate the documentation index.html 
	from the template file templates/index.html.mako.
'''

import sys, os
import pickle
import subprocess
from mako.template import Template

# Adds to add CSS styles to output
def add_styles(code):
	code = code.replace(b':)', b'<span class="smile">:)</span>')
	code = code.replace(b':(', b'<span class="frown">:(</span>')
	code = code.replace(b':\\', b'<span class="normal">:\</span>')
	return code

# Runs a command and gets all the standard output as a string
def run_and_get_stdall(command):
	# Start the process in a real shelll and pipe the std io
	p = subprocess.Popen(
		command, 
		stderr = subprocess.PIPE, 
		stdout = subprocess.PIPE, 
		shell = True, 
		env = os.environ
	)

	# Save the stdout and stderr
	out, err = p.communicate()
	if err:
		out += err

	# Get the return code
	rc = p.returncode
	if hasattr(os, 'WIFEXITED') and os.WIFEXITED(rc):
		rc = os.WEXITSTATUS(rc)

	# Throw if there was an error
	if rc != 0:
		raise Exception('Return not 0 on: ' + command + ', ' + out)

	return out.strip()

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

# A list of the the documentation items to generate examples for
info = {
	'installation' : {},
	'operating_system_support' : {},

	'fs_change_dir' : {}, 
	'fs_move_file' : {}, 
	'fs_copy_file' : {}, 
	'fs_copy_new_file' : {},
	'fs_copy_dir' : {}, 
	'fs_make_dir' : {}, 
	'fs_remove_dir' : {}, 
	'fs_remove_file' : {}, 
	'fs_remove_binaries' : {}, 
	'fs_symlink' : {}, 

	'c_compilers' : {},
	'c_compiler_setup' : {},
	'c_building_object' : {},
	'c_building_program' : {},
	'c_building_library' : {},
	'c_program_installation_and_uninstallation' : 'root',
	'c_library_installation_and_uninstallation' : 'root',
	'c_header_installation_and_uninstallation' : 'root',
	'c_running_and_printing' : {},

	'cxx_compilers' : {},
	'cxx_compiler_setup' : {},
	'cxx_building_object' : {},
	'cxx_building_program' : {},
	'cxx_building_library' : {},
	'cxx_program_installation_and_uninstallation' : 'root',
	'cxx_library_installation_and_uninstallation' : 'root',
	'cxx_header_installation_and_uninstallation' : 'root',
	'cxx_running_and_printing' : {},

	'd_compilers' : {},
	'd_compiler_setup' : {},
	'd_building_object' : {},
	'd_building_program' : {},
	'd_building_library' : {},
	'd_building_interface' : {},
	'd_program_installation_and_uninstallation' : 'root',
	'd_library_installation_and_uninstallation' : 'root',
	'd_interface_installation_and_uninstallation' : 'root',
	'd_running_and_printing' : {},

	'csharp_compilers' : {},
	'csharp_compiler_setup' : 'root',
	'csharp_building_program' : {},
	'csharp_building_library' : {},
	'csharp_program_installation_and_uninstallation' : 'root',
	'csharp_library_installation_and_uninstallation' : 'root',
	'csharp_running_and_printing' : {},

	'java_compilers' : {},
	'java_compiler_setup' : {},
	'java_building_program' : {},
	'java_building_library' : {},
	'java_program_installation_and_uninstallation' : 'root',
	'java_library_installation_and_uninstallation' : 'root',
	'java_running_and_printing' : {},

	'users_running_as_root' : 'skip_run',
	'users_running_as_a_normal_user' : 'skip_run',
	'users_privilege_escalation' : 'root',
	'users_user_name' : {},
	'users_user_id' : {},

	'find_finding_programs' : {},
	'find_requiring_programs' : {},
	'find_finding_libraries' : {},
	'find_requiring_libraries' : {},
	'find_finding_headers' : {},
	'find_requiring_headers' : {},
	'find_requiring_environmental_variable' : {},
	'find_requiring_python_modules' : {},

	'concurrency' : {},

	'cpu' : {},

	'terminal_ok' : {},
	'terminal_warning' : {},
	'terminal_fail' : {},
}

cache = {}

def get_normal_user_id():
	# Get the name from the environmental variable
	user_name = \
		os.getenv('SUDO_USER') or \
		os.getenv('USER') or \
		os.getenv('LOGNAME')

	# Make sure we got a name
	if not user_name:
		raise Exception('Failed to get the normal user name.')

	# Use the user name to get the user id
	return int(os.popen('id -u {0}'.format(user_name)).read())


def to_user(user_id):
	os.setegid(user_id)
	os.seteuid(user_id)

if __name__ == '__main__':
	# Make sure we are root
	if os.getuid() != 0:
		print('Must be run as root. Exiting ...')
		exit(1)

	# Make sure requiremnts are installed
	reqs = ['gcc', 'g++', 'clang', 'clang++', 'dmcs', 'javac', 'dmd', 'ldc2']
	for req in reqs:
		if not program_paths(req):
			print("Could not find '{0}'. Exiting ...".format(req))
			exit(1)

	# Get the normal user id
	normal_user_id = get_normal_user_id()

	# Load the cache
	if os.path.isfile('cache.pickle'):
		with open('cache.pickle', 'rb') as f:
			cache = pickle.loads(f.read())

	# Move the templates directory
	os.chdir('templates')

	# Generate the source code and output for each doc item
	n = 0
	for anchor, value in info.items():
		n += 1
		print("running template {0} of {1} ...".format(n, len(info)))

		# Setup
		run_and_get_stdall('{0} raise setup'.format(sys.executable))

		# Get the source code
		example = run_and_get_stdall('{0} raise -plain -inspect {1}'.format(sys.executable, anchor))
		if len(example.strip()) == 0:
			raise Exception('Example for "{0}" was blank.'.format(anchor))

		output = b'skip'
		# Used the cached value if the code is the same
		if example in cache:
			output = cache[example]
			print('cached ...')
		# Or re-run the code if it has changed
		else:
			# Get the output as ROOT and apply the CSS
			if value == 'root':
				output = run_and_get_stdall('{0} raise -plain {1}'.format(sys.executable, anchor))
				if len(output.strip()) == 0:
					raise Exception('Output for "{0}" was blank.'.format(anchor))
				output = bytes.join(b"\n", output.split(b"\n")[1 : ])
				output = add_styles(output)
			# Get the output and apply CSS styles
			elif value != 'skip_run':
				to_user(normal_user_id)
				output = run_and_get_stdall('{0} raise -plain {1}'.format(sys.executable, anchor))
				to_user(0)
				if len(output.strip()) == 0:
					raise Exception('Output for "{0}" was blank.'.format(anchor))
				output = bytes.join(b"\n", output.split(b"\n")[1 : ])
				output = add_styles(output)
			cache[example] = output

		# Save the code and output
		info[anchor] = {
			'example' : example.decode('utf-8'), 
			'output' : output.decode('utf-8'), 
		}

	# Cleanup
	run_and_get_stdall('{0} raise cleanup'.format(sys.executable))

	# Move back up one directory
	os.chdir('..')

	# Save the cahce
	with open('cache.pickle', 'wb') as f:
		data = pickle.dumps(cache)
		f.write(data)

	# Apply the generated code info to the template
	mytemplate = Template(
		filename='templates/index.html.mako', 
		input_encoding='utf-8',
		output_encoding='utf-8')

	with open('index.html', 'wb') as f:
		f.write(mytemplate.render(template_info=info))



