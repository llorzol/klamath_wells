#!/usr/bin/env python3
#
###############################################################################
# $Id: buildCollectionFile.py
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
version         = "2.20"
version_date    = "October 30, 2024"
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

def processCollectionSites (collection_file, mySiteFields):

   siteInfoD      = {}
   siteCount      = 0
   countUSGS      = 0
   countOWRD      = 0
   countCDWR      = 0

   agencyL        = []

   periodicSitesL = []
   recorderSitesL = []

   keyColumn      = 'site_id'
   
   # Read collection file
   # -------------------------------------------------
   #
   with open(collection_file,'r') as f:
       linesL = f.read().splitlines()
   
   # Check for empty file
   #
   if len(linesL) < 1:
      message = "Empty collection file %s" % collection_file
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
      message = "Missing index column %s" % keyColumn
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
         myValue = ''
         if myColumn in namesL:
            if str(valuesL[ namesL.index(myColumn) ]) == 'None':
               myValue = ''
            else:
               myValue = str(valuesL[ namesL.index(myColumn) ])
               
         else:
            myValue = ''
               
         siteInfoD[site_id][myColumn] = myValue

      # Fix site if needed
      #
      if len(siteInfoD[site_id]['coop_site_no']) > 0:
         siteInfoD[site_id]['coop_site_no'] = '%4s%07d' % (siteInfoD[site_id]['coop_site_no'][:4], int(siteInfoD[site_id]['coop_site_no'][5:]))
         
      if siteInfoD[site_id]['station_nm'].find(' ') > 0:
         siteInfoD[site_id]['station_nm'] = siteInfoD[site_id]['station_nm'].replace(' ', '')
         
      if len(siteInfoD[site_id]['site_no']) > 0:
         siteInfoD[site_id]['agency_cd'] = 'USGS'
         site_no                         = siteInfoD[site_id]['site_no']
         siteInfoD[site_id]['site_id']   = site_no
         siteInfoD[site_no]              = siteInfoD[site_id]
         del siteInfoD[site_id]
      else:
         siteInfoD[site_id]['agency_cd'] = 'OWRD'
         coop_site_no                    = siteInfoD[site_id]['coop_site_no']
         siteInfoD[site_id]['site_id']   = coop_site_no
         siteInfoD[coop_site_no]         = siteInfoD[site_id]
         del siteInfoD[site_id]
         
   
   # Count sites
   # -------------------------------------------------
   #
   usgsSitesL = list({siteInfoD[x]['site_no'] for x in siteInfoD if len(siteInfoD[x]['site_no']) > 0})
   owrdSitesL = list({siteInfoD[x]['coop_site_no'] for x in siteInfoD if len(siteInfoD[x]['coop_site_no']) > 0})
   cdwrSitesL = list({siteInfoD[x]['cdwr_id'] for x in siteInfoD if len(siteInfoD[x]['cdwr_id']) > 0})

   agencyL    = []
   if len(usgsSitesL) > 0:
      agencyL.append('USGS')
   if len(owrdSitesL) > 0:
      agencyL.append('OWRD')
   if len(cdwrSitesL) > 0:
      agencyL.append('CDWR')
  
   periodicSitesL = list({siteInfoD[x]['site_id'] for x in siteInfoD if len(siteInfoD[x]['periodic']) > 0})
   recorderSitesL = list({siteInfoD[x]['site_id'] for x in siteInfoD if len(siteInfoD[x]['recorder']) > 0})

   usgsRecordersL = list({siteInfoD[x]['site_no'] for x in siteInfoD if 'USGS' in siteInfoD[x]['recorder']})
   owrdRecordersL = list({siteInfoD[x]['site_no'] for x in siteInfoD if 'OWRD' in siteInfoD[x]['recorder']})
   cdwrRecordersL = list({siteInfoD[x]['site_no'] for x in siteInfoD if 'CDWR' in siteInfoD[x]['recorder']})
   
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

def processFipsCodes (fipsCodesL):

   fipsCodesD  = {}
   fipsCount   = 0

   tempList    = list(fipsCodesL)

   namesL      = ['stateabbev', 'statecode', 'countycode', 'countyname', 'region']

   # Census service
   # -------------------------------------------------
   #
   # https://www2.census.gov/geo/docs/reference/codes/files/national_county.txt
   #
   #
   URL          = 'https://www2.census.gov/geo/docs/reference/codes/files/national_county.txt'
   noparmsDict  = {}
   contentType  = "text"
   timeOut      = 1000

   #screen_logger.info("Url %s" % URL)
                 
   message, webContent = webRequest(URL, noparmsDict, contentType, timeOut, None, screen_logger)
     
   if webContent is not None:

      # Check for empty file
      #
      if len(webContent) < 1:
         message = "Empty content return from web request %s" % URL
         errorMessage(message)

      linesL =webContent.splitlines()

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
      
      valuesL  = Line.split(',')

      fipsCode = "".join([str(valuesL[ namesL.index('statecode') ]), str(valuesL[ namesL.index('countycode') ])])
   
      if fipsCode in fipsCodesL:
         fipsCodesD[fipsCode] = str(valuesL[ namesL.index('countyname') ])
         tempList.remove(fipsCode)
                              
      
   # Print information
   #
   messages = []
   messages.append('\n\tProcessed fips codes information')
   messages.append('\t%s' % (81 * '-'))
   messages.append('\t%-70s %10d' % ('Number of fips codes user specified', len(fipsCodesL)))
   messages.append('\t%-70s %10d' % ('Number of fips codes matched in the Census database', len(fipsCodesD)))
   messages.append('\t%-70s %10d' % ('Number of fips codes not matched in the Census database', len(tempList)))
   messages.append('\t%s' % (81 * '-'))
   messages.append('\n')
   if len(fipsCodesD) > 0:
      messages.append('\t%-70s' % 'Fips codes matched in Census database')
      messages.append('\t%s' % (81 * '-'))
      for fipCode in sorted(fipsCodesD.keys()):
         messages.append('\t%-20s %60s' % (fipCode, fipsCodesD[fipCode]))
      messages.append('\t%s' % (81 * '-'))
   messages.append('\n')
   if len(tempList) > 0:
      messages.append('\t%-70s' % 'Fips codes not matched in Census database')
      messages.append('\t%s' % (81 * '-'))
      for fipCode in sorted(tempList):
         messages.append('\t%-20s %60s' % (fipCode, ' '))
      messages.append('\t%s' % (81 * '-'))
   messages.append('\n')

   screen_logger.info('\n'.join(messages))
   file_logger.info('\n'.join(messages))
         
   return fipsCodesD
# =============================================================================

