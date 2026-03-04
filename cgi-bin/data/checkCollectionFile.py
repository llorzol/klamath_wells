#!/usr/bin/env python3
#
###############################################################################
# $Id: /var/www/cgi-bin/klamath_wells/checkCollectionFile.py, v 1.02 2026/02/27 10:29:05 llorzol Exp $
# $Revision: 1.02 $
# $Date: 2026/02/27 10:29:05 $
# $Author: llorzol $
#
# Project:  checkCollectionFile.py
# Purpose:  Script determines if the sites listed a tab-limited text collection file of well sites
#           file of well sites from USGS, OWRD, and CDWR sources are located
#           within the Upper Klamath Basin.
#
# Author:   Leonard Orzol <llorzol@usgs.gov>
#
###############################################################################
# Copyright (c) Oregon Water Science Center
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

import argparse

from shapely.geometry import shape, Point, Polygon

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
screen_logger.propagate = False

# Log operational messages
#
logging_file = "fixCollectionFile.txt"
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

program         = "USGS Check Collection File Script"
version         = "1.02"
version_date    = "February 27, 2026"
usage_message   = """
Usage: checkCollectionFile.py
                [--help]
                [--usage]
                [--sites       Name of present collection file listing sites]
                [--output      Name of output file containing processed well sites]
                [--study       Provide a study area boundary in geojson format]
                [--debug       Enable debug operational output to the screen]
"""

# Print information
#
messages   = []
ncol       = 120
activeDate = datetime.datetime.now()

message    = program
fmt        = "%" + str(int(ncol/2-len(message)/2)) + "s%s"
messages.append(fmt % (' ', message))

message    = 'version %s' % version
fmt        = "%" + str(int(ncol/2-len(message)/2)) + "s%s"
messages.append(fmt % (' ', message))

message    = version_date
fmt        = "%" + str(int(ncol/2-len(message)/2)) + "s%s"
messages.append(fmt % (' ', message))

messages.append("=" * ncol)
messages.append("-" * ncol)

message    = activeDate.strftime("%B %d, %Y %H:%M:%S")
fmt        = "%" + str(int(ncol/2-len(message)/2)) + "s%s"
messages.append(fmt % (' ', message))

messages.append("-" * ncol)

screen_logger.info('\n'.join(messages))
file_logger.info('\n'.join(messages))

# =============================================================================
def errorMessage(error_message):

    screen_logger.info(message)

    sys.exit( 1 )
# =============================================================================

# Set arguments
#
parser = argparse.ArgumentParser(prog=program)

parser.add_argument("--usage", help="Provide usage",
                    type=str)

parser.add_argument("-sites", "--sites",
                    help="Name of present collection file listing sites",
                    required = True,
                    type=str)

parser.add_argument("-output", "--output",
                    help="Name of output file containing processed well sites",
                    required = True,
                    type=str)

parser.add_argument("-study", "--study",
                    help="Provide a study area boundary in geojson format",
                    type=str)

parser.add_argument("-debug", "--debug",
                    help="Enable full operational output to a debugging file",
                    action="store_true")

# Parse arguments
#
args = parser.parse_args()

# Set collection file
#
if args.sites:

    collection_file = args.sites
    if not os.path.isfile(collection_file):
        message  = "File listing sites %s does not exist" % collection_file
        errorMessage(message)

if args.output:

    output_file = args.output
    if os.path.isfile(output_file):
        os.remove(output_file)

if args.study:
    studyarea_file = args.study
    if not os.path.isfile(studyarea_file):
        message  = "File %s listing a study area boundary in geojson format does not exist" % studyarea_file
        errorMessage(message)

if args.debug:

    screen_logger.setLevel(logging.DEBUG)


# =============================================================================

