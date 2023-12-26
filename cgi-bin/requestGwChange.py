#!/usr/bin/env python
#
###############################################################################
# $Id: requestGwChange.py
#
# Project:  requestGwChange
# Purpose:  Script processes groundwater measurements to determine a value of
#           water-level change between a user specified begin and end
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
import cgi

# Create instance of FieldStorage
#
params = cgi.FieldStorage()

# ------------------------------------------------------------
# -- Set
# ------------------------------------------------------------
debug           = False

program         = "Groundwater Water-Level Change Of Record Script"
version         = "2.03"
version_date    = "October 1, 2023"

program_args    = []

# =============================================================================

def processWls (keyColumn, SeasonOne, SeasonTwo, columnL, linesL):

   SitesD        = {}
   season1SitesD = {}
   season2SitesD = {}
   message       = ''

   keyColumn     = keyColumn.lower()

   tmpList       = SeasonOne.split(",")
   BeginYear     = tmpList.pop(0)
   StatSeasonOne = tmpList.pop(-1)
   BeginMonths   = list(tmpList)

   tmpList       = SeasonTwo.split(",")
   EndYear       = tmpList.pop(0)
   StatSeasonTwo = tmpList.pop(-1)
   EndMonths     = list(tmpList)

   message = 'Begin %s %s %s' % (BeginYear, StatSeasonOne, " & ".join(BeginMonths))
   screen_logger.debug(message)
   #file_logger.info(message)

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

      # Check for valid records
      #
      lev_va        = valuesL[ namesL.index('lev_va') ]
      lev_web_cd    = valuesL[ namesL.index('lev_web_cd') ]
      lev_status_cd = valuesL[ namesL.index('lev_status_cd') ]
      
      # Check for valid records
      #
      if lev_web_cd == 'Y' and len(lev_va) > 0:
          
         # Check for measurement
         #
         lev_dtm = str(valuesL[ namesL.index('lev_dtm') ])[:10]
         lev_str_dt    = str(valuesL[ namesL.index('lev_str_dt') ])
         lev_dt_acy_cd = str(valuesL[ namesL.index('lev_dt_acy_cd') ])
   
         # Partial date YYYY | YYYY-MM
         #
         if lev_dt_acy_cd in ['Y','M']:
            continue
       
         # Full date YYYY-MM-DD | MM-DD-YYYY
         #
         elif lev_dt_acy_cd == 'D':
   
            tempDate = datetime.datetime.strptime(lev_str_dt, '%Y-%m-%d')
            wlDate   = tempDate.replace(hour=12)
       
         # Full date YYYY-MM-DD HH:MM | MM-DD-YYYY HH:MM
         #
         else:
   
            wlDate = datetime.datetime.strptime(lev_str_dt, '%Y-%m-%d %H:%M')
   
         wlMonth  = '%02d' % wlDate.month
         wlYear   = wlDate.year

         siteFlag = []
         
         # Since Winter Dec, Jan, Feb for year of Dec
         #
         if wlMonth == '12':
            wlYear += 1
   
         site_id = str(valuesL[ namesL.index('site_id') ])

         # Check for measurement year in Season 1
         #
         if str(wlYear) == BeginYear and wlMonth in BeginMonths:
            
            if site_id not in season1SitesD:
               season1SitesD[site_id] = []
               
            season1SitesD[site_id].append(lev_va)

            siteFlag.append('Yes Begin')

         # Check for measurement year in Season 2
         #
         if str(wlYear) == EndYear and wlMonth in EndMonths:
           
            if site_id not in season2SitesD:
               season2SitesD[site_id] = []
               
            season2SitesD[site_id].append(lev_va)

            siteFlag.append('Yes End')

         message = 'Site %s %s %s %s' % (site_id, str(wlYear), wlMonth, " & ".join(siteFlag))
         screen_logger.debug(message)
         #file_logger.info(message)
         
   return season1SitesD, season2SitesD

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


# Check begin and end dates
#
# Start Year 1996
#
# // Set starting and ending seasons
# //-----------------------------------------------
# var SeasonIntervals = { 
#                         'Spring': ['03-20', '06-20', 'Min'],
#                         'Summer': ['06-21', '09-21', 'Max'],
#                         'Fall'  : ['09-22', '12-20', 'Max'],
#                         'Winter': ['12-21', '03-19', 'Min']
#                       };
# var SeasonIntervals = { 
#                         'Spring': ['03-01', '05-31', 'Min'],
#                         'Summer': ['06-01', '08-31', 'Max'],
#                         'Fall'  : ['09-01', '11-30', 'Max'],
#                         'Winter': ['12-01', '02-28', 'Min']
#                       };

#
# https://staging-or.water.usgs.gov/cgi-bin/harney/requestGwChange.py?seasonOne=2001-01-01,20011-03-31,Min&seasonTwo=2020-01-01,20201-03-31,Min

