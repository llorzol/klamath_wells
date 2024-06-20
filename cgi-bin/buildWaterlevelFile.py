#!/usr/bin/env python3
#
###############################################################################
# $Id: buildWaterlevelFile.py
#
# Project:  buildWaterlevelFile.py
# Purpose:  Script builds a tab-limited text file of waterlevel measurements
#           from USGS, OWRD, and CWDR sources for the Upper Klamath Basin.
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
logging_file = "buildWaterlevelFile.txt"
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

program         = "USGS OWRD CDWR Waterlevel Measurement Script"
version         = "2.38"
version_date    = "June 20, 2024"
usage_message   = """
Usage: buildWaterlevelFile.py
                [--help]
                [--usage]
                [--sites       Name of collection file listing sites]
                [--output      Name of output file containing processed waterlevel measurements]
                [--usgs        Process only USGS measurement records]
                [--owrd        Process only OWRD measurement records]
                [--cdwr        Process only CDWR measurement records]
                [--owrd_gw     Provide a filename of OWRD waterlevel file for periodic sites in text format]
                [--owrd_rc     Provide a filename of OWRD waterlevel file for recorder sites in text format]
                [--keepOWRD    Keep OWRD records over USGS matching records [default keep USGS skip OWRD]]
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
def processCollectionSites (file, mySiteFields):

   siteInfoD      = {}
   siteCount      = 0
   countUSGS      = 0
   countOWRD      = 0
   countCDWR      = 0

   agencyL        = []

   periodicSitesL = []
   recorderSitesL = []

   keyColumn      = 'site_id'
   
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

      recordD = {}
   
      for myColumn in namesL:
         myValue = ''
         if len(str(valuesL[ namesL.index(myColumn) ])) > 0:
            myValue = str(valuesL[ namesL.index(myColumn) ])
         recordD[myColumn] = myValue
   
      for myColumn in mySiteFields:
         if myColumn in recordD:
            siteInfoD[site_id][myColumn] = recordD[myColumn]
      
      siteInfoD[site_id]['periodic']           = recordD['periodic']
      siteInfoD[site_id]['gw_agency_cd']       = ''
      siteInfoD[site_id]['gw_status']          = None
      siteInfoD[site_id]['gw_begin_date']      = None
      siteInfoD[site_id]['gw_end_date']        = None
      siteInfoD[site_id]['gw_count']           = 0

      siteInfoD[site_id]['recorder']           = recordD['recorder']
      siteInfoD[site_id]['rc_agency_cd']       = recordD['recorder']
      siteInfoD[site_id]['rc_status']          = None
      siteInfoD[site_id]['rc_begin_date']      = None
      siteInfoD[site_id]['rc_end_date']        = None
      siteInfoD[site_id]['rc_count']           = 0
      
      siteInfoD[site_id]['usgs_begin_date']    = None
      siteInfoD[site_id]['usgs_end_date']      = None
      siteInfoD[site_id]['usgs_status']        = None
      siteInfoD[site_id]['usgs_count']         = 0
      
      siteInfoD[site_id]['usgs_rc_begin_date'] = None
      siteInfoD[site_id]['usgs_rc_end_date']   = None
      siteInfoD[site_id]['usgs_rc_status']     = None
      siteInfoD[site_id]['usgs_rc_count']      = 0
      
      siteInfoD[site_id]['owrd_begin_date']    = None
      siteInfoD[site_id]['owrd_end_date']      = None
      siteInfoD[site_id]['owrd_status']        = None
      siteInfoD[site_id]['owrd_count']         = 0
      
      siteInfoD[site_id]['owrd_rc_begin_date'] = None
      siteInfoD[site_id]['owrd_rc_end_date']   = None
      siteInfoD[site_id]['owrd_rc_status']     = None
      siteInfoD[site_id]['owrd_rc_count']      = 0
      
      siteInfoD[site_id]['cdwr_begin_date']    = None
      siteInfoD[site_id]['cdwr_end_date']      = None
      siteInfoD[site_id]['cdwr_status']        = None
      siteInfoD[site_id]['cdwr_count']         = 0
      
      siteInfoD[site_id]['cdwr_rc_begin_date'] = None
      siteInfoD[site_id]['cdwr_rc_end_date']   = None
      siteInfoD[site_id]['cdwr_rc_status']     = None
      siteInfoD[site_id]['cdwr_rc_count']      = 0

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

   usgsRecordersL = list({siteInfoD[x]['site_no'] for x in siteInfoD if siteInfoD[x]['recorder'].find('USGS') > -1})
   owrdRecordersL = list({siteInfoD[x]['site_no'] for x in siteInfoD if siteInfoD[x]['recorder'].find('OWRD') > -1})
   cdwrRecordersL = list({siteInfoD[x]['site_no'] for x in siteInfoD if siteInfoD[x]['recorder'].find('CDWR') > -1})
   
   # Print information
   #
   ncols    = 90
   messages = []
   messages.append('\n\tProcessed site information in %s file' % file)
   messages.append('\t%s' % (ncols * '-'))
   messages.append('\t%-40s %49s' % ('Monitoring agencies in collection file', ', '.join(agencyL)))
   messages.append('\t%-79s %10d' % ('Number of sites in collection file', len(siteInfoD)))
   messages.append('\t%-79s %10d' % ('Number of periodic sites in collection file', len(periodicSitesL)))
   messages.append('\t%-79s %10d' % ('Number of recorder sites in collection file', len(recorderSitesL)))
   messages.append('\t%-79s %10d' % ('Number of sites correlated to a site in USGS datbase', len(usgsSitesL)))
   messages.append('\t%-79s %10d' % ('Number of recorder sites in collection file in the USGS datbase', len(usgsRecordersL)))
   messages.append('\t%-79s %10d' % ('Number of sites correlated to a site in OWRD datbase', len(owrdSitesL)))
   messages.append('\t%-79s %10d' % ('Number of recorder sites in collection file in the OWRD datbase', len(owrdRecordersL)))
   messages.append('\t%-79s %10d' % ('Number of sites correlated to a site in CDWR datbase', len(cdwrSitesL)))
   messages.append('\t%-79s %10d' % ('Number of recorder sites in collection file in the CDWR datbase', len(cdwrRecordersL)))
   messages.append('\t%s' % (ncols * '-'))
   messages.append('\n')
   messages.append('\n')

   screen_logger.info('\n'.join(messages))
   file_logger.info('\n'.join(messages))
   
   return siteInfoD
# =============================================================================

def processUSGS (siteInfoD, mySiteFields, myGwFields):

   gwInfoD      = {}
   rcInfoD      = {}
   
   usgsRecords  = 0
   owrdRecords  = 0
   cdwrRecords  = 0
   othrRecords  = 0
   totalRecords = 0
   rcRecords    = 0

   numYRecords  = 0
   numNRecords  = 0

   gwCodesD     = {}

   pst_offset   = -8
   days_offset  = 365
   activeDate   = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_offset)

   # Prepare list of site numbers
   # -------------------------------------------------
   #
   usgsSitesD     = dict({siteInfoD[x]['site_no']:siteInfoD[x]['site_id'] for x in siteInfoD if len(siteInfoD[x]['site_no']) > 0})
   usgsSitesL     = list({siteInfoD[x]['site_no'] for x in siteInfoD if len(siteInfoD[x]['site_no']) > 0})
   owrdSitesL     = list({siteInfoD[x]['coop_site_no'] for x in siteInfoD if len(siteInfoD[x]['coop_site_no']) > 0})
   cdwrSitesL     = list({siteInfoD[x]['cdwr_id'] for x in siteInfoD if len(siteInfoD[x]['cdwr_id']) > 0})

   missSitesL = list(usgsSitesL)

   # NwisWeb groundwater service
   # -------------------------------------------------
   #
   tempL  = list(usgsSitesL)
   nsites = 50
   linesL = []

   while len(tempL) > 0:

      nList = ",".join(tempL[:nsites])
      del tempL[:nsites]

      # Web request
      #
      URL          = 'https://waterservices.usgs.gov/nwis/gwlevels/?format=rdb&sites=%s&startDT=1800-01-01&siteStatus=all' % nList
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
   
   # Process groundwater measurements
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
      
      # Set record
      #
      gwRecord = {}
      
      for i in range(len(namesL)):
         gwRecord[namesL[i]] = valuesL[namesL.index(namesL[i])]
      
      # Set site ID
      #
      site_no   = gwRecord['site_no']
      if site_no in usgsSitesD:
         site_id = usgsSitesD[site_no]
      
      # Remove site number
      #
      if site_no in missSitesL:
         missSitesL.remove(site_no)

      # Set waterlevel
      #
      lev_va        = str(gwRecord['lev_va'])
      if lev_va == 'None':
         lev_va = ''

      # Set water-level date information
      #
      lev_dt        = str(gwRecord['lev_dt'])
      lev_tm        = str(gwRecord['lev_tm'])
      lev_tz_cd     = str(gwRecord['lev_tz_cd'])
      lev_dt_acy_cd = str(gwRecord['lev_dt_acy_cd'])
    
      # Partial date YYYY
      #
      if lev_dt_acy_cd == 'Y':
         tempDate   = datetime.datetime.strptime(lev_dt, '%Y')
         wlDate     = tempDate.replace(month=7,day=16,hour=12)
   
      # Partial date YYYY-MM
      #
      elif lev_dt_acy_cd == 'M':
         tempDate   = datetime.datetime.strptime(lev_dt, '%Y-%m')
         wlDate     = tempDate.replace(day=16,hour=12)
         if wlDate.month == 2:
             wlDate = tempDate.replace(day=15,hour=12)
    
      # Full date YYYY-MM-DD
      #
      elif lev_dt_acy_cd == 'D':
         tempDate   = datetime.datetime.strptime(lev_dt, '%Y-%m-%d')
         wlDate     = tempDate.replace(hour=12)
    
      # Full date YYYY-MM-DD HH:MM
      #
      elif lev_dt_acy_cd == 'm':
         tmp_dt = '%s %s' % (lev_dt, lev_tm)
         wlDate = datetime.datetime.strptime(tmp_dt, '%Y-%m-%d %H:%M')

      # Set dtm
      #
      wlDate     = wlDate.replace(tzinfo=datetime.timezone.utc)
      lev_dtm    = wlDate.strftime("%Y-%m-%d %H:%M %Z")

      gwRecord['lev_dtm'] = lev_dtm
      
      # Partial dates YYYY | YYYY-MM | YYYY-MM-DD
      #
      if lev_dt_acy_cd in ['Y', 'M', 'D']:
         lev_str_dt = lev_dt
         lev_tm     = ''
         lev_tz_cd  = ''    
    
      # Full date YYYY-MM-DD HH:MM [Convert to PST time zone]
      #
      elif lev_dt_acy_cd == 'm':
         tmpDate    = wlDate + datetime.timedelta(hours=pst_offset)
         lev_dt     = tmpDate.strftime("%Y-%m-%d")
         lev_tm     = tmpDate.strftime("%H:%M")
         lev_tz_cd  = "PST"
         lev_str_dt = tmpDate.strftime("%Y-%m-%d %H:%M")
    
      # Set lev_mst to YYYY-MM-DD to identify duplicate measurements
      #
      lev_mst = lev_str_dt[:10]
      
      # Set date/time/time zone
      #
      gwRecord['lev_dt']     = lev_dt
      gwRecord['lev_tm']     = lev_tm
      gwRecord['lev_tz_cd']  = lev_tz_cd
      gwRecord['lev_str_dt'] = lev_str_dt
            
      # Set measurement status
      #
      lev_status_cd = str(gwRecord['lev_status_cd'])
      myColumn   = 'lev_status_cd'
      if myColumn not in gwCodesD:
         gwCodesD[myColumn] = []
      if str(lev_status_cd) not in gwCodesD[myColumn]:
         gwCodesD[myColumn].append(str(lev_status_cd))
         
      if len(lev_status_cd) < 1:
         lev_status_cd = ''
      elif lev_status_cd == '1':
         lev_status_cd = ''
      elif lev_status_cd == '2':
         lev_status_cd = 'Z'
      elif lev_status_cd == '3':
         lev_status_cd = 'Z'
      elif lev_status_cd == '4':
         lev_status_cd = 'B'
      elif lev_status_cd == '5':
         lev_status_cd = 'X'
      elif lev_status_cd == '6':
         lev_status_cd = 'Z'
      elif lev_status_cd == '7':
         lev_status_cd = 'L'
      elif lev_status_cd == '8':
         lev_status_cd = 'V'
      elif lev_status_cd == '9':
         lev_status_cd = 'Z'
 
      gwRecord['lev_status_cd'] = lev_status_cd

      # Set measuring method and waterlevel accuracy
      #
      lev_meth_cd   = str(gwRecord['lev_meth_cd'])
      lev_acy_cd    = str(gwRecord['lev_acy_cd'])
      myColumn   = 'lev_meth_cd'
      if myColumn not in gwCodesD:
         gwCodesD[myColumn] = []
      if str(lev_meth_cd) not in gwCodesD[myColumn]:
         gwCodesD[myColumn].append(str(lev_meth_cd))            
      
      if len(lev_meth_cd) > 0:
         if lev_meth_cd in ["A","E","D","G","M","N","O","R","U","X","Z"]:
            lev_acy_cd = '0';
         elif lev_meth_cd in ["B","C","F","H","L","P","T"]:
            lev_acy_cd = '1';
         elif lev_meth_cd in ["S","V","W","H"]:
            lev_acy_cd = '2';

      if len(lev_va) < 1:
         lev_acy_cd = '';

      gwRecord['lev_acy_cd'] = lev_acy_cd
            
      # Set measuring agency
      #
      lev_agency_cd = str(gwRecord['lev_agency_cd']).strip()
      myColumn      = 'lev_agency_cd'
      if myColumn not in gwCodesD:
         gwCodesD[myColumn] = []
      if str(lev_agency_cd) not in gwCodesD[myColumn]:
         gwCodesD[myColumn].append(str(lev_agency_cd))
            
      if len(lev_agency_cd) > 0 and lev_agency_cd == "OR004":
         lev_agency_cd = "OWRD"         
      if len(lev_agency_cd) < 1:
         lev_agency_cd = "USGS"

      gwRecord['lev_agency_cd'] = lev_agency_cd
            
      # Set measuring source
      #
      lev_src_cd = str(gwRecord['lev_src_cd'])
      myColumn   = 'lev_src_cd'
      if myColumn not in gwCodesD:
         gwCodesD[myColumn] = []
      if str(lev_src_cd) not in gwCodesD[myColumn]:
         gwCodesD[myColumn].append(str(lev_src_cd))
      
      if lev_agency_cd == "USGS":
         lev_src_cd = "S"         
      if lev_agency_cd != "USGS":
         lev_src_cd = "A"         

      gwRecord['lev_src_cd'] = lev_src_cd
          
      # Set lev_web_cd
      #
      lev_web_cd    = 'N'
      if len(lev_va) > 0 and lev_status_cd == '':
         lev_web_cd    = 'Y'

      gwRecord['lev_web_cd'] = lev_web_cd

      # New site
      #
      if site_id not in gwInfoD:
         
         gwInfoD[site_id] = {}

      # New waterlevel record for site
      #
      if lev_mst not in gwInfoD[site_id].keys():

         gwInfoD[site_id][lev_mst] = {}

      # Prepare values
      #
      for myColumn in myGwFields:
         if myColumn in mySiteFields:
            gwInfoD[site_id][lev_mst][myColumn] = siteInfoD[site_id][myColumn]
         else:
            gwInfoD[site_id][lev_mst][myColumn] = gwRecord[myColumn]
         

      del linesL[0]

      
   # Period of record for USGS recorder sites
   # ----------------------------------------------------------------------
   #
   tempL  = list(usgsSitesL)
   nsites = 50
   linesL = []

   while len(tempL) > 0:

      nList = ",".join(tempL[:nsites])
      del tempL[:nsites]

      # Web request
      #
      URL          = 'https://waterservices.usgs.gov/nwis/site/?format=rdb&sites=%s&seriesCatalogOutput=true&siteStatus=all&siteType=GW&hasDataTypeCd=dv,iv&outputDataTypeCd=dv,iv' % nList
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
   
   # Process site records
   # -------------------------------------------------
   #
   if len(linesL) > 0:
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
         
         # Set record
         #
         gwRecord = {}
         
         for i in range(len(namesL)):
            gwRecord[namesL[i]] = valuesL[namesL.index(namesL[i])]
         
         # Accept only groundwater parameters
         #
         if gwRecord['parm_cd'] in ['62610', '62611', '72019']:
            
            # Set site ID
            #
            site_no   = gwRecord['site_no']
            if site_no in usgsSitesD:
               site_id = usgsSitesD[site_no]
            
            # Set recorder site
            #
            if site_id not in rcInfoD:
               rcInfoD[site_id] = {}
                  
            # New recorder record for site
            #
            begin_date = str(valuesL[ namesL.index('begin_date') ])
            if begin_date not in rcInfoD[site_id]:
               rcInfoD[site_id][begin_date] = {}
      
            end_date   = str(valuesL[ namesL.index('end_date') ])
            if end_date not in rcInfoD[site_id]:
               rcInfoD[site_id][end_date] = {}
      
            # Prepare values
            #
            for myColumn in gwRecord.keys():
               rcInfoD[site_id][begin_date][myColumn] = gwRecord[myColumn]
               rcInfoD[site_id][end_date][myColumn]   = gwRecord[myColumn]
   
                     
         del linesL[0]
   
               
   # Prepare set of sites
   #
   usgsSet        = set(usgsSitesL)
   missingSet     = set(missSitesL)
   matchSitesL    = list(usgsSet.difference(missingSet))
   
   # Period of record of all measurements for each site and counts
   #
   for site_id in sorted(matchSitesL):

      if site_id in gwInfoD:
         totalRecords += len(gwInfoD[site_id])
         usgsRecords  += len(list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_agency_cd'] == 'USGS'}))
         owrdRecords  += len(list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_agency_cd'] == 'OWRD'}))
         cdwrRecords  += len(list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_agency_cd'] == 'CDWR'}))
         othrRecords  += len(list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_agency_cd'] not in ['USGS', 'OWRD', 'CDWR']}))
               
         # Static and Non-static measurements
         #
         numYRecords  += len(list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_web_cd'] == 'Y'}))
         numNRecords  += len(list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_web_cd'] != 'Y'}))
         
         # Assign other measurements to USGS
         #
         othrDatesL    = list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_agency_cd'] not in ['USGS', 'OWRD', 'CDWR']})
         for gwDate in sorted(othrDatesL):
            gwInfoD[site_id][gwDate]['lev_agency_cd'] = 'USGS'
         
         # USGS period of record of periodic measurements for each site
         #
         siteRecordsL  = sorted(list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_agency_cd'] == 'USGS'}))
         BeginDate     = ''
         EndDate       = ''
         status        = 'Inactive'
         if len(siteRecordsL) > 0:
            BeginDate     = gwInfoD[site_id][siteRecordsL[0]]['lev_str_dt'][:10]
            EndDate       = gwInfoD[site_id][siteRecordsL[-1]]['lev_str_dt'][:10]
            lev_dt_acy_cd = gwInfoD[site_id][siteRecordsL[-1]]['lev_dt_acy_cd']
            dateFmt = '%Y-%m-%d'
            if lev_dt_acy_cd == 'Y':
               dateFmt = '%Y'
            elif lev_dt_acy_cd == 'M':
               dateFmt = '%Y-%m'
            wlDate = datetime.datetime.strptime(gwInfoD[site_id][siteRecordsL[-1]]['lev_str_dt'][:10], dateFmt)
            wlDate = wlDate.replace(tzinfo=datetime.timezone.utc)
            status = 'Inactive'
            if wlDate >= activeDate:
               status  = 'Active'
         else:
            screen_logger.debug('Site %s has no USGS periodic or recorder groundwater measurements' % site_id)
   
         siteInfoD[site_id]['usgs_begin_date']      = BeginDate
         siteInfoD[site_id]['usgs_end_date']        = EndDate
         siteInfoD[site_id]['usgs_status']          = status
         siteInfoD[site_id]['usgs_count']           = len(siteRecordsL)      
         
      # Overall period of record of recorder measurements for each site
      #
      if site_id in rcInfoD:
         siteRecordsL  = sorted(list(rcInfoD[site_id].keys()))
         BeginDate     = rcInfoD[site_id][siteRecordsL[0]]['begin_date']
         EndDate       = rcInfoD[site_id][siteRecordsL[-1]]['end_date']
         wlDate        = datetime.datetime.strptime(EndDate, '%Y-%m-%d')
         wlDate        = wlDate.replace(tzinfo=datetime.timezone.utc)
         status        = 'Inactive'
         if wlDate >= activeDate:
            status  = 'Active'

         siteInfoD[site_id]['usgs_rc_status']     = status
         siteInfoD[site_id]['usgs_rc_begin_date'] = BeginDate
         siteInfoD[site_id]['usgs_rc_end_date']   = EndDate
         siteInfoD[site_id]['usgs_rc_count']      = rcInfoD[site_id][EndDate]['count_nu']

         if rcInfoD[site_id][EndDate]['data_type_cd'] == 'dv':
            rcRecords += int(rcInfoD[site_id][EndDate]['count_nu'])
         
   activeSitesL     = list({x for x in siteInfoD if siteInfoD[x]['usgs_status'] == 'Active'})
   activeRecordersL = list({x for x in siteInfoD if siteInfoD[x]['usgs_rc_status'] == 'Active'})

   # Print information
   #
   ncols    = 150
   messages = []
   messages.append('\n\tProcessed USGS periodic and recorder measurements')
   messages.append('\t%s' % (ncols * '-'))
   messages.append('\t%-79s %10d' % ('Number of sites with periodic measurements', len(siteInfoD)))
   messages.append('\t%-79s %10d' % ('Number of USGS sites in collection file', len(usgsSitesL)))
   messages.append('\t%-79s %10d' % ('Number of USGS sites in collection file NOT retrieved from USGS database', len(missSitesL)))
   messages.append('\t%-79s %10d' % ('Number of Active periodic sites in collection file measured by the USGS', len(activeSitesL)))
   messages.append('\t%-79s %10d' % ('Number of USGS sites with periodic measurements', len(gwInfoD)))
   messages.append('\t%-79s %10d' % ('Number of of static periodic measurements', numYRecords))
   messages.append('\t%-79s %10d' % ('Number of of non-static periodic measurements', numNRecords))
   messages.append('\t%-79s %10d' % ('Number of USGS periodic measurements', usgsRecords))
   messages.append('\t%-79s %10d' % ('Number of OWRD periodic measurements', owrdRecords))
   messages.append('\t%-79s %10d' % ('Number of CDWR periodic measurements', cdwrRecords))
   messages.append('\t%-79s %10d' % ('Number of periodic measurements made by other agencies', othrRecords))
   messages.append('\t%-79s %10d' % ('Number of periodic measurements', totalRecords))
   messages.append('\t%-79s %10d' % ('Number of recorder sites in collection file from USGS database', len(rcInfoD)))
   messages.append('\t%-79s %10d' % ('Number of Active recorder sites in collection file measured by the USGS', len(activeRecordersL)))
   messages.append('\t%-79s %10d' % ('Number of recorder measurements', rcRecords))
   messages.append('\t%s' % (ncols * '-'))
   if len(matchSitesL) > 0:
      messages.append('')
      messages.append('\t%s' % 'USGS periodic sites with USGS measurements in collection file in USGS database')
      messages.append('\t%s' % (ncols * '-'))
      fmt = '\t%-20s %-15s %-20s %-35s %10s %15s %15s %10s'
      messages.append(fmt % ('USGS',        'OWRD',        'CDWR', 'Station', 'Periodic', 'Begin', 'End',  'Active'))
      messages.append(fmt % ('Site Number', 'Well Log ID', 'ID',   ' ',       'Counts',   'Date',  'Date', 'Status'))
      messages.append('\t%s' % (ncols * '-'))
      for site_no in sorted(matchSitesL):
         site_id = usgsSitesD[site_no]
         messages.append(fmt % (siteInfoD[site_id]['site_no'],
                                siteInfoD[site_id]['coop_site_no'],
                                siteInfoD[site_id]['cdwr_id'],
                                siteInfoD[site_id]['station_nm'][:35],
                                siteInfoD[site_id]['usgs_count'],
                                siteInfoD[site_id]['usgs_begin_date'],
                                siteInfoD[site_id]['usgs_end_date'],
                                siteInfoD[site_id]['usgs_status']
                                ))
      messages.append('\t%s' % (ncols * '-'))
   if len(rcInfoD.keys()) > 0:
      messages.append('')
      messages.append('\t%s' % 'USGS recorder sites with USGS measurements in collection file in USGS database')
      messages.append('\t%s' % (ncols * '-'))
      fmt = '\t%-20s %-15s %-20s %-35s %10s %15s %15s %10s'
      messages.append(fmt % ('USGS',        'OWRD',        'CDWR', 'Station', 'Recorder', 'Begin', 'End',  'Active'))
      messages.append(fmt % ('Site Number', 'Well Log ID', 'ID',   ' ',       'Counts',   'Date',  'Date', 'Status'))
      messages.append('\t%s' % (ncols * '-'))
      for site_id in sorted(rcInfoD.keys()):
         messages.append(fmt % (siteInfoD[site_id]['site_no'],
                                siteInfoD[site_id]['coop_site_no'],
                                siteInfoD[site_id]['cdwr_id'],
                                siteInfoD[site_id]['station_nm'][:35],
                                siteInfoD[site_id]['usgs_rc_count'],
                                siteInfoD[site_id]['usgs_rc_begin_date'],
                                siteInfoD[site_id]['usgs_rc_end_date'],
                                siteInfoD[site_id]['usgs_rc_status']
                                ))
      messages.append('\t%s' % (ncols * '-'))
   if len(missSitesL) > 0:
      messages.append('')
      messages.append('\t%s' % 'USGS periodic sites in collection file NOT retrieved from USGS database')
      messages.append('\t%s' % (ncols * '-'))
      fmt = '\t%-20s %-20s %-20s %-35s'
      messages.append(fmt % ('USGS',        'OWRD',        'CDWR', 'Station'))
      messages.append(fmt % ('Site Number', 'Well Log ID', 'ID',   ' '))
      messages.append('\t%s' % (ncols * '-'))
      for site_no in sorted(missSitesL):
         site_id = usgsSitesD[site_no]
         messages.append(fmt % (siteInfoD[site_id]['site_no'],
                                siteInfoD[site_id]['coop_site_no'],
                                siteInfoD[site_id]['cdwr_id'],
                                siteInfoD[site_id]['station_nm'][:35]
                                ))
      messages.append('\t%s' % (ncols * '-'))
   for myCode in sorted(gwCodesD.keys()):
      messages.append('')
      messages.append('\tCode %-70s' % myCode)
      messages.append('\t%s' % (ncols * '-'))
      messages.append('\t%s' % '\n\t'.join(gwCodesD[myCode]))
      messages.append('\t%s' % (ncols * '-'))
   messages.append('\n')

   screen_logger.info('\n'.join(messages))
   file_logger.info('\n'.join(messages))

   return gwInfoD

# =============================================================================

def processOWRD (siteInfoD, mySiteFields, myGwFields, owrd_gw_file, owrd_rc_file):

   gwInfoD      = {}
   rcInfoD      = {}

   keyColumn    = 'gw_logid'
   
   usgsRecords  = 0
   owrdRecords  = 0
   cdwrRecords  = 0
   othrRecords  = 0
   totalRecords = 0
   rcRecords    = 0

   numYRecords  = 0
   numNRecords  = 0

   gwCodesD     = {}
   
   myOwrdFields = [
                   "gw_logid",
                   "measured_date",
                   "measured_time",
                   "measured_datetime",
                   "waterlevel_ft_below_land_surface",
                   "measurement_status_desc",
                   "method_of_water_level_measurement",
                   "measurement_source_organization_desc"
                  ]

   pst_offset   = 8
   days_offset  = 365
   activeDate   = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_offset)

   endYear      = float(datetime.datetime.now().strftime("%Y")) + 1

   # Prepare list of site numbers
   # -------------------------------------------------
   #
   usgsSitesD = dict({siteInfoD[x]['coop_site_no']:siteInfoD[x]['site_no'] for x in siteInfoD if len(siteInfoD[x]['site_no']) > 0})
   owrdSitesD = dict({siteInfoD[x]['coop_site_no']:siteInfoD[x]['site_id'] for x in siteInfoD if len(siteInfoD[x]['coop_site_no']) > 0})
   owrdSitesL = list({siteInfoD[x]['coop_site_no'] for x in siteInfoD if len(siteInfoD[x]['coop_site_no']) > 0})
   missSitesL = list(owrdSitesL)
   
   # Read OWRD periodic waterlevel file
   # -------------------------------------------------
   #
   with open(owrd_gw_file,'r') as f:
       linesL = f.read().splitlines()
   
   # Check for empty file
   #
   if len(linesL) < 1:
      message = "Empty waterlevel file %s" % owrd_gw_file
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

      Line     = linesL[0]
               
      del linesL[0]
      
      valuesL  = Line.split('\t')

      gw_logid = str(valuesL[ namesL.index(keyColumn) ])
    
      # Check if site is wanted
      #
      if gw_logid in owrdSitesL:
                  
         # Remove site from missing list
         #
         if gw_logid in missSitesL:
            missSitesL.remove(gw_logid)
          
         # Set site_id
         #
         site_id = gw_logid
         if gw_logid in owrdSitesD:
            site_id = owrdSitesD[gw_logid]

         # Set record
         #
         gwRecord = {}

         for myColumn in myOwrdFields:
            gwRecord[myColumn] = str(valuesL[ namesL.index(myColumn) ])
           
         # Set waterlevel
         #
         lev_va = str(gwRecord['waterlevel_ft_below_land_surface'])
         if lev_va == 'None':
            lev_va = ''
         
         gwRecord['lev_va'] = lev_va

         # Set water-level date information
         #
         lev_dtm       = gwRecord['measured_datetime'][:-3]
         lev_dt        = gwRecord['measured_datetime'][:10]
         lev_tm        = gwRecord['measured_datetime'][12:-3]
         lev_tz_cd     = ''
         lev_dt_acy_cd = 'D'
            
         if lev_tm in ['00:00', '12:00']:
            lev_tm        = ''
            wlDate        = datetime.datetime.strptime(lev_dt, '%m/%d/%Y')
            wlDate        = wlDate.replace(hour=4)
            lev_str_dt    = wlDate.strftime('%Y-%m-%d')
            lev_dt        = lev_str_dt[:10]
         else:
            tmp_str_dt    = lev_dtm
            wlDate        = datetime.datetime.strptime(tmp_str_dt, '%m/%d/%Y %H:%M')
            lev_dt_acy_cd = 'm'
            lev_tz_cd     = 'PST'
            lev_str_dt    = wlDate.strftime('%Y-%m-%d %H:%M')
            lev_dt        = lev_str_dt[:10]
            lev_tm        = lev_str_dt[11:]
          
         # Set lev_mst to YYYY-MM-DD to identify duplicate measurements
         #
         lev_mst = wlDate.strftime('%Y-%m-%d')
           
         # Convert to UTC time zone
         #
         wlDate     = wlDate + datetime.timedelta(hours=pst_offset)
         wlDate     = wlDate.replace(tzinfo=datetime.timezone.utc)
         lev_dtm    = wlDate.strftime("%Y-%m-%d %H:%M %Z")
      
         gwRecord['lev_dt']        = lev_dt
         gwRecord['lev_tm']        = lev_tm
         gwRecord['lev_tz_cd']     = lev_tz_cd
         gwRecord['lev_dt_acy_cd'] = lev_dt_acy_cd
         gwRecord['lev_str_dt']    = lev_str_dt
         gwRecord['lev_dtm']       = lev_dtm

         #screen_logger.info('Record %s %s' % (myRecord['measured_date'][:10], myRecord['measured_time'][:5]))
         #screen_logger.info('Site %s Coop %s: %s %s %s' % (site_id, well_log_id, lev_dt, lev_tm, lev_dtm))
           
         # Set lev_status_cd
         #
         lev_status_cd = gwRecord['measurement_status_desc']
         myColumn   = 'lev_status_cd'
         if myColumn not in gwCodesD:
            gwCodesD[myColumn] = []
         if str(lev_status_cd) not in gwCodesD[myColumn]:
            gwCodesD[myColumn].append(str(lev_status_cd))
         
         if lev_status_cd is None:
            lev_status_cd = ''
         elif lev_status_cd == "STATIC":
            lev_status_cd = ""
         elif lev_status_cd == "FLOWING":
            lev_status_cd = "F"
         elif lev_status_cd in ["RISING", "FALLING", "PUMPING"]:
            lev_status_cd = "P"
         elif lev_status_cd in ["UNKNOWN", "OTHER"]:
            lev_status_cd = 'Z'
         elif lev_status_cd == "DRY":
            lev_status_cd = 'D'
         else:
            screen_logger.info('OWRD site %s [on %s]: Measurement status "%s" needs to be assigned (currently set to Z for Other' % (gw_logid, lev_str_dt, lev_status_cd))
            lev_status_cd = 'Z'
               
         gwRecord['lev_status_cd']  = lev_status_cd
            
         # Set measuring method
         #
         lev_meth_cd = gwRecord['method_of_water_level_measurement']
         myColumn   = 'lev_meth_cd'
         if myColumn not in gwCodesD:
            gwCodesD[myColumn] = []
         if str(lev_meth_cd) not in gwCodesD[myColumn]:
            gwCodesD[myColumn].append(str(lev_meth_cd))            
      
         if lev_meth_cd == "AIRLINE":
            lev_meth_cd = "A"
         elif lev_meth_cd == "AIRLINE CALIBRATED":
            lev_meth_cd = "C"
         elif lev_meth_cd == "RECORDER DIGITAL":
            lev_meth_cd = "F"
         elif lev_meth_cd == "PRESSURE GAGE":
            lev_meth_cd = "G"
         elif lev_meth_cd == "PRESSURE GAGE CALIBRATED":
            lev_meth_cd = "H"
         elif lev_meth_cd == "GEOPHYSICAL LOG":
            lev_meth_cd = "L"
         elif lev_meth_cd == "MANOMETER":
            lev_meth_cd = "M"
         elif lev_meth_cd == "OBSERVED":
            lev_meth_cd = "O"
         elif lev_meth_cd == "SONIC":
            lev_meth_cd = "P"
         elif lev_meth_cd == "REPORTED":
            lev_meth_cd = "R"
         elif lev_meth_cd == "STEEL TAPE":
            lev_meth_cd = "S"
         elif lev_meth_cd == "ETAPE":
            lev_meth_cd = "T"
         elif lev_meth_cd == "TAPE":
            lev_meth_cd = "T"
         elif lev_meth_cd == "ETAPE CALIBRATED":
            lev_meth_cd = "V"
         elif lev_meth_cd in ["UNKNOWN", "OTHER"]:
            lev_meth_cd = "Z"

         #
         # Skip record no measurement taken
         #
         elif lev_meth_cd == "NOT MEASURED":
            continue
         elif lev_meth_cd is None:
            lev_meth_cd = "Z"
         else:
            screen_logger.info('OWRD site %s [on %s]: Measuring method "%s" [method_of_water_level_measurement] needs to be assigned (currently set to Z' % (gw_logid, lev_str_dt, lev_meth_cd))
            lev_meth_cd = "Z"

         gwRecord['lev_meth_cd'] = lev_meth_cd
          
         # Set measuring accuracy [NOT in file determined by measurement method]
         #
         lev_acy_cd = '0'
         if lev_meth_cd in ["A", "E", "F", "G", "M", "N", "O", "R", "U", "X", "Z"]:
            lev_acy_cd = '0'
         elif lev_meth_cd in ["B", "C", "H", "L", "P", "T"]:
            lev_acy_cd = '1'
         elif lev_meth_cd in ["S", "V", "W"]:
            lev_acy_cd = '2'
         else:
            screen_logger.info('OWRD site %s [on %s]: Measuring accuracy determined by measurement method "%s" needs to be assigned (currently set to 0)' % (gw_logid, lev_str_dt, lev_meth_cd))
            lev_acy_cd = '0'
           
         gwRecord['lev_acy_cd'] = lev_acy_cd
          
         # Set measuring agency [measurement_source_organization]
         #
         lev_agency_cd = gwRecord['measurement_source_organization_desc']
         myColumn      = 'lev_agency_cd'
         if myColumn not in gwCodesD:
            gwCodesD[myColumn] = []
         if str(lev_agency_cd) not in gwCodesD[myColumn]:
            gwCodesD[myColumn].append(str(lev_agency_cd))
            
         if lev_agency_cd == "OWRD":
            lev_agency_cd = "OWRD"
            lev_src_cd    = "S"
         elif lev_agency_cd == "ODEQ":
            lev_agency_cd = "ODEQ"
            lev_src_cd    = "S"
         elif lev_agency_cd == "USGS":
            lev_agency_cd = "USGS"
            lev_src_cd    = "S"
         elif lev_agency_cd == "CDWR":
            lev_agency_cd = "CDWR"
            lev_src_cd    = "S"
         elif lev_agency_cd in ["DRLR", "DRILLER"]:
            lev_meth_cd   = "R"
            lev_agency_cd = "OWRD"
            lev_src_cd    = "D"
         elif lev_agency_cd == "OWNR":
            lev_meth_cd   = "R"
            lev_agency_cd = "OWRD"
            lev_src_cd    = "O"
         elif lev_agency_cd == "OTH":
            lev_meth_cd   = "R"
            lev_agency_cd = "OWRD"
            lev_src_cd    = "Z"
         elif lev_agency_cd in ["PMPI","CON","RG","PE","CWRE","HCWC","BWA"]:
            lev_meth_cd   = "R"
            lev_agency_cd = "OWRD"
            lev_src_cd    = "G"
         elif lev_agency_cd == "Bureau of Reclamation":
            lev_agency_cd = "USBR"
            lev_src_cd    = "S"
         elif lev_agency_cd == "Tulelake Irrigation District" or "Tulelake Irrigation District GSA":
            lev_agency_cd = "CA049 Tulelake Irrigation Distric"
            lev_src_cd    = "S"
         elif lev_agency_cd == "Tulelake Irrigation District GSA":
            lev_agency_cd = "CA049 Tulelake Irrigation Distric"
            lev_src_cd    = "S"
         else:
            screen_logger.info('OWRD site %s: Measuring agency "%s" [measurement_source_organization] needs to be assigned (currently set to OWRD' % (gw_logid, lev_agency_cd))
            lev_agency_cd = 'OWRD'
            lev_src_cd    = "S"
               
         gwRecord['lev_agency_cd']  = lev_agency_cd
         gwRecord['lev_src_cd']     = lev_src_cd
           
         # Set lev_web_cd
         #
         lev_web_cd    = 'N'
         if len(lev_va) > 0 and len(lev_status_cd) < 1:
            lev_web_cd    = 'Y'
            
         gwRecord['lev_web_cd']     = lev_web_cd
           
         # Set remarks
         #
         lev_rmk_tx = ''

         # New site
         #
         if site_id not in gwInfoD:
               
            gwInfoD[site_id] = {}

         # New waterlevel record for site
         #
         if lev_dtm not in gwInfoD[site_id].keys():

            gwInfoD[site_id][lev_mst] = {}

         # Prepare values
         #
         for myColumn in myGwFields:
            if myColumn in mySiteFields:
               gwInfoD[site_id][lev_mst][myColumn] = siteInfoD[site_id][myColumn]
            else:
               gwInfoD[site_id][lev_mst][myColumn] = gwRecord[myColumn]

      
   # Missing OWRD sites for waterlevel information for periodic/recorder wells
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
         # https://apps.wrd.state.or.us/apps/gw/gw_data_rws/api/KLAM0000588/gw_measured_water_level/?start_date=1/1/1905&end_date=1/1/2025&public_viewable=
         #
         URL          = 'https://apps.wrd.state.or.us/apps/gw/gw_data_rws/api/%s/gw_measured_water_level/?start_date=1/1/1900&end_date=1/1/%s&public_viewable=' % (gw_logid, str(endYear))
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
            message = "Warning: OWRD site %s has no OWRD waterlevel measurements available" % gw_logid
            screen_logger.info(message)
            continue

         # Parse records
         #
         jsonRecords  = gwJson['feature_list']
   
         # Process groundwater measurements
         # -------------------------------------------------
         #
         for myRecord in jsonRecords:
         
            # Remove site from missing list
            #
            if gw_logid in missSitesL:
               missSitesL.remove(gw_logid)
         
            # Set site_id
            #
            site_id = gw_logid
            if gw_logid in owrdSitesD:
               site_id = owrdSitesD[gw_logid]

            # Set record
            #
            gwRecord = {}
           
            # Set waterlevel
            #
            lev_va             = str(myRecord['waterlevel_ft_below_land_surface'])
            if lev_va == 'None':
               lev_va = ''
            
            gwRecord['lev_va'] = lev_va

            # Set water-level date information
            #
            lev_dt        = myRecord['measured_date'][:10]
            lev_tm        = myRecord['measured_time'][:5]
            lev_tz_cd     = ''
            lev_dt_acy_cd = 'D'
            
            if lev_tm in ['00:00', '']:
               lev_tm        = ''
               wlDate        = datetime.datetime.strptime(lev_dt, '%Y-%m-%d')
               wlDate        = wlDate.replace(hour=4)
               lev_str_dt    = lev_dt
            else:
               lev_str_dt    = '%s %s' % (lev_dt, lev_tm)
               wlDate        = datetime.datetime.strptime(lev_str_dt, '%Y-%m-%d %H:%M')
               lev_dt_acy_cd = 'm'
               lev_tz_cd     = 'PST'
           
            # Convert to UTC time zone
            #
            gwDate     = wlDate
            wlDate     = wlDate + datetime.timedelta(hours=pst_offset)
            wlDate     = wlDate.replace(tzinfo=datetime.timezone.utc)
            lev_dtm    = wlDate.strftime("%Y-%m-%d %H:%M %Z")
      
            gwRecord['lev_dt']        = lev_dt
            gwRecord['lev_tm']        = lev_tm
            gwRecord['lev_tz_cd']     = lev_tz_cd
            gwRecord['lev_dt_acy_cd'] = lev_dt_acy_cd
            gwRecord['lev_str_dt']    = lev_str_dt
            gwRecord['lev_dtm']       = lev_dtm
          
            # Set lev_dtm to YYYY-MM-DD to identify duplicate measurements
            #
            lev_dtm = lev_dtm[:10]

            #screen_logger.info('Record %s %s' % (myRecord['measured_date'][:10], myRecord['measured_time'][:5]))
            #screen_logger.info('Site %s Coop %s: %s %s %s' % (site_id, well_log_id, lev_dt, lev_tm, lev_dtm))
          
            # Set measuring accuracy
            #
            lev_acy_cd = str(myRecord['waterlevel_accuracy'])
            myColumn   = 'lev_acy_cd'
            if myColumn not in gwCodesD:
               gwCodesD[myColumn] = []
            if str(lev_acy_cd) not in gwCodesD[myColumn]:
               gwCodesD[myColumn].append(str(lev_acy_cd))
      
            if lev_acy_cd == "0.0":
               lev_acy_cd = '2'
            elif lev_acy_cd == "0.01":
               lev_acy_cd = '2'
            elif lev_acy_cd == "0.02":
               lev_acy_cd = '2'
            elif lev_acy_cd == "0.25":
               lev_acy_cd = '1'
            elif lev_acy_cd == "0.5":
               lev_acy_cd = '1'
            elif lev_acy_cd == "0.1":
               lev_acy_cd = '1'
            elif lev_acy_cd == "1.0":
               lev_acy_cd = '0'
            elif lev_acy_cd == "2.0":
               lev_acy_cd = '9'
            elif lev_acy_cd == "4.0":
               lev_acy_cd = '9'
            elif lev_acy_cd == "None":
               lev_acy_cd = 'U'
            else:
               screen_logger.info('OWRD site %s [on %s]: Measuring accuracy "%s" needs to be assigned (currently set to 0 for Unknown' % (wellNumber, lev_str_dt, lev_acy_cd))
               screen_logger.info(myRecord)
               lev_acy_cd = '0'
            
            gwRecord['lev_acy_cd'] = lev_acy_cd
           
            # Set lev_status_cd
            #
            lev_status_cd = myRecord['measurement_status_desc']
            myColumn   = 'lev_status_cd'
            if myColumn not in gwCodesD:
               gwCodesD[myColumn] = []
            if str(lev_status_cd) not in gwCodesD[myColumn]:
               gwCodesD[myColumn].append(str(lev_status_cd))
         
            if lev_status_cd is None:
               lev_status_cd = ''
            elif lev_status_cd == "STATIC":
               lev_status_cd = ""
            elif lev_status_cd == "FLOWING":
               lev_status_cd = "F"
            elif lev_status_cd in ["RISING", "FALLING", "PUMPING"]:
               lev_status_cd = "P"
            elif lev_status_cd in ["UNKNOWN", "OTHER"]:
               lev_status_cd = 'Z'
            elif lev_status_cd == "DRY":
               lev_status_cd = 'D'
            else:
               screen_logger.info('OWRD site %s [on %s]: Measurement status "%s" needs to be assigned (currently set to Z for Other' % (wellNumber, lev_str_dt, lev_status_cd))
               lev_status_cd = 'Z'
               
            gwRecord['lev_status_cd']  = lev_status_cd
            
            # Set measuring method
            #
            lev_meth_cd = myRecord['method_of_water_level_measurement']
            myColumn   = 'lev_meth_cd'
            if myColumn not in gwCodesD:
               gwCodesD[myColumn] = []
            if str(lev_meth_cd) not in gwCodesD[myColumn]:
               gwCodesD[myColumn].append(str(lev_meth_cd))            
      
            if lev_meth_cd == "AIRLINE":
               lev_meth_cd = "A"
            elif lev_meth_cd == "AIRLINE CALIBRATED":
               lev_meth_cd = "C"
            elif lev_meth_cd == "TRANSDUCER":
               lev_meth_cd = "F"
            elif lev_meth_cd == "RECORDER DIGITAL":
               lev_meth_cd = "F"
            elif lev_meth_cd == "PRESSURE GAGE":
               lev_meth_cd = "G"
            elif lev_meth_cd == "PRESSURE GAGE CALIBRATED":
               lev_meth_cd = "H"
            elif lev_meth_cd == "GEOPHYSICAL LOG":
               lev_meth_cd = "L"
            elif lev_meth_cd == "MANOMETER":
               lev_meth_cd = "M"
            elif lev_meth_cd == "OBSERVED":
               lev_meth_cd = "O"
            elif lev_meth_cd == "REPORTED":
               lev_meth_cd = "R"
            elif lev_meth_cd == "STEEL TAPE":
               lev_meth_cd = "S"
            elif lev_meth_cd == "ETAPE":
               lev_meth_cd = "T"
            elif lev_meth_cd == "TAPE":
               lev_meth_cd = "T"
            elif lev_meth_cd == "ETAPE CALIBRATED":
               lev_meth_cd = "V"
            elif lev_meth_cd in ["UNKNOWN", "OTHER"]:
               lev_meth_cd = "Z"
            #
            # Skip record no measurement taken
            #
            elif lev_meth_cd == "NOT MEASURED":
               continue
            elif lev_meth_cd is None:
               lev_meth_cd = "Z"
            else:
               screen_logger.info('OWRD site %s [on %s]: Measuring method "%s" [method_of_water_level_measurement] needs to be assigned (currently set to Z' % (wellNumber, lev_str_dt, lev_meth_cd))
               lev_meth_cd = "Z"

            gwRecord['lev_meth_cd'] = lev_meth_cd
           
            # Set measuring agency [measurement_source_organization]
            #
            lev_agency_cd = myRecord['measurement_source_organization']
            myColumn      = 'lev_agency_cd'
            if myColumn not in gwCodesD:
               gwCodesD[myColumn] = []
            if str(lev_agency_cd) not in gwCodesD[myColumn]:
               gwCodesD[myColumn].append(str(lev_agency_cd))
            
            if lev_agency_cd == "OWRD":
               lev_agency_cd = "OWRD"
               lev_src_cd    = "S"
            elif lev_agency_cd == "ODEQ":
               lev_agency_cd = "ODEQ"
               lev_src_cd    = "S"
            elif lev_agency_cd == "USGS":
               lev_agency_cd = "USGS"
               lev_src_cd    = "S"
            elif lev_agency_cd == "CDWR":
               lev_agency_cd = "CDWR"
               lev_src_cd    = "S"
            elif lev_agency_cd == "DRLR":
               lev_meth_cd   = "R"
               lev_agency_cd = "OWRD"
               lev_src_cd    = "D"
            elif lev_agency_cd == "OWNR":
               lev_meth_cd   = "R"
               lev_agency_cd = "OWRD"
               lev_src_cd    = "O"
            elif lev_agency_cd == "OTH":
               lev_meth_cd   = "R"
               lev_agency_cd = "OWRD"
               lev_src_cd    = "Z"
            elif lev_agency_cd in ["PMPI","CON","RG","PE","CWRE","HCWC","BWA"]:
               lev_meth_cd   = "R"
               lev_agency_cd = "OWRD"
               lev_src_cd    = "G"
            elif lev_agency_cd == "Bureau of Reclamation":
               lev_agency_cd = "USBR"
               lev_src_cd    = "S"
            elif lev_agency_cd == "Tulelake Irrigation District" or "Tulelake Irrigation District GSA":
               lev_agency_cd = "CA049 Tulelake Irrigation Distric"
               lev_src_cd    = "S"
            elif lev_agency_cd == "Tulelake Irrigation District GSA":
               lev_agency_cd = "CA049 Tulelake Irrigation Distric"
               lev_src_cd    = "S"
            else:
               screen_logger.info('OWRD site %s: Measuring agency "%s" [measurement_source_organization] needs to be assigned (currently set to OWRD' % (site_id, lev_agency_cd))
               lev_agency_cd = 'OWRD'
               lev_src_cd    = "S"
               
            gwRecord['lev_agency_cd']  = lev_agency_cd
            gwRecord['lev_src_cd']     = lev_src_cd
           
            # Set lev_web_cd
            #
            lev_web_cd    = 'N'
            if len(lev_va) > 0 and len(lev_status_cd) < 1:
               lev_web_cd    = 'Y'
               
            gwRecord['lev_web_cd']     = lev_web_cd
      
            # Set site information
            #
            if site_id not in gwInfoD:
               gwInfoD[site_id] = {}

            # New waterlevel record for site
            #
            if lev_dtm not in gwInfoD[site_id].keys():
   
               gwInfoD[site_id][lev_mst] = {}
   
            # Prepare values
            #
            for myColumn in myGwFields:
               if myColumn in mySiteFields:
                  gwInfoD[site_id][lev_mst][myColumn] = siteInfoD[site_id][myColumn]
               else:
                  gwInfoD[site_id][lev_mst][myColumn] = gwRecord[myColumn]
         

               
   
   # Read OWRD recorder waterlevel file
   # -------------------------------------------------
   #
   with open(owrd_rc_file,'r') as f:
       linesL = f.read().splitlines()
   
   # Check for empty file
   #
   if len(linesL) < 1:
      message = "Empty waterlevel file %s" % owrd_rc_file
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

      Line = linesL[0]
               
      del linesL[0]
      
      valuesL  = Line.split('\t')

      gw_logid = str(valuesL[ namesL.index(keyColumn) ])
    
      # Check if site is wanted
      #
      if gw_logid in owrdSitesL:
                  
         # Remove site from missing list
         #
         if gw_logid in missSitesL:
            missSitesL.remove(gw_logid)
            
         # Set record
         #
         gwRecord = {}

         for myColumn in namesL:
            gwRecord[myColumn] = str(valuesL[ namesL.index(myColumn) ])

         # Set water-level date information
         #
         tmp_str_dt    = gwRecord['record_date'][:-6]
         wlDate        = datetime.datetime.strptime(tmp_str_dt, '%m/%d/%Y %H:%M')
         lev_str_dt    = wlDate.strftime("%Y-%m-%d %H:%M")
         lev_dt        = lev_str_dt[:10]
         lev_tm        = lev_str_dt[:-5]
         lev_tz_cd     = 'PST'
         lev_dt_acy_cd = 'm'
           
         # Convert to UTC time zone
         #
         wlDate        = datetime.datetime.strptime(tmp_str_dt, '%m/%d/%Y %H:%M')
         wlDate        = wlDate + datetime.timedelta(hours=pst_offset)
         wlDate        = wlDate.replace(tzinfo=datetime.timezone.utc)
         lev_dtm       = wlDate.strftime("%Y-%m-%d %H:%M %Z")

         # Set measuring agency information
         #
         lev_agency_cd = gwRecord['source_description']
      
         # Set record
         #
         gwRecord['lev_dt']        = lev_str_dt[:10]
         gwRecord['lev_tm']        = lev_str_dt[:-5]
         gwRecord['lev_tz_cd']     = lev_tz_cd
         gwRecord['lev_dt_acy_cd'] = lev_dt_acy_cd
         gwRecord['lev_str_dt']    = lev_str_dt
         gwRecord['lev_dtm']       = lev_dtm
         gwRecord['lev_agency_cd'] = lev_dtm
          
         # Set lev_dtm to YYYY-MM-DD to identify duplicate measurements
         #
         lev_dtm = lev_dtm[:10]
           
         # Set site_id
         #
         site_id = gw_logid
         if gw_logid in owrdSitesD:
            site_id = owrdSitesD[gw_logid]
      
         # Set site information
         #
         if site_id not in rcInfoD:
            rcInfoD[site_id] = {}
      
         # Set lev_dtm to YYYY-MM-DD to identify duplicate measurements
         #
         lev_dtm = lev_dtm[:10]
           
         # Set site information
         #
         if lev_dtm not in rcInfoD[site_id]:
            rcInfoD[site_id][lev_dtm] = {}
 
         # Prepare values
         #
         for myColumn in gwRecord.keys():
            rcInfoD[site_id][lev_dtm][myColumn] = gwRecord[myColumn]

      
   # Prepare set of sites
   #
   owrdSet        = set(owrdSitesL)
   missingSet     = set(missSitesL)
   matchSitesL    = list(owrdSet.difference(missingSet))
   
   # Period of record of all measurements for each site and counts
   #
   for well_log_id in sorted(matchSitesL):
      
      site_id = owrdSitesD[well_log_id]
      
      totalRecords += len(gwInfoD[site_id])
      usgsRecords  += len(list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_agency_cd'] == 'USGS'}))
      owrdRecords  += len(list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_agency_cd'] == 'OWRD'}))
      cdwrRecords  += len(list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_agency_cd'] == 'CDWR'}))
      othrRecords  += len(list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_agency_cd'] not in ['USGS', 'OWRD', 'CDWR']}))
            
      # Static and Non-static measurements
      #
      numYRecords  += len(list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_web_cd'] == 'Y'}))
      numNRecords  += len(list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_web_cd'] != 'Y'}))
      
      # Assign other measurements to OWRD
      #
      othrDatesL    = list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_agency_cd'] not in ['USGS', 'OWRD', 'CDWR']})
      for gwDate in sorted(othrDatesL):
         gwInfoD[site_id][gwDate]['lev_agency_cd'] = 'OWRD'
      
      # OWRD period of record of periodic measurements for each site
      #
      siteRecordsL  = sorted(list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_agency_cd'] == 'OWRD'}))
      BeginDate     = ''
      EndDate       = ''
      status        = 'Inactive'
      if len(siteRecordsL) > 0:
         BeginDate     = gwInfoD[site_id][siteRecordsL[0]]['lev_str_dt'][:10]
         EndDate       = gwInfoD[site_id][siteRecordsL[-1]]['lev_str_dt'][:10]
         lev_dt_acy_cd = gwInfoD[site_id][siteRecordsL[-1]]['lev_dt_acy_cd']
         dateFmt = '%Y-%m-%d'
         if lev_dt_acy_cd == 'Y':
            dateFmt = '%Y'
         elif lev_dt_acy_cd == 'M':
            dateFmt = '%Y-%m'
         wlDate = datetime.datetime.strptime(gwInfoD[site_id][siteRecordsL[-1]]['lev_str_dt'][:10], dateFmt)
         wlDate = wlDate.replace(tzinfo=datetime.timezone.utc)
         status = 'Inactive'
         if wlDate >= activeDate:
            status  = 'Active'
      else:
         screen_logger.debug('Site %s has no OWRD periodic or recorder groundwater measurements' % site_id)

      siteInfoD[site_id]['owrd_begin_date']      = BeginDate
      siteInfoD[site_id]['owrd_end_date']        = EndDate
      siteInfoD[site_id]['owrd_status']          = status
      siteInfoD[site_id]['owrd_count']           = len(siteRecordsL)      
      
      # Overall period of record of recorder measurements for each site
      #
      if site_id in rcInfoD:
         siteRecordsL  = sorted(list(rcInfoD[site_id].keys()))
         BeginDate     = rcInfoD[site_id][siteRecordsL[0]]['lev_str_dt'][:10]
         EndDate       = rcInfoD[site_id][siteRecordsL[-1]]['lev_str_dt'][:10]
         lev_dt_acy_cd = rcInfoD[site_id][siteRecordsL[-1]]['lev_dt_acy_cd']
         dateFmt = '%Y-%m-%d'
         if lev_dt_acy_cd == 'Y':
            dateFmt = '%Y'
         elif lev_dt_acy_cd == 'M':
            dateFmt = '%Y-%m'
         wlDate = datetime.datetime.strptime(rcInfoD[site_id][siteRecordsL[-1]]['lev_str_dt'][:10], dateFmt)
         wlDate = wlDate.replace(tzinfo=datetime.timezone.utc)
         status = 'Inactive'
         if wlDate >= activeDate:
            status  = 'Active'

         siteInfoD[site_id]['owrd_rc_status']     = status
         siteInfoD[site_id]['owrd_rc_begin_date'] = BeginDate
         siteInfoD[site_id]['owrd_rc_end_date']   = EndDate
         siteInfoD[site_id]['owrd_rc_count']      = len(rcInfoD[site_id])

         rcRecords                               += len(rcInfoD[site_id])

   activeSitesL     = list({x for x in siteInfoD if siteInfoD[x]['owrd_status'] == 'Active'})
   activeRecordersL = list({x for x in siteInfoD if siteInfoD[x]['owrd_rc_status'] == 'Active'})

             
   # Print information
   #
   ncols    = 150
   messages = []
   messages.append('\n\tProcessed OWRD periodic and recorder measurements')
   messages.append('\t%s' % (ncols * '-'))
   messages.append('\t%-79s %10d' % ('Number of sites in collection file', len(siteInfoD)))
   messages.append('\t%-79s %10d' % ('Number of OWRD sites in collection file', len(owrdSitesL)))
   messages.append('\t%-79s %10d' % ('Number of OWRD sites in collection file NOT retrieved from OWRD database', len(missSitesL)))
   messages.append('\t%-79s %10d' % ('Number of Active sites in collection file measured by the OWRD', len(activeSitesL)))
   messages.append('\t%-79s %10d' % ('Number of OWRD sites in collection file assigned an USGS site number', len(usgsSitesD)))
   messages.append('\t%-79s %10d' % ('Number of of static periodic measurements for OWRD sites in collection file', numYRecords))
   messages.append('\t%-79s %10d' % ('Number of of non-static periodic measurements for OWRD sites in collection file', numNRecords))
   messages.append('\t%-79s %10d' % ('Number of periodic measurements made by USGS', usgsRecords))
   messages.append('\t%-79s %10d' % ('Number of periodic measurements made by OWRD', owrdRecords))
   messages.append('\t%-79s %10d' % ('Number of periodic measurements made by CDWR', cdwrRecords))
   messages.append('\t%-79s %10d' % ('Number of periodic measurements made by other agencies', othrRecords))
   messages.append('\t%-79s %10d' % ('Number of periodic measurements', totalRecords))
   messages.append('\t%-79s %10d' % ('Number of OWRD recorder sites in collection file from OWRD database', len(rcInfoD)))
   messages.append('\t%-79s %10d' % ('Number of Active recorder sites in collection file measured by the OWRD', len(activeRecordersL)))
   messages.append('\t%-79s %10d' % ('Number of recorder measurements', rcRecords))
   messages.append('\t%s' % (ncols * '-'))
   if len(matchSitesL) > 0:
      messages.append('')
      messages.append('\t%s' % 'OWRD periodic sites with OWRD measurements in collection file in OWRD database')
      messages.append('\t%s' % (ncols * '-'))
      fmt = '\t%-20s %-15s %-20s %-35s %10s %15s %15s %10s'
      messages.append(fmt % ('USGS',        'OWRD',        'CDWR', 'Station', 'Periodic', 'Begin', 'End',  'Active'))
      messages.append(fmt % ('Site Number', 'Well Log ID', 'ID',   ' ',       'Counts',   'Date',  'Date', 'Status'))
      messages.append('\t%s' % (ncols * '-'))
      for well_log_id in sorted(matchSitesL):
         site_id = owrdSitesD[well_log_id]
         messages.append(fmt % (siteInfoD[site_id]['site_no'],
                                siteInfoD[site_id]['coop_site_no'],
                                siteInfoD[site_id]['cdwr_id'],
                                siteInfoD[site_id]['station_nm'][:35],
                                siteInfoD[site_id]['owrd_count'],
                                siteInfoD[site_id]['owrd_begin_date'],
                                siteInfoD[site_id]['owrd_end_date'],
                                siteInfoD[site_id]['owrd_status']
                                ))
      messages.append('\t%s' % (ncols * '-'))
   if len(rcInfoD.keys()) > 0:
      messages.append('')
      messages.append('\t%s' % 'OWRD recorder sites with OWRD measurements in collection file in OWRD database')
      messages.append('\t%s' % (ncols * '-'))
      fmt = '\t%-20s %-15s %-20s %-35s %10s %15s %15s %10s'
      messages.append(fmt % ('USGS',        'OWRD',        'CDWR', 'Station', 'Recorder', 'Begin', 'End',  'Active'))
      messages.append(fmt % ('Site Number', 'Well Log ID', 'ID',   ' ',       'Counts',   'Date',  'Date', 'Status'))
      messages.append('\t%s' % (ncols * '-'))
      for site_id in sorted(rcInfoD.keys()):
         messages.append(fmt % (siteInfoD[site_id]['site_no'],
                                siteInfoD[site_id]['coop_site_no'],
                                siteInfoD[site_id]['cdwr_id'],
                                siteInfoD[site_id]['station_nm'][:35],
                                siteInfoD[site_id]['owrd_rc_count'],
                                siteInfoD[site_id]['owrd_rc_begin_date'],
                                siteInfoD[site_id]['owrd_rc_end_date'],
                                siteInfoD[site_id]['owrd_rc_status']
                                ))
      messages.append('\t%s' % (ncols * '-'))
   if len(missSitesL) > 0:
      messages.append('')
      messages.append('\t%s' % 'OWRD periodic sites in collection file NOT retrieved from OWRD database')
      messages.append('\t%s' % (ncols * '-'))
      fmt = '\t%-20s %-20s %-20s %-35s'
      messages.append(fmt % ('USGS',        'OWRD',        'CDWR', 'Station'))
      messages.append(fmt % ('Site Number', 'Well Log ID', 'ID',   ' '))
      messages.append('\t%s' % (ncols * '-'))
      for well_log_id in sorted(missSitesL):
         site_id = owrdSitesD[well_log_id]
         messages.append(fmt % (siteInfoD[site_id]['site_no'],
                                siteInfoD[site_id]['coop_site_no'],
                                siteInfoD[site_id]['cdwr_id'],
                                siteInfoD[site_id]['station_nm'][:35]
                                ))
      messages.append('\t%s' % (ncols * '-'))
   for myCode in sorted(gwCodesD.keys()):
      messages.append('')
      messages.append('\tCode %-70s' % myCode)
      messages.append('\t%s' % (ncols * '-'))
      messages.append('\t%s' % '\n\t'.join(gwCodesD[myCode]))
      messages.append('\t%s' % (ncols * '-'))
   messages.append('\n')

   screen_logger.info('\n'.join(messages))
   file_logger.info('\n'.join(messages))

   return gwInfoD
# =============================================================================

def processCDWR (siteInfoD, mySiteFields, myGwFields):

   gwInfoD      = {}
   rcInfoD      = {}
   
   usgsRecords  = 0
   owrdRecords  = 0
   cdwrRecords  = 0
   othrRecords  = 0
   totalRecords = 0
   rcRecords    = 0

   numYRecords  = 0
   numNRecords  = 0

   gwCodesD     = {}
   
   myCdwrFields = [
                   "_id",
                   "gwe",
                   "wlm_org_name",
                   "wlm_mthd_desc",
                   "wlm_acc_desc",
                   "gse_gwe",
                   "msmt_date",
                   "site_code",
                   "wlm_gse",
                   "wlm_qa_detail",
                   "coop_org_name",
                   "source",
                   "msmt_cmt",
                   "rank site_code",
                   "monitoring_program",
                   "wlm_qa_desc"
                  ]
 
   pst_offset   = 8
   days_offset  = 365
   activeDate   = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_offset)

   # Prepare list of site numbers
   # -------------------------------------------------
   #
   usgsSitesD    = dict({siteInfoD[x]['cdwr_id']:siteInfoD[x]['site_no'] for x in siteInfoD if len(siteInfoD[x]['site_no']) > 0})
   cdwrSitesD    = dict({siteInfoD[x]['cdwr_id']:siteInfoD[x]['site_id'] for x in siteInfoD if len(siteInfoD[x]['cdwr_id']) > 0})
   cdwrSitesL    = list({siteInfoD[x]['cdwr_id'] for x in siteInfoD if len(siteInfoD[x]['cdwr_id']) > 0})
   cdwrStationsL = list({siteInfoD[x]['state_well_nmbr'] for x in siteInfoD if len(siteInfoD[x]['cdwr_id']) > 0 and len(siteInfoD[x]['state_well_nmbr']) > 0})
   cdwrStationsD = dict({siteInfoD[x]['state_well_nmbr']:siteInfoD[x]['site_id'] for x in siteInfoD if len(siteInfoD[x]['cdwr_id']) > 0 and len(siteInfoD[x]['state_well_nmbr']) > 0})
   
   missSitesL    = list(cdwrSitesL)
   missStationsL = list(cdwrStationsL)

   # CDWR periodic service
   # -------------------------------------------------
   #
   tempL  = list(cdwrSitesL)
   nsites = 10
   linesL = []

   while len(tempL) > 0:

      nList = ",".join(list(map(lambda x: "'%s'" % x, tempL[:nsites])))
      del tempL[:nsites]

      # Web request
      #
      # https://data.cnra.ca.gov/api/3/action/datastore_search_sql?sql=SELECT * from "bfa9f262-24a1-45bd-8dc8-138bc8107266" WHERE "site_code" IN ('419980N1215455W001', '419978N1214546W001') ORDER BY "site_code", "msmt_date"
      #
      URL          = 'https://data.cnra.ca.gov/api/3/action/datastore_search_sql?sql=SELECT * from "bfa9f262-24a1-45bd-8dc8-138bc8107266" WHERE "site_code" IN (%s) ORDER BY "site_code", "msmt_date"' % nList
      noparmsDict  = {}
      contentType  = "application/json"
      timeOut      = 1000

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

         # Total records
         #
         numRecords = len(gwJson['result']['records'])

         # Check for failed request
         #
         if numRecords < 1:
            message = "Warning: CWDR sites %s has no waterlevel measurements available" % nList
            screen_logger.info(message)
            continue

         # Parse records
         #
         jsonRecords  = gwJson['result']['records']

         #print(jsonRecords)
   
         # Process groundwater measurements
         # -------------------------------------------------
         #
         for myRecord in jsonRecords:

            # Set record
            #
            gwRecord = {}

            # Set record
            #
            site_code = myRecord['site_code']
            
            # Site ID from collection file
            #
            site_id = cdwrSitesD[site_code]
            
            # Remove site from missing list
            #
            if site_code in missSitesL:
               missSitesL.remove(site_code)
           
            # Set waterlevel
            #
            lev_va             = str(myRecord['gse_gwe'])
            if lev_va == 'None':
               lev_va = ''
            
            gwRecord['lev_va'] = lev_va

            # Set local water-level date information
            #
            lev_dt        = myRecord['msmt_date'][:10]
            lev_tm        = myRecord['msmt_date'][11:]
            lev_tz_cd     = 'PST'
            lev_dt_acy_cd = 'D'
          
            # Set lev_mst to YYYY-MM-DD to identify duplicate measurements
            #
            lev_mst = lev_dt

            if lev_tm in ['00:00:00', '12:00:00']:
               lev_tm     = ''
               lev_tz_cd  = ''
               wlDate     = datetime.datetime.strptime(lev_dt, '%Y-%m-%d')
               lev_str_dt = lev_dt
               wlDate     = wlDate.replace(hour=12)
            elif len(lev_tm) < 1:
               lev_tm     = ''
               lev_tz_cd  = ''
               wlDate     = datetime.datetime.strptime(lev_dt, '%Y-%m-%d')
               lev_str_dt = lev_dt
               wlDate     = wlDate.replace(hour=12)
            else:
               lev_tm        = lev_tm[:5]
               lev_str_dt    = '%s %s' % (lev_dt, lev_tm)
               wlDate        = datetime.datetime.strptime(lev_str_dt, '%Y-%m-%d %H:%M')
               wlDate        = wlDate + datetime.timedelta(hours=pst_offset)
               lev_dt_acy_cd = 'm'
           
            # Convert to UTC time zone
            #
            wlDate     = wlDate.replace(tzinfo=datetime.timezone.utc)
            lev_dtm    = wlDate.strftime("%Y-%m-%d %H:%M %Z")
      
            gwRecord['lev_dt']        = lev_dt
            gwRecord['lev_tm']        = lev_tm
            gwRecord['lev_tz_cd']     = lev_tz_cd
            gwRecord['lev_dt_acy_cd'] = lev_dt_acy_cd
            gwRecord['lev_str_dt']    = lev_str_dt
            gwRecord['lev_dtm']       = lev_dtm
          
            # Set measuring accuracy
            #
            lev_acy_cd = myRecord['wlm_acc_desc']
            myColumn   = 'lev_acy_cd'
            if myColumn not in gwCodesD:
               gwCodesD[myColumn] = []
            if str(lev_acy_cd) not in gwCodesD[myColumn]:
               gwCodesD[myColumn].append(str(lev_acy_cd))
            
            if lev_acy_cd == "Water level accuracy to nearest foot":
               lev_acy_cd = '0'
            elif lev_acy_cd == "Water level accuracy to nearest tenth of a foot":
               lev_acy_cd = '1'
            elif lev_acy_cd == "0.1 Ft":
               lev_acy_cd = '1'
            elif lev_acy_cd == "Water level accuracy to nearest hundredth of a foot":
               lev_acy_cd = '2'
            elif lev_acy_cd == "0.01 Ft":
               lev_acy_cd = '2'
            elif lev_acy_cd == "Water level accuracy to nearest thousandth of a foot":
               lev_acy_cd = 'U'
            elif lev_acy_cd == "Water level accuracy is unknown":
               lev_acy_cd = 'U'
            elif lev_acy_cd == "Unknown":
               lev_acy_cd = 'U'
            elif lev_acy_cd is None:
               lev_acy_cd = 'U'
            else:
               screen_logger.info('CDWR site %s [on %s]: Measuring accuracy "%s" needs to be assigned (currently set to U for Unknown' % (site_id, lev_str_dt, lev_acy_cd))
               screen_logger.info(myRecord)
               lev_acy_cd = 'U'
            
            gwRecord['lev_acy_cd'] = lev_acy_cd
           
            # Set lev_status_cd
            #
            lev_status_cd = myRecord['wlm_qa_detail']
            myColumn   = 'lev_status_cd'
            if myColumn not in gwCodesD:
               gwCodesD[myColumn] = []
            if str(lev_status_cd) not in gwCodesD[myColumn]:
               gwCodesD[myColumn].append(str(lev_status_cd))

            if lev_status_cd is None:
               lev_status_cd = ''
            elif lev_status_cd in ["Good data", "Good quality edited data"]:
               lev_status_cd = ""
            elif lev_status_cd == "Recharge or surface water effects near well":
               lev_status_cd = "J"
            elif lev_status_cd == "Casing leaking or wet":
               lev_status_cd = "K"
            elif lev_status_cd == "Measurement Discontinued":
               lev_status_cd = "N"
            elif lev_status_cd == "Can't get tape in casing":
               lev_status_cd = "O"
            elif lev_status_cd == "Pumping":
               lev_status_cd = "P"
            elif lev_status_cd == "Pumped recently":
               lev_status_cd = "R"
            elif lev_status_cd == "Nearby pump operating":
               lev_status_cd = "S"
            elif lev_status_cd == "Oil or foreign substance in casing":
               lev_status_cd = "V"
            elif lev_status_cd == "Well has been destroyed":
               lev_status_cd = "W"
            elif lev_status_cd in ["Temporarily inaccessible",
                                    "Pump house locked",
                                    "Special/Other",
                                    "Tape hung up",
                                    "Other",
                                    "Unable to locate well",
                                    "Caved or deepened",
                                    "Acoustical sounder",
                                    "Unknown Measurement Quality"]:
               lev_status_cd = "Z"
            else:
               screen_logger.info('CDWR site %s [on %s]: Measurement status "%s" needs to be assigned (currently set to U for Reported' % (site_id, lev_str_dt, lev_status_cd))
               lev_status_cd = 'U'
               
            gwRecord['lev_status_cd']  = lev_status_cd
            
            # Set measuring method
            #
            lev_meth_cd = myRecord['wlm_mthd_desc']
            myColumn   = 'lev_meth_cd'
            if myColumn not in gwCodesD:
               gwCodesD[myColumn] = []
            if str(lev_meth_cd) not in gwCodesD[myColumn]:
               gwCodesD[myColumn].append(str(lev_meth_cd))
            
            if lev_meth_cd == "Electronic pressure transducer":
               lev_meth_cd = "F"
            elif lev_meth_cd == "Acoustic or sonic sounder":
               lev_meth_cd = "P"
            elif lev_meth_cd == "Steel tape measurement":
               lev_meth_cd = "S"
            elif lev_meth_cd == "Electric sounder measurement":
               lev_meth_cd = "T"
            elif lev_meth_cd == "Other":
               lev_meth_cd = "Z"
            elif lev_meth_cd == "Airline measurement, pressure gage, or manometer":
               lev_meth_cd = "A"
            # Depending on accuracy, airline is to nearest foot, pressure gage and manometer (find out accuracy)
            #  Will determine the method
            elif lev_meth_cd == "Unknown":
               lev_meth_cd = "R"
            elif lev_meth_cd is None:
               lev_meth_cd = "R"
            else:
               screen_logger.info('CDWR site %s [on %s]: Measuring method "%s" [wlm_mthd_desc] needs to be assigned (currently set to R' % (site_id, lev_str_dt, lev_meth_cd))
               lev_meth_cd = "R"

            gwRecord['lev_meth_cd'] = lev_meth_cd
           
            # Set measuring agency [coop_org_name]
            #
            lev_agency_cd = myRecord['coop_org_name']
            myColumn   = 'lev_agency_cd'
            if myColumn not in gwCodesD:
               gwCodesD[myColumn] = []
            if str(lev_agency_cd) not in gwCodesD[myColumn]:
               gwCodesD[myColumn].append(str(lev_agency_cd))
            
            if lev_agency_cd == "Department of Water Resources":
               lev_agency_cd = "CDWR"
            elif lev_agency_cd == "United States Geological Survey":
               lev_agency_cd = "USGS"
            elif lev_agency_cd == "Bureau of Reclamation":
               lev_agency_cd = "USBR"
            elif lev_agency_cd == "Tulelake Irrigation District" or "Tulelake Irrigation District GSA":
               lev_agency_cd = "CA049 Tulelake Irrigation District"
            elif lev_agency_cd == "Tulelake Irrigation District GSA":
               lev_agency_cd = "CA049 Tulelake Irrigation District"
            else:
               screen_logger.info('CDWR site %s: Measuring agency "%s" [coop_org_name] needs to be assigned (currently set to CDWR' % (site_id, lev_agency_cd))
               lev_acy_cd = 'CDWR'
               
            gwRecord['lev_agency_cd']  = lev_agency_cd
          
            # Set source agency [wlm_org_name]
            #
            lev_src_cd = myRecord['wlm_org_name']
            myColumn   = 'lev_src_cd'
            if myColumn not in gwCodesD:
               gwCodesD[myColumn] = []
            if str(lev_src_cd) not in gwCodesD[myColumn]:
               gwCodesD[myColumn].append(str(lev_src_cd))
            
            if lev_src_cd == "Department of Water Resources":
               lev_src_cd = "CDWR"
            elif lev_src_cd == "Bureau of Reclamation":
               lev_src_cd = "USBR"
            elif lev_src_cd == "Tulelake Irrigation District" or "Tulelake Irrigation District GSA":
               lev_src_cd = "CA049 Tulelake Irrigation District"
            elif lev_src_cd == "Tulelake Irrigation District GSA":
               lev_src_cd = "CA049 Tulelake Irrigation District"
            else:
               screen_logger.info('CDWR site %s: Measuring source agency "%s" [wlm_org_name] needs to be assigned (currently set to CDWR' % (site_id, lev_src_cd))
               lev_src_cd = 'CDWR'

            # Set source agency if measuring agency is USGS
            #
            if lev_agency_cd == "USGS":
               lev_src_cd = "USGS"
               
            if lev_src_cd == lev_agency_cd:
               lev_src_cd = 'S'
            else:
               #screen_logger.info('CDWR site %s: Measuring agency "%s" [coop_org_name] Measuring agency "%s" [coop_org_name]' % (site_id, lev_agency_cd, lev_src_cd))
               lev_src_cd = 'A'
               
            gwRecord['lev_src_cd'] = lev_src_cd
           
            # Set lev_web_cd
            #
            lev_web_cd = 'N'
            if len(lev_va) > 0 and len(lev_status_cd) < 1:
               lev_web_cd = 'Y'
               
            gwRecord['lev_web_cd'] = lev_web_cd
           
            # Set remarks
            #
            lev_rmk_tx = myRecord['msmt_cmt']
            lev_rmk_tx = myRecord['source']
            if lev_rmk_tx is None:
               lev_rmk_tx = ''
            gwRecord['lev_rmk_tx'] = lev_rmk_tx

            # New site
            #
            if site_id not in gwInfoD:
               
               gwInfoD[site_id] = {}

            # New waterlevel record for site
            #
            if lev_mst not in gwInfoD[site_id].keys():

               gwInfoD[site_id][lev_mst] = {}

            # Prepare values
            #
            for myColumn in myGwFields:
               if myColumn in mySiteFields:
                  gwInfoD[site_id][lev_mst][myColumn] = siteInfoD[site_id][myColumn]
               else:
                  gwInfoD[site_id][lev_mst][myColumn] = gwRecord[myColumn]

                  
   # CDWR recorder service
   # -------------------------------------------------
   #
   tempL  = list(cdwrStationsL)
   nsites = 10
   linesL = []

   while len(tempL) > 0:

      nList = ",".join(list(map(lambda x: "'%s'" % x, tempL[:nsites])))
      del tempL[:nsites]

      # Web request
      #
      # https://data.cnra.ca.gov/api/3/action/datastore_search_sql?sql=SELECT * from "84e02633-00ca-47e8-97ec-c0093313ddcd" WHERE "STATION" IN ('46N05E21M001M', '46N05E22D001M')
      #
      URL          = 'https://data.cnra.ca.gov/api/3/action/datastore_search_sql?sql=SELECT * from "84e02633-00ca-47e8-97ec-c0093313ddcd" WHERE "STATION" IN (%s)' % nList
      noparmsDict  = {}
      contentType  = "application/json"
      timeOut      = 1000

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

         # Total records
         #
         numRecords = len(gwJson['result']['records'])

         # Check for failed request
         #
         if numRecords < 1:
            message = "Warning: CWDR sites %s has no waterlevel measurements available" % nList
            screen_logger.info(message)
            continue

         # Parse records
         #
         jsonRecords  = gwJson['result']['records']

         #print(jsonRecords)
   
         # Process groundwater measurements
         # -------------------------------------------------
         #
         for myRecord in jsonRecords:

            # Set record
            #
            gwRecord = {}

            # Set record
            #
            station = myRecord['STATION']
            
            # Site ID from collection file
            #
            site_id = cdwrStationsD[station]
            
            # Remove site from missing list
            #
            if station in missStationsL:
               missStationsL.remove(station)
     
            # Set water-level date information
            #
            lev_str_dt    = myRecord['MSMT_DATE'][:10]
            lev_dt        = lev_str_dt[:10]
            lev_tm        = '12:00'
            lev_tz_cd     = 'PST'
            lev_dt_acy_cd = 'D'
            lev_dtm       = lev_str_dt
   
            # Set measuring agency information
            #
            lev_agency_cd = 'CDWR'
         
            # Set record
            #
            gwRecord['lev_dt']        = lev_str_dt[:10]
            gwRecord['lev_tm']        = lev_str_dt[:-5]
            gwRecord['lev_tz_cd']     = lev_tz_cd
            gwRecord['lev_dt_acy_cd'] = lev_dt_acy_cd
            gwRecord['lev_str_dt']    = lev_str_dt
            gwRecord['lev_dtm']       = lev_dtm
            gwRecord['lev_agency_cd'] = lev_dtm
              
            # Set site_id
            #
            site_id = station
            if station in cdwrStationsD:
               site_id = cdwrStationsD[station]
         
            # Set site information
            #
            if site_id not in rcInfoD:
               rcInfoD[site_id] = {}
              
            # Set site information
            #
            if lev_dtm not in rcInfoD[site_id]:
               rcInfoD[site_id][lev_dtm] = {}
    
            # Prepare values
            #
            for myColumn in gwRecord.keys():
               rcInfoD[site_id][lev_dtm][myColumn] = gwRecord[myColumn]
               

   # Prepare set of sites
   #
   cdwrSet        = set(cdwrSitesL)
   missingSet     = set(missSitesL)
   matchSitesL    = list(cdwrSet.difference(missingSet))
   
   # Overall period of record of all measurements for each site and counts
   #
   for site_code in sorted(matchSitesL):
      
      site_id = cdwrSitesD[site_code]
      
      # Counts
      #
      totalRecords += len(gwInfoD[site_id])
      usgsRecords  += len(list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_agency_cd'] == 'USGS'}))
      owrdRecords  += len(list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_agency_cd'] == 'OWRD'}))
      cdwrRecords  += len(list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_agency_cd'] == 'CDWR'}))
      othrRecords  += len(list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_agency_cd'] not in ['USGS', 'OWRD', 'CDWR']}))
      
      # Static and Non-static measurements
      #
      numYRecords  += len(list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_web_cd'] == 'Y'}))
      numNRecords  += len(list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_web_cd'] != 'Y'}))
      
      # Assign other measurements to CDWR
      #
      othrDatesL    = list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_agency_cd'] not in ['USGS', 'OWRD', 'CDWR']})
      for gwDate in sorted(othrDatesL):
         gwInfoD[site_id][gwDate]['lev_agency_cd'] = 'CDWR'
      
      # CDWR period of record of periodic measurements for each site
      #
      siteRecordsL  = sorted(list({x for x in gwInfoD[site_id] if gwInfoD[site_id][x]['lev_agency_cd'] == 'CDWR'}))
      BeginDate     = ''
      EndDate       = ''
      status        = 'Inactive'
      if len(siteRecordsL) > 0:
         BeginDate     = gwInfoD[site_id][siteRecordsL[0]]['lev_str_dt'][:10]
         EndDate       = gwInfoD[site_id][siteRecordsL[-1]]['lev_str_dt'][:10]
         lev_dt_acy_cd = gwInfoD[site_id][siteRecordsL[-1]]['lev_dt_acy_cd']
         dateFmt = '%Y-%m-%d'
         if lev_dt_acy_cd == 'Y':
            dateFmt = '%Y'
         elif lev_dt_acy_cd == 'M':
            dateFmt = '%Y-%m'
         wlDate = datetime.datetime.strptime(gwInfoD[site_id][siteRecordsL[-1]]['lev_str_dt'][:10], dateFmt)
         wlDate = wlDate.replace(tzinfo=datetime.timezone.utc)
         status = 'Inactive'
         if wlDate >= activeDate:
            status  = 'Active'
      else:
         screen_logger.debug('Site %s has no CDWR periodic or recorder groundwater measurements' % site_id)

      siteInfoD[site_id]['cdwr_begin_date']      = BeginDate
      siteInfoD[site_id]['cdwr_end_date']        = EndDate
      siteInfoD[site_id]['cdwr_status']          = status
      siteInfoD[site_id]['cdwr_count']           = len(siteRecordsL)      
      
      # CDWR period of record of recorder measurements for each site
      #
      if site_id in rcInfoD:
         siteRecordsL  = sorted(list(rcInfoD[site_id].keys()))
         BeginDate     = rcInfoD[site_id][siteRecordsL[0]]['lev_str_dt'][:10]
         EndDate       = rcInfoD[site_id][siteRecordsL[-1]]['lev_str_dt'][:10]
         lev_dt_acy_cd = rcInfoD[site_id][siteRecordsL[-1]]['lev_dt_acy_cd']
         dateFmt = '%Y-%m-%d'
         if lev_dt_acy_cd == 'Y':
            dateFmt = '%Y'
         elif lev_dt_acy_cd == 'M':
            dateFmt = '%Y-%m'
         wlDate = datetime.datetime.strptime(rcInfoD[site_id][siteRecordsL[-1]]['lev_str_dt'][:10], dateFmt)
         wlDate = wlDate.replace(tzinfo=datetime.timezone.utc)
         status = 'Inactive'
         if wlDate >= activeDate:
            status  = 'Active'

         siteInfoD[site_id]['cdwr_rc_status']     = status
         siteInfoD[site_id]['cdwr_rc_begin_date'] = BeginDate
         siteInfoD[site_id]['cdwr_rc_end_date']   = EndDate
         siteInfoD[site_id]['cdwr_rc_count']      = len(rcInfoD[site_id])

         rcRecords                               += len(rcInfoD[site_id])

   activeSitesL      = list({x for x in siteInfoD if siteInfoD[x]['cdwr_status'] == 'Active'})
   activeRecordersL  = list({x for x in siteInfoD if siteInfoD[x]['cdwr_rc_status'] == 'Active'})
            
   # Print information
   #
   ncols    = 150
   messages = []
   messages.append('\n\tProcessed CDWR periodic and recorder measurements')
   messages.append('\t%s' % (ncols * '-'))
   messages.append('\t%-79s %10d' % ('Number of sites in collection file', len(siteInfoD)))
   messages.append('\t%-79s %10d' % ('Number of CDWR sites in collection file', len(cdwrSet)))
   messages.append('\t%-79s %10d' % ('Number of CDWR sites in collection file NOT retrieved from CDWR database', len(missSitesL)))
   messages.append('\t%-79s %10d' % ('Number of Active sites in collection file measured by the CDWR', len(activeSitesL)))
   messages.append('\t%-79s %10d' % ('Number of CDWR sites in collection file assigned an USGS site number', len(usgsSitesD)))
   messages.append('\t%-79s %10d' % ('Number of of static periodic measurements', numYRecords))
   messages.append('\t%-79s %10d' % ('Number of of non-static periodic measurements', numNRecords))
   messages.append('\t%-79s %10d' % ('Number of USGS periodic measurements', usgsRecords))
   messages.append('\t%-79s %10d' % ('Number of OWRD periodic measurements', owrdRecords))
   messages.append('\t%-79s %10d' % ('Number of CDWR periodic measurements', cdwrRecords))
   messages.append('\t%-79s %10d' % ('Number of periodic measurements made by other agencies', othrRecords))
   messages.append('\t%-79s %10d' % ('Number of periodic measurements', totalRecords))
   messages.append('\t%-79s %10d' % ('Number of CDWR recorder sites in collection file from CDWR database', len(rcInfoD)))
   messages.append('\t%-79s %10d' % ('Number of Active recorder sites in collection file measured by the CDWR', len(activeRecordersL)))
   messages.append('\t%-79s %10d' % ('Number of recorder measurements', rcRecords))
   messages.append('\t%s' % (ncols * '-'))
   if len(matchSitesL) > 0:
      messages.append('')
      messages.append('\t%s' % 'CDWR periodic sites with CDWR measurements in collection file in CDWR database')
      messages.append('\t%s' % (ncols * '-'))
      fmt = '\t%-20s %-15s %-20s %-35s %10s %15s %15s %10s'
      messages.append(fmt % ('USGS',        'OWRD',        'CDWR', 'Station', 'Periodic', 'Begin', 'End',  'Active'))
      messages.append(fmt % ('Site Number', 'Well Log ID', 'ID',   ' ',       'Counts',   'Date',  'Date', 'Status'))
      messages.append('\t%s' % (ncols * '-'))
      for cdwr_id in sorted(matchSitesL):
         site_id = cdwrSitesD[cdwr_id]
         messages.append(fmt % (siteInfoD[site_id]['site_no'],
                                siteInfoD[site_id]['coop_site_no'],
                                siteInfoD[site_id]['cdwr_id'],
                                siteInfoD[site_id]['station_nm'][:35],
                                siteInfoD[site_id]['cdwr_count'],
                                siteInfoD[site_id]['cdwr_begin_date'],
                                siteInfoD[site_id]['cdwr_end_date'],
                                siteInfoD[site_id]['cdwr_status']
                                ))
      messages.append('\t%s' % (ncols * '-'))
   if len(rcInfoD.keys()) > 0:
      messages.append('')
      messages.append('\t%s' % 'CDWR recorder sites with CDWR measurements in collection file in CDWR database')
      messages.append('\t%s' % (ncols * '-'))
      fmt = '\t%-20s %-15s %-20s %-35s %10s %15s %15s %10s'
      messages.append(fmt % ('USGS',        'OWRD',        'CDWR', 'Station', 'Recorder', 'Begin', 'End',  'Active'))
      messages.append(fmt % ('Site Number', 'Well Log ID', 'ID',   ' ',       'Counts',   'Date',  'Date', 'Status'))
      messages.append('\t%s' % (ncols * '-'))
      for site_id in sorted(rcInfoD.keys()):
         messages.append(fmt % (siteInfoD[site_id]['site_no'],
                                siteInfoD[site_id]['coop_site_no'],
                                siteInfoD[site_id]['cdwr_id'],
                                siteInfoD[site_id]['station_nm'][:35],
                                siteInfoD[site_id]['cdwr_rc_count'],
                                siteInfoD[site_id]['cdwr_rc_begin_date'],
                                siteInfoD[site_id]['cdwr_rc_end_date'],
                                siteInfoD[site_id]['cdwr_rc_status']
                                ))
      messages.append('\t%s' % (ncols * '-'))
   if len(missSitesL) > 0:
      messages.append('')
      messages.append('\t%s' % 'CDWR periodic sites in collection file NOT retrieved from CDWR database')
      messages.append('\t%s' % (ncols * '-'))
      fmt = '\t%-20s %-20s %-20s %-35s'
      messages.append(fmt % ('USGS',        'OWRD',        'CDWR', 'Station'))
      messages.append(fmt % ('Site Number', 'Well Log ID', 'ID',   ' '))
      messages.append('\t%s' % (ncols * '-'))
      for cdwr_id in sorted(missSitesL):
         site_id = cdwrSitesD[cdwr_id]
         messages.append(fmt % (siteInfoD[site_id]['site_no'],
                                siteInfoD[site_id]['coop_site_no'],
                                siteInfoD[site_id]['cdwr_id'],
                                siteInfoD[site_id]['station_nm'][:35]
                                ))
      messages.append('\t%s' % (ncols * '-'))
   for myCode in sorted(gwCodesD.keys()):
      messages.append('')
      messages.append('\tCode %-70s' % myCode)
      messages.append('\t%s' % (ncols * '-'))
      messages.append('\t%s' % '\n\t'.join(gwCodesD[myCode]))
      messages.append('\t%s' % (ncols * '-'))
   messages.append('\n')

   screen_logger.info('\n'.join(messages))
   file_logger.info('\n'.join(messages))

   return gwInfoD
# =============================================================================
def LoggingOutput (siteInfoD, ColumnsL, FormatsL):

   ncols        = 400
   
   usgsRecords  = 0
   owrdRecords  = 0
   cdwrRecords  = 0
   totalRecords = 0

   localDate    = datetime.datetime.now().strftime("%B %d, %Y")

   # Print summary file information
   #
   outputL = []
   outputL.append("## Groundwater Site Summary")
   outputL.append("##")
   outputL.append("## Recorded on %-30s" % localDate)
   outputL.append("##")

   outputL.append('%s' % "\t".join(ColumnsL))
   outputL.append('%s' % "\t".join(list(map(lambda x: x[1:], FormatsL))))

   # Print information
   #
   messages = []
   message  = "Groundwater Site Summary Information"
   fmt      = "%" + str(int(ncols/2-len(message)/2)) + "s%s"
   messages.append(fmt % (' ', message))
   messages.append("=" * ncols)
   message  = "Recorded on %s" % localDate
   fmt      = "%" + str(int(ncols/2-len(message)/2)) + "s%s"
   messages.append(fmt % (' ', message))
   messages.append("-" * ncols)

   headLine = []
   for i in range(len(ColumnsL)):
      myColumn = FormatsL[i] % ColumnsL[i]
      headLine.append(myColumn)
                       
   messages.append("   ".join(headLine))

   messages.append("-" * ncols)
          
   # Print information
   #
   for site_id in sorted(siteInfoD.keys()):
      
      headLine = []
      for i in range(len(ColumnsL)):
         if siteInfoD[site_id][ColumnsL[i]] is None:
            siteInfoD[site_id][ColumnsL[i]] = ''
         elif str(siteInfoD[site_id][ColumnsL[i]]) == '0':
            siteInfoD[site_id][ColumnsL[i]] = ''
            
         myValue = FormatsL[i] % str(siteInfoD[site_id][ColumnsL[i]])
         headLine.append(myValue)

      if isinstance(siteInfoD[site_id]['usgs_count'], int):
         usgsRecords  += int(siteInfoD[site_id]['usgs_count'])
      if isinstance(siteInfoD[site_id]['owrd_count'], int):
         owrdRecords  += int(siteInfoD[site_id]['owrd_count'])
      if isinstance(siteInfoD[site_id]['cdwr_count'], int):
         cdwrRecords  += int(siteInfoD[site_id]['cdwr_count'])
      
      messages.append("   ".join(headLine))

      outputL.append("\t".join(list(map(lambda x: '%s' % str(siteInfoD[site_id][x]), ColumnsL))))

   totalRecords = usgsRecords + owrdRecords + cdwrRecords
      
   # Print information
   #
   messages.append("-" * ncols)
   
   file_logger.info("\n".join(messages))
             
   # Print information
   #
   ncols    = 85
   messages = []
   messages.append('') 
   messages.append('')
   messages.append('\n\tProcessed periodic measurements output to the waterlevel file')
   messages.append('\t%s' % (ncols * '-'))
   messages.append('\t%-70s %10d' % ('Number of sites with periodic measurements', len(siteInfoD)))
   messages.append('\t%-70s %10d' % ('Number of USGS periodic measurements', usgsRecords))
   messages.append('\t%-70s %10d' % ('Number of OWRD periodic measurements', owrdRecords))
   messages.append('\t%-70s %10d' % ('Number of CDWR periodic measurements', cdwrRecords))
   messages.append('\t%-70s %10d' % ('Number of periodic measurements', totalRecords))
   messages.append('\t%s' % (ncols * '-'))
   messages.append('') 
   messages.append('')
   
   screen_logger.info("\n".join(messages))
   file_logger.info("\n".join(messages))

   # Print site summary file
   #
   output_file = 'site_summary.txt'
   if os.path.isfile(output_file):
      os.remove(output_file)

   # Output records
   #
   with open(output_file,'w') as f:
      f.write('\n'.join(outputL))
            
   return
# =============================================================================

# ----------------------------------------------------------------------
# -- Main program
# ----------------------------------------------------------------------

# Initialize arguments
#
siteInfoD        = {}
usgsInfoD        = {}
owrdInfoD        = {}
cdwrInfoD        = {}

usgsRecordsD     = {}
owrdRecordsD     = {}
cdwrRecordsD     = {}
   
collection_file  = "data/collection.txt"

usgsOnly         = False
owrdOnly         = False
cdwrOnly         = False

debug            = False
debugLevel       = None

keepUSGS         = True

# Set arguments
#
parser = argparse.ArgumentParser(prog=program)

parser.add_argument("--usage", help="Provide usage",
                    type=str)
 
parser.add_argument("-sites", "--sites",
                    help="Name of collection file listing sites",
                    required = True,
                    type=str)
 
parser.add_argument("-output", "--output",
                    help="Name of output file containing processed waterlevel measurements",
                    required = True,
                    type=str)
 
parser.add_argument("-usgs", "--usgs",
                    help="Process only USGS measurement record",
                    action="store_true")
 
parser.add_argument("-owrd", "--owrd",
                    help="Process only OWRD measurement record",
                    action="store_true")
 
parser.add_argument("-cdwr", "--cdwr",
                    help="Process only CDWR measurement record",
                    action="store_true")
 
parser.add_argument("-owrd_gw", "--owrd_gw",
                    help="Provide a filename of OWRD waterlevel file for periodic sites in text format",
                    required = True,
                    type=str)
 
parser.add_argument("-owrd_rc", "--owrd_rc",
                    help="Provide a filename of OWRD waterlevel file for recorder sites in text format",
                    required = True,
                    type=str)
 
parser.add_argument("-keepOWRD", "--keepOwrd",
                    help="Keep OWRD records over USGS matching records",
                    action="store_true")
 
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

if args.usgs:
   usgsOnly = True

if args.owrd:
   owrdOnly = True

if args.cdwr:
   cdwrOnly = True

if usgsOnly is False and owrdOnly is False and cdwrOnly is False:
   usgsOnly = True
   owrdOnly = True
   cdwrOnly = True

if args.owrd_gw:
   owrd_gw_file = args.owrd_gw
   if not os.path.isfile(owrd_gw_file):
      message  = "File listing waterlevel measurements for periodic sites %s does not exist" % owrd_gw_file
      errorMessage(message)

if args.owrd_rc:
   owrd_rc_file = args.owrd_rc
   if not os.path.isfile(owrd_rc_file):
      message  = "File listing waterlevel measurements for recorder sites %s does not exist" % owrd_rc_file
      errorMessage(message)

if args.debug:

   screen_logger.setLevel(logging.DEBUG)

# Read collection file
# -------------------------------------------------
#
mySiteFields = [
                "site_id",
                "agency_cd",
                "site_no",
                "coop_site_no",
                "cdwr_id",
                "state_well_nmbr",
                "station_nm",
                "gw_agency_cd",
                "gw_begin_date",
                "gw_end_date",
                "gw_status",
                "gw_count",
                "rc_agency_cd",
                "rc_begin_date",
                "rc_end_date",
                "rc_status",
                "rc_count",
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
mySiteFormat = [
                "%20s", # site_id
                "%10s", # agency_cd
                "%20s", # site_no
                "%15s", # coop_site_no
                "%20s", # cdwr_id
                "%20s", # state_well_nmbr
                "%30s", # station_nm
                "%20s", # gw_agency_cd
                "%10s", # gw_begin_date
                "%10s", # gw_end_date
                "%12s", # gw_status
                "%10s", # gw_count
                "%20s", # rc_agency_cd
                "%10s", # rc_begin_date
                "%10s", # rc_end_date
                "%12s", # rc_status
                "%10s", # rc_count
                "%10s", # usgs_begin_date
                "%10s", # usgs_end_date
                "%12s", # usgs_status
                "%10s", # usgs_count
                "%10s", # usgs_rc_begin_date
                "%10s", # usgs_rc_end_date
                "%12s", # usgs_rc_status
                "%10s", # usgs_rc_count
                "%10s", # owrd_begin_date
                "%10s", # owrd_end_date
                "%12s", # owrd_status
                "%10s", # owrd_count
                "%10s", # owrd_rc_begin_date
                "%10s", # owrd_rc_end_date
                "%12s", # owrd_rc_status
                "%10s", # owrd_rc_count
                "%10s", # cdwr_begin_date
                "%10s", # cdwr_end_date
                "%12s", # cdwr_status
                "%10s", # cdwr_count
                "%10s", # cdwr_rc_begin_date
                "%10s", # cdwr_rc_end_date
                "%12s", # cdwr_rc_status
                "%10s"  # cdwr_rc_count
               ]


# Process collection or recorder file
# -------------------------------------------------
#
siteInfoD = processCollectionSites(collection_file, mySiteFields)


# Prepare USGS records
# -------------------------------------------------
#
myGwFields  = [
               "site_id",
               "site_no",
               "agency_cd",
               "coop_site_no",
               "cdwr_id",
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
               "lev_web_cd"
              ]

if usgsOnly:
   usgsRecordsD = processUSGS(siteInfoD, mySiteFields, myGwFields)


# Prepare OWRD records
# -------------------------------------------------
#
if owrdOnly:
   owrdRecordsD = processOWRD(siteInfoD, mySiteFields, myGwFields, owrd_gw_file, owrd_rc_file)


# Prepare CDWR records
# -------------------------------------------------
#
if cdwrOnly:
   cdwrRecordsD = processCDWR(siteInfoD, mySiteFields, myGwFields)

   
# Prepare output
# -------------------------------------------------
#
ncols         = 350

siteCount     = 0

totalUSGS     = 0
totalOWRD     = 0
totalCDWR     = 0

totalY        = 0
totalN        = 0

usgsDups      = 0
owrdDups      = 0
cdwrDups      = 0

localDate     = datetime.datetime.now().strftime("%B %d, %Y")
pst_offset    = 8
days_offset   = 365
activeDate    = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_offset)

# Print header information
#
outputL = []
outputL.append("## Groundwater Waterlevel Information")
outputL.append("##")
outputL.append("## Recorded on %30s" % localDate)
outputL.append("##")

outputL.append("\t".join(myGwFields))

# Print waterlevel information
#
for site_id in sorted(siteInfoD.keys()):

   gwInfoD       = {}

   duplUsgsL  = []
   duplOwrdL  = []
   duplCdwrL  = []

   yRecords   = 0
   nRecords   = 0

   # Build common date list for USGS, OWRD, and CDWR records
   #
   usgsRecordsL = []
   if site_id in usgsRecordsD:
      usgsRecordsL = list(usgsRecordsD[site_id].keys())
   owrdRecordsL = []
   if site_id in owrdRecordsD:
      owrdRecordsL = list(owrdRecordsD[site_id].keys())
   cdwrRecordsL = []
   if site_id in cdwrRecordsD:
      cdwrRecordsL = list(cdwrRecordsD[site_id].keys())

   if len(usgsRecordsL) > 0 or len(owrdRecordsL) > 0 or len(cdwrRecordsL) > 0:

       siteCount += 1

       # Add USGS records
       #
       if len(usgsRecordsL) > 0:
          uniqueUsgs = dict({x:usgsRecordsD[site_id][x] for x in usgsRecordsL})
          gwInfoD.update(uniqueUsgs)
             
       # Insert OWRD records if unique on lev_dtm using YYYY-MM-DD portion only
       #
       if len(owrdRecordsL) > 0:
          owrdSet = set(owrdRecordsL)

          # Exisiting USGS records
          #
          if len(gwInfoD) > 0:
             gwDateSet = set(gwInfoD.keys())
             onlyOwrdL = list(owrdSet.difference(gwDateSet))
             duplOwrdL = list(owrdSet.intersection(gwDateSet))
             
             # Insert unique OWRD records with USGS records
             #
             if len(onlyOwrdL) > 0:
                uniqueOwrdD = dict({x:owrdRecordsD[site_id][x] for x in onlyOwrdL})
                gwInfoD.update(uniqueOwrdD)

          # No exisiting USGS records
          #
          else:
             uniqueOwrd = dict({x:owrdRecordsD[site_id][x] for x in owrdRecordsL})
             gwInfoD.update(uniqueOwrd)
            
       # Insert CDWR records if unique on lev_dtm using YYYY-MM-DD portion only
       #
       if len(cdwrRecordsL) > 0:
          cdwrSet = set(cdwrRecordsL)
          
          # Exisiting USGS and OWRD records
          #
          if len(gwInfoD) > 0:
             gwDateSet = set(gwInfoD.keys())
             onlyCdwrL = list(cdwrSet.difference(gwDateSet))
             duplCdwrL = list(cdwrSet.intersection(gwDateSet))
             
             # Insert unique CDWR records with USGS and OWRD records
             #
             if len(onlyCdwrL) > 0:
                uniqueCdwrD = dict({x:cdwrRecordsD[site_id][x] for x in onlyCdwrL})
                gwInfoD.update(uniqueCdwrD)

          # No exisiting USGS and OWRD records
          #
          else:
             uniqueCdwr = dict({x:cdwrRecordsD[site_id][x] for x in cdwrRecordsL})
             gwInfoD.update(uniqueCdwr)

       # Site lists for measurements by each agency
       #
       usgsRecordsL = sorted(list({x for x in gwInfoD if gwInfoD[x]['lev_agency_cd'] == 'USGS'}))
       owrdRecordsL = sorted(list({x for x in gwInfoD if gwInfoD[x]['lev_agency_cd'] == 'OWRD'}))
       cdwrRecordsL = sorted(list({x for x in gwInfoD if gwInfoD[x]['lev_agency_cd'] == 'CDWR'}))
       siteRecordsL = sorted(list(gwInfoD.keys()))
    
       # Overall period of record for periodic measurements for all agencies
       #
       siteInfoD[site_id]['gw_agency_cd']    = []
       siteInfoD[site_id]['gw_status']       = 'Inactive'
       siteInfoD[site_id]['gw_begin_date']   = gwInfoD[siteRecordsL[0]]['lev_str_dt'][:10]
       siteInfoD[site_id]['gw_end_date']     = gwInfoD[siteRecordsL[-1]]['lev_str_dt'][:10]
       lev_dt_acy_cd                         = gwInfoD[siteRecordsL[-1]]['lev_dt_acy_cd']
       fmt = '%Y-%m-%d'
       if lev_dt_acy_cd == 'Y':
          fmt = '%Y'
       elif lev_dt_acy_cd == 'M':
          fmt = '%Y-%m'
       wlDate = datetime.datetime.strptime(siteInfoD[site_id]['gw_end_date'], fmt)
       wlDate = wlDate.replace(tzinfo=datetime.timezone.utc)
       if wlDate >= activeDate:
          siteInfoD[site_id]['gw_status'] = 'Active'
    
       # Period of record for periodic measurements by USGS
       #
       if len(usgsRecordsL) > 0:
          siteInfoD[site_id]['gw_agency_cd'].append('USGS')
          siteInfoD[site_id]['usgs_status']     = 'Inactive'
          siteInfoD[site_id]['usgs_begin_date'] = gwInfoD[usgsRecordsL[0]]['lev_str_dt'][:10]
          siteInfoD[site_id]['usgs_end_date']   = gwInfoD[usgsRecordsL[-1]]['lev_str_dt'][:10]
          lev_dt_acy_cd                         = gwInfoD[usgsRecordsL[-1]]['lev_dt_acy_cd']
          fmt = '%Y-%m-%d'
          if lev_dt_acy_cd == 'Y':
             fmt = '%Y'
          elif lev_dt_acy_cd == 'M':
             fmt = '%Y-%m'
          wlDate = datetime.datetime.strptime(siteInfoD[site_id]['usgs_end_date'], fmt)
          wlDate = wlDate.replace(tzinfo=datetime.timezone.utc)
          if wlDate >= activeDate:
             siteInfoD[site_id]['usgs_status'] = 'Active'
    
       # Period of record for periodic measurements by OWRD
       #
       if len(owrdRecordsL) > 0:
          siteInfoD[site_id]['gw_agency_cd'].append('OWRD')
          siteInfoD[site_id]['owrd_status']     = 'Inactive'
          siteInfoD[site_id]['owrd_begin_date'] = gwInfoD[owrdRecordsL[0]]['lev_str_dt'][:10]
          siteInfoD[site_id]['owrd_end_date']   = gwInfoD[owrdRecordsL[-1]]['lev_str_dt'][:10]
          lev_dt_acy_cd                         = gwInfoD[owrdRecordsL[-1]]['lev_dt_acy_cd']
          fmt = '%Y-%m-%d'
          if lev_dt_acy_cd == 'Y':
             fmt = '%Y'
          elif lev_dt_acy_cd == 'M':
             fmt = '%Y-%m'
          wlDate = datetime.datetime.strptime(siteInfoD[site_id]['owrd_end_date'], fmt)
          wlDate = wlDate.replace(tzinfo=datetime.timezone.utc)
          if wlDate >= activeDate:
             siteInfoD[site_id]['owrd_status'] = 'Active'
    
       # Period of record for periodic measurements by CDWR
       #
       if len(cdwrRecordsL) > 0:
          siteInfoD[site_id]['gw_agency_cd'].append('CDWR')
          siteInfoD[site_id]['cdwr_status']     = 'Inactive'
          siteInfoD[site_id]['cdwr_begin_date'] = gwInfoD[cdwrRecordsL[0]]['lev_str_dt'][:10]
          siteInfoD[site_id]['cdwr_end_date']   = gwInfoD[cdwrRecordsL[-1]]['lev_str_dt'][:10]
          lev_dt_acy_cd                         = gwInfoD[cdwrRecordsL[-1]]['lev_dt_acy_cd']
          fmt = '%Y-%m-%d'
          if lev_dt_acy_cd == 'Y':
             fmt = '%Y'
          elif lev_dt_acy_cd == 'M':
             fmt = '%Y-%m'
          wlDate = datetime.datetime.strptime(siteInfoD[site_id]['cdwr_end_date'], fmt)
          wlDate = wlDate.replace(tzinfo=datetime.timezone.utc)
          if wlDate >= activeDate:
             siteInfoD[site_id]['cdwr_status'] = 'Active'
    
       # Periodic count
       #
       if len(siteInfoD[site_id]['gw_agency_cd']) > 0:
          siteInfoD[site_id]['gw_agency_cd'] = ",".join(siteInfoD[site_id]['gw_agency_cd'])
       else:
          siteInfoD[site_id]['gw_agency_cd'] = ''
       siteInfoD[site_id]['gw_count']   = len(usgsRecordsL) + len(owrdRecordsL) + len(cdwrRecordsL)
       siteInfoD[site_id]['usgs_count'] = len(usgsRecordsL)
       siteInfoD[site_id]['owrd_count'] = len(owrdRecordsL)
       siteInfoD[site_id]['cdwr_count'] = len(cdwrRecordsL)

       usgsDups    += len(duplUsgsL)
       owrdDups    += len(duplOwrdL)
       cdwrDups    += len(duplCdwrL)

       yRecords     = len(list({x for x in gwInfoD if gwInfoD[x]['lev_web_cd'] == 'Y'}))
       nRecords     = len(list({x for x in gwInfoD if gwInfoD[x]['lev_web_cd'] == 'N'}))
       totalY      += yRecords
       totalN      += nRecords
    
       # Overall period of record for recorder measurements for all agencies
       #
       siteInfoD[site_id]['rc_agency_cd']    = []
       rc_begin_date                         = None
       rc_end_date                           = None
       rc_count                              = 0
       rc_status                             = ''
       
       if siteInfoD[site_id]['usgs_rc_begin_date'] is not None:
          siteInfoD[site_id]['rc_agency_cd'].append('USGS')
          rc_begin_date = siteInfoD[site_id]['usgs_rc_begin_date']
          rc_end_date   = siteInfoD[site_id]['usgs_rc_end_date']
          rc_count     += int(siteInfoD[site_id]['usgs_rc_count'])
          rc_status     = 'Inactive'
          
       if rc_begin_date is None and siteInfoD[site_id]['owrd_rc_begin_date'] is not None:
          siteInfoD[site_id]['rc_agency_cd'].append('OWRD')
          rc_begin_date = siteInfoD[site_id]['owrd_rc_begin_date']
          rc_end_date   = siteInfoD[site_id]['owrd_rc_end_date']
          rc_count     += int(siteInfoD[site_id]['owrd_rc_count'])
          rc_status     = 'Inactive'
       elif rc_begin_date is not None and siteInfoD[site_id]['owrd_rc_begin_date'] is not None:
          siteInfoD[site_id]['rc_agency_cd'].append('OWRD')
          beginDateL    = sorted([rc_begin_date, siteInfoD[site_id]['owrd_rc_begin_date']])
          endDateL      = sorted([rc_end_date, siteInfoD[site_id]['owrd_rc_end_date']])
          rc_begin_date = beginDateL[0]
          rc_end_date   = endDateL[-1]
          rc_count     += int(siteInfoD[site_id]['owrd_rc_count'])
          rc_status     = 'Inactive'
          
       if rc_begin_date is None and siteInfoD[site_id]['cdwr_rc_begin_date'] is not None:
          siteInfoD[site_id]['rc_agency_cd'].append('CDWR')
          rc_begin_date = siteInfoD[site_id]['cdwr_rc_begin_date']
          rc_end_date   = siteInfoD[site_id]['cdwr_rc_end_date']
          rc_count     += int(siteInfoD[site_id]['cdwr_rc_count'])
          rc_status     = 'Inactive'
       elif rc_begin_date is not None and siteInfoD[site_id]['cdwr_rc_begin_date'] is not None:
          siteInfoD[site_id]['rc_agency_cd'].append('CDWR')
          beginDateL    = sorted([rc_begin_date, siteInfoD[site_id]['cdwr_rc_begin_date']])
          endDateL      = sorted([rc_end_date, siteInfoD[site_id]['cdwr_rc_end_date']])
          rc_begin_date = beginDateL[0]
          rc_end_date   = endDateL[-1]
          rc_count     += int(siteInfoD[site_id]['cdwr_rc_count'])
          rc_status     = 'Inactive'
                            
       if rc_end_date is not None:
          wlDate = datetime.datetime.strptime(str(rc_end_date), '%Y-%m-%d')
          wlDate = wlDate.replace(tzinfo=datetime.timezone.utc)
          if wlDate >= activeDate:
             rc_status = 'Active'
          
       siteInfoD[site_id]['rc_agency_cd']  = ",".join(siteInfoD[site_id]['rc_agency_cd'])
       siteInfoD[site_id]['rc_begin_date'] = rc_begin_date
       siteInfoD[site_id]['rc_end_date']   = rc_end_date
       siteInfoD[site_id]['rc_count']      = rc_count
       siteInfoD[site_id]['rc_status']     = rc_status

       # Output periodic records
       #
       for myDate in sorted(gwInfoD.keys()):
          valuesL = list(map(lambda x: gwInfoD[myDate][x], myGwFields))
          #valuesL = list({'%s' % str(gwInfoD[myDate][x]) for x in myGwFields})
          outputL.append("\t".join(valuesL))

       # Print messages
       #
       messages = []
       messages.append("Processed site %s site" % site_id)
       messages.append("\t%40s %20d" % ("USGS Records", len(usgsRecordsL))) 
       messages.append("\t%40s %20d" % ("USGS Records duplicates removed", len(duplUsgsL))) 
       messages.append("\t%40s %20d" % ("OWRD Records", len(owrdRecordsL)))
       messages.append("\t%40s %20d" % ("OWRD Records duplicates removed", len(duplOwrdL))) 
       messages.append("\t%40s %20d" % ("CDWR Records", len(cdwrRecordsL)))
       messages.append("\t%40s %20d" % ("CDWR Records duplicates removed", len(duplCdwrL)))
       messages.append("\t%40s %20d" % ("Static Records", yRecords))
       messages.append("\t%40s %20d" % ("Non-static Records", nRecords)) 
       screen_logger.debug('\n'.join(messages))
 
   else:
       message = "Skipping site %s site with no waterlevels" % site_id
       screen_logger.debug(message)

   totalUSGS   += len(usgsRecordsL)
   totalOWRD   += len(owrdRecordsL)
   totalCDWR   += len(cdwrRecordsL)

totalRecords = totalUSGS + totalOWRD + totalCDWR
totalDups    = usgsDups + owrdDups + cdwrDups

# Output records
#
with open(output_file,'w') as f:
   f.write('\n'.join(outputL))

# Sites with recorder records
#
RecorderSitesL = list({siteInfoD[x]['site_id'] for x in siteInfoD if len(siteInfoD[x]['rc_agency_cd']) > 0})
usgsRecordersL = list({siteInfoD[x]['site_id'] for x in siteInfoD if 'USGS' in siteInfoD[x]['rc_agency_cd']})
owrdRecordersL = list({siteInfoD[x]['site_id'] for x in siteInfoD if 'OWRD' in siteInfoD[x]['rc_agency_cd']})
cdwrRecordersL = list({siteInfoD[x]['site_id'] for x in siteInfoD if 'CDWR' in siteInfoD[x]['rc_agency_cd']})
             
# Print information
#
ncols    = 85
messages = []
messages.append('\n\tPeriodic measurements recorded in waterlevel file')
messages.append('\t%s' % (ncols * '-'))
messages.append('\t%-70s %10d' % ('Number of sites processed from collection file', len(siteInfoD)))
messages.append('\t%-70s %10d' % ('Number of sites with periodic measurements', siteCount))
messages.append('\t%-70s %10d' % ('Number of periodic measurements made by USGS', totalUSGS))
messages.append('\t%-70s %10d' % ('Number of periodic measurements made by OWRD', totalOWRD))
messages.append('\t%-70s %10d' % ('Number of periodic measurements made by CDWR', totalCDWR))
messages.append('\t%-70s %10d' % ('Number of periodic measurements', totalRecords))
messages.append('\t%-70s %10d' % ('Number of periodic static measurements', totalY))
messages.append('\t%-70s %10d' % ('Number of periodic non-static measurements', totalN))
messages.append('\t%s' % (ncols * '-'))
messages.append('\t%-70s %10d' % ('Number of USGS periodic duplicate measurements removed', usgsDups))
messages.append('\t%-70s %10d' % ('Number of OWRD periodic duplicate measurements removed', owrdDups))
messages.append('\t%-70s %10d' % ('Number of CDWR periodic duplicate measurements removed', cdwrDups))
messages.append('\t%-70s %10d' % ('Number of duplicate measurements removed from All sources', totalDups))
messages.append('\t%s' % (ncols * '-'))
messages.append('\t%-70s %10d' % ('Number of sites with recorder measurements', len(RecorderSitesL)))
messages.append('\t%-70s %10d' % ('Number of USGS sites with recorder measurements', len(usgsRecordersL)))
messages.append('\t%-70s %10d' % ('Number of OWRD sites with recorder measurements', len(owrdRecordersL)))
messages.append('\t%-70s %10d' % ('Number of CDWR sites with recorder measurements', len(cdwrRecordersL)))
messages.append('') 
messages.append('')
   
screen_logger.info("\n".join(messages))
file_logger.info("\n".join(messages))


# Print results
# -------------------------------------------------
#
LoggingOutput (siteInfoD, mySiteFields, mySiteFormat)

sys.exit()