def processCsvFile (csv_file):

    collectionSitesL = []
    collectionLinesL = []

    # Read csv file
    # -------------------------------------------------
    #
    try:
        with open(csv_file, mode='r', newline='', encoding='utf-8') as csvfile:

            # Create a reader object, specifying the tab delimiter
            #
            #collectionSitesL = list(csv.DictReader(filter(lambda row: row[:2]!='##' and len(row) > 0, csvfile), delimiter='\t'))
            collectionLinesL = list(csv.reader(csvfile, delimiter='\t'))

            # Remove format line
            #
            #del collectionSitesL[0]

            return collectionLinesL

    except FileNotFoundError:
        message = f"Error: The file '{csv_file}' was not found."
        screen_logger.info(message)
        errorMessage(message)
    except Exception as e:
        message = f"An error occurred: {e}"
        screen_logger.info(message)
        errorMessage(message)

    return collectionLinesL
# =============================================================================

def processCsvFileSave (csv_file):

    collectionSitesL = []

    # Read csv file
    # -------------------------------------------------
    #
    try:
        with open(csv_file, mode='r', newline='', encoding='utf-8') as csvfile:

            # Create a reader object, specifying the tab delimiter
            #
            collectionSitesL = list(csv.DictReader(filter(lambda row: row[:2]!='##' and len(row) > 0, csvfile), delimiter='\t'))

            # Remove format line
            #
            #del collectionSitesL[0]

            return collectionSitesL

    except FileNotFoundError:
        message = f"Error: The file '{collection_file}' was not found."
        screen_logger.info(message)
        errorMessage(message)
    except Exception as e:
        message = f"An error occurred: {e}"
        screen_logger.info(message)
        errorMessage(message)

    return collectionSitesL
# =============================================================================

def ProcessCollectionSites (collection_file, mySiteFields):

    siteInfoD      = {}
    agencyL        = []

    periodicSitesL = []
    recorderSitesL = []

    keyColumn      = 'site_id'
    csv_reader     = None

    # Read collection file
    # -------------------------------------------------
    #
    try:
        with open(collection_file, newline='', encoding='utf-8') as fh:

            # Create a reader object, specifying the tab delimiter
            #
            csv_reader = csv.DictReader(filter(lambda row: row[0]!='#' and len(row) > 0, fh), delimiter='\t')

            # Loop through file
            #
            formatLine = True
            for tempD in csv_reader:

                if formatLine:
                    formatLine = False
                    continue

                # Set empty value to None
                #
                for key, value in tempD.items():
                    if len(value) < 1:
                        tempD[key] = ''

                site_id = str(tempD['site_id'])
                screen_logger.debug("Line %s" % tempD)
                screen_logger.debug("Site %s" % site_id)

                if site_id not in siteInfoD:
                    siteInfoD[site_id] = {}

                for key in tempD.keys():
                    siteInfoD[site_id][key] = str(tempD[key])

                if len(siteInfoD[site_id]['recorder']) > 0:
                    siteInfoD[site_id]['recorder'] = siteInfoD[site_id]['recorder'].split(',')

                if str(siteInfoD[site_id]['periodic']) == 'Y':
                    siteInfoD[site_id]['periodic'] = 1
                else:
                    siteInfoD[site_id]['periodic'] = int(siteInfoD[site_id]['periodic'])

                if str(tempD['agency_cd']) not in agencyL:
                    agencyL.append(str(tempD['agency_cd']))


    except FileNotFoundError:
        message = f"Error: The file '{collection_file}' was not found."
        screen_logger.info(message)
        errorMessage(message)
    except Exception as e:
        message = f"An error occurred: {e}"
        screen_logger.info(message)
        errorMessage(message)


    # Count sites
    # -------------------------------------------------
    #
    usgsSitesL = list({siteInfoD[x]['site_no'] for x in siteInfoD if len(siteInfoD[x]['site_no']) > 0})
    owrdSitesL = list({siteInfoD[x]['coop_site_no'] for x in siteInfoD if len(siteInfoD[x]['coop_site_no']) > 0})
    cdwrSitesL = list({siteInfoD[x]['cdwr_id'] for x in siteInfoD if len(siteInfoD[x]['cdwr_id']) > 0})

    periodicSitesL = list({siteInfoD[x]['site_id'] for x in siteInfoD if siteInfoD[x]['periodic'] > 0})
    recorderSitesL = list({siteInfoD[x]['site_id'] for x in siteInfoD if len(siteInfoD[x]['recorder']) > 0})

    usgsRecordersL = list({siteInfoD[x]['site_no'] for x in siteInfoD if 'USGS' in siteInfoD[x]['recorder']})
    owrdRecordersL = list({siteInfoD[x]['coop_site_no'] for x in siteInfoD if 'OWRD' in siteInfoD[x]['recorder']})
    cdwrRecordersL = list({siteInfoD[x]['cdwr_id'] for x in siteInfoD if 'CDWR' in siteInfoD[x]['recorder']})

    # Print information
    #
    ncols    = 85
    messages = []
    messages.append('\n\tProcessed site information in collection file')
    messages.append('\t%s' % (ncols * '-'))
    messages.append('\t%-40s %44s' % ('Monitoring agencies in collection file', ', '.join(agencyL)))
    messages.append('\t%-79s %5d' % ('Number of sites in collection file', len(siteInfoD)))
    messages.append('\t%-79s %5d' % ('Number of periodic sites in collection file', len(periodicSitesL)))
    messages.append('\t%-79s %5d' % ('Number of recorder sites in collection file', len(recorderSitesL)))
    messages.append('\t%-79s %5d' % ('Number of sites correlated to a site in USGS datbase', len(usgsSitesL)))
    messages.append('\t%-79s %5d' % ('Number of recorder sites in collection file in the USGS datbase', len(usgsRecordersL)))
    messages.append('\t%-79s %5d' % ('Number of sites correlated to a site in OWRD datbase', len(owrdSitesL)))
    messages.append('\t%-79s %5d' % ('Number of recorder sites in collection file in the OWRD datbase', len(owrdRecordersL)))
    messages.append('\t%-79s %5d' % ('Number of sites correlated to a site in CDWR datbase', len(cdwrSitesL)))
    messages.append('\t%-79s %5d' % ('Number of recorder sites in collection file in the CDWR datbase', len(cdwrRecordersL)))
    messages.append('\t%s' % (ncols * '-'))
    messages.append('\n')
    messages.append('\n')

    screen_logger.info('\n'.join(messages))
    file_logger.info('\n'.join(messages))

    return siteInfoD
