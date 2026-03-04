#!/usr/bin/env python3
#
###############################################################################
# $Id: /var/www/cgi-bin/klamath_wells/requestCollectionFile.py, v 3.02 2026/02/27 10:29:05 llorzol Exp $
# $Revision: 3.02 $
# $Date: 2026/02/27 10:29:05 $
# $Author: llorzol $
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

import csv

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
version         = "3.02"
version_date    = "February 27, 2026"

program_args    = []

# =============================================================================
def errorMessage(error_message):

    print("Content-type:application/json\n\n")
    print('{ "message": "%s" }' % error_message)
    sys.exit()

# =============================================================================
def processCollectionSites (collection_file):

    siteInfoD   = {}

    # Read collection file
    # -------------------------------------------------
    #
    try:
        with open(collection_file, newline='', encoding='utf-8') as fh:

            # Create a reader object, specifying the tab delimiter
            #
            collectionSitesL = list(csv.DictReader(filter(lambda row: row[0]!='#' and len(row) > 0, fh), delimiter='\t'))

    except FileNotFoundError:
        message = f"Error: The file '{collection_file}' was not found."
        screen_logger.info(message)
        errorMessage(message)
    except Exception as e:
        message = f"An error occurred: {e}"
        screen_logger.info(message)
        errorMessage(message)


    # Process list from collection file to dictionary
    #
    siteInfoD = dict({x['site_id']:x for x in collectionSitesL})

    message = "Processed %d sites" % len(siteInfoD)
    screen_logger.info(message)

    return siteInfoD
# =============================================================================

def processSummarySites (summary_file):

    siteInfoD   = {}

    keyColumn   = 'site_id'

    # Read summary file
    # -------------------------------------------------
    #
    try:
        with open(summary_file, newline='', encoding='utf-8') as fh:

            # Create a reader object, specifying the tab delimiter
            #
            collectionSitesL = list(csv.DictReader(filter(lambda row: row[0]!='#' and len(row) > 0, fh), delimiter='\t'))

    except FileNotFoundError:
        message = f"Error: The file '{summary_file}' was not found."
        screen_logger.info(message)
        errorMessage(message)
    except Exception as e:
        message = f"An error occurred: {e}"
        screen_logger.info(message)
        errorMessage(message)


    # Process list from collection file to dictionary
    #
    siteInfoD = dict({x['site_id']:x for x in collectionSitesL})

    for site_id in sorted(siteInfoD.keys()):
        for myColumn in ['gw_agency_cd', 'rc_agency_cd']:
            if len(siteInfoD[site_id][myColumn]) > 0:
                siteInfoD[site_id][myColumn] = siteInfoD[site_id][myColumn].split(',')

    message = "Processed %d sites from summary file" % len(siteInfoD)
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
    siteInfoD = processCollectionSites(collection_file)

else:
    message = "Require the path to the file with the list of sites"
    errorMessage(message)

#print(siteInfoD)

# Read
#
if os.path.exists(site_summary_file):

    # Process file
    #
    summaryInfoD = processSummarySites(site_summary_file)

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