def processUSGS (siteInfoD, mySiteFields, fipsCodesL):

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
   tempL  = list(fipsCodesL)
   ncodes = 50
   linesL = []

   while len(tempL) > 0:

      nList = ",".join(tempL[:ncodes])
      del tempL[:ncodes]
      
      # Web request
      #
      URL          = 'https://waterservices.usgs.gov/nwis/site/?format=rdb&countyCd=%s&siteOutput=expanded&siteStatus=all&siteType=GW&hasDataTypeCd=gw,dv,iv' % nList
      noparmsDict  = {}
      contentType  = "text"
      timeOut      = 1000

      #screen_logger.info("Url %s" % URL)
      #file_logger.info('\n\tUrl %s' % URL)

      message, webContent = webRequest(URL, noparmsDict, contentType, timeOut, None, screen_logger)
     
      if webContent is not None:

         # Check for empty file
         #
         if len(webContent) < 1:
            message = "Empty content return from web request %s" % URL
            errorMessage(message)

         newList = list(webContent.splitlines())
         linesL.extend(newList)
   
   # Process site information
   # -------------------------------------------------
   #
   while len(linesL) > 0:

      # Parse for column names [rdb format]
      #
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

   # Parse for data
   #
   while len(linesL) > 0:
      
      if len(linesL[0]) < 1:
         del linesL[0]
         continue
      
      if linesL[0][0] == '#':
         
         while len(linesL) > 0:

            if linesL[0][0] == '#':
               del linesL[0]
               continue

            else:
               del linesL[0]
               del linesL[0]
               break

      valuesL = linesL[0].split('\t')

      site_id = str(valuesL[ namesL.index(keyColumn) ])
                  
      # Remove site from list
      #
      if site_id in missSitesL:
         missSitesL.remove(site_id)
   
      # Set site information
      #
      if site_id not in gwInfoD:
         gwInfoD[site_id] = {}
   
      for myColumn in mySiteFields:
         myValue = ''
         if myColumn == 'site_id':
            myValue = site_id
         elif myColumn in namesL:
            if len(str(valuesL[ namesL.index(myColumn) ])) > 0:
               myValue = str(valuesL[ namesL.index(myColumn) ])
         else:
            if site_id in siteInfoD:
               if myColumn in siteInfoD[site_id]:
                  myValue = siteInfoD[site_id][myColumn]
               
         gwInfoD[site_id][myColumn] = myValue

      # Set well depth if blank with hole depth
      #
      if 'hole_depth_va' in namesL:
         if len(str(gwInfoD[site_id]['well_depth_va'])) < 1:
            if len(str(valuesL[ namesL.index('hole_depth_va') ])) > 0:
               gwInfoD[site_id]['well_depth_va'] = str(valuesL[ namesL.index('hole_depth_va') ])
                  

      del linesL[0]
      

   # NwisWeb site service for period of record for periodic/recorder wells
   # ---------------------------------------------------------------------
   #
   tempL  = list(fipsCodesL)
   ncodes = 50
   linesL = []

   while len(tempL) > 0:

      nList = ",".join(tempL[:ncodes])
      del tempL[:ncodes]
      
      # Web request
      #
      URL          = 'https://waterservices.usgs.gov/nwis/site/?format=rdb&countyCd=%s&siteStatus=all&siteType=GW&hasDataTypeCd=gw,dv,iv&outputDataTypeCd=gw,dv,iv' % nList
      noparmsDict  = {}
      contentType  = "text"
      timeOut      = 1000

      #screen_logger.info("Url %s" % URL)
      #file_logger.info('\n\tUrl %s' % URL)

      message, webContent = webRequest(URL, noparmsDict, contentType, timeOut, None, screen_logger)
     
      if webContent is not None:

         # Check for empty file
         #
         if len(webContent) < 1:
            message = "Empty content return from web request %s" % URL
            errorMessage(message)

         newList = list(webContent.splitlines())
         linesL.extend(newList)
   
   # Process site periodic/recorder information
   # -------------------------------------------------
   #
   while len(linesL) > 0:

      # Parse for column names [rdb format]
      #
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

   # Parse for data
   #
   while len(linesL) > 0:
      
      if len(linesL[0]) < 1:
         del linesL[0]
         continue
      
      if linesL[0][0] == '#':
         
         while len(linesL) > 0:

            if linesL[0][0] == '#':
               del linesL[0]
               continue

            else:
               del linesL[0]
               del linesL[0]
               break

      valuesL = linesL[0].split('\t')

      site_id = str(valuesL[ namesL.index(keyColumn) ])
   
      # Set site information
      #
      if site_id not in gwInfoD:
         gwInfoD[site_id] = {}
   
      # Set periodic/recorder information
      #
      data_type_cd = ''
      count_nu     = ''
      
      myColumn = 'data_type_cd'
      if myColumn in namesL:
         data_type_cd = str(valuesL[ namesL.index(myColumn) ])
      myColumn = 'count_nu'
      if myColumn in namesL:
         count_nu = str(valuesL[ namesL.index(myColumn) ])

      if data_type_cd in ['iv', 'dv']:
         gwInfoD[site_id]['recorder'] = 'USGS'
     
      if data_type_cd in ['gw']:
         gwInfoD[site_id]['periodic'] = count_nu

            
      del linesL[0]

      
   # Missing USGS sites for general information for periodic/recorder wells
   # ----------------------------------------------------------------------
   #
   if len(missSitesL) > 0:
      tempL  = list(missSitesL)
      nsites = 50
      linesL = []
   
      while len(tempL) > 0:
   
         nList = ",".join(tempL[:nsites])
         del tempL[:nsites]
   
         # Web request
         #
         URL          = 'https://waterservices.usgs.gov/nwis/site/?format=rdb&sites=%s&siteOutput=expanded&siteStatus=all&siteType=GW&hasDataTypeCd=gw,dv,iv' % nList
         noparmsDict  = {}
         contentType  = "text"
         timeOut      = 1000
   
         #screen_logger.info("Url %s" % URL)
                    
         message, webContent = webRequest(URL, noparmsDict, contentType, timeOut, None, screen_logger)
        
         if webContent is not None:
   
            # Check for empty file
            #
            if len(webContent) < 1:
               message = "Empty content return from web request %s" % URL
               errorMessage(message)
   
            newList = list(webContent.splitlines())
            linesL.extend(newList)
      
      # Process site measurements
      # -------------------------------------------------
      #
      while len(linesL) > 0:
   
         # Parse for column names [rdb format]
         #
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
   
      # Parse for data
      #
      while len(linesL) > 0:
         
         if len(linesL[0]) < 1:
            del linesL[0]
            continue
         
         if linesL[0][0] == '#':
            
            while len(linesL) > 0:
   
               if linesL[0][0] == '#':
                  del linesL[0]
                  continue
   
               else:
                  del linesL[0]
                  del linesL[0]
                  break
   
         valuesL = linesL[0].split('\t')
   
         site_id = str(valuesL[ namesL.index('site_no') ])
      
         if site_id not in gwInfoD:
            gwInfoD[site_id] = {}
      
         for myColumn in mySiteFields:
            myValue = ''
            if myColumn == 'site_id':
               myValue = site_id
            elif myColumn in namesL:
               if str(valuesL[ namesL.index(myColumn) ]) == 'None':
                  myValue = ''
               else:
                  myValue = str(valuesL[ namesL.index(myColumn) ])
            else:
               myValue = ''
                  
            gwInfoD[site_id][myColumn] = myValue

         # Set well depth if blank with hole depth
         #
         if 'hole_depth_va' in namesL:
            if len(str(gwInfoD[site_id]['well_depth_va'])) < 1:
               if len(str(valuesL[ namesL.index('hole_depth_va') ])) > 0:
                  gwInfoD[site_id]['well_depth_va'] = str(valuesL[ namesL.index('hole_depth_va') ])
   
         del linesL[0]

         
      # NwisWeb site service for period of record for periodic/recorder wells
      # ---------------------------------------------------------------------
      #
      tempL  = list(missSitesL)
      nsites = 50
      linesL = []
   
      while len(tempL) > 0:
   
         nList = ",".join(tempL[:nsites])
         del tempL[:nsites]
         
         # Web request
         #
         URL          = 'https://waterservices.usgs.gov/nwis/site/?format=rdb&sites=%s&siteStatus=all&siteType=GW&hasDataTypeCd=gw,dv,iv&outputDataTypeCd=gw,dv,iv' % nList
         noparmsDict  = {}
         contentType  = "text"
         timeOut      = 1000
   
         #screen_logger.info("Url %s" % URL)
                    
         message, webContent = webRequest(URL, noparmsDict, contentType, timeOut, None, screen_logger)
        
         if webContent is not None:
   
            # Check for empty file
            #
            if len(webContent) < 1:
               message = "Empty content return from web request %s" % URL
               errorMessage(message)
   
            newList = list(webContent.splitlines())
            linesL.extend(newList)
   
         # Process site periodic/recorder information
         # -------------------------------------------------
         #
         while len(linesL) > 0:
      
            # Parse for column names [rdb format]
            #
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
      
         # Parse for data
         #
         while len(linesL) > 0:
            
            if len(linesL[0]) < 1:
               del linesL[0]
               continue
            
            if linesL[0][0] == '#':
               
               while len(linesL) > 0:
      
                  if linesL[0][0] == '#':
                     del linesL[0]
                     continue
      
                  else:
                     del linesL[0]
                     del linesL[0]
                     break
      
            valuesL = linesL[0].split('\t')
      
            site_id = str(valuesL[ namesL.index(keyColumn) ])
         
            # Set site information
            #
            if site_id not in gwInfoD:
               gwInfoD[site_id] = {}
         
            # Set recorder information
            #
            data_type_cd = ''
            count_nu     = ''
            
            myColumn = 'data_type_cd'
            if myColumn in namesL:
               data_type_cd = str(valuesL[ namesL.index(myColumn) ])
            myColumn = 'count_nu'
            if myColumn in namesL:
               count_nu = str(valuesL[ namesL.index(myColumn) ])
     
            if data_type_cd in ['iv', 'dv']:
               gwInfoD[site_id]['recorder'] = 'USGS'
     
            if data_type_cd in ['gw']:
               gwInfoD[site_id]['periodic'] = count_nu

                  
            del linesL[0]
                  
               
   # Separate periodic and recorder sites
   #
   periodicSitesD = {x:gwInfoD[x] for x in gwInfoD if len(gwInfoD[x]['periodic']) > 0}
   recorderSitesD = {x:gwInfoD[x] for x in gwInfoD if len(gwInfoD[x]['recorder']) > 0}

   # Update collection sites for periodic/recorder information
   #
   collectionL = list({x for x in siteInfoD if len(siteInfoD[x]['site_no']) > 0})
   
   for site_id in sorted(collectionL):
      
      if site_id in gwInfoD:

         for myColumn in mySiteFields:

            if len(str(siteInfoD[site_id][myColumn])) < 1:
               if len(str(gwInfoD[site_id][myColumn])) > 0:
                  siteInfoD[site_id][myColumn] = gwInfoD[site_id][myColumn]
         
         if siteInfoD[site_id]['station_nm'].find(gwInfoD[site_id]['station_nm']) < 0:
            siteInfoD[site_id]['station_nm'] = gwInfoD[site_id]['station_nm']
         
         if len(str(siteInfoD[site_id]['well_depth_va'])) < 1:
            if len(str(gwInfoD[site_id]['well_depth_va'])) > 0:
               siteInfoD[site_id]['well_depth_va'] = gwInfoD[site_id]['well_depth_va']
        
         periodic = 0
         if len(str(siteInfoD[site_id]['periodic'])) > 0:
            periodic += int(siteInfoD[site_id]['periodic'])
         if len(str(gwInfoD[site_id]['periodic'])) > 0:
            periodic += int(gwInfoD[site_id]['periodic'])
         siteInfoD[site_id]['periodic'] = periodic
         
         if len(gwInfoD[site_id]['recorder']) > 0:
            if len(siteInfoD[site_id]['recorder']) > 0:
               if siteInfoD[site_id]['recorder'].find(gwInfoD[site_id]['recorder']) < 0:
                  siteInfoD[site_id]['recorder'] += ',%s' % gwInfoD[site_id]['recorder']
            else:
               siteInfoD[site_id]['recorder'] = gwInfoD[site_id]['recorder']
   
   # Count sites
   #
   sitesList      = list(siteInfoD.keys())
   sitesSet       = set(sitesList)
   usgsSet        = set(usgsSitesL)
   
   periodicSitesL = list(periodicSitesD.keys())
   periodicSet    = set(periodicSitesL)
   matchperiodicL = list(sitesSet.intersection(periodicSet))
   newperiodicL   = list(periodicSet.difference(sitesSet))
   
   periodicSitesD = dict({x:periodicSitesD[x] for x in newperiodicL})
   
   recorderSitesL = list(recorderSitesD.keys())
   recorderSet    = set(recorderSitesL)
   matchrecorderL = list(recorderSet.intersection(sitesSet))
   newrecorderL   = list(recorderSet.difference(sitesSet))
   
   recorderSitesD = dict({x:recorderSitesD[x] for x in newrecorderL})

   matchedSitesL  = list(set(matchperiodicL).intersection(set(matchrecorderL)))
      
   # Print information
   #
   ncols    = 85
   messages = []
   messages.append('\n\tProcessed USGS periodic and recorder site information')
   messages.append('\t%s' % (ncols * '-'))
   messages.append('\t%-75s %5d' % ('Number of sites in collection file', len(siteInfoD)))
   messages.append('\t%-75s %5d' % ('Number of USGS sites in collection file', len(usgsSitesL)))
   messages.append('\t%-75s %5d' % ('Number of USGS sites in collection file NOT in specified counties', len(missSitesL)))
   messages.append('\t%-75s %5d' % ('Number of periodic and recorder sites retrieved from USGS database', len(gwInfoD)))
   messages.append('\t%-75s %5d' % ('Number of periodic sites from USGS database', len(periodicSitesL)))
   messages.append('\t%-75s %5d' % ('Number of periodic sites in collection file from USGS database', len(matchperiodicL)))
   messages.append('\t%-75s %5d' % ('Number of periodic sites possible additions from USGS database', len(newperiodicL)))
   messages.append('\t%-75s %5d' % ('Number of recorder sites from USGS database', len(recorderSitesL)))
   messages.append('\t%-75s %5d' % ('Number of recorder sites in collection file from USGS database', len(matchrecorderL)))
   messages.append('\t%-75s %5d' % ('Number of recorder sites possible additions from USGS database', len(newrecorderL)))
   messages.append('\t%s' % (ncols * '-'))
   if len(usgsSitesL) > 0:
      messages.append('')
      messages.append('\t%-70s' % 'USGS periodic and recorder sites in collection file in USGS database')
      messages.append('\t%s' % (ncols * '-'))
      fmt = '\t%-20s %-40s %10s %10s'
      messages.append(fmt % ('USGS',        'USGS',    'Periodic', 'Recorder'))
      messages.append(fmt % ('Site Number', 'Station', 'Counts',   'Counts'))
      messages.append('\t%s' % (ncols * '-'))
      for site_no in sorted(usgsSitesL):
         periodic   = ''
         recorder   = ''
         station_nm = ''
         if site_no in siteInfoD:
            station_nm = siteInfoD[site_no]['station_nm'][:40]
         if site_no in gwInfoD:
            periodic   = gwInfoD[site_no]['periodic']
            recorder   = gwInfoD[site_no]['recorder']
            station_nm = gwInfoD[site_no]['station_nm'][:40]
         messages.append(fmt % (site_no, station_nm, periodic, recorder))
      messages.append('\t%s' % (ncols * '-'))
   if len(newperiodicL) > 0:
      messages.append('')
      messages.append('\t%-70s' % 'USGS periodic sites to possibly add from USGS database')
      messages.append('\t%s' % (ncols * '-'))
      fmt = '\t%-20s %-40s %10s'
      messages.append(fmt % ('USGS',        'USGS',    'Periodic'))
      messages.append(fmt % ('Site Number', 'Station', 'Counts'))
      messages.append('\t%s' % (ncols * '-'))
      for site_no in sorted(newperiodicL):
         periodic = gwInfoD[site_no]['periodic']
         messages.append('\t%-20s %-40s %10s' % (site_no, gwInfoD[site_no]['station_nm'][:40], periodic))
      messages.append('\t%s' % (ncols * '-'))
   if len(newrecorderL) > 0:
      messages.append('')
      messages.append('\t%-70s' % 'USGS recorder sites to possibly add from USGS database')
      messages.append('\t%s' % (ncols * '-'))
      fmt = '\t%-20s %-40s %10s'
      messages.append(fmt % ('USGS',        'USGS',    'Recorder'))
      messages.append(fmt % ('Site Number', 'Station', 'Counts'))
      messages.append('\t%s' % (ncols * '-'))
      for site_no in sorted(newrecorderL):
         recorder = gwInfoD[site_no]['recorder']
         messages.append(fmt % (site_no, gwInfoD[site_no]['station_nm'][:40], recorder))
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

   return periodicSitesD, recorderSitesD

