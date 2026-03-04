#!/usr/bin/env python3
#
###############################################################################
# $Id: /var/www/cgi-bin/klamath_wells/fixCollectionFile.py, v 1.28 2026/02/27 12:54:31 llorzol Exp $
# $Revision: 1.28 $
# $Date: 2026/02/27 12:54:31 $
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

from datetime import datetime

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

# Log operational messages
#
logging_file = "buildCollectionFile.txt"
if os.path.isfile(logging_file):
    os.remove(logging_file)

file_logger  = logging.getLogger('file_logger')
formatter    = logging.Formatter('%(message)s')
handler      = logging.FileHandler(logging_file)
handler.setFormatter(formatter)
file_logger.setLevel(logging.INFO)
file_logger.addHandler(handler)
file_logger.propagate = False

# Web requests
#
from WebRequest_mod import webRequest
from WebRequest_mod import buildURL

program         = "USGS OWRD CDWR Fix Collection File Script"
version         = "1.28"
version_date    = "February 27, 2026"
usage_message   = """
Usage: buildCollectionFile.py
                [--help]
                [--usage]
                [--sites       Name of present collection file listing sites]
                [--output      Name of output file containing processed well sites]
                [--county      Provide a list of county FIPS codes (5 digits) to search for USGS recorder sites]
                [--owrd        Provide a filename of OWRD site summary file containing recorder sites in text format]
                [--other       Provide a filename of OWRD other ID file containing sites in text format]
                [--count       Provide a minimum number of periodic measurements to qualify for adding new sites onto collection file]
                [--debug       Enable debug operational output to the screen]
"""

# =============================================================================

def processCollectionSites (itemColumn, columnL, linesL):

    siteInfoD  = {}
    siteCount  = 0

    itemColumn = itemColumn.lower()

    # Parse for column names [rdb format]
    #
    while 1:
        if linesL[0][0] == '#':
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
    if itemColumn not in namesL:
        message = "Missing index column " + itemColumn
        return message, {}

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

        indexSite = str(valuesL[ namesL.index(itemColumn) ])

        recordD = {}

        for column in columnL:

            if column in columnL:
                indexValue      = valuesL[ namesL.index(column) ]
                recordD[column] = indexValue
            else:
                message  = "Parsing issue for column %s " % column
                message += "Unable to parse %s" % Line
                return message, siteInfoD

            #print column,indexValue

        dec_lat_va     = recordD['dec_lat_va']
        dec_long_va    = recordD['dec_long_va']
        status         = "Active"
        gw_begin_date  = None
        gw_end_date    = None

        siteCount     += 1

        # Check for sites with no valid location
        #
        if len(dec_lat_va) < 1 or len(dec_long_va) < 1:
            continue

        if indexSite not in siteInfoD:
            siteInfoD[indexSite] = {}

        siteInfoD[indexSite]['agency_cd']          = recordD['agency_cd']
        siteInfoD[indexSite]['site_no']            = recordD['site_no']
        siteInfoD[indexSite]['cdwr_id']            = recordD['cdwr_id']
        siteInfoD[indexSite]['coop_site_no']       = recordD['coop_site_no']
        siteInfoD[indexSite]['state_well_nmbr']    = recordD['state_well_nmbr']
        siteInfoD[indexSite]['dec_lat_va']         = recordD['dec_lat_va']
        siteInfoD[indexSite]['dec_long_va']        = recordD['dec_long_va']
        siteInfoD[indexSite]['station_nm']         = recordD['station_nm']
        siteInfoD[indexSite]['status']             = status
        siteInfoD[indexSite]['gw_begin_date']      = gw_begin_date
        siteInfoD[indexSite]['gw_end_date']        = gw_end_date
        siteInfoD[indexSite]['gw_agency_cd']       = []
        siteInfoD[indexSite]['gw_count']           = 0
        siteInfoD[indexSite]['gw_status']          = 'Inactive'
        siteInfoD[indexSite]['rc_begin_date']      = ""
        siteInfoD[indexSite]['rc_end_date']        = ""
        siteInfoD[indexSite]['rc_agency_cd']       = []
        siteInfoD[indexSite]['rc_status']          = ""

    message = "Processed %d sites" % siteCount
    screen_logger.info(message)

    return message, siteInfoD
# =============================================================================

