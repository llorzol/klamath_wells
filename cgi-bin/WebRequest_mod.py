#!/usr/bin/env python3
#
###############################################################################
# $Id: WebRequest_mod.py
#
# Project:  WebRequest_mod.py
# Purpose:  Script manages the web requests to NwisWeb and other sources.
# 
# Author:   Leonard Orzol <llorzol@usgs.gov>
#
###############################################################################
# Copyright (c) Leonard Orzol <llorzol@usgs.gov>
# 
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
###############################################################################

# time
#
import time

# Regular expressions
#
import re

# Set up logging
#
import logging

# Web requests
#
import requests

# Disable requests logging handler to warning level
#
logging.getLogger("requests").setLevel(logging.WARNING)

# ------------------------------------------------------------
# -- Program
# ------------------------------------------------------------
program        = "USGS Web Requests Module Script"
version        = "2.01"
version_date   = "May 22, 2024"

# --------------------------------------------------------                
# -- Format URL string for screen display
# --------------------------------------------------------
def buildURL(parmsDict):

   urlArgs = []
   for key,value in parmsDict.items():
      urlArgs.append("%s=%s" % (key, value))

   return "&".join(urlArgs)
 
# ------------------------------------------------------------
# -- Web request
# ------------------------------------------------------------

def webRequest(url_request, parmsDict, contentType, timeout, cookie, screen_logger):

   pattern    = re.compile(contentType)

   # Set timer
   #
   start_ts   = time.time()
   
   # Set return content
   #
   content    = None
      
   # Print url
   #
   screen_logger.debug("Url request: " + url_request)

   # Send url request
   #
   try:
      agent      = requests.get(url_request, params=parmsDict, cookies=cookie, timeout = timeout)

      # -- Debug message
      #
      elapsed  = time.time() - start_ts
      screen_logger.debug('Web request completed in %.3f seconds' % elapsed)

      # Status code 200
      #
      if agent.status_code == requests.codes.ok:
   
         content_type = agent.headers.get('content-type')
   
         # Content type matches type requested
         #
         if pattern.match(content_type):
   
            content = agent.text
   
         # Content type other than type requested
         #
         else:
            content = None
   
            message  = "Web request failed: " + url_request + "\n"
            message += "Content type should be text returned content type " + content_type
            screen_logger.info(message)
      
      # Error status code != 200
      #
      else:
         content = None
   
         message  = "Web request failed: " + url_request + "\n"
         message += "Status code %d" % agent.status_code
         screen_logger.info(message)

   # Response code
   #
   except requests.exceptions.HTTPError as errh:
      message  = "Web request failed: " + url_request + "\n"
      message += errh.args[0]
      screen_logger.info(message)

   # Request timeout
   #
   except requests.exceptions.Timeout as errrt:
      message  = "Web request failed: " + url_request + "\n"
      message += "Time out encountered"
      screen_logger.info(message)

   # Connection error
   #
   except requests.exceptions.ConnectionError as conerr:
      message  = "Web request failed: " + url_request + "\n"
      message += "Connection error encountered"
      screen_logger.info(message)

   # Too many redirects
   #
   except requests.exceptions.TooManyRedirects:
      message  = "Web request failed: " + url_request + "\n"
      message += "Too many redirects"
      screen_logger.info(message)

   # Exception request
   #
   except requests.exceptions.RequestException as e:
      message  = "Web request failed: " + url_request + "\n"
      message += e
      screen_logger.info(message)

   # Other
   #
   except:
      message  = "Web request failed: " + url_request + "\n"
      screen_logger.info(message)
      
   # - Record message
   # -----------------------------------------------------------
   elapsed = time.time() - start_ts
   message = "Web request finished in %.2f seconds" % elapsed
   screen_logger.debug(message)

   return message, content
# =============================================================================