# =============================================================================

def processOtherIdOWRD (siteInfoD, fipsCodesD, owrd_file):

   otherSitesL  = []
   
   owrdSitesD   = {}
   owrdSitesL   = []
   usgsSitesD   = {}
   usgsSitesL   = []

   keyColumn    = 'gw_logid'

   activeDate   = datetime.datetime.now()

   # Set OWRD columns
   #
   myOwrdFields = {
      'other_identity_id'        : 'site_no',
      'gw_logid'                 : 'coop_site_no'
      }

   # Build county names
   #
   countyL = []
   for fipsCode in sorted(fipsCodesD.keys()):
      countyL.append(fipsCodesD[fipsCode][:4].upper())

   # Prepare list of site numbers
   # -------------------------------------------------
   #
   usgsSitesL = list({siteInfoD[x]['site_no'] for x in siteInfoD if len(siteInfoD[x]['site_no']) > 0})
   owrdSitesL = list({siteInfoD[x]['coop_site_no'] for x in siteInfoD if len(siteInfoD[x]['coop_site_no']) > 0})

   missSitesL = list(owrdSitesL)

   # Parse OWRD file
   #
   with open(owrd_file,'r') as f:
       linesL = f.read().splitlines()

   # Check for empty file
   #
   if len(linesL) < 1:
      message = "Empty OWRD file %s" % owrd_file
      errorMessage(message)

   # Build county names
   #
   countyL = []
   for fipsCode in sorted(fipsCodesD.keys()):
      countyL.append(fipsCodesD[fipsCode][:4].upper())

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

      Line     = linesL[0]
      
      valuesL  = Line.split('\t')

      gw_logid = str(valuesL[ namesL.index(keyColumn) ])

      # Check county name
      #
      if gw_logid[:4].upper() in countyL:

         if gw_logid not in otherSitesL:
            otherSitesL.append(gw_logid)

         # Process recorder sites
         #
         if str(valuesL[ namesL.index('other_identity_name') ]).upper() == 'USGS SITE ID':
            
            # Remove matched well log_id
            #
            if gw_logid in missSitesL:
               missSitesL.remove(gw_logid)
            
            # Prepare other ID
            #
            if gw_logid not in owrdSitesD:

               otherID = valuesL[ namesL.index('other_identity_id') ]
   
               owrdSitesD[gw_logid] = otherID.replace('\'','')
   
               if otherID not in usgsSitesD:
                  
                  usgsSitesD[otherID] = gw_logid
                     
      del linesL[0]
                
   # Set counts
   #
   owrdSet        = set(owrdSitesL)
   missingSet     = set(missSitesL)
   matchSitesL    = list(owrdSet.difference(missingSet))
                
   # Print information
   #
   ncols    = 91
   messages = []
   messages.append('\n\tProcessed OWRD Other ID information')
   messages.append('\t%s' % (ncols * '-'))
   messages.append('\t%-10s %80s' % ('Counties', ", ".join(countyL)))
   messages.append('\t%-85s %5d' % ('Number of sites retrieved from OWRD database in the specified counties', len(otherSitesL)))
   messages.append('\t%-85s %5d' % ('Number of USGS sites retrieved from OWRD database in the specified counties', len(usgsSitesD)))
   messages.append('\t%-85s %5d' % ('Number of OWRD sites in collection file with USGS site number', len(owrdSitesL)))
   messages.append('\t%-85s %5d' % ('Number of OWRD sites in collection file NOT retrieved from OWRD database', len(missSitesL)))
   messages.append('\t%s' % (ncols * '-'))
   if len(matchSitesL) > 0:
      messages.append('')
      messages.append('\t%s' % 'OWRD sites in collection file with an USGS site number')
      messages.append('\t%s' % (ncols * '-'))
      fmt = '\t%-20s %-20s %-45s'
      messages.append(fmt % ('USGS',        'OWRD',        'Station'))
      messages.append(fmt % ('Site Number', 'Well Log ID', ' '))
      messages.append('\t%s' % (ncols * '-'))
      for well_log_id in sorted(matchSitesL):
         station_nm = ''
         if owrdSitesD[well_log_id] in siteInfoD:
            station_nm = siteInfoD[owrdSitesD[well_log_id]]['station_nm'][:45]
         messages.append(fmt % (owrdSitesD[well_log_id], well_log_id, station_nm))
      messages.append('\t%s' % (ncols * '-'))
   if len(missSitesL) > 0:
      messages.append('')
      messages.append('\t%s' % 'OWRD sites in collection file NOT in OWRD database with an USGS site number')
      messages.append('\t%s' % (ncols * '-'))
      fmt = '\t%-20s %-20s %-45s'
      messages.append(fmt % ('USGS',        'OWRD',        'Station'))
      messages.append(fmt % ('Site Number', 'Well Log ID', ' '))
      messages.append('\t%s' % (ncols * '-'))
      for gw_logid in sorted(missSitesL):
         site_no    = ''
         station_nm = ''
         for site_id in siteInfoD:
            coop_site_no = siteInfoD[site_id]['coop_site_no']
            site_no      = siteInfoD[site_id]['site_no']
            station_nm   = siteInfoD[site_id]['station_nm'][:45]
            if gw_logid == coop_site_no:
               break
         messages.append(fmt % (gw_logid, site_no, station_nm))
      messages.append('\t%s' % (ncols * '-'))
   messages.append('\n')
   messages.append('\n')

   screen_logger.info('\n'.join(messages))
   file_logger.info('\n'.join(messages))

   return usgsSitesD, owrdSitesD
