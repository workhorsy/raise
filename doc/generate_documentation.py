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

	return out

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
	'c_program_installation_and_uninstallation' : 'skip_run',
	'c_library_installation_and_uninstallation' : 'skip_run',
	'c_header_installation_and_uninstallation' : 'skip_run',
	'c_running_and_printing' : {},

	'cxx_compilers' : {},
	'cxx_compiler_setup' : {},
	'cxx_building_object' : {},
	'cxx_building_program' : {},
	'cxx_building_library' : {},
	'cxx_program_installation_and_uninstallation' : 'skip_run',
	'cxx_library_installation_and_uninstallation' : 'skip_run',
	'cxx_header_installation_and_uninstallation' : 'skip_run',
	'cxx_running_and_printing' : {},

	'd_compilers' : {},
	'd_compiler_setup' : {},
	'd_building_object' : {},
	'd_building_program' : {},
	'd_building_library' : {},
	'd_building_interface' : {},
	'd_program_installation_and_uninstallation' : 'skip_run',
	'd_library_installation_and_uninstallation' : 'skip_run',
	'd_interface_installation_and_uninstallation' : 'skip_run',
	'd_running_and_printing' : {},

	'csharp_compilers' : {},
	'csharp_compiler_setup' : {},
	'csharp_building_program' : {},
	'csharp_building_library' : {},
	'csharp_program_installation_and_uninstallation' : 'skip_run',
	'csharp_library_installation_and_uninstallation' : 'skip_run',
	'csharp_running_and_printing' : {},

	'java_compilers' : {},
	'java_compiler_setup' : {},
	'java_building_program' : {},
	'java_building_library' : {},
	'java_program_installation_and_uninstallation' : 'skip_run',
	'java_library_installation_and_uninstallation' : 'skip_run',
	'java_running_and_printing' : {},

	'users_running_as_root' : 'skip_run',
	'users_running_as_a_normal_user' : 'skip_run',
	'users_privilege_escalation' : {},
	'users_user_name' : 'skip_run',
	'users_user_id' : 'skip_run',

	'find_finding_programs' : {},
	'find_requiring_programs' : {},
	'find_finding_libraries' : {},
	'find_requiring_libraries' : {},
	'find_finding_headers' : {},
	'find_requiring_headers' : {},
	'find_requiring_python_modules' : {},

	'concurrency' : {},

	'cpu' : {},

	'terminal_ok' : {},
	'terminal_warning' : {},
	'terminal_fail' : {},
}

cache = {}

if __name__ == '__main__':
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
			# Get the output and apply CSS styles
			if value != 'skip_run':
				output = run_and_get_stdall('{0} raise -plain {1}'.format(sys.executable, anchor))
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



