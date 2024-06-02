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
# -- Program header
# ------------------------------------------------------------
quiet           = False
debug           = False

program         = "USGS OWRD Seasonal Interval Script"
version         = "2.04"
version_date    = "February 9, 2024"

program_args    = []

# =============================================================================

def processSeasons (keyColumn, SeasonsL, SeasonIntervals, startingYear, columnL, linesL):

   serviceL    = []
   recordCount = 0
   yearCount   = 0
   message     = ''
   seasonsD    = {}
   seasonYears = []

   keyColumn   = keyColumn.lower()

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

      lev_dtm       = str(valuesL[ namesL.index('lev_dtm') ])[:10]
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
      
      # Since Winter Dec, Jan, Feb for year of Dec
      #
      if wlMonth in ['01', '02']:
         wlYear -= 1

      wlSeason = "--"
      seasonS  = "--"

      # Check for valid records
      #
      site_id       = str(valuesL[ namesL.index('site_id') ])
      
      lev_va        = valuesL[ namesL.index('lev_va') ]
      lev_web_cd    = valuesL[ namesL.index('lev_web_cd') ]
      lev_status_cd = valuesL[ namesL.index('lev_status_cd') ]
      
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
      
      # Check for status of water-level record
      #
      screen_logger.debug(' %-15s %-15s %-15s %-15s\n' % (site_id, lev_str_dt, str(wlYear), str(wlMonth)))
      screen_logger.debug(' %-15s %-15s %-15s %-6s\n' % (site_id, lev_str_dt, seasonS, lev_web_cd))
      #sys.exit()

   return message, seasonsD

# =============================================================================

# ----------------------------------------------------------------------
# -- Main program
# ----------------------------------------------------------------------
waterlevel_file  = "data/waterlevels.txt"
json_file        = "data/porGwChange.json"
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
#HardWired = 1

# Set input
#
if HardWired is not None:
   params= {}
   params['SeasonalIntervals'] = 'Spring,02,03,04,Min Summer,05,06,07,Max Fall,08,09,10,Max Winter,12,01,02,Min'
   params['SeasonalIntervals'] = 'Spring,02-01,04-30,Min Summer,05-01,07-31,Max Fall,08-01,10-31,Max Winter,11-01,01-31,Min'
   params['SeasonalIntervals'] = 'Winter,12,01,02,Min Spring,02,03,04,Min Summer,05,06,07,Max Fall,08,09,10,Max'
   params['startingYear']      = '1996'

# Check seasonal intervals
#
SeasonsL = []
if 'SeasonalIntervals' in params:
   if HardWired is None:
      Seasons = params.getvalue('SeasonalIntervals')
   else:
      Seasons = params['SeasonalIntervals']

   SeasonalIntervals = {}

   Intervals = Seasons.split(" ")

#   screen_logger.info('Intervals %s' % "|".join(Intervals))

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

   #screen_logger.info(SeasonalIntervals)
   #sys.exit()

else:
   message = "Provide seasonal interval information "
   print ("Content-type:application/json\n\n")
   print ('{ "message": "%s" }' % message)
   sys.exit()

# Check starting year
#
if 'startingYear' in params:
   if HardWired is None:
      startingYear = params.getvalue('startingYear')
   else:
      startingYear = params['startingYear']

   
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
   message, seasonsD = processSeasons(keyColumn, SeasonsL, SeasonalIntervals, startingYear, myGwFields, linesL)
   
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