# =============================================================================

def processStudyAreaFile (studyarea_file):

    # Load the GeoJSON file content
    #
    with open(studyarea_file, 'r') as f:
        js = json.load(f)

    # The file might contain multiple features in a FeatureCollection
    # Iterate through each feature to find the containing polygon
    #
    for feature in js['features']:
        #polygon = shape(feature['geometry'])
        coords  = feature['geometry']['coordinates']
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        poly = Polygon(coords)

    #return polygon
    return poly
# ----------------------------------------------------------------------
# -- Main program
# ----------------------------------------------------------------------

# Initialize arguments
#
siteInfoD        = {}
usgsInfoD        = {}
usgsRecorderD    = {}
owrdInfoD        = {}
owrdRecorderD    = {}
cdwrInfoD        = {}
cdwrRecorderD    = {}

minimumCount     = 0

debug            = False
debugLevel       = None

mySiteFields = [
                "site_id",
                "agency_cd",
                "site_no",
                "coop_site_no",
                "state_well_nmbr",
                "cdwr_id",
                "station_nm",
                "periodic",
                "recorder",
                "dec_lat_va",
                "dec_long_va",
                "alt_va",
                "alt_acy_va",
                "alt_datum_cd",
                "well_depth_va",
                "active"
               ]

# Process study area file
# -------------------------------------------------
#
polygon = processStudyAreaFile (studyarea_file)

# Process collection file
# -------------------------------------------------
#
#siteInfoD = processCollectionSites(collection_file, mySiteFields)

