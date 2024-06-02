#!/usr/bin/env python3
#
###############################################################################
# $Id: requestCollectionFile.py
#
# Project:  requestCollectionFile.py
# Purpose:  Script reads an tab-limited collection text file for USGS and OWRD
#           sites.
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

# ------------------------------------------------------------
# -- Set
# ------------------------------------------------------------
debug           = False

program         = "USGS OWRD CDWR Site Loading Script"
version         = "2.06"
version_date    = "January 21, 2023"

program_args    = []

# =============================================================================
def errorMessage(error_message):

   print("Content-type:application/json\n\n")
   print('{ "message": "%s" }' % message)
   sys.exit()

# =============================================================================
def processCollectionSites (collection_file, mySiteFields):

   siteInfoD   = {}
   siteCount   = 0

   keyColumn   = 'site_id'
   
   # Read collection or recorder file
   # -------------------------------------------------
   #
   with open(collection_file,'r') as f:
       linesL = f.read().splitlines()

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
   del linesL[0]

   # Check column names
   #
   if keyColumn not in namesL: 
      message = "Missing index column " + keyColumn
      errorMessage(message)

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
      site_id = str(valuesL[ namesL.index(keyColumn) ])
   
      if site_id not in siteInfoD:
         siteInfoD[site_id] = {}
   
      for myColumn in mySiteFields:
         if myColumn in namesL:
            if str(valuesL[ namesL.index(myColumn) ]) == 'None':
               myValue = ''
            else:
               myValue = str(valuesL[ namesL.index(myColumn) ])

            siteInfoD[site_id][myColumn] = myValue
         else:
            siteInfoD[site_id][myColumn] = None

   message = "Processed %d sites" % len(siteInfoD)
   screen_logger.info(message)
   
   return siteInfoD
# =============================================================================

def processSummarySites (file, mySiteFields):

   siteInfoD   = {}

   keyColumn   = 'site_id'
   
   # Read file
   # -------------------------------------------------
   #
   with open(file,'r') as f:
       linesL = f.read().splitlines()
   
   # Check for empty file
   #
   if len(linesL) < 1:
      message = "Empty file %s" % file
      errorMessage(message)

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
   del linesL[0]

   # Check column names
   #
   if keyColumn not in namesL: 
      message = "Missing index column %s in %s file" % (keyColumn, file)
      errorMessage(message)

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
      site_id = str(valuesL[ namesL.index(keyColumn) ])
   
      if site_id not in siteInfoD:
         siteInfoD[site_id] = {}
   
      for myColumn in mySiteFields:
         if myColumn in namesL:
            if str(valuesL[ namesL.index(myColumn) ]) == 'None':
               myValue = ''
            else:
               myValue = str(valuesL[ namesL.index(myColumn) ])

            siteInfoD[site_id][myColumn] = myValue
            
         if myColumn in ['gw_agency_cd', 'rc_agency_cd']:
            if len(siteInfoD[site_id][myColumn]) > 0:
               siteInfoD[site_id][myColumn] = siteInfoD[site_id][myColumn].split(',')
            

   message = "Processed %d sites" % len(siteInfoD)
   screen_logger.info(message)
   
   return siteInfoD
# =============================================================================

# ----------------------------------------------------------------------
# -- Main program
# ----------------------------------------------------------------------
collection_file   = "data/collection.txt"
site_summary_file = "data/site_summary.txt"

siteInfoD         = {}
summaryInfoD      = {}
   
# Set column names
#
mySiteFields = [
                "site_id",
                "agency_cd",
                "site_no",
                "coop_site_no",
                "cdwr_id",
                "state_well_nmbr",
                "station_nm",
                "dec_lat_va",
                "dec_long_va",
                "alt_va",
                "alt_acy_va",
                "alt_datum_cd",
                "well_depth_va",
                "periodic",
                "recorder",
                "gw_agency_cd",
                "gw_begin_date",
                "gw_end_date",
                "gw_count",
                "gw_status",
                "rc_agency_cd",
                "rc_begin_date",
                "rc_end_date",
                "rc_count",
                "rc_status",
                "usgs_begin_date",
                "usgs_end_date",
                "usgs_status",
                "usgs_count",
                "usgs_rc_begin_date",
                "usgs_rc_end_date",
                "usgs_rc_status",
                "usgs_rc_count",
                "owrd_begin_date",
                "owrd_end_date",
                "owrd_status",
                "owrd_count",
                "owrd_rc_begin_date",
                "owrd_rc_end_date",
                "owrd_rc_status",
                "owrd_rc_count",
                "cdwr_begin_date",
                "cdwr_end_date",
                "cdwr_status",
                "cdwr_count",
                "cdwr_rc_begin_date",
                "cdwr_rc_end_date",
                "cdwr_rc_status",
                "cdwr_rc_count"
               ]

# Read
#
if os.path.exists(collection_file):

   # Process file
   #
   siteInfoD = processCollectionSites(collection_file, mySiteFields)
   
else:
   message = "Require the path to the file with the list of sites"
   errorMessage(message)

#print(siteInfoD)

# Read
#
if os.path.exists(site_summary_file):

   # Process file
   #
   summaryInfoD = processSummarySites(site_summary_file, mySiteFields)
   
else:
   message = "Require the path to the summary file with the list of sites"
   errorMessage(message)

#print(summaryInfoD)


# Prepare JSON output
# -------------------------------------------------
#
message = "Outputting %d sites" % len(siteInfoD)
screen_logger.info(message)

jsonL = []
jsonL.append('{')
jsonL.append('  "type" : "FeatureCollection",')
#jsonL.append('  "crs" : {')
#jsonL.append('    "type" : "name",')
#jsonL.append('    "properties" : {')
#jsonL.append('                   "name" : "EPSG:4326"')
#jsonL.append('                   }')
#jsonL.append('           },')
jsonL.append('  "features" : [')

# Site information
#
features        = []

# Loop through site information
#
for site_id in sorted(siteInfoD.keys()):
   
   x_pt     = siteInfoD[site_id]['dec_long_va']
   y_pt     = siteInfoD[site_id]['dec_lat_va']
   
   feature  = '                {'
   feature += '"type": "Feature", '
   feature += '"geometry": {"type": "Point", "coordinates": [%s, %s]}, ' % (str(x_pt), str(y_pt))
   feature += '"properties": { '
   recordL = []
   recordL.append('"%s" : %s' % ('site_id', json.dumps(site_id)))
   for column in mySiteFields:
      myValue = None
      if column in siteInfoD[site_id]:
         if siteInfoD[site_id][column] is not None:
            myValue = json.dumps(siteInfoD[site_id][column])
      if column in summaryInfoD[site_id]:
         if summaryInfoD[site_id][column] is not None:
            myValue = json.dumps(summaryInfoD[site_id][column])

      if myValue is not None:
         recordL.append('"%s" : %s' % (column, myValue))
      else:
         recordL.append('"%s" : %s' % (column, "null"))

   feature += ", ".join(recordL)
   feature += '} }'
   features.append(feature)

jsonL.append('%s' % ",\n".join(features))
jsonL.append('               ]')

# Finish json output
#
jsonL.append('}')


# Output json
# -------------------------------------------------
#
print("Content-type:application/json\n\n")
print('\n'.join(jsonL))


sys.exit()

