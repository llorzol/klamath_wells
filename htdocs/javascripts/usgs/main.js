/**
 * Namespace: Main
 *
 * Main is a JavaScript library to provide a set of functions to manage
 *  the web requests.
 *
 * version 3.17
 * May 30, 2024
*/

/*
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
*/

// Global variables for icon symbols
//
var mySites;
var BasinBoundary;

var mapSymbolUrl         = "icons/";

// Global variables for images
//
var imageSrc             = "images/";

// Link specs for table and popup content
//
var projectName          = "project=klamath_wells";

var gwLink               = "http://127.0.0.1/discrete_gw/index.html?" + projectName + "&";
//var gwLink               = "https://or.water.usgs.gov/projs_dir/discrete_gw/index.html?" + projectName + "&";
//var gwLink               = "https://staging-or.water.usgs.gov/discrete_gw/index.html?" + projectName + "&";

var nwisLink             = "https://waterdata.usgs.gov/nwis/";

var lithologyLink        = "http://127.0.0.1/lithology/index.html?";
//var lithologyLink        = "https://staging-or.water.usgs.gov/lithology/index.html?";
//var lithologyLink        = "https://or.water.usgs.gov/projs_dir/lithology/index.html?";

var wellconstructionLink = "http://127.0.0.1/well_construction/index.html?";
//var wellconstructionLink = "https://staging-or.water.usgs.gov/well_construction/index.html?";
//var wellconstructionLink = "https://or.water.usgs.gov/projs_dir/well_construction/index.html?";

var dvLink               = "https://waterdata.usgs.gov/nwis/dv?";

var owrdLink             = 'https://apps.wrd.state.or.us/apps/gw/gw_info/gw_hydrograph/Hydrograph.aspx?gw_logid='

var cdwrLink             = 'https://wdl.water.ca.gov/WaterDataLibrary/GroundWaterLevel.aspx?SiteCode='

var BasinBoundary        = "gis/klamath_wells_studyarea.json";

var delimiter            = '\t';

var aboutTitle           = 'Upper Klamath Basin Well Mapper';


// Prepare when the DOM is ready 
//
$(document).ready(function() 
  {
   // Loading message
   //
   message = "Preparing sites and basin information";
   openModal(message);
   //closeModal();
 
   // Set selection of agency and status
   //
   $("#monitoringAgency").val('ALL');
   $("#monitoringStatus").val('All wells');
   $("#finderLinks").val('byStationName wells');

   // Build ajax requests
   //
   var webRequests  = [];

   // Request for site information
   //
   var request_type = "GET";
   var script_http  = "/cgi-bin/klamath_wells/requestCollectionFile.py";
   var dataType     = "json";
      
   // Web request
   //
    webRequests.push($.ajax( {
      method:   request_type,
      url:      script_http,
      data:     data_http,
      dataType: dataType,
      success: function (myData) {
        message = "Processed site information";
        openModal(message);
        fadeModal(2000);
        mySites = myData;
        console.log(`mySites ${mySites}`);
      },
      error: function (error) {
        message = `Failed to load site information ${error}`;
        openModal(message);
        fadeModal(2000);
        return false;
      }
   }));

   // Request for water-level information
   //
   var request_type = "GET";
   var script_http  = "/cgi-bin/klamath_wells/porGwChange.py";
   var data_http    = "SeasonalIntervals=" + SeasonAgruments.join(" ");
   if(startingYear.length > 0)
     {
      data_http += "&startingYear=" + startingYear;
     }
   var dataType     = "json";
      
   // Web request
   //
    webRequests.push($.ajax( {
      method:   request_type,
      url:      script_http,
      data:     data_http,
      dataType: dataType,
      success: function (myData) {
        message = "Processed groundwater change information";
        openModal(message);
        fadeModal(2000);
        processGwChange(myData);
        console.log(`processGwChange ${myData}`);
      },
      error: function (error) {
        message = `Failed to load groundwater change information ${error}`;
        openModal(message);
        fadeModal(2000);
        return false;
      }
   }));

   // Set basin boundary
   //	
   if(BasinBoundary)
     {
      console.log("Adding BasinBoundary " + BasinBoundary);

      // Request for basin boundary
      //
      var request_type = "GET";
      var script_http  = BasinBoundary;
      var data_http    = "";
      var dataType     = "json";
      
      // Web request
      //
       webRequests.push($.ajax( {
         method:   request_type,
         url:      script_http,
         data:     data_http,
         dataType: dataType,
         success: function (myData) {
           message = "Processed basin boundary information";
           openModal(message);
           fadeModal(2000);
           BasinBoundary = myData;
           console.log(`mySites ${mySites}`);
         },
         error: function (error) {
           message = `Failed to load basin boundary information ${error}`;
           openModal(message);
           fadeModal(2000);
           return false;
         }
       }));
     }

   // Run ajax requests
   //
   $.when.apply($, webRequests).then(function() {

        fadeModal(2000);

        buildMap();
   });
  });
