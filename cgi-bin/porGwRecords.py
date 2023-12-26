#!/usr/bin/env python
#
###############################################################################
# $Id: porGwRecords.py
#
# Project:  porGwRecords
# Purpose:  Script processes groundwater measurements to determine a list of with
#           sites that have a measurement between a user specified begin and end
#           dates.
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

import os, sys, string, re

import datetime

import subprocess

import json

# Set up logging
#
import logging

# -- Set logging file
#
# Create screen handler
#
screen_logger = logging.getLogger()
formatter     = logging.Formatter(fmt='%(message)s')
console       = logging.StreamHandler()
console.setFormatter(formatter)
screen_logger.addHandler(console)
screen_logger.setLevel(logging.INFO)

# Import modules for CGI handling
#
import cgi, cgitb 

# Create instance of FieldStorage
#
params = cgi.FieldStorage()

# ------------------------------------------------------------
# -- Set
# ------------------------------------------------------------
debug           = False

program         = "USGS OWRD Groundwater Measurements Period Of Record Script"
version         = "2.03"
version_date    = "October 2, 2023"

program_args    = []

# =============================================================================

def processWls (keyColumn, beginDate, endDate, columnL, linesL):

   serviceL    = []
   recordCount = 0
   message     = ''
   sitesD      = {}

   keyColumn   = keyColumn.lower()

   BeginDate   = datetime.datetime.strptime(beginDate, '%Y-%m-%d')
   EndDate     = datetime.datetime.strptime(endDate, '%Y-%m-%d')

   # Parse for column names [rdb format]
   #
   while 1:
      if len(linesL) < 1:
         del linesL[0]
      elif linesL[0][0] == '#':
         del linesL[0]
      else:
         namesL = linesL[0].lower().split('\t')
         del linesL[0]
         break

   # Format line in header section
   #
   #del linesL[0]

   # Check column names
   #
   if keyColumn not in namesL:
      message = "Missing index column " + keyColumn
      print("Content-type:application/json\n\n")
      print('{ "message": "%s" }' % message)
      sys.exit()

   # Parse data lines
   #
   while len(linesL) > 0:
      
      if len(linesL[0]) < 1:
         del linesL[0]
         continue
      
      if linesL[0][0] == '#':
         del linesL[0]
         continue

      Line    = linesL[0]
      del linesL[0]

      valuesL = Line.split('\t')

      lev_dtm = str(valuesL[ namesL.index('lev_dtm') ])[:10]
    
      # Partial date
      #
      if len(lev_dtm) < 10:
         continue
    
      # Full date YYYY-MM-DD | MM-DD-YYYY
      #
      elif len(lev_dtm) <= 10:

         if re.search('^(\d{4})-', lev_dtm):
            tempDate = datetime.datetime.strptime(lev_dtm, '%Y-%m-%d')
                  
         elif re.search('^(\d{2})-', lev_dtm):
            tempDate = datetime.datetime.strptime(lev_dtm, '%m-%d-%Y')
               
         wlDate   = tempDate.replace(hour=12)
    
      # Full date YYYY-MM-DD HH:MM | MM-DD-YYYY HH:MM
      #
      elif len(lev_dtm) <= 16:

         if re.search('^(\d{4})-', lev_dtm):
            if re.search('(\d{2}:\d{2})', lev_dtm):
               wlDate = datetime.datetime.strptime(lev_dtm, '%Y-%m-%d %H:%M')
            else:
               wlDate = datetime.datetime.strptime(lev_dtm, '%Y-%m-%d %H%M')
            
         elif re.search('^(\d{2})-', lev_dtm):
            if re.search('(\d{2}:\d{2})', lev_dtm):
               wlDate = datetime.datetime.strptime(lev_dtm, '%m-%d-%Y %H:%M')
            else:
               wlDate = datetime.datetime.strptime(lev_dtm, '%m-%d-%Y %H%M')
    
      # Full date YYYY-MM-DD HH:MM:SS | MM-DD-YYYY HH:MM:SS
      #
      else:
         lev_dtm = lev_dtm[:-3].strip()

         if re.search('^(\d{4})-', lev_dtm):
            if re.search('(\d{2}:\d{2})', lev_dtm):
               wlDate = datetime.datetime.strptime(lev_dtm, '%Y-%m-%d %H:%M')
            else:
               wlDate = datetime.datetime.strptime(lev_dtm, '%Y-%m-%d %H%M')
                  
         elif re.search('^(\d{2})-', lev_dtm):
            if re.search('(\d{2}:\d{2})', lev_dtm):
               wlDate = datetime.datetime.strptime(lev_dtm, '%m-%d-%Y %H:%M')
            else:
               wlDate = datetime.datetime.strptime(lev_dtm, '%m-%d-%Y %H%M')

      # Check for valid records
      #
      site_id       = str(valuesL[ namesL.index('site_id') ])
      
      lev_va        = valuesL[ namesL.index('lev_va') ]
      lev_web_cd    = valuesL[ namesL.index('lev_web_cd') ]
      lev_status_cd = valuesL[ namesL.index('lev_web_cd') ]
   
      # Check for valid records
      #
      if lev_web_cd == 'Y' and len(lev_va) > 0:
   
         # Check if site is already included
         #
         if site_id not in sitesD:
   
            # Check for water-level records
            #
            if (wlDate - BeginDate).days >= 0 and (wlDate - EndDate).days <= 0:

               sitesD[site_id] = 1
            
               recordCount += 1

   return message, sitesD

