/**
 * Namespace: Main
 *
 * Main is a JavaScript library to provide a set of functions to manage
 *  the web requests.
 *
 * version 3.16
 * January 29, 2024
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
                             dataType: dataType
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
   console.log("just ran porGwChange.py")
      
   // Web request
   //
   webRequests.push($.ajax( {
                             method:   request_type,
                             url:      script_http, 
                             data:     data_http, 
                             dataType: dataType
   }));

   // Set basin boundary
   //	
   //console.log("BasinBoundary " + BasinBoundary);
           
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
                                dataType: dataType
      }));
     }

   // Run ajax requests
   //
   var j       = 0;
   $.when.apply($, webRequests).then(function() {
        console.log('Responses');
        //console.log("Responses length " + arguments.length);
        //console.log(arguments);

        // Retrieve site information
        //
        var i = 0;
        if(arguments.length > 0)
          {
           var myInfo  = arguments[i];
           //console.log("arguments " + i);
           //console.log(arguments[i]);

           if(myInfo[1] === "success")
             {
              // Loading message
              //
              message = "Processed site information";
              openModal(message);
              fadeModal(2000);

              mySites     = myInfo[0];
             }
            else
             {
              // Loading message
              //
              message = "Failed to load site information";
              openModal(message);
              fadeModal(2000);
              return false;
             }
          }

        // Retrieve groundwater change information
        //
        i++;
        console.log("Retrieve groundwater change information ");
        //console.log(arguments[i]);
        if(arguments.length > i)
          {
           var myInfo = arguments[i];

           if(myInfo[1] === "success")
             {
              // Loading message
              //
              message = "Processed groundwater change information";
              openModal(message);
              fadeModal(2000);

              processGwChange(myInfo[0]);
             }
            else
             {
              // Loading message
              //
              message = "Failed to load groundwater change information";
              openModal(message);
              fadeModal(2000);
              return false;
             }
          }

        // Retrieve basin boundary information
        //
        i++;
        console.log("Retrieve basin boundary " + i);
        //console.log(arguments[i]);
        if(arguments.length > i)
          {
           var myInfo = arguments[i];

           if(myInfo[1] === "success")
             {
              // Loading message
              //
              message = "Processed basin boundary information";
              openModal(message);
              fadeModal(2000);

              BasinBoundary = myInfo[0];
             }
            else
             {
              // Loading message
              //
              message = "Failed to load basin boundary information";
              openModal(message);
              fadeModal(2000);
              return false;
             }
          }

        //console.log("done with main");
        fadeModal(2000);

        buildMap();

        // Side panel
        //
        //leftPanel();
   });
  });
