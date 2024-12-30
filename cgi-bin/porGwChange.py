#!/usr/bin/env python
#
###############################################################################
# $Id: porGwChange.py
#
# Project:  porGwChange
# Purpose:  Script processes groundwater measurements to determine a list of 
#           seasonal interval available for a gw change map.
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
   os.environ['QUERY_STRING'] = 'SeasonalIntervals=Spring,02,03,04,Min Summer,05,06,07,Max Fall,08,09,10,Max Winter,12,01,02,Min&startingYear=1996'

if 'QUERY_STRING' in os.environ:
    #queryString = re.escape(os.environ['QUERY_STRING'])
    queryString = os.environ['QUERY_STRING']

    queryStringD = parse_qs(queryString, encoding='utf-8')

    myParmsL = [
        'SeasonalIntervals',
        'startingYear'
    ]

    for key, values in queryStringD.items():
        if key in myParmsL:
            params[key] = values[0]

# Check seasonal intervals
#
SeasonsL = []
if 'SeasonalIntervals' in params:
    Seasons = params['SeasonalIntervals']

    SeasonalIntervals = {}

    Intervals = Seasons.split()

    # Prepare intervals
    #
    for Interval in Intervals:

        IntervalL    = Interval.split(",")

        seasonName   = IntervalL.pop(0)
        seasonLevel  = IntervalL.pop(-1)
        seasonMonths = list(IntervalL)

        if seasonName not in SeasonsL:
            SeasonsL.append(seasonName)

        if seasonName not in SeasonalIntervals:
            SeasonalIntervals[seasonName] = {}

            SeasonalIntervals[seasonName]['Months'] = seasonMonths
            SeasonalIntervals[seasonName]['Level']  = seasonLevel

    #SeasonalIntervals.append(Interval.split(","))

else:
    message = "Provide seasonal interval information "
    print("Content-type:application/json\n\n")
    print('{ "message": "%s" }' % message)
    sys.exit()

# Check starting year
#
if 'startingYear' in params:
      startingYear = params['startingYear']
else:
    message = "Provide starting waterlevel year "
    print("Content-type:application/json\n\n")
    print('{ "message": "%s" }' % message)
    sys.exit()

# ------------------------------------------------------------
# -- Program header
# ------------------------------------------------------------
quiet           = False
debug           = False

program         = "USGS OWRD Seasonal Interval Script"
version         = "2.05"
version_date    = "December 29, 2024"

program_args    = []

# =============================================================================
def errorMessage(error_message):

   print("Content-type:application/json\n\n")
   print('{ "message": "%s" }' % message)
   sys.exit()

# =============================================================================

def processSeasons (waterlevel_file, SeasonsL, SeasonIntervals, startingYear):

    # Set
    #
    seasonsD    = {}
    seasonYears = []

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

                # Set measurement date
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

                wlSeason = "--"
                seasonS  = "--"

                # Check for valid records
                #
                site_id       = str(tempD['site_id'])

                lev_va        = tempD['lev_va']
                lev_web_cd    = tempD['lev_web_cd']
                lev_status_cd = tempD['lev_status_cd']

                # Check for status of water-level record
                #
                if str(lev_web_cd) == 'Y' and len(lev_va) > 0:

                    # Check starting year
                    #
                    if len(startingYear) > 0 and float(wlYear) < float(startingYear):
                        continue

                    # Prepare year
                    #
                    if wlYear not in seasonYears:
                        seasonYears.append(wlDate.year)

                    # Prepare intervals
                    #
                    for Season in SeasonalIntervals.keys():

                        MonthsL = SeasonalIntervals[Season]['Months']

                        if wlMonth in MonthsL:

                            # Check for year of water-level record [already included]
                            #
                            if wlYear not in seasonsD:
                                seasonsD[wlYear] = {}

                            # Check for water-level records
                            #
                            if Season not in seasonsD[wlYear]:

                                seasonsD[wlYear][Season] = 1

                            break
                    
    except FileNotFoundError:
        message = 'File %s not found' % waterlevel_file
        errorMessage(message)
    except PermissionError:
        message = 'No permission to access file %s' % waterlevel_file
        errorMessage(message)
    except Exception as e:
        message = 'An error occurred: %s' % e
        errorMessage(message)

    return seasonsD

# =============================================================================

# ----------------------------------------------------------------------
# -- Main program
# ----------------------------------------------------------------------
waterlevel_file  = "data/waterlevels.txt"
json_file        = "data/porGwChange.json"
siteInfoD        = {}
message          = ''

   
# Read
#
if os.path.exists(waterlevel_file):

   # Process file
   #
   seasonsD = processSeasons(waterlevel_file, SeasonsL, SeasonalIntervals, startingYear)
   
else:
   message = "Require a water-level file"
   print ("Content-type:application/json\n\n")
   print ('{ "message": "%s" }' % message)
   sys.exit()

# Prepare JSON output
# -------------------------------------------------
#
jsonL = []
jsonL.append('{')

# Loop through waterlevel information
#
recordsL = []
for year in sorted(seasonsD.keys()):

   myList   = []

   seasonsL = seasonsD[year].keys()

   if len(seasonsL) > 0:

       for mySeason in ['Spring', 'Summer', 'Fall', 'Winter']:
    
          if mySeason in seasonsL:
             myList.append(mySeason)   
    
       recordsL.append( '"%s": [ %s ]' % (year, ",".join('"{0}"'.format(w) for w in myList)))
   
jsonL.append("%s" % ",\n".join(recordsL))


# Finish json output
#
jsonL.append('}')

# Write file
# -------------------------------------------------
#
#if os.path.isfile(json_file):
#   os.remove(json_file)
#
## Open file
##
#fh = open(json_file, 'w')
#if fh is None:
#   message = "Can not open output file %s" % json_file
#   print ("Content-type:application/json\n\n")
#   print ('{ "message": "%s" }' % message)
#   sys.exit()
#
#fh.write("%s" % '\n'.join(jsonL))
#
#fh.close()

# Output json
# -------------------------------------------------
#
print ("Content-type:application/json\n\n")
print ('\n'.join(jsonL))


sys.exit()