def processNwis (keyColumn, service_rdbL):

    serviceL    = []
    recordCount = 0
    message     = ''
    sitesD      = {}

    # Parse head lines
    #
    while len(service_rdbL) > 0:

        Line = service_rdbL[0].strip("\n|\r")
        del service_rdbL[0]

        # Grab column names in header
        #
        if Line[0] != '#':
            namesL = Line.split('\t')
            break

    # Format line in header section
    #
    del service_rdbL[0]

    # Check column names
    #
    if keyColumn not in namesL:
        message = "Missing index column " + keyColumn
        print("Content-type:application/json\n\n")
        print('{ "message": "%s" }' % message)
        sys.exit()

    # Parse data lines
    #
    while len(service_rdbL) > 0:

        Line = service_rdbL[0].strip("\n|\r")
        del service_rdbL[0]

        valuesL    = Line.split('\t')

        site_no    = str(valuesL[ namesL.index('site_no') ])

        # Check if site is commented out
        #
        if Line[0][0] != "#":

            # Check if site is already included
            #
            if site_no not in sitesD:

                sitesD[site_no] = {}

                for column in namesL:

                    indexValue      = valuesL[ namesL.index(column) ]
                    sitesD[site_no][column] = indexValue

    message = "Processed %d sites" % len(sitesD)
    screen_logger.info(message)

    return message, sitesD
# =============================================================================

# ----------------------------------------------------------------------
# -- Main program
# ----------------------------------------------------------------------
collection_file  = "data/collection.txt"
nwis_file        = "data/USGS/gw_coop_01.txt"
owrd_file        = "data/OWRD/gw_other_identity.txt"
siteInfoD        = {}
nwisInfoD        = {}

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
                "alt_datum_cd"
               ]

# Read
#
if os.path.exists(collection_file):

    # Parse entire file
    #
    with open(collection_file,'r') as f:
        linesL = f.read().splitlines()

    # Check for empty file
    #
    if len(linesL) < 1:
        message = "Empty collection file %s" % collection_file
        print("Content-type:application/json\n\n")
        print('{ "message": "%s" }' % message)
        sys.exit( 1 )

    # Process file
    #
    message, siteInfoD = processCollectionSites("site_id", mySiteFields, linesL)

else:
    message = "Require the path to the file with the list of sites"
    print("Content-type:application/json\n\n")
    print('{ "message": "%s" }' % message)
    sys.exit()

#print(siteInfoD)

# Read
#
if os.path.exists(nwis_file):

    # Parse entire file
    #
    with open(nwis_file,'r') as f:
        linesL = f.read().splitlines()

    if len(linesL) > 0:
        message, nwisInfoD = processNwis("site_no", linesL)

    else:
        print("Content-type:application/json\n\n")
        print('{ "message": "%s" }' % message)
        sys.exit()

else:
    message = "Require the nwis file"
    print("Content-type:application/json\n\n")
    print('{ "message": "%s" }' % message)
    sys.exit()


# Prepare sites
# -------------------------------------------------
#
writeFile = False
coopSite  = {}
cdwrSite  = {}

for site_id in siteInfoD:

    site_no      = siteInfoD[site_id]['site_no']
    coop_site_no = siteInfoD[site_id]['coop_site_no']
    cdwr_id      = siteInfoD[site_id]['cdwr_id']

    if len(site_no) > 0:

        if site_no in nwisInfoD:
            tempId     = nwisInfoD[site_no]['coop_site_no']
            if tempId[:4] == 'KLAM':
                coopSiteNo = tempId

                if len(coop_site_no) < 1:
                    coop_site_no = coopSiteNo
                    print("Site %s Coop %s" % (site_no, coop_site_no))
                    coopSite[site_id] = coop_site_no

                    writeFile = True


            elif tempId[:4] == 'CDWR':
                cdwrId     = tempId

                if len(cdwr_id) < 1:
                    cdwr_id = cdwrId[4:]
                    print("Site %s CDWR %s" % (site_no, cdwr_id))
                    cdwrSite[site_id] = cdwr_id

                    writeFile = True


# Prepare output
# -------------------------------------------------
#
message = "Outputting %d sites" % len(siteInfoD)
screen_logger.info(message)

if writeFile:

    outputLines = []

    # Parse entire file
    #
    with open(collection_file,'r') as f:
        linesL = f.read().splitlines()

    while len(linesL) > 0:

        if linesL[0][0] == '#':
            outputLines.append(linesL[0])

        elif linesL[0][0] == 's':
            outputLines.append(linesL[0])
            namesL = linesL[0].lower().split('\t')
            del linesL[0]

        elif len(linesL[0]) < 1:
            outputLines.append(linesL[0])

        else:
            valuesL = linesL[0].split('\t')

            site_id = str(valuesL[ namesL.index('site_id') ])

            if site_id in coopSite or site_id in cdwrSite:
                if site_id in coopSite:
                    valuesL[ namesL.index('coop_site_no') ] = coopSite[site_id]

                if site_id in cdwrSite:
                    valuesL[ namesL.index('cdwr_id') ] = cdwrSite[site_id]

                linesL[0] = "\t".join(valuesL)

            outputLines.append(linesL[0])

        del linesL[0]


    myFile = "temp.txt"
    with open(myFile, "w") as f:
        f.write("\n".join(outputLines))

sys.exit()