# =============================================================================

def processOWRD (siteInfoD, mySiteFields, owrdOtherIdD, fipsCodesD, owrd_file):

   gwInfoD        = {}

   keyColumn      = 'gw_logid'

   # Prepare site information
   # -------------------------------------------------
   #
   usgsSitesD = dict({siteInfoD[x]['coop_site_no']:siteInfoD[x]['site_no'] for x in siteInfoD if len(siteInfoD[x]['site_no']) > 0 and len(siteInfoD[x]['coop_site_no']) > 0})
   owrdSitesD = dict({siteInfoD[x]['coop_site_no']:siteInfoD[x]['site_id'] for x in siteInfoD if len(siteInfoD[x]['coop_site_no']) > 0})
   owrdSitesL = list({siteInfoD[x]['coop_site_no'] for x in siteInfoD if len(siteInfoD[x]['coop_site_no']) > 0})
   missSitesL = list(owrdSitesL)
   
   # Set OWRD columns
   #
   myOwrdFields = {
      'site_id'                    : 'site_id',
      'agency_cd'                  : 'site_source_organization',
      'site_no'                    : 'site_no',
      'coop_site_no'               : 'gw_logid',
      'state_well_nmbr'            : 'state_observation_well_nbr',
      'cdwr_id'                    : 'cdwr_id',
      'station_nm'                 : 'station_nm',
      'periodic'                   : 'measured_waterlevel_blsd_count',
      'recorder'                   : 'recorder_waterlevel_mean_daily_blsd_count',
      'dec_lat_va'                 : 'latitude_dec',
      'dec_long_va'                : 'longitude_dec',
      'alt_va'                     : 'lsd_elevation',
      'alt_acy_va'                 : 'lsd_accuracy',
      'alt_datum_cd'               : 'elevation_datum',
      'well_depth_va'              : 'max_depth'
      }

   activeDate   = datetime.datetime.now()
   
   myQtrD = {
      'NW'                  : 'A',
      'NE'                  : 'B',
      'SE'                  : 'C',
      'SW'                  : 'D'
      }

   # Build county names
   #
   countyL = []
   for fipsCode in sorted(fipsCodesD.keys()):
      countyL.append(fipsCodesD[fipsCode][:4].upper())
   
   # Parse OWRD file
   #
   with open(owrd_file,'r') as f:
       linesL = f.read().splitlines()

   # Check for empty file
   #
   if len(linesL) < 1:
      message = "Empty OWRD file %s" % owrd_file
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
   #del linesL[0]

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

      Line     = linesL[0]
      
      valuesL  = Line.split('\t')

      gw_logid = str(valuesL[ namesL.index(keyColumn) ])

      # Check county name
      #
      if gw_logid[:4].upper() in countyL:
                  
         # Remove site from missing list
         #
         if gw_logid in missSitesL:
            missSitesL.remove(gw_logid)
          
         # Set site_id
         #
         site_id = gw_logid
         if gw_logid in owrdSitesD:
            site_id = owrdSitesD[gw_logid]
               
         # Check for USGS site number
         #
         site_no = ''
         if gw_logid in usgsSitesD:
            site_no = usgsSitesD[gw_logid]
         elif gw_logid in owrdOtherIdD:
            site_no = owrdOtherIdD[gw_logid]
      
         # Set site information
         #
         if site_id not in gwInfoD:
            gwInfoD[site_id] = {}
  
         for myColumn in mySiteFields:
            
            owrdColumn = myOwrdFields[myColumn]

            gwInfoD[site_id][myColumn] = ''
                  
            # Column site_id
            #
            if myColumn == 'site_id':
               gwInfoD[site_id][myColumn] = site_id
                  
            # Column site_no
            #
            elif myColumn == 'site_no':
               gwInfoD[site_id][myColumn] = site_no
                  
            # Column station_nm
            #
            elif myColumn == 'station_nm':
               trsL = []
               for column in ['township', 'township_char', 'range', 'range_char', 'sctn', 'qtr160', 'qtr40', 'qtr10']:
                  if column in ['township', 'range']:
                     valuesL[ namesL.index(column) ] = '%05.2f' % float(valuesL[ namesL.index(column) ])
                  elif column == 'township_char':
                     valuesL[ namesL.index(column) ] += '/'
                  elif column == 'range_char':
                     valuesL[ namesL.index(column) ] += '-'
                  elif column == 'sctn':
                     sctn = valuesL[ namesL.index(column) ]
                     if sctn.isnumeric():
                        valuesL[ namesL.index(column) ] = '%02d' % int(sctn)
                     else:
                        valuesL[ namesL.index(column) ] = sctn
                  elif column in ['qtr160', 'qtr40', 'qtr10']:
                     if len(valuesL[ namesL.index(column) ]) > 0:
                        valuesL[ namesL.index(column) ] = myQtrD[valuesL[ namesL.index(column) ]]
                  trsL.append(str(valuesL[ namesL.index(column) ]))
               gwInfoD[site_id][myColumn] = ''.join(trsL)
               
            # Set search column for count of periodic records
            #
            elif myColumn == 'periodic':
               count_nu = ''
               if len(valuesL[ namesL.index(owrdColumn) ]) > 0:
                  count_nu = str(valuesL[ namesL.index(owrdColumn) ])
          
               if len(count_nu) > 0:
                  gwInfoD[site_id][myColumn] = count_nu
               
            # Set search column for count of recorder records
            #
            elif myColumn == 'recorder':
               count_nu =''
               if len(valuesL[ namesL.index(owrdColumn) ]) > 0:
                  count_nu = str(valuesL[ namesL.index(owrdColumn) ])
          
               if len(count_nu) > 0:
                  gwInfoD[site_id][myColumn] = 'OWRD'
                  
            # Columns in OWRD database
            #
            elif owrdColumn in namesL:
               gwInfoD[site_id][myColumn] = str(valuesL[ namesL.index(owrdColumn) ])

               
      del linesL[0]

      
   # Missing OWRD sites for general information for periodic/recorder wells
   # ----------------------------------------------------------------------
   #
   if len(missSitesL) > 0:
      tempL  = list(missSitesL)
      linesL = []
   
      while len(tempL) > 0:
   
         gw_logid = tempL[0]
         del tempL[0]
   
         # Web request
         #
         URL          = 'https://apps.wrd.state.or.us/apps/gw/gw_data_rws/api/%s/gw_site_summary/?public_viewable=' % gw_logid
         noparmsDict  = {}
         contentType  = "application/json"
         timeOut      = 1000
   
         #screen_logger.info("Url %s" % URL)
                    
         message, webContent = webRequest(URL, noparmsDict, contentType, timeOut, None, screen_logger)
        
         if webContent is not None:
   
            # Check for empty file
            #
            if len(webContent) < 1:
               message = "Empty content return from web request %s" % URL
               errorMessage(message)
    
         # Convert to json format
         #
         gwJson       = json.loads(webContent)

         # Total records
         #
         numRecords   = gwJson['feature_count']

         # Check for failed request
         #
         if numRecords < 1:
            message = "Warning: Site %s has no OWRD site summary available" % gw_logid
            screen_logger.info(message)
            continue

         # Parse records
         #
         jsonRecords  = gwJson['feature_list']
   
         # Process groundwater measurements
         # -------------------------------------------------
         #
         for myRecord in jsonRecords:

            gw_logid = myRecord['gw_logid']
         
            # Remove site from missing list
            #
            if gw_logid in missSitesL:
               missSitesL.remove(gw_logid)
         
            # Set site_id
            #
            site_id = gw_logid
            if gw_logid in owrdSitesD:
               site_id = owrdSitesD[gw_logid]
               
            # Check for USGS site number
            #
            site_no = ''
            if gw_logid in usgsSitesD:
               site_no = usgsSitesD[gw_logid]
            elif gw_logid in owrdOtherIdD:
               site_no = owrdOtherIdD[gw_logid]
         
            # Set site information
            #
            if site_id not in gwInfoD:
               gwInfoD[site_id] = {}
     
            for myColumn in mySiteFields:
               
               owrdColumn = myOwrdFields[myColumn]
   
               gwInfoD[site_id][myColumn] = ''
                     
               # Column site_id
               #
               if owrdColumn == 'site_id':
                  gwInfoD[site_id][myColumn] = site_id
                     
               # Column site_no
               #
               elif owrdColumn == 'site_no':
                  gwInfoD[site_id][myColumn] = site_no
               
               # Column station_nm
               #
               elif owrdColumn == 'station_nm':
                  gwInfoD[site_id][myColumn] = myRecord['trsqq_key']
                  if site_id in siteInfoD:
                     gwInfoD[site_id][myColumn] = siteInfoD[site_id][myColumn]
                  elif myRecord['usgs_pls_notation_display'] is not None:
                     gwInfoD[site_id][myColumn] = myRecord['usgs_pls_notation_display']
               
               # Set search column for count of periodic records
               #
               elif myColumn == 'periodic':
                  count_nu   = ''
                  owrdColumn = 'water_level_count'
                  if owrdColumn in myRecord:
                     if len(str(myRecord[owrdColumn])) > 0:
                        gwInfoD[site_id]['periodic'] = str(myRecord[owrdColumn])
                  
               # Set search column for count of recorder records
               #
               elif myColumn == 'recorder':
                  gwInfoD[site_id]['recorder'] = ''
                  
               # Columns in OWRD database
               #
               elif owrdColumn in myRecord:
                  gwInfoD[site_id][myColumn] = str(myRecord[owrdColumn])
             

   # Create periodic/recorder sites
   #
   periodicSitesD = {x:gwInfoD[x] for x in gwInfoD if len(gwInfoD[x]['periodic']) > 0}
   recorderSitesD = {x:gwInfoD[x] for x in gwInfoD if len(gwInfoD[x]['recorder']) > 0}

   # Update collection sites for periodic/recorder information
   #
   collectionL = list({x for x in siteInfoD if len(siteInfoD[x]['coop_site_no']) > 0})
   
   for site_id in sorted(collectionL):
      
      if site_id in gwInfoD:
         
         if len(siteInfoD[site_id]['site_no']) < 1 :
            if siteInfoD[site_id]['station_nm'].find(gwInfoD[site_id]['station_nm']) < 0:
               siteInfoD[site_id]['station_nm'] = gwInfoD[site_id]['station_nm']
         
         periodic = 0
         if len(str(siteInfoD[site_id]['periodic'])) > 0:
            periodic += int(siteInfoD[site_id]['periodic'])
         if len(str(gwInfoD[site_id]['periodic'])) > 0:
            periodic += int(gwInfoD[site_id]['periodic'])
         siteInfoD[site_id]['periodic'] = periodic
         
         if len(gwInfoD[site_id]['recorder']) > 0:
            if len(siteInfoD[site_id]['recorder']) > 0:
               if siteInfoD[site_id]['recorder'].find(gwInfoD[site_id]['recorder']) < 0:
                  siteInfoD[site_id]['recorder'] += ',%s' % gwInfoD[site_id]['recorder']
            else:
               siteInfoD[site_id]['recorder'] = gwInfoD[site_id]['recorder']

   # Count sites
   #
   owrdSet        = set(owrdSitesL)
   missingSet     = set(missSitesL)
   matchSitesL    = list(owrdSet.difference(missingSet))
   
   periodicSitesL = list({periodicSitesD[x]['coop_site_no'] for x in periodicSitesD})
   periodicSet    = set(periodicSitesL)
   matchperiodicL = list(owrdSet.intersection(periodicSet))
   newperiodicL   = list(periodicSet.difference(owrdSet))
   
   periodicSitesD = dict({x:periodicSitesD[x] for x in newperiodicL})
   
   recorderSitesL = list({recorderSitesD[x]['coop_site_no'] for x in recorderSitesD})
   recorderSet    = set(recorderSitesL)
   matchrecorderL = list(recorderSet.intersection(owrdSet))
   newrecorderL   = list(recorderSet.difference(owrdSet))
   
   recorderSitesD = dict({x:recorderSitesD[x] for x in newrecorderL})

   usgsSitesL     = list({gwInfoD[x]['site_no'] for x in gwInfoD if len(gwInfoD[x]['site_no']) > 0})
             
   # Print information
   #
   ncols    = 85
   messages = []
   messages.append('\n\tProcessed OWRD periodic and recorder site information')
   messages.append('\t%s' % (ncols * '-'))
   messages.append('\t%-79s %5d' % ('Number of sites in collection file', len(siteInfoD)))
   messages.append('\t%-79s %5d' % ('Number of OWRD sites in collection file', len(owrdSitesL)))
   messages.append('\t%-79s %5d' % ('Number of OWRD sites in collection file NOT retrieved from OWRD database', len(missSitesL)))
   messages.append('\t%-79s %5d' % ('Number of sites retrieved from OWRD database', len(gwInfoD)))
   messages.append('\t%-79s %5d' % ('Number of periodic sites with waterlevels from OWRD database', len(periodicSitesL)))
   messages.append('\t%-79s %5d' % ('Number of periodic sites in collection file from OWRD database', len(matchperiodicL)))
   messages.append('\t%-79s %5d' % ('Number of periodic sites possible additions from OWRD database', len(newperiodicL)))
   messages.append('\t%-79s %5d' % ('Number of recorder sites from OWRD database', len(recorderSitesL)))
   messages.append('\t%-79s %5d' % ('Number of recorder sites in collection file from OWRD database', len(matchrecorderL)))
   messages.append('\t%-79s %5d' % ('Number of recorder sites possible additions from OWRD database', len(newrecorderL)))
   messages.append('\t%-79s %5d' % ('Number of OWRD sites assigned an USGS site number from OWRD database', len(usgsSitesL)))
   messages.append('\t%s' % (ncols * '-'))
   if len(matchSitesL) > 0:
      messages.append('')
      messages.append('\t%-70s' % 'OWRD periodic and recorder sites in collection file in OWRD database')
      messages.append('\t%s' % (ncols * '-'))
      fmt = '\t%-20s %-15s %-25s %10s %10s'
      messages.append(fmt % ('USGS',        'OWRD',        'USGS',    'Periodic', 'Recorder'))
      messages.append(fmt % ('Site Number', 'Well Log ID', 'Station', 'Counts',   'Counts'))
      messages.append('\t%s' % (ncols * '-'))
      for gw_logid in sorted(matchSitesL):
         site_id  = owrdSitesD[gw_logid]
         periodic = gwInfoD[site_id]['periodic']
         recorder = gwInfoD[site_id]['recorder']
         messages.append(fmt % (gwInfoD[site_id]['site_no'], gw_logid, gwInfoD[site_id]['station_nm'][:25], periodic, recorder))
      messages.append('\t%s' % (ncols * '-'))
   if len(missSitesL) > 0:
      messages.append('')
      messages.append('\t%-70s' % 'OWRD sites in collection file NOT in OWRD database')
      messages.append('\t%s' % (ncols * '-'))
      fmt = '\t%-15s %-15s %-40s'
      messages.append(fmt % ('USGS',        'OWRD',        'USGS'))
      messages.append(fmt % ('Site Number', 'Well Log ID', 'Station'))
      messages.append('\t%s' % (ncols * '-'))
      for gw_logid in sorted(missSitesL):
         site_id    = owrdSitesD[gw_logid]
         site_no    = siteInfoD[site_id]['site_no']
         station_nm = siteInfoD[site_id]['station_nm'][:40]
         messages.append(fmt % (site_no, gw_logid, station_nm))
      messages.append('\t%s' % (ncols * '-'))
   if len(newperiodicL) > 0:
      messages.append('')
      messages.append('\t%-70s' % 'OWRD periodic sites to possibly add from OWRD database')
      messages.append('\t%s' % (ncols * '-'))
      fmt = '\t%-20s %-15s %-25s %10s %10s'
      messages.append(fmt % ('USGS',        'OWRD',         'USGS',    'Periodic', 'Recorder'))
      messages.append(fmt % ('Site Number', 'Well Log ID',  'Station', 'Counts',   'Counts'))
      messages.append('\t%s' % (ncols * '-'))
      for gw_logid in sorted(newperiodicL):
         messages.append(fmt % (gw_logid, gwInfoD[gw_logid]['site_no'], gwInfoD[gw_logid]['station_nm'][:25], gwInfoD[gw_logid]['periodic'], gwInfoD[gw_logid]['recorder']))
      messages.append('\t%s' % (ncols * '-'))
   if len(newrecorderL) > 0:
      messages.append('')
      messages.append('\t%-70s' % 'OWRD recorder sites to possibly add from OWRD database')
      messages.append('\t%s' % (ncols * '-'))
      fmt = '\t%-20s %-15s %-25s %10s %10s'
      messages.append(fmt % ('USGS',        'OWRD',         'USGS',    'Periodic', 'Recorder'))
      messages.append(fmt % ('Site Number', 'Well Log ID',  'Station', 'Counts',   'Counts'))
      messages.append('\t%s' % (ncols * '-'))
      for gw_logid in sorted(newrecorderL):
         messages.append(fmt % (gwInfoD[gw_logid]['site_no'], gw_logid, gwInfoD[gw_logid]['station_nm'][:25], gwInfoD[gw_logid]['periodic'], gwInfoD[gw_logid]['recorder']))
      messages.append('\t%s' % (ncols * '-'))
   messages.append('\n')
   messages.append('\n')

   screen_logger.info('\n'.join(messages))
   file_logger.info('\n'.join(messages))

   return periodicSitesD, recorderSitesD
