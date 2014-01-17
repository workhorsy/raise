#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''
	Running this script will generate the documentation index.html 
	from the template file templates/index.html.mako.
'''

import sys, os
import subprocess
from mako.template import Template

# Adds to add CSS styles to output
def add_styles(code):
	code = code.replace(':)', '<span class="smile">:)</span>')
	code = code.replace(':(', '<span class="frown">:(</span>')
	code = code.replace(':\\', '<span class="normal">:\</span>')
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
	'c_building_object' : {},
	'c_building_program' : {},
	'c_building_shared_library' : {},
	'c_program_installation_and_uninstallation' : 'skip_run',
	'c_library_installation_and_uninstallation' : 'skip_run',
	'c_header_installation_and_uninstallation' : 'skip_run',
	'c_running_and_printing' : {},

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
}

if __name__ == '__main__':
	# Move the templates directory
	os.chdir('templates')

	# Generate the source code and output for each doc item
	for anchor, value in info.items():
		# Cleanup
		run_and_get_stdall('./raise setup')

		# Get the source code
		example = run_and_get_stdall('./raise -plain -inspect {0}'.format(anchor))
		if len(example.strip()) == 0:
			raise Exception('Example for "{0}" was blank.'.format(anchor))

		# Get the output and apply CSS styles
		output = 'skip'
		if value != 'skip_run':
			output = run_and_get_stdall('./raise -plain {0}'.format(anchor))
			if len(output.strip()) == 0:
				raise Exception('Output for "{0}" was blank.'.format(anchor))
			output = str.join("\n", output.split("\n")[1 : ])
			output = add_styles(output)

		# Save the code and output
		info[anchor] = {
			'example' : example, 
			'output' : output, 
		}

	# Move back up one directory
	os.chdir('..')

	# Apply the generated code info to the template
	mytemplate = Template(
		filename='templates/index.html.mako', 
		input_encoding='utf-8',
		output_encoding='utf-8')

	with open('index.html', 'wb') as f:
		f.write(mytemplate.render(template_info=info))



