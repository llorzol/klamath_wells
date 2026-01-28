/**
 * Namespace: Main
 *
 * Main is a JavaScript library to provide a set of functions to manage
 *  the web requests.
 *
 $Id: /var/www/html/klamath_wells/javascripts/usgs/main.js, v 3.22 2026/01/27 20:02:09 llorzol Exp $
 $Revision: 3.22 $
 $Date: 2026/01/27 20:02:09 $
 $Author: llorzol $
 *
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
var mySites = null;
var myGwData = null;
var errorMessage = null;

var mapSymbolUrl         = "icons/";

// Global variables for images
//
var imageSrc             = "images/";

// Link specs for table and popup content
//
var projectName          = "klamath_wells";

var gwLink               = '/gw_hydrograph/index.html?';
//var gwLink               = "https://or.water.usgs.gov/projs_dir/discrete_gw/index.html?" + projectName + "&";
//var gwLink               = "https://staging-or.water.usgs.gov/discrete_gw/index.html?" + projectName + "&";

var nwisLink             = "https://waterdata.usgs.gov/nwis/";

var lithologyLink        = "/lithology/index.html?";
//var lithologyLink        = "https://staging-or.water.usgs.gov/lithology/index.html?";
//var lithologyLink        = "https://or.water.usgs.gov/projs_dir/lithology/index.html?";

var wellconstructionLink = "/well_construction/index.html?";
//var wellconstructionLink = "https://staging-or.water.usgs.gov/well_construction/index.html?";
//var wellconstructionLink = "https://or.water.usgs.gov/projs_dir/well_construction/index.html?";

var dvLink               = "https://waterdata.usgs.gov/nwis/dv?";
//var dvLink               = `https://waterdata.usgs.gov/monitoring-location/USGS-${site_no}/#dataTypeId=daily-72019-0&period=periodOfRecord&showFieldMeasurements=true`
var dvLink               = 'https://waterdata.usgs.gov/monitoring-location'

var owrdLink             = 'https://apps.wrd.state.or.us/apps/gw/gw_info/gw_hydrograph/Hydrograph.aspx?gw_logid='

var cdwrLink             = 'https://wdl.water.ca.gov/WaterDataLibrary/GroundWaterLevel.aspx?SiteCode='

var BasinBoundary        = "gis/klamath_wells_studyarea.json";

var delimiter            = '\t';

var aboutTitle           = 'Upper Klamath Basin Well Mapper';


// Prepare when the DOM is ready 
//
$(document).ready(function() {
    // Loading message
    //
    message = "Preparing sites and basin information";
    openModal(message);
    closeModal();

    // Set selection of agency and status
    //
    $("#monitoringAgency").val('ALL');
    $("#monitoringStatus").val('All wells');
    $("#finderLinks").val('byStationName wells');

    // Build ajax requests
    //
    const urls   = [];

    // Request for site information
    //
    urls.push("/cgi-bin/klamath_wells/requestCollectionFile.py");

    // Request for water-level information
    //
    let Url = "/cgi-bin/klamath_wells/porGwChange.py";
    let params = new URLSearchParams();
    params.append("SeasonalIntervals", `${SeasonAgruments.join(" ")}`)
    if(startingYear.length > 0) { params.append("startingYear", startingYear); }

    // Web request
    //
    urls.push(`${Url}?${params}`);

    // Set basin boundary
    //
    if(BasinBoundary) {
        console.log(`Adding BasinBoundary ${BasinBoundary}`);
        urls.push(BasinBoundary)
    }

    // Call the async function
    //
    webRequests(urls, 'json', processData)
});

function processData([mySites, myGwData, BasinBoundary]) {
    console.log("processData");
    console.log(mySites);
    console.log(myGwData);
    console.log(BasinBoundary);

    // Check for site data
    //
    if (!mySites) {

        // Warning message
        //
        message = `No site information for Klamath Basin website`;
        console.log(message);
        updateModal(message);
        fadeModal(3000);

        return false;
    }
    
    // Check for site period of recod data
    //
    if (!myGwData) {

        // Warning message
        //
        message = `No site groundwater information for Klamath Basin website`;
        console.log(message);
        updateModal(message);
        fadeModal(3000);

        return false;
    }
    processGwChange(myGwData);
    
    // Set basin boundary
    //
    if(BasinBoundary) {
        console.log("Adding BasinBoundary ", BasinBoundary);
    }
           
    // Build map
    //	
    buildMap(mySites, myGwData, BasinBoundary);

}