collectionLinesL = processCsvFile(collection_file)
screen_logger.info('Processed %d lines in collection file' % len(collectionLinesL))

# Process lines from the collection file
# -------------------------------------------------
#
outputL = []
columnL = []

for Line in collectionLinesL:

    if Line[0][:2] == '##':
        outputL.append('\t'.join(Line))

    else:
        if len(columnL) < 1:
            columnL = Line
            screen_logger.debug(columnL)
            outputL.append('\t'.join(Line))

        elif Line[0][0] == '#':
            outputL.append('\t'.join(Line))

        else:
            screen_logger.debug(Line)
            LineD   = dict(zip(columnL, Line))
            screen_logger.debug(LineD)
            site_id = LineD['site_id']

            if site_id not in siteInfoD:
                siteInfoD[site_id] = {}

            siteInfoD[site_id] = LineD
            screen_logger.debug(siteInfoD[site_id])

            longitude = siteInfoD[site_id]['dec_long_va']
            latitude  = siteInfoD[site_id]['dec_lat_va']
            siteFlag  = False
            if len(str(longitude)) > 0 and len(str(latitude)) > 0:
                sitePoint = Point(longitude, latitude)

                siteFlag  = sitePoint.within(polygon)

            if siteFlag:
                outputL.append('\t'.join(Line))
            else:
                Line[0] = '#%s' % Line[0]
                outputL.append('\t'.join(Line))

            siteInfoD[site_id]['studyarea'] = siteFlag

studyareaSitesL = list({siteInfoD[x]['site_id'] for x in siteInfoD if siteInfoD[x]['studyarea']})

screen_logger.info('Processed %d USGS, OWRD, and CDWR established and proposed sites in collection file' % len(siteInfoD))
screen_logger.info('Processed %d USGS, OWRD, and CDWR established in collection file within Study Area' % len(studyareaSitesL))

# Output records
#
with open(output_file,'w') as f:
    f.write('\n'.join(outputL))

sys.exit()

collectionSitesL = processCsvFile(collection_file)
siteInfoD = dict({x['site_id']:x for x in collectionSitesL})

# Process sites within study area boundary
# -------------------------------------------------
#
for site_id in sorted(siteInfoD.keys()):

    longitude = siteInfoD[site_id]['dec_long_va']
    latitude  = siteInfoD[site_id]['dec_lat_va']
    siteFlag  = False
    if len(str(longitude)) > 0 and len(str(latitude)) > 0:
        sitePoint = Point(longitude, latitude)

        siteFlag  = sitePoint.within(polygon)

    siteInfoD[site_id]['studyarea'] = siteFlag
    #screen_logger.info('Site %s in study area %s' % (site_id, str(siteFlag)))

# Prepare report
# -------------------------------------------------
#
localDate = datetime.datetime.now().strftime("%B %d, %Y")

# Print header information
#
ncols    = 81
messages = []
messages.append("## U.S. Geological Survey")
messages.append("## Groundwater Periodic and Recorder Sites")
messages.append("##")
messages.append("## Version %-30s" % version)
messages.append("## Version_Date on %-30s" % localDate)
messages.append("##")
messages.append("##==========================================================================================")

# Established sites
# -------------------------------------------------
#
establishedSitesL = list({siteInfoD[x]['site_id'] for x in siteInfoD if siteInfoD[x]['site_id'][0] != '#'})
proposedSitesL = list({siteInfoD[x]['site_id'] for x in siteInfoD if siteInfoD[x]['site_id'][0] == '#'})
periodicSitesL = list({siteInfoD[x]['site_id'] for x in establishedSitesL if len(str(siteInfoD[x]['periodic'])) > 0 and int(siteInfoD[x]['periodic']) > 0})
recorderSitesL = list({siteInfoD[x]['site_id'] for x in establishedSitesL if len(siteInfoD[x]['recorder']) > 0})
proposedPeriodicSitesL = list({siteInfoD[x]['site_id'] for x in proposedSitesL if len(str(siteInfoD[x]['periodic'])) > 0 and int(siteInfoD[x]['periodic']) > 0})
proposedRecorderSitesL = list({siteInfoD[x]['site_id'] for x in proposedSitesL if len(siteInfoD[x]['recorder']) > 0})

