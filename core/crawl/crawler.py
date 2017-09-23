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
import json
import re
from urlparse import urlsplit, urljoin
from urllib import unquote
import urllib2
import threading
import subprocess
from random import choice
import string
import ssl


from core.lib.exception import *
from core.lib.cookie import Cookie
from core.lib.database import Database


from lib.shared import *
from lib.crawl_result import *
from core.lib.request import Request
from core.lib.http_get import HttpGet
from core.lib.shell import CommandExecutor
#from core.dirburp.dirscan import Dirbuster
from crawler_thread import CrawlerThread

from core.lib.utils import *
from core.constants import *
from tld import get_tld
from lib.utils import *

class Crawler:

	def __init__(self, argv):
		USER_AGENTS = [
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
    "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
    "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
    "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
    "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
    "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5",
    "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
    "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52",]

        

		self.base_dir = getrealdir(__file__) + os.sep

		self.crawl_start_time = int(time.time())
		self.crawl_end_time = None
		self.taskid = ''

		self.defaults = {
			"useragent": choice(USER_AGENTS),
			"num_threads": 10,
			"max_redirects": 10*10,
			"out_file_overwrite": False,
			"proxy": None,
			"http_auth": None,
			"use_urllib_onerror": True,
			"group_qs": False,
			"process_timeout": 450, # when lots of element(~25000) are added dynamically it can take some time..
			"set_referer": True,
			"scope": CRAWLSCOPE_DOMAIN,
			"mode": CRAWLMODE_AGGRESSIVE,
			"max_depth": 10000,
			"max_post_depth": 1000,
			"override_timeout_functions": True,
			'crawl_forms': True# only if mode == CRAWLMODE_AGGRESSIVE
		}


		self.main(argv)



	def usage(self):
		print (
			   "usage: htcap [options] url outfile\n"
			   "Options: \n"
			   "  -h               this help\n"
			   "  -q               do not display progress informations\n"
			   "  -m MODE          set crawl mode:\n"
			   "                      - "+CRAWLMODE_PASSIVE+": do not intract with the page\n"
			   "                      - "+CRAWLMODE_ACTIVE+": trigger events\n"
			   "                      - "+CRAWLMODE_AGGRESSIVE+": also fill input values and crawl forms (default)\n"
			   "  -s SCOPE         set crawl scope\n"
			   "                      - "+CRAWLSCOPE_DOMAIN+": limit crawling to current domain (default)\n"
			   "                      - "+CRAWLSCOPE_DIRECTORY+": limit crawling to current directory (and subdirecotries) \n"
			   "                      - "+CRAWLSCOPE_URL+": do not crawl, just analyze a single page\n"
			   "  -D               maximum crawl depth (default: " + str(Shared.options['max_depth']) + ")\n"
			   "  -P               maximum crawl depth for consecutive forms (default: " + str(Shared.options['max_post_depth']) + ")\n"
			   "  -F               even if in aggressive mode, do not crawl forms\n"
			   "  -H               save HTML generated by the page\n"
			   "  -d DOMAINS       comma separated list of allowed domains (ex *.target.com)\n"
			   "  -c COOKIES       cookies as json or name=value pairs separaded by semicolon\n"
			   "  -C COOKIE_FILE   path to file containing COOKIES \n"
			   "  -r REFERER       set initial referer\n"
			   "  -x EXCLUDED      comma separated list of urls to exclude (regex) - ie logout urls\n"
			   "  -p PROXY         proxy string protocol:host:port -  protocol can be 'http' or 'socks5'\n"
			   "  -n THREADS       number of parallel threads (default: " + str(self.defaults['num_threads']) + ")\n"
			   "  -A CREDENTIALS   username and password used for HTTP authentication separated by a colon\n"
			   "  -U USERAGENT     set user agent\n"
			   "  -t TIMEOUT       maximum seconds spent to analyze a page (default " + str(self.defaults['process_timeout']) + ")\n"
			   "  -u USER_SCRIPT   inject USER_SCRIPT into any loaded page\n"
			   "  -S               skip initial checks\n"
			   "  -G               group query_string parameters with the same name ('[]' ending excluded)\n"
			   "  -N               don't normalize URL path (keep ../../)\n"
			   "  -R               maximum number of redirects to follow (default " + str(self.defaults['max_redirects']) + ")\n"
			   "  -I               ignore robots.txt\n"
			   "  -O               dont't override timeout functions (setTimeout, setInterval)\n"
			   "  -K               keep elements in the DOM (prevent removal)\n"
			   )

	


	def generate_filename(self, name, out_file_overwrite):
		fname = generate_filename(name, None, out_file_overwrite)
		if out_file_overwrite:
			if os.path.exists(fname):
				os.remove(fname)

		return fname



	def kill_threads(self, threads):
		for th in threads:
			if th.isAlive(): th.exit = True
		# start notify() chain
		Shared.th_condition.acquire()
		Shared.th_condition.notifyAll()
		Shared.th_condition.release()



	def parse_cookie_string(self, string):

		cookies = []
		try:
			cookies = json.loads(string)
		except ValueError:
			tok = re.split("; *", string)
			for t in tok:
				k, v = t.split("=", 1)
				cookies.append({"name":k.strip(), "value":unquote(v.strip())})
		except Exception as e:
			raise

		return cookies



	def init_db(self, dbname, report_name):
		infos = {
			"target": Shared.starturl,
			"scan_date": -1,
			"urls_scanned": -1,
			"scan_time": -1,
			'command_line': " ".join(sys.argv)
		}

		database = Database(dbname, report_name, infos)
		return database

	def check_startrequest(self, request):

		h = HttpGet(request, Shared.options['process_timeout'], 2, Shared.options['useragent'], Shared.options['proxy'])
		try:
			h.get_requests()
		except NotHtmlException:
			print "\nError: Document is not html"
			sys.exit(1)
		except Exception as e:
			print "\nError: unable to open url: %s" % e
			sys.exit(1)

	def get_requests_from_robots(self, request):
    		purl = urlsplit(request.url)
		url = "%s://%s/robots.txt" % (purl.scheme, purl.netloc)

		getreq = Request(REQTYPE_LINK, "GET", url)
		try:
			# request, timeout, retries=None, useragent=None, proxy=None):
			httpget = HttpGet(getreq, 10, 1, "Googlebot", Shared.options['proxy'])
			lines = httpget.get_file().split("\n")
		except urllib2.HTTPError:
			return []
		except:
			raise

		requests = []
		for line in lines:
			directive = ""
			url = None
			try:
				directive, url = re.sub("\#.*","",line).split(":",1)
			except:
				continue # ignore errors

			if re.match("(dis)?allow", directive.strip(), re.I):
				req = Request(REQTYPE_LINK, "GET", url.strip(), parent=request)
				requests.append(req)


		return adjust_requests(requests) if requests else []


	def randstr(self, length):
		all_chars = string.digits + string.letters + string.punctuation
		random_string = ''.join(choice(all_chars) for _ in range(length))
		return random_string



	def main_loop(self, threads, start_requests, database, display_progress = True, verbose = False,taskid=''):
		pending = len(start_requests)
		crawled = 0

		req_to_crawl = start_requests
		try:
			while True:

				if display_progress and not verbose:
					tot = (crawled + pending)
					print_progressbar(tot, crawled, self.crawl_start_time, "pages processed")

				if pending == 0:
					# is the check of running threads really needed?
					running_threads = [t for t in threads if t.status == THSTAT_RUNNING]
					if len(running_threads) == 0:
						if display_progress or verbose:
							print ""
						break

				if len(req_to_crawl) > 0:
					Shared.th_condition.acquire()
					Shared.requests.extend(req_to_crawl)
					Shared.th_condition.notifyAll()
					Shared.th_condition.release()

				req_to_crawl = []
				Shared.main_condition.acquire()
				Shared.main_condition.wait(1)
				if len(Shared.crawl_results) > 0:
					#database.connect()
					#database.begin()
					for result in Shared.crawl_results:
						crawled += 1
						pending -= 1
						if verbose:
							print "crawl result for: %s " % result.request
							if len(result.request.user_output) > 0:
								print "  user: %s" % json.dumps(result.request.user_output)
							if result.errors:
								print "* crawler errors: %s" % ", ".join(result.errors)

						#database.save_crawl_result(result, True)
						for req in result.found_requests:
    							######tips
    							#print req.url,req.data,req.method,Shared.allowed_domains

							if verbose:
								print "  new request found %s" % req
							
							urlfilt = HostFilter(req.url)
							if urlfilt.urlfilter():
								database.save_request(req,taskid)

							if request_is_crawlable(req) and req not in Shared.requests and req not in req_to_crawl:
								if request_depth(req) > Shared.options['max_depth'] or request_post_depth(req) > Shared.options['max_post_depth']:
									if verbose:
										print "  * cannot crawl: %s : crawl depth limit reached" % req
									result = CrawlResult(req, errors=[ERROR_CRAWLDEPTH])
									#database.save_crawl_result(result, False)
									continue

								if req.redirects > Shared.options['max_redirects']:
									if verbose:
										print "  * cannot crawl: %s : too many redirects" % req
									result = CrawlResult(req, errors=[ERROR_MAXREDIRECTS])
									#database.save_crawl_result(result, False)
									continue

								pending += 1
								req_to_crawl.append(req)

					Shared.crawl_results = []
				Shared.main_condition.release()

		except KeyboardInterrupt:
			print "\nTerminated by user"
			try:
				Shared.main_condition.release()
				Shared.th_condition.release()
			except:
				pass


	def check_user_script_syntax(self, probe_cmd, user_script):
		try:
			exe = CommandExecutor(probe_cmd + ["-u", user_script, "-v"] , False)
			out = exe.execute(5)
			if out:
				print "\n* USER_SCRIPT error: %s" % out
				sys.exit(1)
			stdoutw(". ")
		except KeyboardInterrupt:
			print "\nAborted"
			sys.exit(0)


	def init_crawl(self, start_req, check_starturl, get_robots_txt):
		start_requests = [start_req]
		try:
			if check_starturl:
				self.check_startrequest(start_req)
				stdoutw(". ")

			if get_robots_txt:
				rrequests = self.get_requests_from_robots(start_req)
				stdoutw(". ")
				for req in rrequests:
					if request_is_crawlable(req) and not req in start_requests:
						start_requests.append(req)
		except KeyboardInterrupt:
			print "\nAborted"
			sys.exit(0)

		return start_requests


	def main(self, argv):
		Shared.options = self.defaults
		Shared.th_condition = threading.Condition()
		Shared.main_condition = threading.Condition()


		probe_cmd = get_phantomjs_cmd()
		if not probe_cmd:
			print "Error: unable to find phantomjs executable"
			sys.exit(1)

		start_cookies = []
		start_referer = None

		probe_options = ["-R", self.randstr(20)]
		threads = []
		num_threads = self.defaults['num_threads']

		out_file = ""
		out_file_overwrite = self.defaults['out_file_overwrite']
		cookie_string = None
		display_progress = True
		verbose = False
		initial_checks = True
		http_auth = None
		get_robots_txt = True
		save_html = False
		user_script = None

		try:
			opts, args = getopt.getopt(argv, 'hc:t:jn:x:A:p:d:BGR:U:wD:s:m:C:qr:SIHFP:Ovu:')
		except getopt.GetoptError as err:
			print str(err)
			sys.exit(1)

		
		if len(args) < 1:
			self.usage()
			sys.exit(1)
		


		for o, v in opts:
			if o == '-h':
				self.usage()
				sys.exit(0)
			elif o == '-c':
				cookie_string = v
			elif o == '-C':
				try:
					with open(v) as cf:
						cookie_string = cf.read()
				except Exception as e:
					print "error reading cookie file"
					sys.exit(1)
			elif o == '-r':
				start_referer = v
			elif o == '-n':
				num_threads = int(v)
			elif o == '-t':
				Shared.options['process_timeout'] = int(v)
			elif o == '-q':
				display_progress = False
			elif o == '-A':
				http_auth = v
			elif o == '-p':
				if v == "tor": v = "socks5:127.0.0.1:9150"
				proxy =  v.split(":")
				if proxy[0] not in ("http", "socks5"):
					print "only http and socks5 proxies are supported"
					sys.exit(1)
				Shared.options['proxy'] = {"proto":proxy[0], "host":proxy[1], "port":proxy[2]}
			elif o == '-d':
				for ad in v.split(","):
					# convert *.domain.com to *.\.domain\.com
					pattern = re.escape(ad).replace("\\*\\.","((.*\\.)|)")
					Shared.allowed_domains.add(pattern)
			elif o == '-x':
				for eu in v.split(","):
					Shared.excluded_urls.add(eu)
			elif o == "-G":
				Shared.options['group_qs'] = True
			#elif o == "-w":
			#	out_file_overwrite = True
			elif o == "-R":
				Shared.options['max_redirects'] = int(v)
			elif o == "-U":
				Shared.options['useragent'] = v
			elif o == "-s":
				if not v in (CRAWLSCOPE_DOMAIN, CRAWLSCOPE_DIRECTORY, CRAWLSCOPE_URL):
					self.usage()
					print "* ERROR: wrong scope set '%s'" % v
					sys.exit(1)
				Shared.options['scope'] = v
			elif o == "-m":
				if not v in (CRAWLMODE_PASSIVE, CRAWLMODE_ACTIVE, CRAWLMODE_AGGRESSIVE):
					self.usage()
					print "* ERROR: wrong mode set '%s'" % v
					sys.exit(1)
				Shared.options['mode'] = v
			elif o == "-S":
				initial_checks = False
			elif o == "-I":
				get_robots_txt = False
			elif o == "-H":
				save_html = True
			elif o == "-D":
				Shared.options['max_depth'] = int(v)
			elif o == "-P":
				Shared.options['max_post_depth'] = int(v)
			elif o == "-O":
				Shared.options['override_timeout_functions'] = False
			elif o == "-F":
				Shared.options['crawl_forms'] = False
			elif o == "-u":
				if os.path.isfile(v):
					user_script = os.path.abspath(v)
				else:
					print "error: unable to open USER_SCRIPT"
					sys.exit(1)


		if Shared.options['scope'] != CRAWLSCOPE_DOMAIN and len(Shared.allowed_domains) > 0:
			print "* Warinig: option -d is valid only if scope is %s" % CRAWLSCOPE_DOMAIN

		if cookie_string:
			try:
				start_cookies = self.parse_cookie_string(cookie_string)
			except Exception as e:
				print "error decoding cookie string"
				sys.exit(1)

		if Shared.options['mode'] != CRAWLMODE_AGGRESSIVE:
			probe_options.append("-f") # dont fill values
		if Shared.options['mode'] == CRAWLMODE_PASSIVE:
			probe_options.append("-t") # dont trigger events

		if Shared.options['proxy']:
			probe_cmd.append("--proxy-type=%s" % Shared.options['proxy']['proto'])
			probe_cmd.append("--proxy=%s:%s" % (Shared.options['proxy']['host'], Shared.options['proxy']['port']))

		probe_cmd.append(self.base_dir + 'probe/analyze.js')


		if len(Shared.excluded_urls) > 0:
			probe_options.extend(("-X", ",".join(Shared.excluded_urls)))

		if save_html:
			probe_options.append("-H")

		if user_script:
			probe_options.extend(("-u", user_script))

		probe_options.extend(("-x", str(Shared.options['process_timeout'])))
		probe_options.extend(("-A", Shared.options['useragent']))

		if not Shared.options['override_timeout_functions']:
			probe_options.append("-O")

		Shared.probe_cmd = probe_cmd + probe_options


		Shared.starturl = normalize_url(args[0])
		#out_file = args[1]

		purl = urlsplit(Shared.starturl)
		try:
			pdomain = get_tld(Shared.starturl)
		except:
			pdomain = purl.hostname
		if purl.hostname == pdomain:
			Shared.allowed_domains.add(purl.hostname)
		else:
			Shared.allowed_domains.add(pdomain)
			Shared.allowed_domains.add(purl.hostname)


		for sc in start_cookies:
			Shared.start_cookies.append(Cookie(sc, Shared.starturl))


		start_req = Request(REQTYPE_LINK, "GET", Shared.starturl, set_cookie=Shared.start_cookies, http_auth=http_auth, referer=start_referer)

		if not hasattr(ssl, "SSLContext"):
			print "* WARNING: SSLContext is not supported with this version of python, consider to upgrade to >= 2.7.9 in case of SSL errors"

		if user_script and initial_checks:
			self.check_user_script_syntax(probe_cmd, user_script)

		start_requests = self.init_crawl(start_req, initial_checks, get_robots_txt)
		
		database = None
		fname = None
		try:
			database = self.init_db(fname, out_file)
		except Exception as e:
			print str(e)
		
		taskid = database.save_crawl_info(
			target = Shared.starturl,
			start_date = self.crawl_start_time,
			commandline = cmd_to_str(argv),
			user_agent = Shared.options['useragent']
		)
		self.taskid = taskid
		
		for req in start_requests:
    			urlfilt = HostFilter(req.url)
                if urlfilt.urlfilter():
    				database.save_request(req,self.taskid)

		print "initialized, crawl started with %d threads" % (num_threads)

		for n in range(0, num_threads):
			thread = CrawlerThread()
			threads.append(thread)
			thread.start()


		self.main_loop(threads, start_requests, database, display_progress, verbose,self.taskid)

		self.kill_threads(threads)

		self.crawl_end_time = int(time.time())

		print "Crawl finished, %d pages analyzed in %d minutes" % (Shared.requests_index, (self.crawl_end_time - self.crawl_start_time) / 60)
		database.update_crawl_info(self.taskid,self.crawl_end_time)
