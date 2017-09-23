#!/usr/bin/env python
# -*- coding: utf-8 -*- 

"""
HTCAP - beta 1
Author: filippo.cavallarin@wearesegment.com

This program is free software; you can redistribute it and/or modify it under 
the terms of the GNU General Public License as published by the Free Software 
Foundation; either version 2 of the License, or (at your option) any later 
version.
"""

from __future__ import unicode_literals
import sys
import os
import datetime
import time
import getopt

from core.lib.utils import *
from core.crawl.crawler import Crawler

from core.util.util import Util

reload(sys)
sys.setdefaultencoding('utf8')
log = "*"*53
log += """
* / _ \|  _ \  / \\ \ / / ___/ ___|  ___ __ _| \ | | *
*| | | | | | |/ _ \\ V /|___ \___ \ / __/ _` |  \| | *
*| |_| | |_| / ___ \| |  ___) |__) | (_| (_| | |\  |*
* \___/|____/_/   \_\_| |____/____/ \___\__,_|_| \_|*
"""
log += "*"*53
print log

def usage():
	print (
		   "usage: htcap <command>\n" 
		   "Commands: \n"
		   "  crawl                  run crawler\n"
		   "  util                   run utility\n"
		   )


if __name__ == '__main__':

	if len(sys.argv) < 2:
		usage()
		sys.exit(1)

	elif sys.argv[1] == "crawl":
		Crawler(sys.argv[2:])
	elif sys.argv[1] == "util":
		Util(sys.argv[2:])
	else:
		usage();
		sys.exit(1)

	sys.exit(0)
