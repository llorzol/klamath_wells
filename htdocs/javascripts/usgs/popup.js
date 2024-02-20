/**
 * Namespace: Popup Functions
 *
 * Provides set of functions to build a Popup.
 *
 * version 4.05
 * February 18, 2024
*/

/*
###############################################################################
# Copyright (c) U.S. Geological Survey Oregon Water Science Center
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

// Popup specs
//
var popupOptions = { 'maxHeight': '200', 'maxWidth': '300', offset: new L.Point(0, -15) };

// Adds a new DIV table row with two columns
//
function addTableRow(col1, col2) {
   var content = '<div class="divTableRow">';
   content    += ' <div class="divTableCell">';
   content    += col1;
   content    += ' </div>';
   if(col2.length > 0)
     {
      content    += ' <div class="divTableCell">';
      content    += col2;
      content    += ' </div>';
     }
   content    += '</div>';

   return content;
}

// Adds a new DIV table row with two columns
//
function addDivSeparator2() {
	var content = '<div class="divTableRow">';
	content    += ' <hr class="divSeparator"></hr>';
	content    += '</div>';

	return content;
}

// Adds a new DIV table row with two columns
//
function addDivSeparator() {
	var content = '<div class="divTableRow">';
	content    += ' <div class="divTableCell">';
	content    += '  <hr class="divSeparator"></hr>';
	content    += ' </div>';
	content    += ' <div class="divTableCell">';
	content    += '  <hr class="divSeparator"></hr>';
	content    += ' </div>';
	content    += '</div>';

	return content;
}

// Build popup
//
function createPopUp(site, siteID)
  {  
   //console.log("buildPopUp -> " + siteID);
   //console.log("buildPopUp -> " + site.options.opacity);
   //console.log("buildPopUp -> " + site.options.zIndexOffset);

   //  Skip popup content not active
   //
   //if(site.options.opacity < 0.9) { return; }

   //  Create popup content
   //
   var popupContent  = '<div class="leaflet-popup-body rounded-4">';
   popupContent     += '<div class="divTable">';
   popupContent     += '<div class="divTableBody">';

   // Attributes
   //
   var site_id              = mySiteInfo[siteID].site_id;
   var site_no              = mySiteInfo[siteID].site_no;
   var agency_cd            = mySiteInfo[siteID].agency_cd;
   var coop_site_no         = mySiteInfo[siteID].coop_site_no;
   var cdwr_id              = mySiteInfo[siteID].cdwr_id;
   var station_nm           = mySiteInfo[siteID].station_nm;
   var site_tp_cd           = "GW";
   var latitude             = mySiteInfo[siteID].dec_lat_va;
   var longitude            = mySiteInfo[siteID].dec_long_va;
   var status               = mySiteInfo[siteID].gw_status;
   var state_well_nmbr      = mySiteInfo[siteID].state_well_nmbr;
   var gw_begin_dt          = mySiteInfo[siteID].gw_begin_date;
   var gw_end_dt            = mySiteInfo[siteID].gw_end_date;
   var gw_count             = mySiteInfo[siteID].gw_count;
   var gw_agency_cd         = mySiteInfo[siteID].gw_agency_cd;

   var rc_agency_cd         = mySiteInfo[siteID].rc_agency_cd;
   var rc_status            = mySiteInfo[siteID].rc_status;
   var rc_begin_dt          = mySiteInfo[siteID].rc_begin_date;
   var rc_end_dt            = mySiteInfo[siteID].rc_end_date;

   //  Create General entries
   //
   if(site_no)
     {
      popupContent     += addTableRow('<span class="label">NWIS Site Number:</span>', site_no);
      popupContent     += addTableRow('<span class="label">NWIS Agency Code:</span>', agency_cd);
     }
   if(coop_site_no)
     {
      popupContent     += addTableRow('<span class="label">OWRD well logID:</span>', coop_site_no);
     }
   if(cdwr_id)
     {
      popupContent     += addTableRow('<span class="label">CWDR site code:</span>', cdwr_id);
     }
  
   popupContent     += addTableRow('<span class="label">Station Name:</span>', station_nm);
  
   if(state_well_nmbr)
     {
      popupContent     += addTableRow('<span class="label">State Observation Number:</span>', state_well_nmbr);
     }
  
   if(status != "None")
     {
      popupContent     += addTableRow('<span class="label">Observation Status:</span>', status);
     }
  
   if(gw_agency_cd.length > 0)
     {
      var measuringAgencies = gw_agency_cd.join(", ");
      popupContent     += addTableRow('<span class="label">Measured by:</span>', measuringAgencies);
      var measuringPOR  = ["from", gw_begin_dt, "to", gw_end_dt].join(" ");
      popupContent     += addTableRow('<span class="label">Measured</span>', measuringPOR);
     }
          
      var gw_url       = gwLink + "site_id=" + site_id;
      var gw_link      ='  <a class="popupLink" href="#" onclick="window.open(\'' + gw_url + '\' , \'_blank\'); return;">Link</a>';
      popupContent     += addTableRow('<span class="label">Hydrograph</span>', gw_link);
          
   if(site_no)
     {
      var well_url      = wellconstructionLink + "site_no=" + site_no;
      var well_link     ='  <a class="popupLink" href="#" onclick="window.open(\'' + well_url + '\' , \'_blank\'); return;">Link</a>';
      popupContent     += addTableRow('<span class="label">Well Construction</span>', well_link);
     }

      console.log(" ");
      console.log("Site " + site_id + " gw_agency " + gw_agency_cd + " rc_agency_cd " + rc_agency_cd);
      console.log("rc_agency_cd " + rc_agency_cd.length)
      console.log(rc_agency_cd.includes('USGS'))
          
   // Recorder
   //
   if(rc_agency_cd.length > 0)
      {
          // USGS recorder
          //
          // https://waterdata.usgs.gov/nwis/dv?cb_72019=on&format=gif_mult_parms&site_no=415104121232901&referred_module=sw&period=&begin_date=2018-02-17&end_date=2019-02-17
          //
          if(rc_agency_cd.includes('USGS'))
          {
              var dv_url    = dvLink + 'deferred_module=sw&site_no=' + site_no;
              dv_url       += '&format=gif_mult_parms';
              dv_url       += '&cb_72019=on'
              dv_url       += '&begin_date=' + rc_begin_dt + '&end_date=' + rc_end_dt;
              var dv_link   = '  <a class="popupLink" href="#" onclick="window.open(\'' + dv_url + '\' , \'_blank\'); return;">Link</a>';
              popupContent += addTableRow('<span class="label">USGS Recorder hydrograph</span>', dv_link);
          }
          // OWRD recorder
          //
          // https://apps.wrd.state.or.us/apps/gw/gw_info/gw_hydrograph/Hydrograph.aspx?gw_logid=KLAM0010252
          //
          if(rc_agency_cd.includes('OWRD'))
          {
              var dv_url    = 'https://apps.wrd.state.or.us/apps/gw/gw_info/gw_hydrograph/Hydrograph.aspx?gw_logid=' + coop_site_no
              var dv_link   = '  <a class="popupLink" href="#" onclick="window.open(\'' + dv_url + '\' , \'_blank\'); return;">Link</a>';
              popupContent += addTableRow('<span class="label">OWRD Recorder hydrograph</span>', dv_link);
          }
          // CDWR recorder
          //
          // https://wdl.water.ca.gov/WaterDataLibrary/StationDetails.aspx?dateFrom2=01%2f01%2f1900&StationTypeCode=&Station=12N04E03N003M&IncludeVarData=False&SelectedAll=False&dateTo2=01%2f01%2f1900&source=search
          //
          if(rc_agency_cd.includes('CDWR'))
          {
              var dv_url    = 'https://wdl.water.ca.gov/WaterDataLibrary/StationDetails.aspx?dateFrom2=01%2f01%2f1900&StationTypeCode=&Station=' + state_well_nmbr;
              dv_url       += '&IncludeVarData=False&SelectedAll=False&dateTo2=01%2f01%2f1900&source=search';
              var dv_link   = '  <a class="popupLink" href="#" onclick="window.open(\'' + dv_url + '\' , \'_blank\'); return;">Link</a>';
              popupContent += addTableRow('<span class="label">CDWR Recorder hydrograph</span>', dv_link);
          }
     }
          
   if(coop_site_no)
     {
      var lith_url      = lithologyLink + "coop_site_no=" + coop_site_no;
      var lith_link     ='  <a class="popupLink" href="#" onclick="window.open(\'' + lith_url + '\' , \'_blank\'); return;">Link</a>';
      popupContent     += addTableRow('<span class="label">Well Lithology</span>', lith_link);
     }
          
   if(cdwr_id)
     {
      var cdwr_url      = cdwrLink + cdwr_id;
      var cdwr_link     ='  <a class="popupLink" href="#" onclick="window.open(\'' + cdwr_url + '\' , \'_blank\'); return;">Link</a>';
      popupContent     += addTableRow('<span class="label">CDWR data</span>', cdwr_link);
     }

   //popupContent     += addTableRow('<span class="label">Latitude:</span>', latitude.toFixed(3));
   //popupContent     += addTableRow('<span class="label">Longitude:</span>', longitude.toFixed(3));

   popupContent     += '</div></div></div>';

   // Open popup 
   //
   //var myPopup = site.bindPopup(popupContent, popupOptions).openPopup();
   var latlng  = L.latLng(latitude, longitude);
   var myPopup = L.popup(popupOptions).setLatLng(latlng).setContent(popupContent).openOn(map);
   $(".leaflet-popup-close-button").before('<div class="leaflet-popup-title">Site Information</div>');
 
   return;
}
