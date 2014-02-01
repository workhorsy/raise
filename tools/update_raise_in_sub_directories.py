#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''
	Running this script will copy the 'raise' file in the root
	directory, over all the 'raise' files in the sub directories.
'''

import os
import shutil

print('Updating all copies of "raise" in sub directories ...')

# Move the pwd to the path of this file
current_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_path)

# Walk through all the sub directories
for root, dirs, files in os.walk('..'):
	for file_name in files:
		# Get the relative and absolute path of the file
		relative_name = os.path.join(root, file_name)
		abs_name = os.path.abspath(relative_name)

		# Skip the file if it is in a VCS directory
		if '.bzr' in relative_name:
			continue

		# Skip the file if it is not named 'raise'
		if file_name != 'raise':
			continue

		# Skip the file if it is the original 'raise' file
		if relative_name == '../raise':
			continue

		shutil.copy2('../raise', relative_name)
		print('    Copied "raise" to "{0}"'.format(abs_name))

print('Done!')