# =============================================================================

# ----------------------------------------------------------------------
# -- Main program
# ----------------------------------------------------------------------
waterlevel_file  = "data/waterlevels.txt"
siteInfoD        = {}
message          = ''
   
# Set column names
#
myGwFields = [
                "site_id",
                "site_no",
                "agency_cd",
                "coop_site_no",
                "lev_va",
                "lev_acy_cd",
                "lev_dtm",
                "lev_dt",
                "lev_tm",
                "lev_tz_cd",
                "lev_dt_acy_cd",
                "lev_str_dt",
                "lev_status_cd",
                "lev_meth_cd",
                "lev_agency_cd",
                "lev_src_cd",
                "lev_web_cd",
                "lev_rmk_tx"
               ]
   
# Set 
#
keyColumn = 'site_id'

HardWired = None
HardWired = 1

# Set input
#
if HardWired is not None:
   params= {}
   params['beginDate'] = '1959-05-22'
   params['endDate']   = '1970-08-21'

# Check begin and end dates
#
if 'beginDate' in params:
   if HardWired is None:
      beginDate      = params.getvalue('beginDate')
   else:
      beginDate      = params['beginDate']

if 'endDate' in params:
   if HardWired is None:
      endDate      = params.getvalue('endDate')
   else:
      endDate      = params['endDate']

if os.path.exists(waterlevel_file):

   # Parse entire file
   #
   with open(waterlevel_file,'r') as f:
       linesL = f.read().splitlines()

   # Check for empty file
   #
   if len(linesL) < 1:
      message = "Empty waterlevel file %s" % waterlevel_file
      print("Content-type:application/json\n\n")
      print('{ "message": "%s" }' % message)
      sys.exit( 1 )

   # Process file
   #
   message, siteInfoL = processWls(keyColumn, beginDate, endDate, myGwFields, linesL)
   
else:
   message = "Require a beginnin and ending date"
   print "Content-type:application/json\n\n"
   print '{ "message": "%s" }' % message
   sys.exit()

# Prepare JSON output
# -------------------------------------------------
#
jsonL = []
jsonL.append('{')
#jsonL.append('  "%s" : {' % site_id)

jsonL.append('    "number_of_sites" : %d,' % len(siteInfoL))

# Loop through waterlevel information
#
recordsL = []
for site_no in sorted(siteInfoL):
   recordString = '"%s"' % site_no
   recordsL.append(recordString.replace("\'","\""))
   
jsonL.append('    "siteList" : [')
jsonL.append("%s" % ",\n".join(recordsL))
jsonL.append('               ]')
#jsonL.append('  },')

# Finish json output
#
jsonL.append('}')

# Output json
# -------------------------------------------------
#
print "Content-type:application/json\n\n"
print '\n'.join(jsonL)


sys.exit()

