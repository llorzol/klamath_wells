/**
 * Namespace: Map
 *
 * Map is a JavaScript library to set of functions to build
 *  a map.
 *
 * version 3.14
 * December 20, 2023
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
// Set for map
//
var map;
var miniMap;

var allSites            = new L.FeatureGroup();
var customSite          = new L.FeatureGroup();
var customSites         = new L.FeatureGroup();
var customLevels        = new L.FeatureGroup();

var mySiteInfo          = {};

// Keeps track of present bounding box [used by refresh map feature]
//
var maximumZoom         = 15;
var minimumZoom         =  7;
var presentMapExtent    = {};

// Set basemap
//
var ESRItopoBasemap     = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}", {attribution: 'MRLC, State of Oregon, State of Oregon DOT, State of Oregon GEO, Esri, DeLorme, HERE, TomTom, USGS, NGA, EPA, NPS, U.S. Forest Service'});
var ESRIusaTopoMinimap  = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/USA_Topo_Maps/MapServer/tile/{z}/{y}/{x}", {opacity: 0.7,attribution: 'Copyright:&copy; 2013 National Geographic Society, i-cubed'});
 
// Clear text
//
$("#searchSites").val('');

$(".gwLevelContent").html('');


// Build the map and initialize map features
//
function buildMap() 
  {
   // Message
   //
   message = "Building map";
   openModal(message);
   console.log(message);
      
   // Create map and add controls
   //  disable scrollwheel
   //
   map = new L.map('map', { scrollWheelZoom: false, zoomControl: false, maxZoom: maximumZoom, minZoom: minimumZoom });
   //map.maxZoom = maximumZoom;

   // Create map pane for higlighted/unlighted site
   //
   customPane = map.createPane('customPane');
   map.getPane('customPane').style.zIndex = 620;

   // Create map pane for selected set using the left panel
   //
   customPane = map.createPane('customSites');
   map.getPane('customSites').style.pointerEvents = 'auto';
   map.getPane('customSites').style.zIndex = 615;

   // Create map pane for groundwater level circles
   //
   customPane = map.createPane('gwChangePane');
   map.getPane('gwChangePane').style.zIndex = 610;

   // Create map pane for all sites
   //
   dummyPane = map.createPane('allSites');
   map.getPane('allSites').style.pointerEvents = 'none';
   map.getPane('allSites').style.zIndex = 600;

   // Set site objects
   //
   siteCount = 0;
   allSites  = L.geoJson(mySites, {
       pointToLayer: function (feature, latlng) {
 
           var site_id      = feature.properties.site_id;
           var gw_agency_cd = feature.properties.gw_agency_cd;
           var gw_status    = feature.properties.gw_status;

           siteCount++;

           // Set hash of for site information
           //
           if(typeof mySiteInfo[site_id] === "undefined")
           {
               mySiteInfo[site_id] = {};
           }

           // Build hash of site information
           //
           var ColumnsL = Object.keys(feature.properties);
           
           for (myColumn of ColumnsL)
           {

               mySiteInfo[site_id][myColumn] = feature.properties[myColumn]
           }
           
           // Set site type
           //
           var site_tp_cd   = 'GW';
           mySiteInfo[site_id].site_tp_cd = site_tp_cd;

           // Icon
           //
           myIcon                        = setIcon(site_id, site_tp_cd, gw_status);
           feature.properties.icon       = myIcon;
           mySiteInfo[site_id].icon      = myIcon;
           feature.properties.site_tp_cd = site_tp_cd;

           if(site_id == "418174N1213955W001")
           {
               //console.log("Site " + site_id);
               //console.log(mySiteInfo[site_id]);
           }
                         
           // Build marker title
           //
           var myTitle      = [];
           var site_no      = mySiteInfo[site_id].site_no;
           var coop_site_no = mySiteInfo[site_id].coop_site_no;
           var cdwr_id      = mySiteInfo[site_id].cdwr_id;
           if(site_no)      { myTitle.push("USGS " + site_no); }
           if(coop_site_no) { myTitle.push("OWRD " + coop_site_no); }
           if(cdwr_id)      { myTitle.push("CDWR " + cdwr_id); }

           return L.marker(latlng, { pane: 'allSites', icon: myIcon, title: myTitle.join(" "), siteID: site_id } );
          },

       onEachFeature: function (feature, layer) {
         
                        // Set
                        //
                        layer.setOpacity(0.1);
         
                        // Highlight site in list of left panel
                        //
                        //layer.on({
                        //          mouseover: highlightList,
                        //          mouseout:  unhighlightList
                        //});
       }
   });

   // Set the bounds 
   //
   map.fitBounds(allSites.getBounds());

   // Show on map
   //
   allSites.addTo(map);
	  
   // Add base map
   //
   map.addLayer(ESRItopoBasemap);
      
   // Create the miniMap
   //
   miniMap = new L.Control.MiniMap(ESRIusaTopoMinimap, { toggleDisplay: true }).addTo(map);

   // Add basin boundary
   //
   console.log("BasinBoundary " + BasinBoundary);
   if(BasinBoundary)
     {
      console.log("Adding BasinBoundary " + BasinBoundary);
      // Set basin boundary
      //	
      var  basinBoundary = L.geoJson(BasinBoundary, {
         style: function (feature) {
         return {color: "red"};
      }});
         
      map.addLayer(basinBoundary);
     }

   // Add control
   //
   var zoomHome = L.Control.zoomHome();
   zoomHome.addTo(map);

   // Show initial map zoom level
   //
   //jQuery( ".mapZoom" ).html( "<b>Zoom Level: </b>" + map.getZoom());
 
   // Refresh sites on extent change
   //
   map.on('zoomend dragend', function(evt) {
       //jQuery( ".mapZoom" ).html( "<b>Zoom Level: </b>" + map.getZoom());

       map.closePopup();
   });
 
   // Refresh sites on extent change
   //
   map.on('zoomend dragend', function(evt) {
 
      console.log('zoomend dragend');

      // Remove existing groundwater change level
      //
      if(!map.hasLayer(customLevels))
        {
 
      console.log('Reset table');
 
      // Build tables
      //
      var mySiteSet =  buildSiteList();
      leftPanel(mySiteSet);
      var siteTable = createTable(mySiteSet);
      $('#siteTable').html("");
      $('#siteTable').html(siteTable);
      $(".siteCount").text(mySiteSet.length);
 
      // Add table sorting
      //
      var myTitle = $('caption#stationsCaption').text();
      DataTables ("#stationsTable");
      $(".dt-buttons").css('width', '100%');
     }
 
   });

  // Build tables
  //
  var mySiteSet =  buildSiteList();
  leftPanel (mySiteSet);
  var siteTable = createTable (mySiteSet);
  $('#siteTable').html("");
  $('#siteTable').html(siteTable);

  // Add table sorting
  //
  var myTable = DataTables ("#stationsTable");
  $(".dt-buttons").css('width', '100%');

//  var myTable = new DataTables ("#stationsTable", {
//      paging: false,
//      scrollCollapse: true,
//      scrollY: '200px'
//  });

   // Close
   //
   closeModal();
	
} //End of buildMap

// ==================================================
// Functions
// ==================================================

// Add NWIS site number to circle marker
//
customCircleMarker = L.CircleMarker.extend( {
   options: { site_id: 'Site number' }
});

// Determine icon
//
function setIcon (site_no, site_tp_cd, status)
  {
   var iconType   = [];

   switch(site_tp_cd.substring(0,2))
     {
       case "ES":
       case "LK":
       case "OC":
       case "ST":
       case "WE":
         iconType.push('sw');
         break;

       case "GW":
       case "SB":
         iconType.push('gw');
         break;

       case "SP":
         iconType.push('sp');
         break;

       case "AT":
         iconType.push('at');
         break;

       default:
         iconType.push('ot');
         break;
     }

   //console.log(message);
   switch(status.toLowerCase())
     {
       case "active":
         iconType.push('act_30');
         break;
       case "active/multi":
         iconType = ['multi', iconType, 'act'];
         break;
       case "inactive":
         iconType.push('ina_30');
         break;
       case "highlight":
         iconType = ['yellow', iconType];
         break;
       default:
         iconType = ['multi', iconType, 'ina'];
         break;
     }

   var iconUrl  = mapSymbolUrl + iconType.join("_") + '.png';
   var iconSize = [16,22];

   return L.icon({
                 iconUrl: iconUrl,
                 iconSize: iconSize,
                 iconAnchor: [5,30],
                 popupAnchor: [0, -20],
                 className: site_no
                });
}

// Set map bounds based on sites in study area
//
function fullExtent()
  {
   //console.log("setMapExtent");
   map.fitBounds(allSites.getBounds());
  }

// Build site summary table
//
function createTable (mySiteSet) 
  {
   console.log("createTable ");
   console.log(mySiteSet);

   // Set active date
   //
   var activeDate = new Date(2018, 0, 1, 0, 0, 0);

   // Check what the agency currently set to
   //
   var myAgency = $("#monitoringAgency").prop('value');
   //console.log("myAgency " + myAgency);
   if(/^all/i.test(myAgency)) { myAgency = 'All Agencies'; }

   // Check what the network type currently set to
   //
   var myStatus = $("#monitoringStatus").prop('value');
   //console.log("myStatus " + myStatus);
   if(/^all/i.test(myStatus)) { myStatus = 'Active and Inactive'; }

   // Create table caption
   //
   var myCaption = [];
   myCaption.push('Groundwater Sites for Upper Klamath Basin - ');
   myCaption.push(mySiteSet.length + ' sites');
   myCaption.push('(Monitored by ' + myAgency + ' -- ');
   myCaption.push(myStatus + ' sites)');

   // Set
   //
   var NumberUSGS          = 0;
   var NumberOWRD          = 0;
   var NumberCDWR          = 0;
   var NumberALL           = 0;

   var NumberUSGSactive    = 0;
   var NumberUSGSinactive  = 0;
   var NumberOWRDactive    = 0;
   var NumberOWRDinactive  = 0;
   var NumberCDWRactive    = 0;
   var NumberCDWRinactive  = 0;
   var NumberALLactive     = 0;
   var NumberALLinactive   = 0;


   var summary_table = [];

       summary_table.push('<table id="stationsTable" class="stations_table">');
       summary_table.push('<caption id="stationsCaption">' +  myCaption.join(" ") + '</caption>');
       summary_table.push('<thead>');
       summary_table.push('<tr>');
       summary_table.push(' <th>Status</th>');
       summary_table.push(' <th>Graph</th>');
       summary_table.push(' <th>USGS site number</th>');
       summary_table.push(' <th>OWRD well log ID</th>');
       summary_table.push(' <th>CDWR site code</th>');
       summary_table.push(' <th>Station Name</th>');
       summary_table.push(' <th>Groundwater Change</th>');
       summary_table.push(' <th>Monitoring Agency: Period of Record</th>');
       summary_table.push('</tr>');
       summary_table.push('</thead>');
      
       summary_table.push('<tbody>');

   // Loop through sites
   //
   for(var i = 0; i <  mySiteSet.length; i++)
     {
      var siteID               = mySiteSet[i].site_id;
      var site_status          = mySiteSet[i].site_status;
          
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
      var state_well_nmbr      = mySiteInfo[siteID].state_well_nmbr;
      var periodic             = mySiteInfo[siteID].periodic;
      var recorder             = mySiteInfo[siteID].recorder;
          
      var gw_status            = mySiteInfo[siteID].gw_status;
      var gw_begin_date        = mySiteInfo[siteID].gw_begin_date;
      var gw_end_date          = mySiteInfo[siteID].gw_end_date;
      var gw_count             = mySiteInfo[siteID].gw_count;
      var gw_agency_cd         = mySiteInfo[siteID].gw_agency_cd;

      var rc_agency_cd         = mySiteInfo[siteID].rc_agency_cd;
      var rc_begin_date        = mySiteInfo[siteID].rc_begin_date;
      var rc_end_date          = mySiteInfo[siteID].rc_end_date;
      var rc_count             = mySiteInfo[siteID].rc_count;
      var rc_status            = mySiteInfo[siteID].rc_status;
          
      var usgs_begin_date      = mySiteInfo[siteID].usgs_begin_date;
      var usgs_end_date        = mySiteInfo[siteID].usgs_end_date;
      var usgs_count           = mySiteInfo[siteID].usgs_count;
      var usgs_status          = mySiteInfo[siteID].usgs_status;
      var usgs_rc_begin_date   = mySiteInfo[siteID].usgs_rc_begin_date;
      var usgs_rc_end_date     = mySiteInfo[siteID].usgs_rc_end_date;
      var usgs_rc_count        = mySiteInfo[siteID].usgs_rc_count;
      var usgs_rc_status       = mySiteInfo[siteID].usgs_rc_status;
          
      var owrd_begin_date      = mySiteInfo[siteID].owrd_begin_date;
      var owrd_end_date        = mySiteInfo[siteID].owrd_end_date;
      var owrd_count           = mySiteInfo[siteID].owrd_count;
      var owrd_status          = mySiteInfo[siteID].owrd_status;
      var owrd_rc_begin_date   = mySiteInfo[siteID].owrd_rc_begin_date;
      var owrd_rc_end_date     = mySiteInfo[siteID].owrd_rc_end_date;
      var owrd_rc_count        = mySiteInfo[siteID].owrd_rc_count;
      var owrd_rc_status       = mySiteInfo[siteID].owrd_rc_status;
          
      var cdwr_begin_date      = mySiteInfo[siteID].cdwr_begin_date;
      var cdwr_end_date        = mySiteInfo[siteID].cdwr_end_date;
      var cdwr_count           = mySiteInfo[siteID].cdwr_count;
      var cdwr_status          = mySiteInfo[siteID].cdwr_status;
      var cdwr_rc_begin_date   = mySiteInfo[siteID].cdwr_rc_begin_date;
      var cdwr_rc_end_date     = mySiteInfo[siteID].cdwr_rc_end_date;
      var cdwr_rc_count        = mySiteInfo[siteID].cdwr_rc_count;
      var cdwr_rc_status       = mySiteInfo[siteID].cdwr_rc_status;

      //console.log("gw_agency_cd " + gw_agency_cd);
      //console.log("Site " + siteID + " rc_agency_cd " + rc_agency_cd);

      var myIcon               = mySiteSet[i].site_icon;
      var symbol_img_src       = myIcon.options.iconUrl;
         
      var gw_url               = gwLink + "site_id=" + site_id;
      var gw_link              ='  <a class="popupLink" href="#" onclick="window.open(\'' + gw_url + '\' , \'_blank\'); return;">Link</a>';
         
      var nwis_link = '';
      if(site_no)
        {
         var nwis_url  = nwisLink + '/inventory?site_no=' + site_no;
         nwis_link     ='  <a class="popupLink" href="#" onclick="window.open(\'' + nwis_url + '\' , \'_blank\'); return;">' + site_no + '</a>';
        }
         
      var owrd_link = '';
      if(coop_site_no)
        {
         var owrd_url  = owrdLink + coop_site_no;
         owrd_link     ='  <a class="popupLink" href="#" onclick="window.open(\'' + owrd_url + '\' , \'_blank\'); return;">' + coop_site_no + '</a>';
        }
         
      var cdwr_link = '';
      if(cdwr_id)
        {
         var cdwr_url  = cdwrLink + cdwr_id;
         cdwr_link     ='  <a class="popupLink" href="#" onclick="window.open(\'' + cdwr_url + '\' , \'_blank\'); return;">' + cdwr_id + '</a>';
        }

      // Counters
      //
      site_agency_cd = gw_agency_cd
      if(/recorder/i.test(myStatus)) { site_agency_cd = rc_agency_cd; }

         //console.log(site_id);
         //console.log(gw_agency_cd);
         if(site_agency_cd.length == 1)
           {
            if(site_agency_cd.includes("USGS"))
              {
               NumberUSGS++;
               if(/^active/i.test(site_status)) { NumberUSGSactive++; }
               else { NumberUSGSinactive++; }
              }
            if(site_agency_cd.includes("OWRD"))
              {
               NumberOWRD++;
               if(/^active/i.test(site_status)) { NumberOWRDactive++; }
               else { NumberOWRDinactive++; }
              }
            if(site_agency_cd.includes("CDWR"))
              {
               NumberCDWR++;
               if(/^active/i.test(site_status)) { NumberCDWRactive++; }
               else { NumberCDWRinactive++; }
              }
           }
         else
           {
            NumberALL++;
            if(/^active/i.test(site_status)) { NumberALLactive++; }
            else { NumberALLinactive++; }
           }
           
      if(i == 0)
        {
//         summary_table.push('<tr class="topBorder symbols">');
         summary_table.push('<tr id="tr_' + site_id + '" class="topBorder">');
        }
      else
        {
//         summary_table.push('<tr class="symbols">');
         summary_table.push('<tr id="tr_' + site_id + '">');
        }
      summary_table.push(
                         ' <td class="symbols">',
                         '<img alt="' + status + ' site" src="' + symbol_img_src + '">',
                         status,
                         ' </td>'
                        );
      
      // Graph
      //
      summary_table.push(
                         ' <td>',
                         gw_link,
                         ' </td>'
                        );
      
      // Nwis site number
      //
      summary_table.push(
                         ' <td class="stationName">',
                         nwis_link,
                         ' </td>'
                        );
      
      // OWRD site number
      //
      summary_table.push(
                         ' <td class="stationName">',
                         owrd_link,
                         ' </td>'
                        );

      // CDWR Inventory page
      //
      //  Inventory page work  https://wdl.water.ca.gov/WaterDataLibrary/GroundWaterLevel.aspx?SiteCode=417786N1220041W001
      //
      //
      summary_table.push(
                         ' <td class="stationName">',
                         cdwr_link,
                         ' </td>'
                        );

      
      // Station name
      //
      summary_table.push(
                         ' <td class="stationName">',
                         station_nm,
                         ' </td>'
                        );
      
      // Groundwater change
      //
      summary_table.push(
                         ' <td id="gw_' + site_id + '" class="stationName">',
                         '',
                         ' </td>'
                        );

      var por_txt    = '';
      var porRecords = [];
      var td_color   = '';
      if(gw_agency_cd.length > 0)
        {
         var activeFlag = [];
         var sortedList = gw_agency_cd.sort()
         for(var ii = 0; ii < sortedList.length; ii++)
            {
             var AgencyRecord = sortedList[ii].toLowerCase();

             var beginDate    = mySiteInfo[siteID][AgencyRecord + '_begin_date'];
             var endDate      = mySiteInfo[siteID][AgencyRecord + '_end_date'];
             var counts       = mySiteInfo[siteID][AgencyRecord + '_count'];
             var activeFlag   = mySiteInfo[siteID][AgencyRecord + '_status'];

             porRecords.push([AgencyRecord.toUpperCase(), ':', 'From', beginDate,'to', endDate, '(counts ' + counts + ')'].join(" "));
            }
         if(activeFlag.length >= sortedList.length) { td_color = ' class="overlap"'; }
        }
      if(rc_agency_cd.length > 0)
        {
         var sortedList = rc_agency_cd.sort()
         for(var ii = 0; ii < sortedList.length; ii++)
            {
             var AgencyRecord = sortedList[ii].toLowerCase();

             var beginDate    = mySiteInfo[siteID][AgencyRecord + '_rc_begin_date'];
             var endDate      = mySiteInfo[siteID][AgencyRecord + '_rc_end_date'];
             var counts       = mySiteInfo[siteID][AgencyRecord + '_rc_count'];
             var activeFlag   = mySiteInfo[siteID][AgencyRecord + '_rc_status'];

             porRecords.push([AgencyRecord.toUpperCase() + " Recorder", ':', 'From', beginDate,'to', endDate, '(counts ' + counts + ')'].join(" "));
            }
        }
      por_txt = porRecords.join("<br />");
      
      summary_table.push(
                         ' <td' + td_color + '>',
                         por_txt,
                         ' </td>'
                        );
      
      summary_table.push('</tr>');
      //if(gw_agency_cd.length > 1) { break; }
     }
	
   summary_table.push('</tbody>');
   summary_table.push('</table>');

   // Update counts in explanation table
   //
   $("#TotalStations").text(mySiteSet.length);

   $(".NumberUSGS").text(NumberUSGS);
   $(".NumberOWRD").text(NumberOWRD);
   $(".NumberCDWR").text(NumberCDWR);
   $(".NumberALL").text(NumberALL);

   $(".NumberUSGSactive").text(NumberUSGSactive);
   $(".NumberUSGSinactive").text(NumberUSGSinactive);
   $(".NumberOWRDactive").text(NumberOWRDactive);
   $(".NumberOWRDinactive").text(NumberOWRDinactive);
   $(".NumberCDWRactive").text(NumberCDWRactive);
   $(".NumberCDWRinactive").text(NumberCDWRinactive);
   $(".NumberALLactive").text(NumberALLactive);
   $(".NumberALLinactive").text(NumberALLinactive);
 
   return summary_table.join("\n");
  }