# Print information
#
messages.append('\n\tProcessed Periodic and Recorder sites in the collection file')
messages.append('\t%s' % (81 * '='))
messages.append('\t%-70s %10d' % ('Total number of all sites listed in collection file', len(siteInfoD)))
messages.append('')
messages.append('\t%-70s %10d' % ('Total number of established sites listed in collection file', len(establishedSitesL)))
messages.append('\t%-70s %10d' % ('Total number of established periodic sites listed in collection file', len(periodicSitesL)))
messages.append('\t%-70s %10d' % ('Total number of established recorder sites listed in collection file', len(recorderSitesL)))
messages.append('')
messages.append('\t%-70s %10d' % ('Total number of additional sites listed in collection file', len(proposedSitesL)))
messages.append('\t%-70s %10d' % ('Total number of additional periodic sites listed in collection file', len(proposedPeriodicSitesL)))
messages.append('\t%-70s %10d' % ('Total number of additional recorder sites listed in collection file', len(proposedRecorderSitesL)))

messages.append('')
messages.append('')
messages.append('\t%-80s' % 'Processing sites from USGS database')
messages.append('\t%s' % (ncols * '-'))

usgsAllSitesL = list({siteInfoD[x]['site_id'] for x in siteInfoD if len(siteInfoD[x]['site_no']) > 0})
usgsAllPeriodicSitesL = list({siteInfoD[x]['site_id'] for x in usgsAllSitesL if len(str(siteInfoD[x]['periodic'])) > 0 and int(siteInfoD[x]['periodic']) > 0})
usgsAllRecordersL = list({siteInfoD[x]['site_id'] for x in usgsAllSitesL if 'USGS' in siteInfoD[x]['recorder']})

messages.append('')
messages.append('\t%-70s %10d' % ('Total number of all USGS sites listed in collection file', len(usgsAllSitesL)))
messages.append('\t%-70s %10d' % ('Total number of all USGS periodic sites listed in collection file', len(usgsAllPeriodicSitesL)))
messages.append('\t%-70s %10d' % ('Total number of all USGS recorder sites listed in collection file', len(usgsAllRecordersL)))

usgsSitesL = list({siteInfoD[x]['site_id'] for x in establishedSitesL if len(siteInfoD[x]['site_no']) > 0 and siteInfoD[x]['site_id'][0] != '#'})
usgsPeriodicL = list({siteInfoD[x]['site_id'] for x in usgsSitesL if len(str(siteInfoD[x]['periodic'])) > 0 and int(siteInfoD[x]['periodic']) > 0})
usgsRecorderL = list({siteInfoD[x]['site_id'] for x in usgsSitesL if 'USGS' in siteInfoD[x]['recorder']})

messages.append('')
messages.append('\t%-70s %10d' % ('Number of established USGS sites in collection file', len(usgsSitesL)))
messages.append('\t%-70s %10d' % ('Number of established USGS periodic sites in collection file', len(usgsPeriodicL)))
messages.append('\t%-70s %10d' % ('Number of established USGS recorder sites in collection file', len(usgsRecorderL)))

usgsProposedSitesL = list({siteInfoD[x]['site_id'] for x in proposedSitesL if len(siteInfoD[x]['site_no']) > 0})
usgsProposedPeriodicL = list({siteInfoD[x]['site_id'] for x in usgsProposedSitesL if len(str(siteInfoD[x]['periodic'])) > 0 and int(siteInfoD[x]['periodic']) > 0})
usgsProposedRecorderL = list({siteInfoD[x]['site_id'] for x in usgsProposedSitesL if 'USGS' in siteInfoD[x]['recorder']})