# =============================================================================

def processCDWR (siteInfoD, mySiteFields, fipsCodesD):

   gwInfoD        = {}

   keyColumn      = 'site_code'

   activeDate     = datetime.datetime.now()

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
            
   # CDWR service for periodic site information
   # -------------------------------------------------
   #
   tempL        = ",".join(countyL)
   sqlTable     = 'af157380-fb42-4abf-b72a-6f9f98868077'
   countyColumn = 'county_name'

   # Set CDWR columns for periodic table
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
      'well_depth_va'              : 'well_depth'
      }

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
      
         # Process site information
         # -------------------------------------------------
         #
         for myRecord in jsonRecords:
   
            site_code = myRecord[keyColumn]
               
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
            if site_code not in gwInfoD:
               gwInfoD[site_code] = {}
                  
            # Prepare information
            # -------------------------------------------------
            #
            for myColumn in mySiteFields:
            
               cdwrColumn = myCdwrFields[myColumn].lower()

               gwInfoD[site_code][myColumn] = ''
                     
               # Column site_id
               #
               if myColumn == 'site_id':
                  gwInfoD[site_code][myColumn] = site_id
                     
               # Column site_no
               #
               elif myColumn == 'site_no':
                  gwInfoD[site_code][myColumn] = site_no
                     
               # Column agency_cd
               #
               elif myColumn == 'agency_cd':
                  gwInfoD[site_code][myColumn] = agency_cd
                     
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
                     
                  gwInfoD[site_code][myColumn] = station_nm
                     
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
                     
                  gwInfoD[site_code][myColumn] = state_well_nmbr
                     
               # Column periodic
               #
               elif myColumn == 'periodic':
                  gwInfoD[site_code][myColumn] = 'Y'
                     
               # Column recorder
               #
               elif myColumn == 'recorder':
                  if cdwrColumn in myRecord:
                     if myRecord[cdwrColumn] is not None:
                        gwInfoD[site_code][myColumn] = 'CDWR'

               # Columns in CDWR database
               #
               elif cdwrColumn in myRecord:
                  if myRecord[cdwrColumn] is not None:
                     gwInfoD[site_code][myColumn] = str(myRecord[cdwrColumn])
               else:
                  if site_code in usgsSitesD:
                     site_id = usgsSitesD[site_code]
                     if myColumn in siteInfoD[site_id]:
                        gwInfoD[site_code][myColumn] = str(siteInfoD[site_id][myColumn])
                        
   # CDWR service for recorder site information
   # -------------------------------------------------
   #
   tempL        = ",".join(countyL)
   sqlTable     = '03967113-1556-4100-af2c-b16a4d41b9d0'
   keyColumn    = keyColumn.upper()
   countyColumn = countyColumn.upper()

   # Set CDWR columns for recorder table
   #
   myCdwrFields = {
      'site_id'                    : 'site_code',
      'agency_cd'                  : 'agency_cd',
      'site_no'                    : 'site_no',
      'coop_site_no'               : 'coop_site_no',
      'state_well_nmbr'            : 'station',
      'cdwr_id'                    : 'site_code',
      'station_nm'                 : 'station',
      'periodic'                   : 'periodic',
      'recorder'                   : 'continuous_data_station_number',
      'dec_lat_va'                 : 'latitude',
      'dec_long_va'                : 'longitude',
      'alt_va'                     : 'elev',
      'alt_acy_va'                 : 'elevacc',
      'alt_datum_cd'               : 'elevdatum',
      'well_depth_va'              : 'well_depth'
      }

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
      
         # Process site information
         # -------------------------------------------------
         #
         for myRecord in jsonRecords:
   
            site_code = myRecord[keyColumn]
               
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
            if site_code not in gwInfoD:
               gwInfoD[site_code] = {}
                  
            # Prepare information
            # -------------------------------------------------
            #
            for myColumn in mySiteFields:
            
               cdwrColumn = myCdwrFields[myColumn].upper()

               gwInfoD[site_code][myColumn] = ''
                     
               # Column site_id
               #
               if myColumn == 'site_id':
                  gwInfoD[site_code][myColumn] = site_id
                     
               # Column site_no
               #
               elif myColumn == 'site_no':
                  gwInfoD[site_code][myColumn] = site_no
                     
               # Column agency_cd
               #
               elif myColumn == 'agency_cd':
                  gwInfoD[site_code][myColumn] = agency_cd
                     
               # Column station_nm
               #
               elif myColumn == 'station_nm':
                  station    = myRecord[cdwrColumn]
                  station_nm = site_code
                  if station is not None:
                     station_nm = '%02s.00%1s/%02s.00%1s-%s' % (station[:2], station[2:3], station[3:5], station[5:6], station[6:])
                  elif myRecord['WELL_NAME'] is not None:
                     station_nm = myRecord['WELL_NAME']
                  elif myRecord['STNAME'] is not None:
                     station_nm = myRecord['STNAME']
                     
                  gwInfoD[site_code][myColumn] = station_nm
                     
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
                     
                  gwInfoD[site_code][myColumn] = state_well_nmbr
                    
               # Column periodic
               #
               elif myColumn == 'periodic':
                  gwInfoD[site_code][myColumn] = 'Y'
                     
               # Column recorder
               #
               elif myColumn == 'recorder':
                  gwInfoD[site_code]['recorder'] = 'CDWR'

               # Columns in CDWR database
               #
               elif cdwrColumn in myRecord:
                  if myRecord[cdwrColumn] is not None:
                     gwInfoD[site_code][myColumn] = str(myRecord[cdwrColumn])
               else:
                  if site_code in usgsSitesD:
                     site_id = usgsSitesD[site_code]
                     if myColumn in siteInfoD[site_id]:
                        gwInfoD[site_code][myColumn] = str(siteInfoD[site_id][myColumn])


   # Create periodic/recorder sites
   #
   periodicSitesD = {x:gwInfoD[x] for x in gwInfoD if len(gwInfoD[x]['periodic']) > 0}
   recorderSitesD = {x:gwInfoD[x] for x in gwInfoD if len(gwInfoD[x]['recorder']) > 0}

   # Update collection sites for periodic/recorder information
   #
   collectionL = list({x for x in siteInfoD if len(siteInfoD[x]['cdwr_id']) > 0})
   
   for site_id in sorted(collectionL):
      
      if site_id in gwInfoD:
         if len(str(siteInfoD[site_id]['periodic'])) < 1:
             if len(str(gwInfoD[site_id]['periodic'])) > 0:
                siteInfoD[site_id]['periodic'] = 'Y'
         
         if len(gwInfoD[site_id]['recorder']) > 0:
            if len(siteInfoD[site_id]['recorder']) > 0:
               if siteInfoD[site_id]['recorder'].find(gwInfoD[site_id]['recorder']) < 0:
                  siteInfoD[site_id]['recorder'] += ',%s' % gwInfoD[site_id]['recorder']
            else:
               siteInfoD[site_id]['recorder'] = gwInfoD[site_id]['recorder']
   
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
                "well_depth_va"
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
                    required = True,
                    nargs='+')
 
