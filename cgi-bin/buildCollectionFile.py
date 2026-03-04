#!/usr/bin/env python3
#
###############################################################################
# $Id: /var/www/cgi-bin/klamath_wells/buildCollectionFile.py, v 3.06 2026/02/27 15:37:35 llorzol Exp $
# $Revision: 3.06 $
# $Date: 2026/02/27 15:37:35 $
# $Author: llorzol $
#
# Project:  buildCollectionFile.py
# Purpose:  Script builds a tab-limited text collection file of well sites
#           from USGS, OWRD, and CDWR sources for the Upper Klamath Basin.
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

program         = "USGS Build Collection File Script"
version         = "3.06"
version_date    = "February 27, 2026"
usage_message   = """
Usage: buildCollectionFile.py
                [--help]
                [--usage]
                [--sites       Name of present collection file listing sites]
                [--output      Name of output file containing processed well sites]
                [--county      Provide a list of county FIPS codes (5 digits) to search for USGS recorder sites]
                [--hucs        Provide a list of hydrologic unit codes (4 or more digits) for wildcard search for USGS sites]
                [--owrdsites   Provide a filename of OWRD site summary file containing recorder sites in text format]
                [--owrdwls     Provide a filename of OWRD waterlevel measurements file in text format]
                [--owrdother   Provide a filename of OWRD other ID file containing sites in text format]
                [--count       Provide a minimum number of periodic measurements to qualify for adding new sites onto collection file]
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

parser.add_argument("-counties", "--counties",
                    help="Provide a list county FIPS code (5 digits) to search for recorder sites",
                    default=[],
                    nargs='+')

parser.add_argument("-hucs", "--hucs",
                    help="Provide a list of hydrologic unit codes (4 or more digits) for wildcard search for USGS sites",
                    default=[],
                    nargs='+')

parser.add_argument("-owrdsites", "--owrdsites",
                    help="Provide a filename of OWRD site summary file containing recorder sites in text format",
                    required = True,
                    type=str)

parser.add_argument("-owrdwls", "--owrdwls",
                    help="Provide a filename of OWRD waterlevel measurements file in text format",
                    required = True,
                    type=str)

parser.add_argument("-owrdother", "--owrdother",
                    help="Provide a filename of OWRD other ID file containing sites in text format",
                    required = True,
                    type=str)

parser.add_argument("-count", "--count",
                    help="Provide a minimum number of periodic measurements to qualify for adding new sites onto collection file",
                    default=0,
                    type=int)

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

fipsCodesL = []
if args.counties:
    fipsCodesL = args.counties

hydrologicCodesL = []
if args.hucs:
    hydrologicCodesL = args.hucs

if args.owrdsites:
    owrdsites_file = args.owrdsites
    if not os.path.isfile(owrdsites_file):
        message  = "File listing OWRD sites %s does not exist" % owrdsites_file
        errorMessage(message)

if args.owrdwls:
    owrdwls_file = args.owrdwls
    if not os.path.isfile(owrdwls_file):
        message  = "File listing OWRD waterlevel measurements %s does not exist" % owrdwls_file
        errorMessage(message)

if args.owrdother:
    owrdother_file = args.owrdother
    if not os.path.isfile(owrdother_file):
        message  = "File listing OWRD other ID sites %s does not exist" % owrdother_file
        errorMessage(message)

if args.count:
    try:
        minimumCount = int(args.count)
    except:
        message  = 'Provide a minimum number of periodic measurements to qualify for adding new sites onto collection file'
        errorMessage(message)

if args.study:
    studyarea_file = args.study
    if not os.path.isfile(studyarea_file):
        message  = "File %s listing a study area boundary in geojson format does not exist" % studyarea_file
        errorMessage(message)

if args.debug:
    screen_logger.setLevel(logging.DEBUG)


# =============================================================================

def processFipsCodes (fipsCodesL):

    fipsCodesD  = {}
    fipsCount   = 0

    tempList    = list(fipsCodesL)

    # Ogcapi service
    # -------------------------------------------------
    #
    # https://api.waterdata.usgs.gov/ogcapi/v0/collections/counties/items?limit=50000&filter-lang=cql-text&filter=state_fips_code IN ('41') AND county_fips_code IN ('035')&skipGeometry=true&f=json&api_key=nTsVxhFct7I3vFQgl2ANx3wphLyvDrmrjy5JIsSV
    #
    #
    URL          = 'https://api.waterdata.usgs.gov/ogcapi/v0/collections/counties/items'
    noparmsDict  = {
        'filter-lang' : 'cql-text',
        'filter' : "id IN (%s)" % ", ".join(f"'US-{item[:2]}-{item[2:]}'" for item in fipsCodesL),
        'sortby' : 'county_name',
        'skipGeometry' : 'true',
        'limit' : 50000,
        'f' : 'json',
        'api_key' : 'nTsVxhFct7I3vFQgl2ANx3wphLyvDrmrjy5JIsSV'
        }
    contentType  = "application/json"
    timeOut      = 1000

    screen_logger.debug("Url %s parms %s" % (URL, noparmsDict))

    message, webContent = webRequest(URL, noparmsDict, contentType, timeOut, None, screen_logger)

    if webContent is not None:

        # Check for empty file
        #
        if len(webContent) < 1:
            message = "Empty content return from web request %s" % URL
            errorMessage(message)

        # Process records
        # -------------------------------------------------
        #
        Json = json.loads(webContent)
        numRecords = Json['numberReturned']
        screen_logger.debug("Process %d Fips codes for %d user specified list" % (numRecords, len(fipsCodesL)))
        if numRecords > 0:

            myRecords = Json['features']

            # Loop through records
            #
            for myRecord in myRecords:
                fipsCode = myRecord['properties']['id'].replace('US','').replace('-','')
                fipsCodesD[fipsCode] = myRecord['properties']['county_name']
                tempList.remove(fipsCode)

    # Print information
    #
    messages = []
    messages.append('\n\tProcessed fips codes information')
    messages.append('\t%s' % (81 * '-'))
    messages.append('\t%-70s %10d' % ('Number of fips codes user specified', len(fipsCodesL)))
    messages.append('\t%-70s %10d' % ('Number of fips codes matched in the USGS database', len(fipsCodesD)))
    messages.append('\t%-70s %10d' % ('Number of fips codes not matched in the USGS database', len(tempList)))
    messages.append('\t%s' % (81 * '-'))
    messages.append('\n')
    if len(fipsCodesD) > 0:
        messages.append('\t%-70s' % 'Fips codes matched in USGS database')
        messages.append('\t%s' % (81 * '-'))
        for fipCode in sorted(fipsCodesD.keys()):
            messages.append('\t%-20s %60s' % (fipCode, fipsCodesD[fipCode]))
        messages.append('\t%s' % (81 * '-'))
    messages.append('\n')
    if len(tempList) > 0:
        messages.append('\t%-70s' % 'Fips codes not matched in USGS database')
        messages.append('\t%s' % (81 * '-'))
        for fipCode in sorted(tempList):
            messages.append('\t%-20s %60s' % (fipCode, ' '))
        messages.append('\t%s' % (81 * '-'))
    messages.append('\n')

    screen_logger.info('\n'.join(messages))
    file_logger.info('\n'.join(messages))

    return fipsCodesD
# =============================================================================

def processCollectionSites (collection_file, mySiteFields):

    collectionSitesL = []

    siteInfoD      = {}
    agencyL        = []

    periodicSitesL = []
    recorderSitesL = []

    keyColumn      = 'site_id'

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

    # Prepare summary
    # -------------------------------------------------
    #
    agencyL = []
    [agencyL.extend(siteInfoD[x]['recorder'].split(',')) for x in siteInfoD.keys() if len(siteInfoD[x]['recorder']) > 0]

    usgsSitesL = list({siteInfoD[x]['site_no'] for x in siteInfoD if len(siteInfoD[x]['site_no']) > 0})
    owrdSitesL = list({siteInfoD[x]['coop_site_no'] for x in siteInfoD if len(siteInfoD[x]['coop_site_no']) > 0})
    cdwrSitesL = list({siteInfoD[x]['cdwr_id'] for x in siteInfoD if len(siteInfoD[x]['cdwr_id']) > 0})

    periodicSitesL = list({siteInfoD[x]['site_id'] for x in siteInfoD if str(siteInfoD[x]['periodic']) == 'Y' or int(siteInfoD[x]['periodic']) > 0})
    recorderSitesL = list({siteInfoD[x]['site_id'] for x in siteInfoD if len(siteInfoD[x]['recorder']) > 0})

    usgsRecordersL = list({siteInfoD[x]['site_no'] for x in siteInfoD if 'USGS' in siteInfoD[x]['recorder']})
    owrdRecordersL = list({siteInfoD[x]['coop_site_no'] for x in siteInfoD if 'OWRD' in siteInfoD[x]['recorder']})
    cdwrRecordersL = list({siteInfoD[x]['cdwr_id'] for x in siteInfoD if 'CDWR' in siteInfoD[x]['recorder']})

    # Set periodic and recorder
    #
    [siteInfoD[x].update({'periodic':0}) for x in siteInfoD.keys()]
    [siteInfoD[x].update({'recorder':[]}) for x in siteInfoD.keys()]
    [siteInfoD[x].update({'active':False}) for x in siteInfoD.keys()]

    # Print information
    #
    ncols    = 85
    messages = []
    messages.append('\n\tProcessed site information in collection file')
    messages.append('\t%s' % (ncols * '-'))
    messages.append('\t%-40s %44s' % ('Monitoring agencies in collection file', ', '.join(set(agencyL))))
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

def processOgcapiUSGS (siteInfoD, mySiteFields, fipsCodesL):

    gwInfoD      = {}

    pst_offset   = -8
    days_offset  = 365
    activeDate   = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_offset)

    # Prepare list of site numbers
    # -------------------------------------------------
    #
    usgsSitesD = dict({siteInfoD[x]['site_no']:siteInfoD[x]['site_id'] for x in siteInfoD if len(siteInfoD[x]['site_no']) > 0})
    usgsSitesL = list({siteInfoD[x]['site_no'] for x in siteInfoD if len(siteInfoD[x]['site_no']) > 0})
    owrdSitesL = list({siteInfoD[x]['coop_site_no'] for x in siteInfoD if len(siteInfoD[x]['coop_site_no']) > 0})
    cdwrSitesL = list({siteInfoD[x]['cdwr_id'] for x in siteInfoD if len(siteInfoD[x]['cdwr_id']) > 0})

    missSitesL = list(usgsSitesL)
    missGwL    = list(usgsSitesL)
    gisNadL    = []

    agencyL    = []
    if len(usgsSitesL) > 0:
        agencyL.append('USGS')
    if len(owrdSitesL) > 0:
        agencyL.append('OWRD')
    if len(cdwrSitesL) > 0:
        agencyL.append('CDWR')

    # NwisWeb site service for general information for periodic/recorder wells
    # ------------------------------------------------------------------------
    #
    tempL  = list(fipsCodesL)
    ncodes = 15
    myRecords = []

    # Set Ogcapi columns
    #
    myOgcapiFields = {
       'site_id'                    : 'monitoring_location_number',
       'agency_cd'                  : 'agency_code',
       'site_no'                    : 'monitoring_location_number',
       'coop_site_no'               : 'coop_site_no',
       'state_well_nmbr'            : 'xxx',
       'cdwr_id'                    : 'site_code',
       'station_nm'                 : 'monitoring_location_name',
       'periodic'                   : 'periodic',
       'recorder'                   : 'recorder',
       'dec_lat_va'                 : 'latitude',
       'dec_long_va'                : 'longitude',
       'alt_va'                     : 'altitude',
       'alt_acy_va'                 : 'altitude_accuracy',
       'alt_datum_cd'               : 'vertical_datum',
       'well_depth_va'              : 'well_constructed_depth',
       'active'                     : 'active'
       }

    # Loop through Fips codes
    #
    while len(tempL) > 0:

        nList = list(tempL[:ncodes])
        del tempL[:ncodes]

        # Web request
        #
        URL          = 'https://api.waterdata.usgs.gov/ogcapi/v0/collections/monitoring-locations/items'
        noparmsDict  = {
            'filter-lang' : 'cql-text',
            'filter' : " AND ".join([
                "%s" % " OR ".join(f"(state_code = '{item[:2]}' AND county_code = '{item[2:]}')" for item in nList),
                "site_type_code LIKE 'GW%'"
            ]),
            'sortby' : 'id',
            #'properties' : 'parameter_code,monitoring_location_id,observing_procedure,observing_procedure_code,value,unit_of_measure,time,qualifier,vertical_datum,approval_status,measuring_agency',
            #'skipGeometry' : 'true',
            'crs' : 'http://www.opengis.net/def/crs/OGC/1.3/CRS83',
            'limit' : 50000,
            'f' : 'json',
            'api_key' : 'nTsVxhFct7I3vFQgl2ANx3wphLyvDrmrjy5JIsSV'
        }
        contentType  = "application/json"
        timeOut      = 1000

        screen_logger.debug("Url %s" % URL)

        message, webContent = webRequest(URL, noparmsDict, contentType, timeOut, None, screen_logger)

        # Check for failed request
        #
        if len(message) > 0 and 'Web request failed:' in message:
            message = "Web request failed"
            errorMessage(message)

        if webContent is not None:

            # Check for empty file
            #
            if len(webContent) < 1:
                message = "Empty content return from web request %s" % URL
                errorMessage(message)

            # Process site information
            # -------------------------------------------------
            #
            screen_logger.debug("Groundwater records /n%s" % webContent)
            gwJson = json.loads(webContent)
            numRecords = gwJson['numberReturned']

            screen_logger.info("Process %d monitoring_location records for %d Fips codes" % (numRecords, len(nList)))
            if numRecords > 0:

                myRecords.extend(gwJson['features'])

    # Process site information
    # -------------------------------------------------
    #
    if len(myRecords) > 0:

        columnL = myOgcapiFields.keys()
        namesL  = myRecords[0]['properties'].keys()

        # Loop through records
        #
        for myRecord in myRecords:

            myProperties = myRecord['properties']
            myGeometry   = myRecord['geometry']

            # Set site number
            #
            site_id = myProperties['monitoring_location_number']

            # Remove site from list
            #
            if site_id in missSitesL:
                missSitesL.remove(site_id)

            # Set site information
            #
            gwInfoD[site_id] = {}
            gwInfoD[site_id] = myProperties
            gwInfoD[site_id]['recorder'] = ''
            gwInfoD[site_id]['periodic'] = 0
            gwInfoD[site_id]['active'] = False

            # Set site location if blank
            #
            if len(myGeometry['coordinates']) > 0:
                gwInfoD[site_id]['longitude'] = myGeometry['coordinates'][0]
                gwInfoD[site_id]['latitude'] = myGeometry['coordinates'][1]

            if myProperties['original_horizontal_datum'] not in gisNadL:
                gisNadL.append(myProperties['original_horizontal_datum'])


    # Ogcapi site service for period of record for periodic wells
    # ---------------------------------------------------------------------
    #
    tempL  = list(gwInfoD.keys())
    nsites = 30
    myRecords = []

    screen_logger.info("Process field-measurement records for period of record of periodic wells for groundwater %d sites" % len(tempL))

    while len(tempL) > 0:

        nList = list(tempL[:nsites])
        del tempL[:nsites]

        # Web request
        #
        URL          = 'https://api.waterdata.usgs.gov/ogcapi/v0/collections/field-measurements/items'
        noparmsDict  = {
            'filter-lang' : 'cql-text',
            'filter' : " AND ".join([
                "monitoring_location_id IN (%s)" % ", ".join(f"'USGS-{item}'" for item in nList),
                "parameter_code = '72019'"
            ]),
            'sortby' : 'monitoring_location_id,time',
            #'properties' : 'parameter_code,monitoring_location_id,observing_procedure,observing_procedure_code,value,unit_of_measure,time,qualifier,vertical_datum,approval_status,measuring_agency',
            'skipGeometry' : 'true',
            'limit' : 50000,
            'f' : 'json',
            'api_key' : 'nTsVxhFct7I3vFQgl2ANx3wphLyvDrmrjy5JIsSV'
        }
        contentType  = "application/json"
        timeOut      = 1000

        screen_logger.debug("\tRequesting period of record for groundwater periodic sites %s" % ", ".join(nList))
        message, webContent = webRequest(URL, noparmsDict, contentType, timeOut, None, screen_logger)

        # Check for failed request
        #
        if len(message) > 0 and 'Web request failed:' in message:
            message = "Web request failed"
            errorMessage(message)

        if webContent is not None:

            # Check for empty file
            #
            if len(webContent) < 1:
                message = "Empty content return from web request %s" % URL
                errorMessage(message)

            # Process groundwater measurements
            # -------------------------------------------------
            #
            #screen_logger.info("Groundwater records /n%s" % webContent)
            gwJson = json.loads(webContent)
            numRecords = gwJson['numberReturned']
            screen_logger.debug("Process %d groundwater measurements for %d sites" % (numRecords, len(nList)))
            if numRecords > 0:

                myRecords.extend(gwJson['features'])

    # Process site periodic information
    # -------------------------------------------------
    #
    if len(myRecords) > 0:

        # Loop through records
        #
        for myRecord in myRecords:

            # Set site ID
            #
            agency_cd, site_no = myRecord['properties']['monitoring_location_id'].split('-')
            site_id = site_no
            if site_no in usgsSitesD:
                site_id = usgsSitesD[site_no]

            # Remove site from list
            #
            if site_id in missGwL:
                missGwL.remove(site_id)

            # Set count for field measurements
            #
            if site_id in gwInfoD:
                gwInfoD[site_id]['periodic'] += 1

                # Set whether measured in the last 365 days
                #
                wlDate = datetime.datetime.strptime(myRecord['properties']['time'][:16], '%Y-%m-%dT%H:%M')
                wlDate = wlDate.replace(tzinfo=datetime.timezone.utc)
                if wlDate >= activeDate:
                    gwInfoD[site_id]['active'] = True


    # Ogcapi time-series-metadata service for period of record for recorder wells
    # ---------------------------------------------------------------------
    #
    tempL  = list(gwInfoD.keys())
    nsites = 50
    myRecords = []

    screen_logger.info("Process time-series-metadata records for period of record of recorder wells for groundwater %d sites" % len(tempL))

    while len(tempL) > 0:

        nList = list(tempL[:nsites])
        del tempL[:nsites]

        # Web request
        #
        URL          = 'https://api.waterdata.usgs.gov/ogcapi/v0/collections/time-series-metadata/items'
        noparmsDict  = {
            'filter-lang' : 'cql-text',
            'filter' : " AND ".join([
                "monitoring_location_id IN (%s)" % ", ".join(f"'USGS-{item}'" for item in nList),
                "computation_period_identifier IN ('Points', 'Daily')",
                "parameter_code = '72019'"
            ]),
            'sortby' : 'monitoring_location_id',
            #'properties' : 'parameter_code,monitoring_location_id,observing_procedure,observing_procedure_code,value,unit_of_measure,time,qualifier,vertical_datum,approval_status,measuring_agency',
            'skipGeometry' : 'true',
            'limit' : 50000,
            'f' : 'json',
            'api_key' : 'nTsVxhFct7I3vFQgl2ANx3wphLyvDrmrjy5JIsSV'
        }
        contentType  = "application/json"
        timeOut      = 1000

        screen_logger.debug("\tRequesting period of record for groundwater periodic sites %s" % ", ".join(nList))
        message, webContent = webRequest(URL, noparmsDict, contentType, timeOut, None, screen_logger)

        # Check for failed request
        #
        if len(message) > 0 and 'Web request failed:' in message:
            message = "Web request failed"
            errorMessage(message)

        if webContent is not None:

            # Check for empty file
            #
            if len(webContent) < 1:
                message = "Empty content return from web request %s" % URL
                errorMessage(message)

            # Process groundwater measurements
            # -------------------------------------------------
            #
            #screen_logger.info("Groundwater records /n%s" % webContent)
            gwJson = json.loads(webContent)
            numRecords = gwJson['numberReturned']
            screen_logger.debug("Process %d groundwater recorder measurements for %d sites" % (numRecords, len(nList)))
            if numRecords > 0:

                myRecords.extend(gwJson['features'])

    # Process groundwater recorder information
    # -------------------------------------------------
    #
    if len(myRecords) > 0:

        # Loop through records
        #
        for myRecord in myRecords:

            # Set site ID
            #
            agency_cd, site_no = myRecord['properties']['monitoring_location_id'].split('-')
            site_id = site_no
            if site_no in usgsSitesD:
                site_id = usgsSitesD[site_no]

            # Set defaults for measuring agencies
            #
            gwInfoD[site_id]['recorder'] = 'USGS'

            # Set whether measured in the last 365 days
            #
            wlDate = datetime.datetime.strptime(myRecord['properties']['end_utc'][:16], '%Y-%m-%dT%H:%M')
            wlDate = wlDate.replace(tzinfo=datetime.timezone.utc)
            if wlDate >= activeDate:
                gwInfoD[site_id]['active'] = True


    # Convert ogcapi columns to Klamath columns
    #
    for site_id in sorted(gwInfoD.keys()):

            # Fill empty values
            #
        for myColumn in mySiteFields:

            ogcapiColumn = myOgcapiFields[myColumn]

            if ogcapiColumn in gwInfoD[site_id]:
                gwInfoD[site_id][myColumn] = gwInfoD[site_id][ogcapiColumn]
            else:
                gwInfoD[site_id][myColumn] = ''


    # Update collection sites for periodic/recorder information
    #
    for site_id in sorted(usgsSitesL):

        if site_id in gwInfoD:

        # Fill empty values
        #
            for myColumn in mySiteFields:

                if site_id in siteInfoD:
                    if len(str(siteInfoD[site_id][myColumn])) < 1:
                        if len(str(gwInfoD[site_id][myColumn])) > 0:
                            siteInfoD[site_id][myColumn] = gwInfoD[site_id][myColumn]

                    # Check station name
                    #
                    if myColumn == 'station_nm':
                        if siteInfoD[site_id]['station_nm'] != gwInfoD[site_id]['monitoring_location_name']:
                            siteInfoD[site_id]['station_nm'] = gwInfoD[site_id]['monitoring_location_name']

                    # Check counts for periodic field measurements [first reset to 0]
                    #
                    siteInfoD[site_id]['periodic'] = 0
                    if int(gwInfoD[site_id]['periodic']) > 0:
                        siteInfoD[site_id]['periodic'] = gwInfoD[site_id]['periodic']

                    # Check agencies for recorder measurements
                    #
                    if len(gwInfoD[site_id]['recorder']) > 0:
                        if gwInfoD[site_id]['recorder'] not in siteInfoD[site_id]['recorder']:
                            siteInfoD[site_id]['recorder'].append(gwInfoD[site_id]['recorder'])


    # Count sites
    #
    establishedSitesL   = list(siteInfoD.keys())
    establishedSitesSet = set(establishedSitesL)
    usgsSitesSet        = set(usgsSitesL)

    allPeriodicSitesL = {x for x in gwInfoD if gwInfoD[x]['periodic'] > 0}
    activePeriodicSitesL = {x for x in allPeriodicSitesL if gwInfoD[x]['active']}
    allRecorderSitesL = {x for x in gwInfoD if len(gwInfoD[x]['recorder']) > 0}

    allPeriodicSet    = set(allPeriodicSitesL)
    matchPeriodicL = list(usgsSitesSet.intersection(allPeriodicSet))
    proposedPeriodicSitesL = list(allPeriodicSet.difference(usgsSitesSet))

    proposedPeriodicSitesD = dict({x:gwInfoD[x] for x in proposedPeriodicSitesL})

    recorderSet    = set(allRecorderSitesL)
    matchRecorderL = list(recorderSet.intersection(usgsSitesSet))
    proposedRecorderL = list(recorderSet.difference(usgsSitesSet))

    proposedRecorderSitesD = dict({x:gwInfoD[x] for x in proposedRecorderL})

    matchedActivePeriodicL = {x for x in matchPeriodicL if gwInfoD[x]['active']}

    # Print information
    #
    ncols    = 105
    messages = []
    messages.append('\n\tProcessed USGS periodic and recorder site information')
    messages.append('\t%s' % (ncols * '-'))
    messages.append('\t%-75s %5d' % ('Number of sites in collection file', len(establishedSitesL)))
    messages.append('\t%-75s %5d' % ('Number of USGS sites in collection file', len(usgsSitesL)))
    messages.append('\t%-75s %5d' % ('Number of USGS sites in collection file NOT in specified counties', len(missSitesL)))
    messages.append('\t%-75s %5d' % ('Total number of periodic and recorder sites retrieved from USGS database', len(gwInfoD)))
    messages.append('\t%-75s %5d' % ('Number of periodic sites from USGS database', len(allPeriodicSitesL)))
    messages.append('\t%-75s %5d' % ('Total number of USGS periodic sites measured in the last 365 days', len(activePeriodicSitesL)))
    messages.append('\t%-75s %5d' % ('Number of periodic sites in collection file from USGS database', len(matchPeriodicL)))
    messages.append('\t%-75s %5d' % ('Number of periodic sites in collection file measured in the last 365 days', len(matchedActivePeriodicL)))
    messages.append('\t%-75s %5d' % ('Number of additional USGS sites possible with periodic msts', len(proposedPeriodicSitesL)))
    messages.append('\t%-75s %5d' % ('Total number of recorder sites from USGS database', len(allRecorderSitesL)))
    messages.append('\t%-75s %5d' % ('Number of recorder sites in collection file from USGS database', len(matchRecorderL)))
    messages.append('\t%-75s %5d' % ('Number of additional recorder sites possible from USGS database', len(proposedRecorderL)))
    messages.append('\t%s' % (ncols * '-'))
    if len(usgsSitesL) > 0:
        messages.append('')
        messages.append('\t%-70s' % 'USGS periodic and recorder sites in collection file in USGS database')
        messages.append('\t%s' % (ncols * '-'))
        fmt = '\t%-20s %-40s %10s %10s %10s'
        messages.append(fmt % ('USGS',        'USGS',    'Periodic', 'Recorder', 'Active'))
        messages.append(fmt % ('Site Number', 'Station', 'Counts',   'Counts',   'Status'))
        messages.append('\t%s' % (ncols * '-'))
        for site_no in sorted(usgsSitesL):
            activeStatus = ' '
            if gwInfoD[site_no]['active']:
                activeStatus = 'True'
            messages.append(fmt % (site_no,
                                   gwInfoD[site_no]['station_nm'][:40],
                                   gwInfoD[site_no]['periodic'],
                                   gwInfoD[site_no]['recorder'],
                                   activeStatus
                                   ))
        messages.append('\t%s' % (ncols * '-'))
    if len(proposedPeriodicSitesL) > 0:
        messages.append('')
        messages.append('\t%-70s' % 'USGS periodic sites to possibly add from USGS database')
        messages.append('\t%s' % (ncols * '-'))
        fmt = '\t%-20s %-40s %10s %10s'
        messages.append(fmt % ('USGS',        'USGS',    'Periodic', 'Active'))
        messages.append(fmt % ('Site Number', 'Station', 'Counts',   'Status'))
        messages.append('\t%s' % (ncols * '-'))
        for site_no in sorted(proposedPeriodicSitesL):
            activeStatus = ' '
            if gwInfoD[site_no]['active']:
                activeStatus = 'True'
            messages.append(fmt % (site_no,
                                   gwInfoD[site_no]['station_nm'][:40],
                                   gwInfoD[site_no]['periodic'],
                                   activeStatus
                                   ))
        messages.append('\t%s' % (ncols * '-'))
    if len(proposedRecorderL) > 0:
        messages.append('')
        messages.append('\t%-70s' % 'USGS recorder sites to possibly add from USGS database')
        messages.append('\t%s' % (ncols * '-'))
        fmt = '\t%-20s %-40s %10s'
        messages.append(fmt % ('USGS',        'USGS',    'Recorder'))
        messages.append(fmt % ('Site Number', 'Station', 'Counts'))
        messages.append('\t%s' % (ncols * '-'))
        for site_no in sorted(proposedRecorderL):
            messages.append(fmt % (site_no, gwInfoD[site_no]['station_nm'][:40], gwInfoD[site_no]['recorder']))
        messages.append('\t%s' % (ncols * '-'))
    if len(missSitesL) > 0:
        messages.append('')
        messages.append('\t%-70s' % 'USGS sites in collection file NOT in specified counties')
        messages.append('\t%s' % (ncols * '-'))
        fmt = '\t%-20s %-40s %10s %10s'
        messages.append(fmt % ('USGS',        'USGS',    'Periodic', 'Recorder'))
        messages.append(fmt % ('Site Number', 'Station', 'Counts',   'Counts'))
        messages.append('\t%s' % (ncols * '-'))
        for site_no in sorted(missSitesL):
            periodic   = ''
            recorder   = ''
            station_nm = ''
            if site_no in siteInfoD:
                station_nm = siteInfoD[site_no]['station_nm'][:40]
            if site_no in gwInfoD:
                periodic   = gwInfoD[site_no]['periodic']
                recorder   = gwInfoD[site_no]['recorder']
                station_nm = gwInfoD[site_no]['station_nm'][:40]
            messages.append('\t%-20s %-40s %10s %10s' % (site_no, station_nm, periodic, recorder))
        messages.append('\t%s' % (ncols * '-'))
    messages.append('\n')
    messages.append('\n')

    screen_logger.info('\n'.join(messages))
    file_logger.info('\n'.join(messages))

    return proposedPeriodicSitesD, proposedRecorderSitesD
# =============================================================================

def processOWRD (siteInfoD, mySiteFields, fipsCodesD, owrdsites_file, owrdother_file, owrdwls_file):

    pst_offset   = -8
    days_offset  = 365
    activeDate   = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_offset)

    # Build county names
    #
    countyL = []
    for fipsCode in sorted(fipsCodesD.keys()):
        countyL.append(fipsCodesD[fipsCode][:4].upper())

    myQtrD = {
       'NW'                  : 'A',
       'NE'                  : 'B',
       'SE'                  : 'C',
       'SW'                  : 'D'
       }

    # Identifies OWRD sites with USGS site numbers
    # -------------------------------------------------
    #
    otherSitesL = processFileOWRD (owrdother_file)

    # Process list from OWRD other ID file to dictionary
    #
    owrdOtherD = dict({x['gw_logid']:x['other_identity_id'].strip('"\'') for x in otherSitesL if x['gw_logid'][:4].upper() in countyL and x['other_identity_name'].upper() == 'USGS SITE ID'})
    usgsOtherD = dict({x['other_identity_id'].strip('"\''):x['gw_logid'] for x in otherSitesL if x['gw_logid'][:4].upper() in countyL and x['other_identity_name'].upper() == 'USGS SITE ID'})
    #screen_logger.info(owrdOtherD)
    #screen_logger.info(usgsOtherD)


    # Prepare OWRD waterlevel records
    # -------------------------------------------------
    #
    csvRecordsL = processFileOWRD(owrdwls_file)
    wlsRecordsL = [x for x in csvRecordsL if x['gw_logid'][:4].upper() in countyL]
    waterlevelRecordsL = sorted(wlsRecordsL, key=lambda x: (x['gw_logid'], datetime.datetime.strptime(x['measured_date'], '%m/%d/%Y')))

    # Process OWRD waterlevel records
    #
    waterlevelSitesD = {}
    for myRecord in waterlevelRecordsL:
        if myRecord['gw_logid'] not in waterlevelSitesD:
            waterlevelSitesD[myRecord['gw_logid']] = {}
            waterlevelSitesD[myRecord['gw_logid']]['waterlevels'] = []
            waterlevelSitesD[myRecord['gw_logid']]['beginDate'] = None
            waterlevelSitesD[myRecord['gw_logid']]['active'] = False

        waterlevelSitesD[myRecord['gw_logid']]['waterlevels'].append(myRecord['measured_date'])
        if waterlevelSitesD[myRecord['gw_logid']]['beginDate'] is None:
            waterlevelSitesD[myRecord['gw_logid']]['beginDate'] = myRecord['measured_date']
        waterlevelSitesD[myRecord['gw_logid']]['endDate'] = myRecord['measured_date']


    # Prepare OWRD site records
    # -------------------------------------------------
    #
    siteRecordsL = processFileOWRD(owrdsites_file)

    # Process list from OWRD site file to dictionary
    #
    owrdSitesD = dict({x['gw_logid']:x for x in siteRecordsL if x['gw_logid'][:4].upper() in countyL})

    # Prepare OWRD records
    # -------------------------------------------------
    #
    siteCollectionD  = dict({siteInfoD[x]['coop_site_no']:siteInfoD[x] for x in siteInfoD if len(siteInfoD[x]['coop_site_no']) > 0})

    for gw_logid in sorted(owrdSitesD.keys()):
        site_id = gw_logid
        agency_cd = 'OWRD'
        site_no = ''
        coop_site_no = gw_logid
        state_well_nmbr = owrdSitesD[gw_logid]['state_observation_well_nbr']
        cdwr_id = ''
        station_nm = ''
        dec_long_va = ''
        dec_lat_va = ''
        alt_va = ''
        alt_acy_va = ''
        alt_datum_cd = ''
        well_depth_va = ''

        if gw_logid in siteCollectionD:
            site_id = siteCollectionD[gw_logid]['site_id']
            agency_cd = siteCollectionD[gw_logid]['agency_cd']
            site_no = siteCollectionD[gw_logid]['site_no']
            station_nm = siteCollectionD[gw_logid]['station_nm']
            dec_long_va = siteCollectionD[gw_logid]['dec_long_va']
            dec_lat_va = siteCollectionD[gw_logid]['dec_lat_va']
            alt_va = siteCollectionD[gw_logid]['alt_va']
            alt_acy_va = siteCollectionD[gw_logid]['alt_acy_va']
            alt_datum_cd = siteCollectionD[gw_logid]['alt_datum_cd']
            well_depth_va = siteCollectionD[gw_logid]['well_depth_va']

        else:
            trsL = []
            trsL.append('%05.2f' % float(owrdSitesD[gw_logid]['township']))
            trsL.append(owrdSitesD[gw_logid]['township_char'])
            trsL.append('/')
            trsL.append('%05.2f' % float(owrdSitesD[gw_logid]['range']))
            trsL.append(owrdSitesD[gw_logid]['range_char'])
            trsL.append('-')
            trsL.append('%02d' % int(owrdSitesD[gw_logid]['sctn']))
            for column in ['qtr160', 'qtr40', 'qtr10']:
                if len(owrdSitesD[gw_logid][column]) > 0:
                    trsL.append(myQtrD[owrdSitesD[gw_logid][column]])

            station_nm = ''.join(trsL)

            dec_long_va = owrdSitesD[gw_logid]['longitude_dec']
            dec_lat_va = owrdSitesD[gw_logid]['latitude_dec']
            alt_va = owrdSitesD[gw_logid]['lsd_elevation']
            alt_acy_va = owrdSitesD[gw_logid]['lsd_accuracy']
            alt_datum_cd = owrdSitesD[gw_logid]['elevation_datum']
            well_depth_va = owrdSitesD[gw_logid]['max_depth']

        owrdSitesD[gw_logid]['site_id'] = site_id
        owrdSitesD[gw_logid]['agency_cd'] = agency_cd
        owrdSitesD[gw_logid]['site_no'] = site_no
        owrdSitesD[gw_logid]['coop_site_no'] = gw_logid
        owrdSitesD[gw_logid]['state_well_nmbr'] = state_well_nmbr
        owrdSitesD[gw_logid]['cdwr_id'] = cdwr_id
        owrdSitesD[gw_logid]['station_nm'] = station_nm
        owrdSitesD[gw_logid]['dec_long_va'] = dec_long_va
        owrdSitesD[gw_logid]['dec_lat_va'] = dec_lat_va
        owrdSitesD[gw_logid]['alt_va'] = alt_va
        owrdSitesD[gw_logid]['alt_acy_va'] = alt_acy_va
        owrdSitesD[gw_logid]['alt_datum_cd'] = alt_datum_cd
        owrdSitesD[gw_logid]['well_depth_va'] = well_depth_va

        # Set field measurement count
        #
        owrdSitesD[gw_logid]['periodic'] = 0
        if len(str(owrdSitesD[gw_logid]['measured_waterlevel_blsd_count'])) > 0:
            owrdSitesD[gw_logid]['periodic'] = int(owrdSitesD[gw_logid]['measured_waterlevel_blsd_count'])

        # Set recorder agency [set collection site if needed]
        #
        owrdSitesD[gw_logid]['recorder'] = []
        if len(str(owrdSitesD[gw_logid]['recorder_waterlevel_mean_daily_blsd_count'])) > 0:
            owrdSitesD[gw_logid]['recorder'].append('OWRD')
            if gw_logid in siteCollectionD and 'OWRD' not in siteCollectionD[gw_logid]['recorder']:
                siteInfoD[siteCollectionD[gw_logid]['site_id']]['recorder'].append('OWRD')

        # Set whether measured in the last 365 days
        #
        owrdSitesD[gw_logid]['active'] = False
        if gw_logid in waterlevelSitesD:
            wlDate = datetime.datetime.strptime(waterlevelSitesD[gw_logid]['endDate'], '%m/%d/%Y')
            wlDate = wlDate.replace(tzinfo=datetime.timezone.utc)
            if wlDate >= activeDate:
                waterlevelSitesD[gw_logid]['active'] = True
                if site_id in siteInfoD:
                    siteInfoD[site_id]['active'] = True
                if gw_logid in owrdSitesD:
                    owrdSitesD[gw_logid]['active'] = True



    # Prepare summary
    # -------------------------------------------------
    #
    usgsCollectionL  = list({siteInfoD[x]['site_no'] for x in siteInfoD if len(siteInfoD[x]['site_no']) > 0})
    owrdCollectionL  = list({siteInfoD[x]['coop_site_no'] for x in siteInfoD if len(siteInfoD[x]['coop_site_no']) > 0})

    usgsCollectionSet = set(usgsCollectionL)
    owrdCollectionSet = set(owrdCollectionL)
    owrdSitesSet      = set(owrdSitesD.keys())
    matchSitesL = list(owrdCollectionSet.intersection(owrdSitesSet))
    missSitesL  = list(owrdCollectionSet.difference(owrdSitesSet))

    # Create periodic/recorder sites
    #
    owrdPeriodicSitesD  = {x:owrdSitesD[x] for x in owrdSitesD if owrdSitesD[x]['periodic'] > 0}
    owrdSitesSet        = set(owrdPeriodicSitesD.keys())
    matchPeriodicSitesL = list(owrdCollectionSet.intersection(owrdSitesSet))
    missPeriodicSitesL  = list(owrdCollectionSet.difference(owrdSitesSet))
    proposedPeriodicSitesL = list(owrdSitesSet.difference(owrdCollectionSet))
    proposedPeriodicSitesD = dict({owrdSitesD[x]['site_id']:owrdSitesD[x] for x in proposedPeriodicSitesL})

    owrdRecorderSitesD = {x:owrdSitesD[x] for x in owrdSitesD if len(owrdSitesD[x]['recorder']) > 0}
    owrdSitesSet        = set(owrdRecorderSitesD.keys())
    matchRecorderSitesL = list(owrdCollectionSet.intersection(owrdSitesSet))
    missRecorderSitesL  = list(owrdCollectionSet.difference(owrdSitesSet))
    proposedRecorderSitesL = list(owrdSitesSet.difference(owrdCollectionSet))
    proposedRecorderSitesD = dict({owrdSitesD[x]['site_id']:owrdSitesD[x] for x in proposedRecorderSitesL})

    # Print information
    #
    ncols    = 115
    messages = []
    messages.append('\n\tProcessed OWRD information')
    messages.append('\t%s' % (ncols * '-'))
    messages.append('\t%-10s %80s' % ('Counties', ", ".join(countyL)))
    messages.append('\t%-85s %5d' % ('Number of sites in collection file', len(siteInfoD)))
    messages.append('\t%-85s %5d' % ('Number of OWRD sites in collection file with USGS site number', len(usgsCollectionL)))
    messages.append('\t%-85s %5d' % ('Number of sites retrieved from OWRD database in the specified counties', len(owrdSitesD)))
    messages.append('\t%-85s %5d' % ('Number of OWRD sites assigned an USGS site number from OWRD database', len(usgsOtherD.keys())))
    messages.append('\t%-85s %5d' % ('Number of OWRD sites in collection file NOT retrieved from OWRD database', len(missSitesL)))
    messages.append('\t%-85s %5d' % ('Number of periodic sites with waterlevels from OWRD database', len(owrdPeriodicSitesD)))
    messages.append('\t%-85s %5d' % ('Number of periodic sites in collection file from OWRD database', len(matchPeriodicSitesL)))
    messages.append('\t%-85s %5d' % ('Number of periodic sites possible additions from OWRD database', len(proposedPeriodicSitesL)))
    messages.append('\t%-85s %5d' % ('Number of recorder sites from OWRD database', len(owrdRecorderSitesD)))
    messages.append('\t%-85s %5d' % ('Number of recorder sites in collection file from OWRD database', len(matchRecorderSitesL)))
    messages.append('\t%-85s %5d' % ('Number of recorder sites possible additions from OWRD database', len(proposedRecorderSitesL)))
    messages.append('\t%s' % (ncols * '-'))
    if len(matchSitesL) > 0:
        messages.append('')
        messages.append('\t%s' % 'OWRD sites in collection file')
        messages.append('\t%s' % (ncols * '-'))
        fmt = '\t%-20s %-20s %-40s %10s %10s %10s'
        messages.append(fmt % ('USGS',        'OWRD',        'Station','Periodic', 'Recorder', 'Active'))
        messages.append(fmt % ('Site Number', 'Well Log ID', 'Name',    'Counts',  ' ',        'Status'))
        messages.append('\t%s' % (ncols * '-'))
        for gw_logid in sorted(matchSitesL):
            site_no = owrdSitesD[gw_logid]['site_no']
            station_nm = owrdSitesD[gw_logid]['station_nm'][:40]
            periodicCounts = str(owrdSitesD[gw_logid]['periodic'])
            recorderL = ''
            if len(str(owrdSitesD[gw_logid]['recorder'])) > 0:
                recorderL = ', '.join(owrdSitesD[gw_logid]['recorder'])
            activeStatus = ''
            if owrdSitesD[gw_logid]['active']:
                activeStatus = 'True'
            messages.append(fmt % (site_no, gw_logid, station_nm, periodicCounts, recorderL, activeStatus))
        messages.append('\t%s' % (ncols * '-'))
    if len(proposedPeriodicSitesL) > 0:
        messages.append('')
        messages.append('\t%s' % 'OWRD sites that are possible additions into collection file')
        messages.append('\t%s' % (ncols * '-'))
        fmt = '\t%-20s %-20s %-40s %10s %10s %10s'
        messages.append(fmt % ('USGS',        'OWRD',        'Station','Periodic', 'Recorder', 'Active'))
        messages.append(fmt % ('Site Number', 'Well Log ID', 'Name',    'Counts',  ' ',        'Status'))
        messages.append('\t%s' % (ncols * '-'))
        for gw_logid in sorted(proposedPeriodicSitesL):
            site_no = owrdSitesD[gw_logid]['site_no']
            station_nm = owrdSitesD[gw_logid]['station_nm'][:40]
            activeStatus = ''
            periodicCounts = str(owrdSitesD[gw_logid]['periodic'])
            recorderL = ''
            if len(str(owrdSitesD[gw_logid]['recorder'])) > 0:
                recorderL = ', '.join(owrdSitesD[gw_logid]['recorder'])
            if owrdSitesD[gw_logid]['active']:
                activeStatus = 'True'
            messages.append(fmt % (site_no, gw_logid, station_nm, periodicCounts, recorderL, activeStatus))
        messages.append('\t%s' % (ncols * '-'))

    screen_logger.info('\n'.join(messages))
    file_logger.info('\n'.join(messages))

    return proposedPeriodicSitesD, proposedRecorderSitesD, owrdSitesD
# =============================================================================

def processFileOWRD (owrd_file):

    csvRecordsL  = []

    # Read OWRD file
    # -------------------------------------------------
    #
    try:
        with open(owrd_file, newline='', encoding='utf-8') as fh:

            # Create a reader object, specifying the tab delimiter
            #
            csvRecordsL = list(csv.DictReader(filter(lambda row: row[0]!='#' and len(row) > 0, fh), delimiter='\t'))

    except FileNotFoundError:
        message = f"Error: The file '{owrd_file}' was not found."
        screen_logger.info(message)
        errorMessage(message)
    except Exception as e:
        message = f"An error occurred: {e}"
        screen_logger.info(message)
        errorMessage(message)

    return csvRecordsL
# =============================================================================

def processCDWR (siteInfoD, mySiteFields, fipsCodesD):

    gwInfoD        = {}

    pst_offset   = -8
    days_offset  = 365
    activeDate   = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_offset)

    # Set CDWR columns for tables
    #
    myCdwrFields = {
       'site_id'                    : 'site_code',
       'agency_cd'                  : 'agency_cd',
       'site_no'                    : 'site_no',
       'coop_site_no'               : 'coop_site_no',
       'state_well_nmbr'            : 'swn',
       'cdwr_id'                    : 'site_code',
       'station_nm'                 : 'swn',
       'periodic'                   : 'periodic',
       'recorder'                   : 'continuous_data_station_number',
       'dec_lat_va'                 : 'latitude',
       'dec_long_va'                : 'longitude',
       'alt_va'                     : 'gse',
       'alt_acy_va'                 : 'gse_acc',
       'alt_datum_cd'               : 'gse_method',
       'well_depth_va'              : 'well_depth',
       'active'                     : 'active'
       }

    # Prepare site information
    # -------------------------------------------------
    #
    usgsSitesD = dict({siteInfoD[x]['cdwr_id']:siteInfoD[x]['site_no'] for x in siteInfoD if len(siteInfoD[x]['site_no']) > 0 and len(siteInfoD[x]['cdwr_id']) > 0})
    cdwrSitesD = dict({siteInfoD[x]['cdwr_id']:siteInfoD[x]['site_id'] for x in siteInfoD if len(siteInfoD[x]['cdwr_id']) > 0})
    cdwrSitesL = list({siteInfoD[x]['cdwr_id'] for x in siteInfoD if len(siteInfoD[x]['cdwr_id']) > 0})
    missSitesL = list(cdwrSitesL)

    # Build county names
    #
    countyL = []
    for fipsCode in sorted(fipsCodesD.keys()):
        countyName = "%s" % fipsCodesD[fipsCode].lower().capitalize().replace('county','').strip()
        if countyName == 'Klamath':
            countyName += ', OR'
        countyL.append("'%s'" % countyName)

    # CDWR service for site location information
    # -------------------------------------------------
    #
    tempL        = ",".join(countyL)
    sqlTable     = 'af157380-fb42-4abf-b72a-6f9f98868077'
    countyColumn = 'county_name'

    # Web request
    #
    #  https://data.cnra.ca.gov/api/3/action/datastore_search_sql?sql=SELECT * from "af157380-fb42-4abf-b72a-6f9f98868077" WHERE "county_name" IN ('Modoc','Siskiyou','Klamath, Or')
    #
    URL          = 'https://data.cnra.ca.gov/api/3/action/datastore_search_sql?sql=SELECT * from "%s" WHERE "%s" IN (%s)' % (sqlTable, countyColumn, tempL)
    noparmsDict  = {}
    contentType  = "application/json"
    timeOut      = 10

    screen_logger.debug("Url %s" % URL)

    message, webContent = webRequest(URL, noparmsDict, contentType, timeOut, None, screen_logger)

    screen_logger.debug("webContent %s" % webContent)

    if webContent is not None:

        # Check for empty
        #
        if len(webContent) < 1:
            message = "Empty content return from web request %s" % URL
            errorMessage(message)

        # Convert to json format
        #
        gwJson = json.loads(webContent)

        # Check for failed request
        #
        if gwJson['success'] is False:
            message = "Error: %s for %s content return from web request %s" % (gwJson['error'], URL)
            errorMessage(message)

        # Successful request
        #
        else:

            # Parse records
            #
            jsonRecords = gwJson['result']['records']
            numRecords  = len(jsonRecords)

            screen_logger.info("Processed %d CDWR sites for site information in California/Oregon counties %s" % (numRecords, tempL))

            # Process site information
            # -------------------------------------------------
            #
            for myRecord in jsonRecords:

                site_code = myRecord['site_code']

                # Remove site from missing list
                #
                if site_code in missSitesL:
                    missSitesL.remove(site_code)

                # Set site_id
                #
                site_id = site_code
                if site_code in cdwrSitesD:
                    site_id = cdwrSitesD[site_code]

                # Check for USGS site number
                #
                site_no   = ''
                agency_cd = 'CDWR'
                if site_code in usgsSitesD:
                    site_no   = usgsSitesD[site_code]
                    agency_cd = 'USGS'

                # Set information
                #
                if site_id not in gwInfoD:
                    gwInfoD[site_id] = {}

                # Prepare information
                # -------------------------------------------------
                #
                for myColumn in mySiteFields:

                    cdwrColumn = myCdwrFields[myColumn].lower()

                    # Column site_id
                    #
                    if myColumn == 'site_id':
                        gwInfoD[site_id][myColumn] = site_id

                    # Column agency_cd
                    #
                    elif myColumn == 'agency_cd':
                        gwInfoD[site_id][myColumn] = agency_cd

                    # Column site_no
                    #
                    elif myColumn == 'site_no':
                        gwInfoD[site_id][myColumn] = site_no

                    # Column coop_site_no
                    #
                    elif myColumn == 'coop_site_no':
                        gwInfoD[site_id][myColumn] = ''

                    # Column state_well_nmbr
                    #
                    elif myColumn == 'state_well_nmbr':
                        state_well_nmbr = ''

                        if site_code in cdwrSitesL:
                            cdwr_well_nmbr = siteInfoD[site_code][myColumn]
                            if cdwr_well_nmbr is not None and len(cdwr_well_nmbr) > 0:
                                state_well_nmbr = cdwr_well_nmbr
                        if len(state_well_nmbr) < 1:
                            cdwr_well_nmbr  = myRecord[cdwrColumn]
                            if cdwr_well_nmbr is not None and len(cdwr_well_nmbr) > 0:
                                state_well_nmbr = cdwr_well_nmbr
                        if len(state_well_nmbr) < 1:
                            cdwr_well_nmbr  = myRecord['stn_id']
                            if cdwr_well_nmbr is not None and len(cdwr_well_nmbr) > 0:
                                state_well_nmbr = cdwr_well_nmbr

                        gwInfoD[site_id][myColumn] = state_well_nmbr

                    # Column cdwr_id
                    #
                    elif myColumn == 'cdwr_id':
                        gwInfoD[site_id][myColumn] = myRecord[cdwrColumn]

                    # Column station_nm
                    #
                    elif myColumn == 'station_nm':
                        station_nm = site_code

                        if site_code in cdwrSitesL:
                            station_nm = siteInfoD[site_code]['station_nm']
                        else:
                            station    = myRecord[cdwrColumn]
                            if station is not None:
                                station_nm = '%02s.00%1s/%02s.00%1s-%s' % (station[:2], station[2:3], station[3:5], station[5:6], station[6:])
                            elif myRecord['well_name'] is not None:
                                station_nm = myRecord['well_name']
                            elif myRecord['stn_id'] is not None:
                                station_nm = myRecord['stn_id']

                        gwInfoD[site_id][myColumn] = station_nm

                    # Column periodic
                    #
                    elif myColumn == 'periodic':
                        gwInfoD[site_id][myColumn] = 0

                    # Column recorder [continuous_data_station_number]
                    #
                    elif myColumn == 'recorder':
                        gwInfoD[site_id][myColumn] = ''
                        if cdwrColumn in myRecord:
                            if myRecord[cdwrColumn] is not None:
                                gwInfoD[site_id][myColumn] = 'CDWR'

                    # Column active
                    #
                    elif myColumn == 'active':
                        gwInfoD[site_id][myColumn] = False

                    # Column alt_datum_cd
                    #
                    elif myColumn == 'alt_datum_cd':
                        gwInfoD[site_id][myColumn] = 'NAVD88'

                    # Columns in CDWR database
                    #
                    elif cdwrColumn in myRecord:
                        gwInfoD[site_id][myColumn] = ''
                        if myRecord[cdwrColumn] is not None:
                            gwInfoD[site_id][myColumn] = str(myRecord[cdwrColumn])
                    else:
                        if site_code in usgsSitesD:
                            site_id = usgsSitesD[site_code]
                            if myColumn in siteInfoD[site_id]:
                                gwInfoD[site_id][myColumn] = str(siteInfoD[site_id][myColumn])


    # CDWR recorder sites with the periodical site information
    # -------------------------------------------------
    cdwrRecorderL = list({x for x in gwInfoD if len(gwInfoD[x]['recorder']) > 0})
    screen_logger.info("Processed %d CDWR recorder sites indentified within the site information in California/Klamath county, Oregon" % len(cdwrRecorderL))


    # CDWR service for periodical measurement count
    # -------------------------------------------------
    #
    tempL        = ",".join(countyL)
    sqlTable     = 'bfa9f262-24a1-45bd-8dc8-138bc8107266'
    countyColumn = 'county_name'

    # Web request for counts of periodical records for sites
    #
    #  https://data.cnra.ca.gov/api/3/action/datastore_search_sql?sql=SELECT site_code, COUNT(*) AS count_nu from "bfa9f262-24a1-45bd-8dc8-138bc8107266" WHERE "county_name" IN ('Modoc','Siskiyou') GROUP BY "site_code" ORDER BY "site_code"
    #
    URL          = 'https://data.cnra.ca.gov/api/3/action/datastore_search_sql?sql=SELECT site_code, COUNT(*) AS count_nu, MAX(msmt_date) from "%s" WHERE "%s" IN (%s) GROUP BY "site_code" ORDER BY "site_code"&limit=500000' % (sqlTable, countyColumn, tempL)
    noparmsDict  = {}
    contentType  = "application/json"
    timeOut      = 10

    screen_logger.debug("Url %s" % URL)

    message, webContent = webRequest(URL, noparmsDict, contentType, timeOut, None, screen_logger)

    screen_logger.debug("webContent %s" % webContent)

    if webContent is not None:

        # Check for empty
        #
        if len(webContent) < 1:
            message = "Empty content return from web request %s" % URL
            errorMessage(message)

        # Convert to json format
        #
        gwJson = json.loads(webContent)

        # Check for failed request
        #
        if gwJson['success'] is False:
            message = "Error: %s for %s content return from web request %s" % (gwJson['error'], URL)
            errorMessage(message)

        # Successful request
        #
        else:

            # Parse records
            #
            jsonRecords = gwJson['result']['records']
            numRecords  = len(jsonRecords)

            screen_logger.info("Processed %d CDWR sites for periodic measurement counts in California/Oregon counties %s" % (numRecords, tempL))

            # Process site information
            # -------------------------------------------------
            #
            for myRecord in jsonRecords:

                site_code = myRecord['site_code']
                count_nu  = int(myRecord['count_nu'])

                active = False
                wlDate = datetime.datetime.strptime(myRecord['max'][:10], '%Y-%m-%d')
                wlDate = wlDate.replace(tzinfo=datetime.timezone.utc)
                if wlDate >= activeDate:
                    active = True

                # Set site_id
                #
                site_id = site_code
                if site_code in cdwrSitesD:
                    site_id = cdwrSitesD[site_code]

                # Set count for field measurements
                #
                if site_id in gwInfoD:
                    gwInfoD[site_id]['periodic'] = count_nu
                    gwInfoD[site_id]['active'] = active


    # CDWR service for recorder site information
    # -------------------------------------------------
    #
    tempL        = ",".join(countyL)
    sqlTable     = '03967113-1556-4100-af2c-b16a4d41b9d0'
    countyColumn = countyColumn.upper()

    newRecorderL  = []

    # Web request
    #
    #  https://data.cnra.ca.gov/api/3/action/datastore_search_sql?sql=SELECT * from "03967113-1556-4100-af2c-b16a4d41b9d0" WHERE "COUNTY_NAME" IN ('Modoc','Siskiyou','Klamath, Or')
    #
    URL          = 'https://data.cnra.ca.gov/api/3/action/datastore_search_sql?sql=SELECT * from "%s" WHERE "%s" IN (%s)' % (sqlTable, countyColumn, tempL)
    noparmsDict  = {}
    contentType  = "application/json"
    timeOut      = 10

    screen_logger.debug("Url %s" % URL)

    message, webContent = webRequest(URL, noparmsDict, contentType, timeOut, None, screen_logger)

    screen_logger.debug("webContent %s" % webContent)

    if webContent is not None:

        # Check for empty
        #
        if len(webContent) < 1:
            message = "Empty content return from web request %s" % URL
            errorMessage(message)

        # Convert to json format
        #
        gwJson = json.loads(webContent)

        # Check for failed request
        #
        if gwJson['success'] is False:
            message = "Error: %s for %s content return from web request %s" % (gwJson['error'], URL)
            errorMessage(message)

        # Successful request
        #
        else:

            # Parse records
            #
            jsonRecords = gwJson['result']['records']
            numRecords  = len(jsonRecords)

            screen_logger.info("Processed %d CDWR recorder sites for site information in California/Oregon counties %s" % (numRecords, tempL))

            # Process site information
            # -------------------------------------------------
            #
            for myRecord in jsonRecords:

                site_code = myRecord['SITE_CODE']

                # Skip site no site_code
                #
                if site_code is None:
                    continue

                # Set site_id
                #
                site_id = site_code
                if site_code in cdwrSitesD:
                    site_id = cdwrSitesD[site_code]

                # Check for USGS site number
                #
                site_no   = ''
                agency_cd = 'CDWR'
                if site_code in usgsSitesD:
                    site_no   = usgsSitesD[site_code]
                    agency_cd = 'USGS'

                # Recorder already reported
                #
                if site_id in cdwrRecorderL:
                    cdwrRecorderL.remove(site_id)

                # New recorder site
                #
                else:
                    gwInfoD[site_id] = {}
                    newRecorderL.append(site_id)
                    screen_logger.debug("CDWR recorder site %s not in California site by county" % site_id)

                    # Prepare information for new recorder site
                    # -------------------------------------------------
                    #
                    for myColumn in mySiteFields:

                        cdwrColumn = myCdwrFields[myColumn].upper()

                        # Column site_id
                        #
                        if myColumn == 'site_id':
                            gwInfoD[site_code][myColumn] = site_id

                        # Column agency_cd
                        #
                        elif myColumn == 'agency_cd':
                            gwInfoD[site_code][myColumn] = agency_cd

                        # Column site_no
                        #
                        elif myColumn == 'site_no':
                            gwInfoD[site_code][myColumn] = site_no

                        # Column coop_site_no
                        #
                        elif myColumn == 'coop_site_no':
                            gwInfoD[site_code][myColumn] = ''

                        # Column state_well_nmbr
                        #
                        elif myColumn == 'state_well_nmbr':
                            gwInfoD[site_code][myColumn] = myRecord['STATION']

                        # Column cdwr_id
                        #
                        elif myColumn == 'cdwr_id':
                            gwInfoD[site_code][myColumn] = site_code

                        # Column station_nm
                        #
                        elif myColumn == 'station_nm':
                            if myRecord['STATION'] is not None and len(str(myRecord['STATION'])) > 0:
                                station_nm = myRecord['STATION']
                                station_nm = '%02s.00%1s/%02s.00%1s-%s' % (station[:2], station[2:3], station[3:5], station[5:6], station[6:])
                            elif myRecord['STNAME'] is not None and len(str(myRecord['STNAME'])) > 0:
                                station_nm = myRecord['STATION']
                            else:
                                station_nm = myRecord['WELL_NAME']

                            gwInfoD[site_code][myColumn] = station_nm

                        # Column periodic
                        #
                        elif myColumn == 'periodic':
                            gwInfoD[site_code][myColumn] = 0

                        # Column recorder [recorder service]
                        #
                        elif myColumn == 'recorder':
                            gwInfoD[site_code][myColumn] = 'CDWR'

                        # Column alt_va
                        #
                        elif myColumn == 'alt_va':
                            cdwrColumn = 'ELEV'
                            gwInfoD[site_code][myColumn] = myRecord[cdwrColumn]

                        # Column alt_acy_va
                        #
                        elif myColumn == 'alt_acy_va':
                            cdwrColumn = 'ELEVACC'
                            gwInfoD[site_code][myColumn] = myRecord[cdwrColumn]

                        # Column alt_datum_cd
                        #
                        elif myColumn == 'alt_datum_cd':
                            cdwrColumn = 'ELEVDATUM'
                            gwInfoD[site_code][myColumn] = myRecord[cdwrColumn]

                        # Column well_depth_va
                        #
                        elif myColumn == 'well_depth_va':
                            cdwrColumn = 'WELL_DEPTH'
                            gwInfoD[site_code][myColumn] = myRecord[cdwrColumn]

                        # Column dec_long_va
                        #
                        elif myColumn == 'dec_long_va':
                            cdwrColumn = 'LONGITUDE'
                            gwInfoD[site_code][myColumn] = myRecord[cdwrColumn]

                        # Column dec_lat_va
                        #
                        elif myColumn == 'dec_lat_va':
                            cdwrColumn = 'LATITUDE'
                            gwInfoD[site_code][myColumn] = myRecord[cdwrColumn]


    # CDWR service for recorder sites for measurement counts
    # -------------------------------------------------
    #
    if len(newRecorderL) > 0:
        tempL  = sorted(newRecorderL)
        nsites = 50
        sqlTable     = 'bfa9f262-24a1-45bd-8dc8-138bc8107266'

        # CDWR field-measurements service [groundwater]
        # -------------------------------------------------
        #
        while len(tempL) > 0:

            nList = ", ".join(f"'{item}'" for item in list(tempL[:nsites]))
            del tempL[:nsites]

            # Web request for counts periodical records in sites
            #
            #  https://data.cnra.ca.gov/api/3/action/datastore_search_sql?sql=SELECT site_code, COUNT(*) AS count_nu from "bfa9f262-24a1-45bd-8dc8-138bc8107266" WHERE "county_name" IN ('Modoc','Siskiyou') GROUP BY "site_code" ORDER BY "site_code"
            #
            URL          = 'https://data.cnra.ca.gov/api/3/action/datastore_search_sql?sql=SELECT site_code, COUNT(*) AS count_nu, MAX(msmt_date) from "bfa9f262-24a1-45bd-8dc8-138bc8107266" WHERE "site_code" IN (%s) GROUP BY "site_code" ORDER BY "site_code"&limit=500000' %  nList
            noparmsDict  = {}
            contentType  = "application/json"
            timeOut      = 10

            screen_logger.debug("Url %s" % URL)

            message, webContent = webRequest(URL, noparmsDict, contentType, timeOut, None, screen_logger)

            screen_logger.debug("webContent %s" % webContent)

            if webContent is not None:

                # Check for empty
                #
                if len(webContent) < 1:
                    message = "Empty content return from web request %s" % URL
                    errorMessage(message)

                # Convert to json format
                #
                gwJson = json.loads(webContent)

                # Check for failed request
                #
                if gwJson['success'] is False:
                    message = "Error: %s for %s content return from web request %s" % (gwJson['error'], URL)
                    errorMessage(message)

                # Successful request
                #
                else:

                    # Parse records
                    #
                    jsonRecords = gwJson['result']['records']
                    numRecords  = len(jsonRecords)

                    screen_logger.info("Process %d CDWR recorder sites for measurement counts in California/Oregon counties" % numRecords)

                    # Process site information
                    # -------------------------------------------------
                    #
                    for myRecord in jsonRecords:

                        site_code = myRecord['site_code']
                        count_nu  = int(myRecord['count_nu'])

                        active = False
                        wlDate = datetime.datetime.strptime(myRecord['max'][:10], '%Y-%m-%d')
                        wlDate = wlDate.replace(tzinfo=datetime.timezone.utc)
                        if wlDate >= activeDate:
                            active = True

                        # Set site_id
                        #
                        site_id = site_code
                        if site_code in cdwrSitesD:
                            site_id = cdwrSitesD[site_code]

                        # Set count for field measurements
                        #
                        if site_id in gwInfoD:
                            gwInfoD[site_id]['periodic'] = count_nu
                            gwInfoD[site_id]['active'] = active


    # Create periodic/recorder sites
    #
    periodicSitesD = {x:gwInfoD[x] for x in gwInfoD if gwInfoD[x]['periodic'] > 0}
    recorderSitesD = {x:gwInfoD[x] for x in gwInfoD if len(gwInfoD[x]['recorder']) > 0}

    # Update collection sites for periodic/recorder information
    #
    collectionL = list({x for x in siteInfoD if len(siteInfoD[x]['cdwr_id']) > 0})

    for site_id in sorted(collectionL):

        if site_id in gwInfoD:
            siteInfoD[site_id]['periodic'] += gwInfoD[site_id]['periodic']

            if len(gwInfoD[site_id]['recorder']) > 0:
                if len(siteInfoD[site_id]['recorder']) > 0:
                    if gwInfoD[site_id]['recorder'] not in siteInfoD[site_id]['recorder']:
                        siteInfoD[site_id]['recorder'].append(gwInfoD[site_id]['recorder'])
                else:
                    siteInfoD[site_id]['recorder'].append(gwInfoD[site_id]['recorder'])

            if gwInfoD[site_id]['active']:
                siteInfoD[site_id]['active'] = True


    # Count sites
    #
    cdwrSet        = set(cdwrSitesL)
    missingSet     = set(missSitesL)
    matchSitesL    = list(cdwrSet.difference(missingSet))

    periodicSitesL = list({periodicSitesD[x]['cdwr_id'] for x in periodicSitesD})
    periodicSet    = set(periodicSitesL)
    matchperiodicL = list(cdwrSet.intersection(periodicSet))
    newperiodicL   = list(periodicSet.difference(cdwrSet))

    recorderSitesL = list({recorderSitesD[x]['cdwr_id'] for x in recorderSitesD})
    recorderSet    = set(recorderSitesL)
    matchrecorderL = list(recorderSet.intersection(cdwrSet))
    newrecorderL   = list(recorderSet.difference(cdwrSet))

    usgsSitesL     = list({gwInfoD[x]['site_no'] for x in gwInfoD if len(gwInfoD[x]['site_no']) > 0})

    # Print information
    #
    ncols    = 85
    messages = []
    messages.append('\n\tProcessed CDWR site information')
    messages.append('\t%s' % (ncols * '-'))
    messages.append('\t%-79s %5d' % ('Number of sites in collection file', len(siteInfoD)))
    messages.append('\t%-79s %5d' % ('Number of CDWR sites in collection file', len(cdwrSitesL)))
    messages.append('\t%-79s %5d' % ('Number of CDWR sites in collection file NOT retrieved from CDWR database', len(missSitesL)))
    messages.append('\t%-79s %5d' % ('Number of sites retrieved from CDWR database', len(gwInfoD)))
    messages.append('\t%-79s %5d' % ('Number of periodic sites with waterlevels from CDWR database', len(periodicSitesD)))
    messages.append('\t%-79s %5d' % ('Number of periodic sites in collection file from CDWR database', len(matchperiodicL)))
    messages.append('\t%-79s %5d' % ('Number of periodic sites possible additions from CDWR database', len(newperiodicL)))
    messages.append('\t%-79s %5d' % ('Number of recorder sites from CDWR database', len(recorderSitesD)))
    messages.append('\t%-79s %5d' % ('Number of recorder sites in collection file from CDWR database', len(matchrecorderL)))
    messages.append('\t%-79s %5d' % ('Number of recorder sites possible additions from CDWR database', len(newrecorderL)))
    messages.append('\t%-79s %5d' % ('Number of CDWR sites assigned an USGS site number from CDWR database', len(usgsSitesL)))
    messages.append('\t%s' % (ncols * '-'))
    if len(matchSitesL) > 0:
        messages.append('')
        messages.append('\t%-70s' % 'CDWR periodic and recorder sites in collection file in CDWR database')
        messages.append('\t%s' % (ncols * '-'))
        fmt = '\t%-15s %-20s %-25s %10s %10s'
        messages.append(fmt % ('USGS',        'CDWR',      'USGS',    'Periodic', 'Recorder'))
        messages.append(fmt % ('Site Number', 'Site Code', 'Station', 'Flag',     'Flag'))
        messages.append('\t%s' % (ncols * '-'))
        for site_code in sorted(matchSitesL):
            site_id  = cdwrSitesD[site_code]
            periodic = gwInfoD[site_id]['periodic']
            recorder = gwInfoD[site_id]['recorder']
            messages.append(fmt % (gwInfoD[site_id]['site_no'], site_code, gwInfoD[site_id]['station_nm'][:25], periodic, recorder))
        messages.append('\t%s' % (ncols * '-'))
    if len(missSitesL) > 0:
        messages.append('')
        messages.append('\t%-70s' % 'CDWR sites in collection file NOT in CDWR database')
        messages.append('\t%s' % (ncols * '-'))
        fmt = '\t%-20s %-20s %-40s'
        messages.append(fmt % ('USGS',        'CDWR',      'USGS'))
        messages.append(fmt % ('Site Number', 'Site Code', 'Station'))
        messages.append('\t%s' % (ncols * '-'))
        for site_code in sorted(missSitesL):
            site_id    = cdwrSitesD[site_code]
            site_no    = siteInfoD[site_id]['site_no']
            station_nm = siteInfoD[site_id]['station_nm'][:40]
            messages.append(fmt % (site_no, site_code, station_nm))
        messages.append('\t%s' % (ncols * '-'))
    if len(newperiodicL) > 0:
        messages.append('')
        messages.append('\t%-70s' % 'CDWR periodic sites to possibly add from CDWR database')
        messages.append('\t%s' % (ncols * '-'))
        fmt = '\t%-20s %-15s %-25s %10s %10s'
        messages.append(fmt % ('CDWR', 'CDWR',        'CDWR',    'Periodic', 'Recorder'))
        messages.append(fmt % ('ID',   'State Number','Station', 'Flag',     'Flag'))
        messages.append('\t%s' % (ncols * '-'))
        for site_code in sorted(newperiodicL):
            #screen_logger.info("CDWR periodic site %s to possibly add from CDWR database" % site_code)
            messages.append(fmt % (site_code, gwInfoD[site_code]['state_well_nmbr'], gwInfoD[site_code]['station_nm'][:25], gwInfoD[site_code]['periodic'], gwInfoD[site_code]['recorder']))
        messages.append('\t%s' % (ncols * '-'))
    if len(newrecorderL) > 0:
        messages.append('')
        messages.append('\t%-70s' % 'CDWR recorder sites to possibly add from CDWR database')
        messages.append('\t%s' % (ncols * '-'))
        fmt = '\t%-20s %-15s %-25s %10s %10s'
        messages.append(fmt % ('CDWR', 'CDWR Recorder', 'CDWR',    'Periodic', 'Recorder'))
        messages.append(fmt % ('ID',   'State Number',  'Station', 'Flag',     'Flag'))
        messages.append('\t%s' % (ncols * '-'))
        for site_code in sorted(newrecorderL):
            messages.append(fmt % (site_code, gwInfoD[site_code]['state_well_nmbr'], gwInfoD[site_code]['station_nm'][:25], gwInfoD[site_code]['periodic'], gwInfoD[site_code]['recorder']))
        messages.append('\t%s' % (ncols * '-'))
    messages.append('\n')
    messages.append('\n')

    screen_logger.info('\n'.join(messages))
    file_logger.info('\n'.join(messages))

    return periodicSitesD, recorderSitesD
# =============================================================================

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
mySiteFormat = [
                "20s", # site_id
                "10s", # agency_cd
                "20s", # site_no
                "15s", # coop_site_no
                "20s", # state_well_nmbr
                "30s", # cdwr_id
                "30s", # station_nm
                "10s", # periodic
                "10s", # recorder
                "16s", # dec_lat_va
                "16s", # dec_long_va
                "12s", # alt_va
                "10s", # alt_acy_va
                "16s", # alt_datum_cd
                "16s"  # well_depth
               ]

# Process Fips codes
# -------------------------------------------------
#
fipsCodesD = processFipsCodes (fipsCodesL)
if len(fipsCodesL) != len(fipsCodesD):
    message = 'Warning: Not all FIPS codes specified were matched in the Census database\n\tPlease check the list'
    errorMessage(message)

# Process collection or recorder file
# -------------------------------------------------
#
siteInfoD = processCollectionSites(collection_file, mySiteFields)

# Prepare OWRD records
# -------------------------------------------------
#
owrdPeriodicD, owrdRecorderD, owrdSitesD = processOWRD(siteInfoD, mySiteFields, fipsCodesD, owrdsites_file, owrdother_file, owrdwls_file)

owrdOtherD = dict({owrdSitesD[x]['coop_site_no']:owrdSitesD[x]['site_no'] for x in owrdSitesD if len(owrdSitesD[x]['site_no']) > 0})
usgsOtherD = dict({owrdSitesD[x]['site_no']:owrdSitesD[x]['coop_site_no'] for x in owrdSitesD if len(owrdSitesD[x]['site_no']) > 0})

# Prepare USGS records from NwisWeb site service
# -------------------------------------------------
#
if len(hydrologicCodesL) > 0:
    usgsPeriodicD, usgsRecorderD = ProcessOgcapiUSGS(siteInfoD, mySiteFields, hydrologicCodesL)
if len(fipsCodesL) > 0:
    nothing = ''
    usgsPeriodicD, usgsRecorderD = processOgcapiUSGS(siteInfoD, mySiteFields, fipsCodesL)

# Prepare CDWR records
# -------------------------------------------------
#
cdwrPeriodicD, cdwrRecorderD = processCDWR(siteInfoD, mySiteFields, fipsCodesD)


# Print operational report
#
ncols    = 81
messages = []
messages.append('\n\tProcessed Periodic and Recorder site information')
messages.append('\t%s' % (81 * '='))
messages.append('\t%-70s %10d' % ('Number of sites in current collection file', len(siteInfoD)))

# Count sites
#
usgsSitesL        = list({siteInfoD[x]['site_no'] for x in siteInfoD if len(siteInfoD[x]['site_no']) > 0})
usgsPeriodicL     = list({siteInfoD[x]['site_no'] for x in usgsSitesL if siteInfoD[x]['periodic'] > 0})
usgsRecorderL     = list({siteInfoD[x]['site_no'] for x in usgsSitesL if 'USGS' in siteInfoD[x]['recorder']})

usgsPeriodicList  = list({x for x in usgsPeriodicD if usgsPeriodicD[x]['periodic'] >= minimumCount})
usgsRecorderList  = list(usgsRecorderD.keys())

messages.append('')
messages.append('\t%-80s' % 'Processing sites from USGS database')
messages.append('\t%s' % (ncols * '-'))
messages.append('\t%-70s %10d' % ('Number of USGS sites in current collection file', len(usgsSitesL)))
messages.append('\t%-70s %10d' % ('Number of USGS periodic sites in current collection file', len(usgsPeriodicL)))
messages.append('\t%-70s %10d' % ('Total number of periodic sites possible additions from USGS database', len(usgsPeriodicD)))
messages.append('\t%-70s %10d' % ('Number of additional USGS sites possible with periodic msts >= %d' % minimumCount, len(usgsPeriodicList)))
messages.append('\t%-70s %10d' % ('Number of USGS recorder sites in current collection file', len(usgsRecorderL)))
messages.append('\t%-70s %10d' % ('Number of additional recorder sites possible from USGS database', len(usgsRecorderList)))

owrdSitesL        = list({siteInfoD[x]['site_id'] for x in siteInfoD if len(siteInfoD[x]['coop_site_no']) > 0})
owrdPeriodicL     = list({siteInfoD[x]['coop_site_no'] for x in owrdSitesL if int(str(siteInfoD[x]['periodic'])) > 0})
owrdRecorderL     = list({siteInfoD[x]['coop_site_no'] for x in owrdSitesL if 'OWRD' in siteInfoD[x]['recorder']})

owrdPeriodicList  = list({x for x in owrdPeriodicD if owrdPeriodicD[x]['periodic'] >= minimumCount})
owrdRecorderList  = list(owrdRecorderD.keys())

messages.append('')
messages.append('\t%-80s' % 'Processing sites from OWRD database')
messages.append('\t%s' % (ncols * '-'))
messages.append('\t%-70s %10d' % ('Number of OWRD sites in current collection file', len(owrdSitesL)))
messages.append('\t%-70s %10d' % ('Number of OWRD periodic sites in current collection file', len(owrdPeriodicL)))
messages.append('\t%-70s %10d' % ('Total number of periodic sites possible additions from OWRD database', len(owrdPeriodicD)))
messages.append('\t%-70s %10d' % ('Number of additional OWRD sites possible with periodic msts >= %d' % minimumCount, len(owrdPeriodicList)))
messages.append('\t%-70s %10d' % ('Number of OWRD recorder sites in current collection file', len(owrdRecorderL)))
messages.append('\t%-70s %10d' % ('Number of additional recorder sites possible from OWRD database', len(owrdRecorderList)))

cdwrSitesL        = list({siteInfoD[x]['site_id'] for x in siteInfoD if len(siteInfoD[x]['cdwr_id']) > 0})
cdwrPeriodicL     = list({siteInfoD[x]['cdwr_id'] for x in cdwrSitesL if siteInfoD[x]['periodic'] > 0})
cdwrRecorderL     = list({siteInfoD[x]['cdwr_id'] for x in cdwrSitesL if 'CDWR' in siteInfoD[x]['recorder']})

cdwrPeriodicList  = list({x for x in cdwrPeriodicD if cdwrPeriodicD[x]['periodic'] >= minimumCount})
cdwrRecorderList  = list(cdwrRecorderD.keys())

messages.append('')
messages.append('\t%-80s' % 'Processing sites from CDWR database')
messages.append('\t%s' % (ncols * '-'))
messages.append('\t%-70s %10d' % ('Number of CDWR sites in current collection file', len(cdwrSitesL)))
messages.append('\t%-70s %10d' % ('Number of CDWR periodic sites in current collection file', len(cdwrPeriodicL)))
messages.append('\t%-70s %10d' % ('Total number of periodic sites possible additions from CDWR database', len(cdwrPeriodicD)))
messages.append('\t%-70s %10d' % ('Number of additional CDWR sites possible with periodic msts >= %d' % minimumCount, len(cdwrPeriodicList)))
messages.append('\t%-70s %10d' % ('Number of CDWR recorder sites in current collection file', len(cdwrRecorderL)))
messages.append('\t%-70s %10d' % ('Number of additional recorder sites possible from CDWR database', len(cdwrRecorderList)))

messages.append('\t%s' % (ncols * '='))
messages.append('')

screen_logger.info('\n'.join(messages))
file_logger.info('\n'.join(messages))


# Prepare periodic/recorder collection file
# -------------------------------------------------
#
headerText = 'Periodic and Recorder'

localDate     = datetime.datetime.now().strftime("%B %d, %Y")

# Print header information
#
outputL = []
outputL.append("## U.S. Geological Survey")
outputL.append("## Groundwater Periodic and Recorder Sites")
outputL.append("##")
outputL.append("## Version %-30s" % version)
outputL.append("## Version_Date on %-30s" % localDate)
outputL.append("##")
outputL.append("##==========================================================================================")

outputL.append("\t".join(mySiteFields))
#outputL.append("\t".join(mySiteFormat))

# Print information
#
for site_id in sorted(siteInfoD.keys()):

    recordL = []
    for myColumn in mySiteFields:
        if myColumn == 'coop_site_no' and len(str(siteInfoD[site_id][myColumn])) < 1:
            if site_id in usgsOtherD and len(str(usgsOtherD[site_id][myColumn])) > 0:
                siteInfoD[site_id][myColumn] = usgsOtherD[site_id][myColumn]
        if myColumn == 'state_well_nmbr' and len(str(siteInfoD[site_id]['state_well_nmbr'])) < 1 and len(str(siteInfoD[site_id]['coop_site_no'])) > 0:
            coop_site_no = siteInfoD[site_id]['coop_site_no']
            if coop_site_no in owrdSitesD and len(str(owrdSitesD[coop_site_no][myColumn])) > 0:
                siteInfoD[site_id][myColumn] = owrdSitesD[coop_site_no][myColumn]
        if myColumn == 'recorder':
            if len(siteInfoD[site_id][myColumn]) > 0:
                siteInfoD[site_id][myColumn] = ', '.join(siteInfoD[site_id][myColumn])
            else:
                siteInfoD[site_id][myColumn] = ''

        recordL.append(str(siteInfoD[site_id][myColumn]))

    outputL.append("\t".join(recordL))

# Print information
#
if len(usgsPeriodicList) > 0:

    outputL.append("##")
    outputL.append("## Possble New Periodic Sites from USGS source")
    outputL.append("##")

    for site_id in sorted(usgsPeriodicList):

        recordL = []

        for myColumn in mySiteFields:
            if myColumn == 'coop_site_no' and len(str(usgsPeriodicD[site_id][myColumn])) < 1:
                if site_id in usgsOtherD and len(str(usgsOtherD[site_id][myColumn])) > 0:
                    usgsPeriodicD[site_id][myColumn] = usgsOtherD[site_id][myColumn]
            recordL.append(usgsPeriodicD[site_id][myColumn])

        outputL.append("#%s" % '\t'.join(str(item) for item in recordL))

if len(usgsRecorderList) > 0:

    outputL.append("##")
    outputL.append("## Possble New Recorder Sites from USGS source")
    outputL.append("##")

    for site_id in sorted(usgsRecorderList):

        recordL = []

        usgsRecorderD[site_id]['recorder'] = 'USGS'
        for myColumn in mySiteFields:
            if myColumn == 'coop_site_no' and len(str(usgsRecorderD[site_id][myColumn])) < 1:
                if site_id in usgsOtherD and len(str(usgsOtherD[site_id][myColumn])) > 0:
                    usgsRecorderD[site_id][myColumn] = usgsOtherD[site_id][myColumn]
            recordL.append(usgsRecorderD[site_id][myColumn])

        outputL.append("#%s" % '\t'.join(str(item) for item in recordL))

# Print information
#
if len(owrdPeriodicList) > 0:

    outputL.append("##")
    outputL.append("## Possble Additional Periodic Sites from OWRD source")
    outputL.append("##")

    for site_id in sorted(owrdPeriodicList):

        recordL = []

        for myColumn in mySiteFields:
            if myColumn == 'site_no' and len(str(owrdPeriodicD[site_id][myColumn])) < 1:
                if site_id in owrdOtherD and len(str(owrdOtherD[site_id][myColumn])) > 0:
                    owrdPeriodicD[site_id][myColumn] = owrdOtherD[site_id][myColumn]
            if myColumn == 'recorder' and len(owrdPeriodicD[site_id][myColumn]) > 0:
                owrdPeriodicD[site_id][myColumn] = ', '.join(owrdPeriodicD[site_id][myColumn])
            elif myColumn == 'recorder' and len(owrdPeriodicD[site_id][myColumn]) < 1:
                owrdPeriodicD[site_id][myColumn] = ''

            recordL.append(owrdPeriodicD[site_id][myColumn])

        outputL.append("#%s" % '\t'.join(str(item) for item in recordL))

if len(owrdRecorderList) > 0:

    outputL.append("##")
    outputL.append("## Possble New Recorder Sites from OWRD source")
    outputL.append("##")

    for site_id in sorted(owrdRecorderList):

        recordL = []

        owrdRecorderD[site_id]['recorder'] = 'OWRD'
        for myColumn in mySiteFields:
            if myColumn == 'site_no' and len(str(owrdRecorderD[site_id][myColumn])) < 1:
                if site_id in owrdOtherD and len(str(owrdOtherD[site_id][myColumn])) > 0:
                    owrdRecorderD[site_id][myColumn] = owrdOtherD[site_id][myColumn]
            if myColumn == 'recorder' and len(owrdPeriodicD[site_id][myColumn]) < 1:
                owrdPeriodicD[site_id][myColumn] = ''

            recordL.append(owrdRecorderD[site_id][myColumn])

        outputL.append("#%s" % '\t'.join(str(item) for item in recordL))

# Print information
#
if len(cdwrPeriodicList) > 0:

    outputL.append("##")
    outputL.append("## Possble New Periodic Sites from CDWR source")
    outputL.append("##")

    for site_id in sorted(cdwrPeriodicList):

        recordL = []

        cdwrPeriodicD[site_id]['recorder'] = ''
        for myColumn in mySiteFields:
            recordL.append(cdwrPeriodicD[site_id][myColumn])

        outputL.append("#%s" % '\t'.join(str(item) for item in recordL))

if len(cdwrRecorderList) > 0:

    outputL.append("##")
    outputL.append("## Possble New Recorder Sites from CDWR source")
    outputL.append("##")

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

# =============================================================================

def ProcessOgcapiUSGS (siteInfoD, mySiteFields, hydrologicCodesL):

    gwInfoD        = {}

    keyColumn      = 'site_no'

    activeDate     = datetime.datetime.now()

    # Prepare list of site numbers
    # -------------------------------------------------
    #
    usgsSitesL = list({siteInfoD[x]['site_no'] for x in siteInfoD if len(siteInfoD[x]['site_no']) > 0})
    owrdSitesL = list({siteInfoD[x]['coop_site_no'] for x in siteInfoD if len(siteInfoD[x]['coop_site_no']) > 0})
    cdwrSitesL = list({siteInfoD[x]['cdwr_id'] for x in siteInfoD if len(siteInfoD[x]['cdwr_id']) > 0})

    missSitesL = list(usgsSitesL)

    agencyL    = []
    if len(usgsSitesL) > 0:
        agencyL.append('USGS')
    if len(owrdSitesL) > 0:
        agencyL.append('OWRD')
    if len(cdwrSitesL) > 0:
        agencyL.append('CDWR')

    # NwisWeb site service for general information for periodic/recorder wells
    # ------------------------------------------------------------------------
    #
    tempL  = list(hydrologicCodesL)
    ncodes = 15
    propertiesL = []

    while len(tempL) > 0:

        nList = ",".join(tempL[:ncodes])
        del tempL[:ncodes]

        # Web request
        #
        URL          = 'https://waterservices.usgs.gov/nwis/site/?format=rdb&countyCd=%s&siteOutput=expanded&siteStatus=all&siteType=GW&hasDataTypeCd=gw,dv,iv' % nList
        noparmsDict  = {
            'filter-lang' : 'cql-text',
            'filter' : " AND ".join([
                "%s" % " OR ".join(f"hydrologic_unit_code LIKE '{item}%'" for item in nList),
                "site_type IN ('Well')"
            ]),
            'sortby' : 'id',
            #'properties' : 'parameter_code,monitoring_location_id,observing_procedure,observing_procedure_code,value,unit_of_measure,time,qualifier,vertical_datum,approval_status,measuring_agency',
            'skipGeometry' : 'true',
            'limit' : 50000,
            'f' : 'json',
            'api_key' : 'nTsVxhFct7I3vFQgl2ANx3wphLyvDrmrjy5JIsSV'
        }
        contentType  = "application/json"
        timeOut      = 1000

        screen_logger.info("Url %s" % URL)
        #file_logger.info('\n\tUrl %s' % URL)

        message, webContent = webRequest(URL, noparmsDict, contentType, timeOut, None, screen_logger)

        if webContent is not None:

            # Check for empty file
            #
            if len(webContent) < 1:
                message = "Empty content return from web request %s" % URL
                errorMessage(message)

            # Process site information
            # -------------------------------------------------
            #
            #screen_logger.info("Groundwater records /n%s" % webContent)
            gwJson = json.loads(webContent)
            numRecords = gwJson['numberReturned']

            screen_logger.info("Process %d monitoring_location records for %d huc" % (numRecords, len(nList)))
            if numRecords > 0:

                propertiesL.extend(gwJson['features'])