messages.append('')
messages.append('\t%-70s %10d' % ('Number of additional USGS sites in collection file', len(usgsProposedSitesL)))
messages.append('\t%-70s %10d' % ('Number of additional USGS periodic sites in collection file', len(usgsProposedPeriodicL)))
messages.append('\t%-70s %10d' % ('Number of additional USGS recorder sites in collection file', len(usgsProposedRecorderL)))

messages.append('')
messages.append('')
messages.append('\t%-80s' % 'Processing sites from OWRD database')
messages.append('\t%s' % (ncols * '-'))

owrdAllSitesL = list({siteInfoD[x]['site_id'] for x in siteInfoD if len(siteInfoD[x]['coop_site_no']) > 0})
owrdAllPeriodicSitesL = list({siteInfoD[x]['site_id'] for x in owrdAllSitesL if len(str(siteInfoD[x]['periodic'])) > 0 and int(siteInfoD[x]['periodic']) > 0})
owrdAllRecordersL = list({siteInfoD[x]['site_id'] for x in owrdAllSitesL if 'OWRD' in siteInfoD[x]['recorder']})

messages.append('')
messages.append('\t%-70s %10d' % ('Total number of all OWRD sites listed in collection file', len(owrdAllSitesL)))
messages.append('\t%-70s %10d' % ('Total number of all OWRD periodic sites listed in collection file', len(owrdAllPeriodicSitesL)))
messages.append('\t%-70s %10d' % ('Total number of all OWRD recorder sites listed in collection file', len(owrdAllRecordersL)))

owrdSitesL = list({siteInfoD[x]['site_id'] for x in establishedSitesL if len(siteInfoD[x]['coop_site_no']) > 0})
owrdPeriodicL = list({siteInfoD[x]['site_id'] for x in owrdSitesL if len(str(siteInfoD[x]['periodic'])) > 0 and int(siteInfoD[x]['periodic']) > 0})
owrdRecorderL = list({siteInfoD[x]['site_id'] for x in owrdSitesL if 'OWRD' in siteInfoD[x]['recorder']})

messages.append('')
messages.append('\t%-70s %10d' % ('Number of established OWRD sites in collection file', len(owrdSitesL)))
messages.append('\t%-70s %10d' % ('Number of established OWRD periodic sites in collection file', len(owrdPeriodicL)))
messages.append('\t%-70s %10d' % ('Number of established OWRD recorder sites in collection file', len(owrdRecorderL)))

owrdProposedSitesL = list({siteInfoD[x]['site_id'] for x in proposedSitesL if len(siteInfoD[x]['coop_site_no']) > 0})
owrdProposedPeriodicL = list({siteInfoD[x]['site_id'] for x in owrdProposedSitesL if len(str(siteInfoD[x]['periodic'])) > 0 and int(siteInfoD[x]['periodic']) > 0})
owrdProposedRecorderL = list({siteInfoD[x]['site_id'] for x in owrdProposedSitesL if 'OWRD' in siteInfoD[x]['recorder']})

messages.append('')
messages.append('\t%-70s %10d' % ('Number of additional OWRD sites in collection file', len(owrdProposedSitesL)))
messages.append('\t%-70s %10d' % ('Number of additional OWRD periodic sites in collection file', len(owrdProposedPeriodicL)))
messages.append('\t%-70s %10d' % ('Number of additional OWRD recorder sites in collection file', len(owrdProposedRecorderL)))

screen_logger.info('\n'.join(messages))
file_logger.info('\n'.join(messages))

sys.exit()

messages.append('')
messages.append('\t%-80s' % 'Processing sites from OWRD database')
messages.append('\t%s' % (ncols * '-'))
messages.append('\t%-70s %10d' % ('Number of OWRD sites in current collection file', len(owrdSitesL)))
messages.append('\t%-70s %10d' % ('Number of OWRD periodic sites in current collection file', len(owrdPeriodicL)))
messages.append('\t%-70s %10d' % ('Number of periodic sites possible additions from OWRD database', len(owrdPeriodicList)))
messages.append('\t%-70s %10d' % ('Number of OWRD recorder sites in current collection file', len(owrdRecorderL)))
messages.append('\t%-70s %10d' % ('Number of recorder sites possible additions from OWRD database', len(owrdRecorderList)))