parser.add_argument("-owrd", "--owrd",
                    help="Provide a filename of OWRD site summary file containing recorder sites in text format",
                    required = True,
                    type=str)
 
parser.add_argument("-count", "--count",
                    help="Provide a minimum number of periodic measurements to qualify for adding new sites onto collection file",
                    type=int)

 
parser.add_argument("-other", "--other",
                    help="Provide a filename of OWRD other ID file containing sites in text format",
                    required = True,
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

if args.counties:
   fipsCodesL = args.counties
   fipsCodesD = processFipsCodes (fipsCodesL)
   if len(fipsCodesL) != len(fipsCodesD):
      message = 'Warning: Not all FIPS codes specified were matched in the Census database\n\tPlease check the list'
      errorMessage(message)

if args.owrd:
   owrd_file = args.owrd
   if not os.path.isfile(owrd_file):
      message  = "File listing OWRD sites %s does not exist" % owrd_file
      errorMessage(message)

if args.other:
   other_file = args.other
   if not os.path.isfile(other_file):
      message  = "File listing OWRD other ID sites %s does not exist" % other_file
      errorMessage(message)

if args.count:
   try:
      minimumCount = int(args.count)
   except:
      message  = 'Provide a minimum number of periodic measurements to qualify for adding new sites onto collection file'
      errorMessage(message)

if args.debug:

   screen_logger.setLevel(logging.DEBUG)


# Process collection or recorder file
# -------------------------------------------------
#
siteInfoD = processCollectionSites(collection_file, mySiteFields)

# Identifies OWRD sites with USGS site numbers
# -------------------------------------------------
#
usgsOtherIdsD, owrdOtherIdsD = processOtherIdOWRD (siteInfoD, fipsCodesD, other_file)

# Prepare USGS records from NwisWeb site service
# -------------------------------------------------
#
usgsPeriodicD, usgsRecorderD = processUSGS(siteInfoD, mySiteFields, fipsCodesL)

# Prepare OWRD records
# -------------------------------------------------
#
owrdPeriodicD, owrdRecorderD = processOWRD(siteInfoD, mySiteFields, owrdOtherIdsD, fipsCodesD, owrd_file)

# Prepare CDWR records
# -------------------------------------------------
#
cdwrPeriodicD, cdwrRecorderD = processCDWR(siteInfoD, mySiteFields, fipsCodesD)


   
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
outputL.append("\t".join(mySiteFormat))
      
# Print information
#
ncols    = 81
messages = []
messages.append('\n\tProcessed Periodic and Recorder site information')
messages.append('\t%s' % (81 * '='))
messages.append('\t%-70s %10d' % ('Number of sites in current collection file', len(siteInfoD)))
          
# Count sites
#
usgsSitesL        = list({siteInfoD[x]['site_no'] for x in siteInfoD if len(siteInfoD[x]['site_no']) > 0})
usgsPeriodicL     = list({siteInfoD[x]['site_no'] for x in usgsSitesL if int(str(siteInfoD[x]['periodic'])) > 0})
usgsRecorderL     = list({siteInfoD[x]['site_no'] for x in usgsSitesL if 'USGS' in siteInfoD[x]['recorder']})
          
usgsPeriodicList  = list(usgsPeriodicD.keys())
usgsRecorderList  = list(usgsRecorderD.keys())

messages.append('')
messages.append('\t%-80s' % 'Processing sites from USGS database')
messages.append('\t%s' % (ncols * '-'))
messages.append('\t%-70s %10d' % ('Number of USGS sites in current collection file', len(usgsSitesL)))
messages.append('\t%-70s %10d' % ('Number of USGS periodic sites in current collection file', len(usgsPeriodicL)))
messages.append('\t%-70s %10d' % ('Number of periodic sites possible additions from USGS database', len(usgsPeriodicList)))
messages.append('\t%-70s %10d' % ('Number of USGS recorder sites in current collection file', len(usgsRecorderL)))
messages.append('\t%-70s %10d' % ('Number of recorder sites possible additions from USGS database', len(usgsRecorderList)))

owrdSitesL        = list({siteInfoD[x]['site_id'] for x in siteInfoD if len(siteInfoD[x]['coop_site_no']) > 0})
owrdPeriodicL     = list({siteInfoD[x]['coop_site_no'] for x in owrdSitesL if int(str(siteInfoD[x]['periodic'])) > 0})
owrdRecorderL     = list({siteInfoD[x]['coop_site_no'] for x in owrdSitesL if 'OWRD' in siteInfoD[x]['recorder']})
          
owrdPeriodicList  = list(owrdPeriodicD.keys())
owrdRecorderList  = list(owrdRecorderD.keys())

messages.append('')
messages.append('\t%-80s' % 'Processing sites from OWRD database')
messages.append('\t%s' % (ncols * '-'))
messages.append('\t%-70s %10d' % ('Number of OWRD sites in current collection file', len(owrdSitesL)))
messages.append('\t%-70s %10d' % ('Number of OWRD periodic sites in current collection file', len(owrdPeriodicL)))
messages.append('\t%-70s %10d' % ('Number of periodic sites possible additions from OWRD database', len(owrdPeriodicList)))
messages.append('\t%-70s %10d' % ('Number of OWRD recorder sites in current collection file', len(owrdRecorderL)))
messages.append('\t%-70s %10d' % ('Number of recorder sites possible additions from OWRD database', len(owrdRecorderList)))

cdwrSitesL        = list({siteInfoD[x]['site_id'] for x in siteInfoD if len(siteInfoD[x]['cdwr_id']) > 0})
cdwrPeriodicL     = list({siteInfoD[x]['cdwr_id'] for x in cdwrSitesL if len(siteInfoD[x]['periodic']) > 0})
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

      if int(usgsPeriodicD[site_id]['periodic']) >= minimumCount:
         outputL.append("#" + "\t".join(recordL))
  
if len(usgsRecorderList) > 0:
                        
   outputL.append("#")
   outputL.append("# Possble New Recorder Sites from USGS source")
   outputL.append("#")

   for site_id in sorted(usgsRecorderList):

      recordL = []

      usgsRecorderD[site_id]['recorder'] = 'USGS'
      for myColumn in mySiteFields:
         recordL.append(usgsRecorderD[site_id][myColumn])

      outputL.append("#" + "\t".join(recordL))
  
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

      if int(owrdPeriodicD[site_id]['periodic']) >= minimumCount:
         outputL.append("#" + "\t".join(recordL))
  
if len(owrdRecorderList) > 0:
                        
   outputL.append("#")
   outputL.append("# Possble New Recorder Sites from OWRD source")
   outputL.append("#")

   for site_id in sorted(owrdRecorderList):

      recordL = []

      owrdRecorderD[site_id]['recorder'] = 'OWRD'
      for myColumn in mySiteFields:
         recordL.append(owrdRecorderD[site_id][myColumn])

      outputL.append("#" + "\t".join(recordL))
  
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
                        
      outputL.append("#" + "\t".join(recordL))
  
if len(cdwrRecorderList) > 0:
                        
   outputL.append("#")
   outputL.append("# Possble New Recorder Sites from CDWR source")
   outputL.append("#")

   for site_id in sorted(cdwrRecorderList):

      recordL = []

      cdwrRecorderD[site_id]['recorder'] = 'CDWR'
      for myColumn in mySiteFields:
         recordL.append(cdwrRecorderD[site_id][myColumn])

      outputL.append("#" + "\t".join(recordL))
   
# Output records
#
with open(output_file,'w') as f:
   f.write('\n'.join(outputL))

sys.exit()

