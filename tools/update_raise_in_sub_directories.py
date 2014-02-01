#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''
	Running this script will copy the 'raise' file in the root
	directory, over all the 'raise' files in the sub directories.
'''

import os
import shutil


for root, dirs, files in os.walk('..'):
	for file_name in files:
		complete_name = os.path.join(root, file_name)
		if not complete_name.startswith('./.bzr') and \
			file_name == 'raise' and \
			complete_name != './raise':
			shutil.copy2('../raise', complete_name)
			print('Copied "raise" to "{0}"'.format(complete_name))