cdwrSitesL        = list({siteInfoD[x]['site_id'] for x in siteInfoD if len(siteInfoD[x]['cdwr_id']) > 0})
cdwrPeriodicL     = list({siteInfoD[x]['cdwr_id'] for x in cdwrSitesL if siteInfoD[x]['periodic'] > 0})
cdwrRecorderL     = list({siteInfoD[x]['cdwr_id'] for x in cdwrSitesL if 'CDWR' in siteInfoD[x]['recorder']})

cdwrPeriodicList  = list(cdwrPeriodicD.keys())
cdwrRecorderList  = list(cdwrRecorderD.keys())

messages.append('')
messages.append('\t%-80s' % 'Processing sites from CDWR database')
messages.append('\t%s' % (ncols * '-'))
messages.append('\t%-70s %10d' % ('Number of CDWR sites in current collection file', len(cdwrSitesL)))
messages.append('\t%-70s %10d' % ('Number of CDWR periodic sites in current collection file', len(cdwrPeriodicL)))
messages.append('\t%-70s %10d' % ('Number of periodic sites possible additions from CDWR database', len(cdwrPeriodicList)))
messages.append('\t%-70s %10d' % ('Number of CDWR recorder sites in current collection file', len(cdwrRecorderL)))
messages.append('\t%-70s %10d' % ('Number of recorder sites possible additions from CDWR database', len(cdwrRecorderList)))

messages.append('\t%s' % (ncols * '='))
messages.append('')

screen_logger.info('\n'.join(messages))
file_logger.info('\n'.join(messages))

sys.exit()

# Count sites
# -------------------------------------------------
#
usgsSitesD = dict({x['site_no']:x for x in collectionSitesL if len(x['site_no']) > 0})
screen_logger.info('Processed %d USGS established and proposed sites in collection file' % len(usgsSitesD))
usgsSitesL = list({siteInfoD[x]['site_no'] for x in siteInfoD if len(siteInfoD[x]['site_no']) > 0 and x['site_id'][0] != '#'})
screen_logger.info('Processed %d USGS established sites in collection file' % len(usgsSitesD))
proposedUsgsSitesD = dict({x['site_no']:x for x in collectionSitesL if len(x['site_no']) > 0 and x['site_id'][0] == '#'})
screen_logger.info('Processed %d proposed USGS sites in collection file' % len(proposedUsgsSitesD))
owrdSitesD = dict({x['coop_site_no']:x for x in collectionSitesL if len(x['coop_site_no']) > 0})
screen_logger.info('Processed %d OWRD in collection file' % len(owrdSitesD))
cdwrSitesD = dict({x['cdwr_id']:x for x in collectionSitesL if len(x['cdwr_id']) > 0})
screen_logger.info('Processed %d CDWR in collection file' % len(cdwrSitesD))
sys.exit()

screen_logger.info('Collection sites list %s' % collectionSitesL)
screen_logger.info('Proposed sites list %s' % proposedSitesL)
sys.exit()

outputL.append("\t".join(mySiteFields))
outputL.append("\t".join(mySiteFormat))

# Count sites
#
usgsSitesL        = list({siteInfoD[x]['site_no'] for x in siteInfoD if len(siteInfoD[x]['site_no']) > 0})
usgsPeriodicL     = list({siteInfoD[x]['site_no'] for x in usgsSitesL if siteInfoD[x]['periodic'] > 0})
usgsRecorderL     = list({siteInfoD[x]['site_no'] for x in usgsSitesL if 'USGS' in siteInfoD[x]['recorder']})

usgsPeriodicList  = list(usgsPeriodicD.keys())
usgsRecorderList  = list(usgsRecorderD.keys())