HardWired = None
#HardWired = 1

# Set input
#
if HardWired is not None:
   params= {}
   params['seasonOne'] = '2019,12,01,02,Min'
   params['seasonTwo'] = '2020,12,01,02,Min'

# Check arguements
#
if 'seasonOne' in params:
   if HardWired is None:
      seasonOne      = params.getvalue('seasonOne')
   else:
      seasonOne      = params['seasonOne']

if 'seasonTwo' in params:
   if HardWired is None:
      seasonTwo      = params.getvalue('seasonTwo')
   else:
      seasonTwo      = params['seasonTwo']

if HardWired is not None:

   screen_logger.setLevel(logging.INFO)

   logging_file = "requestGwChange.txt"
   if os.path.isfile(logging_file):
      os.remove(logging_file)

   formatter    = logging.Formatter('%(message)s')
   handler      = logging.FileHandler(logging_file)
   handler.setFormatter(formatter)
   file_logger  = logging.getLogger('file_logger')
   file_logger.setLevel(logging.INFO)
   file_logger.addHandler(handler)
   file_logger.propagate = False

# Read
#
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
   season1SitesD, season2SitesD = processWls(keyColumn, seasonOne, seasonTwo, myGwFields, linesL)
   
else:
   message = "Require a begining and ending date"
   print("Content-type:application/json\n\n")
   print('{ "message": "%s" }' % message)
   sys.exit()

# No sites for user specified interval
# -------------------------------------------------
#
if len(season1SitesD) < 1 or len(season2SitesD) < 1:
    seasons = seasonOne.split(',')
    season1 = "Year %s and months %s" % (seasons[0], ", ".join(seasons[1:4]))
    seasons = seasonTwo.split(',')
    season2 = "Year %s and months %s" % (seasons[0], ", ".join(seasons[1:4]))
    message = "No site(s) were measured in both the %s interval and the %s interval" % (season1, season2)
    print("Content-type:application/json\n\n")
    print('{ "message": "%s" }' % message)
    sys.exit( 1 )

# Loop through waterlevel information
#
recordsL      = []
countSites    = 0

season1SitesL = set(season1SitesD.keys())
season2SitesL = set(season2SitesD.keys())
Sites1L       = list(season1SitesL.intersection(season2SitesL))

for site_id in sorted(Sites1L):

   countSites += 1

   screen_logger.debug("Site %s one -> %s two -> %s" % (site_id, (",").join(season1SitesD[site_id]), (",").join(season2SitesD[site_id])))
      
   valueSeasonOne = None
      
   lev_vas = season1SitesD[site_id]

   # Default behavior of Python is to sort ascending, that is, smallest to largest.
   # Reverse sort (reverse=True) sorts in descending order (largest to smallest).
   # If the 2nd element of the seasonOne object = 'Min', the lev_vas object is sorted in descending order and the value for that season (valueSeasonOne[0]) will be the largest value in the list.
   # If the 2nd element of the seasonOne object = 'Max', the lev_vas object is sorted in ascending order and the value for that season (valueSeasonOne[0]) will be the smallest value in the list.

   if seasonOne[-1] == 'Min':
      lev_vas.sort(reverse=True)
   else:
      lev_vas.sort()

   valueSeasonOne = lev_vas[0]

   ##print "\tone -> %s" % str(valueSeasonOne)
      
   lev_vas = season2SitesD[site_id]

   if seasonTwo[-1] == 'Min':
      lev_vas.sort(reverse=True)
   else:
      lev_vas.sort()

   valueSeasonTwo = lev_vas[0]

   ##print "\ttwo -> %s" % str(valueSeasonTwo)

   if valueSeasonOne is not None and valueSeasonTwo is not None:
      deltaGw = float(valueSeasonOne) - float(valueSeasonTwo)
      ##print "\t\tdeltaGw -> %s" % str(deltaGw)
         
      recordString = '"%s": %.2f' % (site_id, deltaGw)
      recordsL.append(recordString.replace("\'","\""))

# No sites for user specified interval
# -------------------------------------------------
#
if countSites < 1:
    seasons = seasonOne.split(',')
    season1 = " to ".join([seasons[0], seasons[1]])
    seasons = seasonTwo.split(',')
    season2 = " to ".join([seasons[0], seasons[1]])
    message = "No site(s) were measured in both the %s interval and the %s interval" % (season1, season2)
    print("Content-type:application/json\n\n")
    print('{ "message": "%s" }' % message)
    sys.exit( 1 )

# Prepare JSON output
# -------------------------------------------------
#
jsonL = []
jsonL.append('{')
jsonL.append("%s" % ",\n".join(recordsL))
jsonL.append('}')

# Output json
# -------------------------------------------------
#
print("Content-type:application/json\n\n")
print('\n'.join(jsonL))


sys.exit()

