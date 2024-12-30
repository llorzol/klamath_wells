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

import csv

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
from urllib.parse import urlparse, parse_qs

# Parse the Query String
#
params = {}

HardWired = None
#HardWired = 1

if HardWired is not None:
   os.environ['QUERY_STRING'] = 'seasonOne=2001,03,04,05,Min&seasonTwo=2024,03,04,05,Min'

if 'QUERY_STRING' in os.environ:
    #queryString = re.escape(os.environ['QUERY_STRING'])
    queryString = os.environ['QUERY_STRING']

    queryStringD = parse_qs(queryString, encoding='utf-8')

    myParmsL = [
        'seasonOne',
        'seasonTwo'
    ]

    for key, values in queryStringD.items():
        if key in myParmsL:
            params[key] = values[0]

# Check arguements
#
if 'seasonOne' in params:
   seasonOne = params['seasonOne']

else:
    message = "Provide seasonal one information "
    print("Content-type:application/json\n\n")
    print('{ "message": "%s" }' % message)
    sys.exit()

if 'seasonTwo' in params:
   seasonTwo = params['seasonTwo']

else:
    message = "Provide seasonal two information "
    print("Content-type:application/json\n\n")
    print('{ "message": "%s" }' % message)
    sys.exit()

# ------------------------------------------------------------
# -- Set
# ------------------------------------------------------------
debug           = False

program         = "Groundwater Water-Level Change Of Record Script"
version         = "2.05"
version_date    = "December 29, 2024"

program_args    = []

# =============================================================================
def errorMessage(error_message):

   print("Content-type:application/json\n\n")
   print('{ "message": "%s" }' % message)
   sys.exit()

# =============================================================================

def processWls (waterlevel_file, SeasonOne, SeasonTwo):

    # Set
    #
    SitesD        = {}
    season1SitesD = {}
    season2SitesD = {}

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

    # Create a CSV reader object and remove comment header lines
    #
    try:
        with open(waterlevel_file, "r") as fh:
            csv_reader = csv.DictReader(filter(lambda row: row[0]!='#', fh), delimiter='\t')

            # Loop through file
            #
            for tempD in csv_reader:

                # Set empty value to None
                #
                for key, value in tempD.items():
                    if len(value) < 1:
                        tempD[key] = None

                # Check for valid records
                #
                lev_va        = tempD['lev_va']
                lev_web_cd    = tempD['lev_web_cd']

                # Check for valid records
                #
                if lev_web_cd == 'Y' and lev_va is not None:

                    # Check for measurement
                    #
                    lev_dtm       = str(tempD['lev_dtm'])[:10]
                    lev_str_dt    = str(tempD['lev_str_dt'])
                    lev_dt_acy_cd = str(tempD['lev_dt_acy_cd'])

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

                    # Set month and year
                    #
                    wlMonth  = '%02d' % wlDate.month
                    wlYear   = wlDate.year

                    # Since Winter Dec, Jan, Feb for year of Dec
                    #
                    if wlMonth in ['01', '02']:
                        wlYear -= 1

                    siteFlag = []

                    site_id = tempD['site_id']

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
                     
    except FileNotFoundError:
        message = 'File %s not found' % waterlevel_file
        errorMessage(message)
    except PermissionError:
        message = 'No permission to access file %s' % waterlevel_file
        errorMessage(message)
    except Exception as e:
        message = 'An error occurred: %s' % e
        errorMessage(message)
        
    return season1SitesD, season2SitesD

# =============================================================================

# ----------------------------------------------------------------------
# -- Main program
# ----------------------------------------------------------------------
waterlevel_file  = "data/waterlevels.txt"
siteInfoD        = {}

# Read
#
if os.path.exists(waterlevel_file):

   # Process file
   #
   season1SitesD, season2SitesD = processWls(waterlevel_file, seasonOne, seasonTwo)
   
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

   if site_id in ['425804121344701', '430649121305201', '430029121552101']:
      screen_logger.info("Site %s one -> %s two -> %s" % (site_id, (",").join(season1SitesD[site_id]), (",").join(season2SitesD[site_id])))
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

      if site_id in ['425804121344701', '430649121305201', '430029121552101']:
         message = "Site %s one -> %s two -> %s = %s" % (site_id, str(valueSeasonOne),  str(valueSeasonTwo), str(deltaGw))
         screen_logger.info(message)

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