# Print information
#
for site_id in sorted(siteInfoD.keys()):

    recordL = []
    for myColumn in mySiteFields:
        recordL.append(str(siteInfoD[site_id][myColumn]))

    outputL.append("\t".join(recordL))

# Print information
#
if len(usgsPeriodicList) > 0:

    outputL.append("#")
    outputL.append("# Possble New Periodic Sites from USGS source")
    outputL.append("#")

    for site_id in sorted(usgsPeriodicList):

        recordL = []

        for myColumn in mySiteFields:
            recordL.append(usgsPeriodicD[site_id][myColumn])

        if minimumCount is not None and usgsPeriodicD[site_id]['periodic'] >= minimumCount:
            outputL.append("#%s" % '\t'.join(str(item) for item in recordL))
        elif minimumCount is None and usgsPeriodicD[site_id]['periodic'] > 0:
            outputL.append("#%s" % '\t'.join(str(item) for item in recordL))

if len(usgsRecorderList) > 0:

    outputL.append("#")
    outputL.append("# Possble New Recorder Sites from USGS source")
    outputL.append("#")

    for site_id in sorted(usgsRecorderList):

        recordL = []

        usgsRecorderD[site_id]['recorder'] = 'USGS'
        for myColumn in mySiteFields:
            recordL.append(usgsRecorderD[site_id][myColumn])

        outputL.append("#%s" % '\t'.join(str(item) for item in recordL))

# Print information
#
if len(owrdPeriodicList) > 0:

    outputL.append("#")
    outputL.append("# Possble New Periodic Sites from OWRD source")
    outputL.append("#")

    for site_id in sorted(owrdPeriodicList):

        recordL = []

        for myColumn in mySiteFields:
            recordL.append(owrdPeriodicD[site_id][myColumn])

        if minimumCount is not None and owrdPeriodicD[site_id]['periodic'] >= minimumCount:
            outputL.append("#%s" % '\t'.join(str(item) for item in recordL))
        elif minimumCount is None and owrdPeriodicD[site_id]['periodic'] > 0:
            outputL.append("#%s" % '\t'.join(str(item) for item in recordL))

if len(owrdRecorderList) > 0:

    outputL.append("#")
    outputL.append("# Possble New Recorder Sites from OWRD source")
    outputL.append("#")

    for site_id in sorted(owrdRecorderList):

        recordL = []

        owrdRecorderD[site_id]['recorder'] = 'OWRD'
        for myColumn in mySiteFields:
            recordL.append(owrdRecorderD[site_id][myColumn])

        outputL.append("#%s" % '\t'.join(str(item) for item in recordL))

# Print information
#
if len(cdwrPeriodicList) > 0:

    outputL.append("#")
    outputL.append("# Possble New Periodic Sites from CDWR source")
    outputL.append("#")

    for site_id in sorted(cdwrPeriodicList):

        recordL = []

        cdwrPeriodicD[site_id]['recorder'] = ''
        for myColumn in mySiteFields:
            recordL.append(cdwrPeriodicD[site_id][myColumn])

        if minimumCount is not None and cdwrPeriodicD[site_id]['periodic'] >= minimumCount:
            outputL.append("#%s" % '\t'.join(str(item) for item in recordL))
        elif minimumCount is None and cdwrPeriodicD[site_id]['periodic'] > 0:
            outputL.append("#%s" % '\t'.join(str(item) for item in recordL))

if len(cdwrRecorderList) > 0:

    outputL.append("#")
    outputL.append("# Possble New Recorder Sites from CDWR source")
    outputL.append("#")

    for site_id in sorted(cdwrRecorderList):

        recordL = []

        cdwrRecorderD[site_id]['recorder'] = 'CDWR'
        for myColumn in mySiteFields:
            recordL.append(cdwrRecorderD[site_id][myColumn])

        outputL.append("#%s" % '\t'.join(str(item) for item in recordL))

# Output records
#
with open(output_file,'w') as f:
    f.write('\n'.join(outputL))

sys.exit()
