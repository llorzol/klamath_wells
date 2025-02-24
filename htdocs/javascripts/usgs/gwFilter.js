/**
 * Namespace: gwFilter
 *
 * parameterData is a JavaScript library to provide a set of functions to manage
 *  the data exploration tool.
 *
 * version 3.34
 * February 23, 2025
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

// Set groundwater change data
//-----------------------------------------------
var gwChangeSites = {};

// Set starting year
//-----------------------------------------------
var startingYear = "2001";

// Set starting and ending seasons
//-----------------------------------------------
var SeasonIntervals = { 
                        'Spring': ['03-01', '05-31', 'Min'],
                        'Summer': ['06-01', '08-31', 'Max'],
                        'Fall'  : ['09-01', '11-30', 'Max'],
                        'Winter': ['12-01', '02-28', 'Min']
                      };
var SeasonIntervals = { 
    'Spring': ['03','04','05','Min'],
    'Summer': ['06','07','08','Max'],
    'Fall'  : ['09','10','11','Max'],
    'Winter': ['12','01','02','Min']
                      };
var SeasonsList = ['Spring','Summer','Fall','Winter'];

var selectedSeasonIntervals;

var gwLevelContent     = ''
   
var SeasonAgruments    = [];
for (var season in SeasonIntervals)
    {
        SeasonAgruments.push([season, SeasonIntervals[season].join(',')]);
    }

// Select sites by site number
//-----------------------------------------------
var filterGroundwater = [];

filterGroundwater.push('  <!-- Groundwater Filter -->');
filterGroundwater.push('  <div id="groundWater" class="chooseGw">');
filterGroundwater.push('   <div>');
filterGroundwater.push('    <div class="section text-start">');
filterGroundwater.push('    </div> <!-- class="section" -->');
filterGroundwater.push('    <div class="filterGw"></div>');
filterGroundwater.push('   </div> <!-- id="selectGwChange" -->');
filterGroundwater.push('  </div> <!-- class="chooseGw" -->');

jQuery("span#filterGroundwaterContent").html(filterGroundwater.join("\n"));


// Create groundwater level change legend
//
$('.gwChangeLegend').hide();

// Add legend
//
var interval     = [0,1,5,10,20,30];
var circleRadius = 10;
var content      = '<ul class="list-group list-group-flush">';
content         += '<li class="list-group-item">';
content         += ' <span class="gwDecliningCircle rounded-circle align-middle" style="width: ' + 2*circleRadius +'px; height: ' + 2*circleRadius + 'px"></span>';
content         += ' <span class="fs-6 text-start align-middle">Groundwater Level Decline</span>';
content         += '</li>';
content         += '<li class="list-group-item">';
content         += ' <span class="gwRisingCircle rounded-circle align-middle" style="width: ' + 2*circleRadius +'px; height: ' + 2*circleRadius + 'px"></span>';
content         += ' <span class="fs-6 text-start align-middle">Groundwater Level Rise</span>';
content         += '</li>';
content         += '<li class="list-group-item">';
content         += ' <span class="gwNeutralCircle rounded-circle align-middle" style="width: ' + 2*circleRadius +'px; height: ' + 2*circleRadius + 'px"></span>';
content         += ' <span class="fs-6 text-start align-middle">No Change</span>';
content         += '</li>';

for(var i = 0; i < interval.length-1; i++)
  {
   content += '<li class="list-group-item"><span class="circleBase rounded-circle align-middle" style="width: ' + 2*circleRadius +'px; height: ' + 2*circleRadius +'px"></span>';
   content += '    <span class="fs-6 text-start align-middle">' + interval[i].toFixed(1) + (interval[i + 1].toFixed(1) ? '&ndash;' + interval[i + 1].toFixed(1) + '</span>' : '+');
   content += '</li>';

   circleRadius += 5;
  }
content         += '<li class="list-group-item">';
content         += ' <span class="circleBase rounded-circle align-middle" style="width: ' + 2*circleRadius +'px; height: ' + 2*circleRadius +'px"></span>';
content         += ' <span class="fs-6 text-start align-middle">>' + interval[i].toFixed(1) + '</span>';
content         += '</li>';
content         += '</ul>';
      
$('.gwChangeLegend').html(content);


// Set radius for circle marker represent the magnitude of the groundwater
//  level change
//-----------------------------------------------
function getRadius(val)
  {
   if(val <=  1.0)      { return 10; }
   else if(val <= 5.0)  { return 15; }
   else if(val <= 10.0) { return 20; }
   else if(val <= 20.0) { return 25; }
   else if(val <= 30.0) { return 30; }
   else                 { return 35; }
  }

// Set color for circle marker represent the magnitude of the groundwater
//  level change
//-----------------------------------------------
function getColor(val)
  {
   if(val > 0)      { return "#006699"; }
   else if(val < 0) { return "#f06c00"; }
   else             { return "#990099"; }
  }


// Builds selected sites
//
function processGwChange(jsonData)
  {
   console.log("processGwChange ");
   closeModal();

   selectedSeasonIntervals = jsonData;

   setfilterGwHtml();
  }

// filterSitesHtml
//
function setfilterGwHtml()
  {
   console.log("setfilterGwHtml");

   QueryOption = "selectGwChange";
        
   // Clear content
   //
   jQuery(".filterContent").empty();
   jQuery(".dlist").empty();
   //clearCustomSites()
   //clearSelectModal();
        
   // Build list of years
   //
   var oldestYears = jQuery.map(selectedSeasonIntervals, function(element,index) {return index});
   var newestYears = jQuery.map(selectedSeasonIntervals, function(element,index) {return index}).reverse();
        
   // Define content
   //
   var content = '<div class="sectionHead mb-2 p-1 rounded">Select a Year then Season</div>';
   content    += '<div class="warningModal">';
   content    += ' <div class="dlist mb-2">Choose an Older Year and Season:';
   //content    += "  <div class='row'>";
        
   // Define oldest year and season
   //
   content    += "   <select id='startingYear' class='mb-2 me-5 ps-3 pe-5'>";
   var firstYear = oldestYears[0];
   jQuery.each(oldestYears, function(index, year) 
     {
      if(year === firstYear)
        {
         content += "    <option value='" + year + "' selected='selected'>" + year + "</option>";
        }
      else
        {
         content += "    <option value='" + year + "'>" + year + "</option>";
        }
     });
   content    += "   </select>";

   content    += "   <select id='startingSeason' class='mb-2 ps-3 pe-5'>";
   var selectedOption = true;
   for (season of SeasonsList)
     {
      if(selectedSeasonIntervals[firstYear].includes(season))
        {
         if(selectedOption)
           {
            content += "    <option value='" + season + "' selected='selected'>" + season + "</option>";
            selectedOption = false;
           }
         else
           {
            content += "    <option value='" + season + "'>" + season + "</option>";
           }
        }
     }
   content    += "   </select>";

   content    += "  </div>";
   //content    += " </div>";

   // Define youngest year and season
   //
   content    += ' <div class="dlist mb-2">Choose a Younger Year and Season:';
   //content    += "  <div class='row'>";
   content    += "   <select id='endingYear' class='mb-2 me-5 ps-3 pe-5'>";
   var firstYear = newestYears[0];
   jQuery.each(newestYears, function(index, year) 
     {
      if(year === firstYear)
        {
         content += "    <option value='" + year + "' selected='selected'>" + year + "</option>";
        }
      else
        {
         content += "    <option value='" + year + "'>" + year + "</option>";
        }
     });
   content    += "   </select>";

   content    += "   <select id='endingSeason' class='mb-2 ps-3 pe-5'>";
   var selectedOption = true;
   for (season of SeasonsList)
     {
      if(selectedSeasonIntervals[firstYear].includes(season))
        {
         if(selectedOption)
           {
            content += "    <option value='" + season + "' selected='selected'>" + season + "</option>";
            selectedOption = false;
           }
         else
           {
            content += "    <option value='" + season + "'>" + season + "</option>";
           }
        }
     }
   content    += "   </select>";
   //content    += "  </div>";
   content    += " </div>";
   content    += "</div>";

   content    += ' <div><button type="button" class="btn btn-primary makeList rounded mb-2 p-1" data-toggle="button">Display Selection</button></div>';
   content    += ' <div><button type="button" class="btn-default refresh rounded mb-2 p-1" data-toggle="button">Refresh Map</button></div>';
   content    += "</div>";

   // Set content for site filter
   //
   jQuery(".filterGw").html(content);

   // Monitor year and season
   //-----------------------------------------------
   jQuery('#startingYear').change(function() 
     {
      //console.log("Handler for .change() called." );

      // Set available season for selected year
      //
      var startingYear = jQuery('#startingYear').prop('value');
      jQuery("#startingSeason").empty();
      var content = "";
      for (season of SeasonsList)
        {
         if(selectedSeasonIntervals[startingYear].includes(season))
           {
            content    += "    <option value='" + season + "'>" + season + "</option>";
           }
      }
      jQuery("#startingSeason").append(content);

     });

   jQuery('#endingYear').change(function() 
     {
      //console.log("Handler for .change() called." );

      // Set available season for selected year
      //
      var endingYear = jQuery('#endingYear').prop('value');
      jQuery("#endingSeason").empty();
      var content = "";
      for (season of SeasonsList)
        {
         if(selectedSeasonIntervals[endingYear].includes(season))
           {
            content    += "    <option value='" + season + "'>" + season + "</option>";
           }
      }
      jQuery("#endingSeason").append(content);

     });

   // Display selection button clicked
   //
   jQuery('.makeList').click(function() {

      console.log("makeGwChange clicked");

      // Ensure starting season has been selected
      //
      var startingYear   = jQuery('#startingYear').prop('value');
      var startingSeason = jQuery('#startingSeason').prop('value');

      // Ensure ending season has been selected
      //
      var endingYear     = jQuery('#endingYear').prop('value');
      var endingSeason   = jQuery('#endingSeason').prop('value');

      // Ensure starting season < ending season
      //
      if(startingYear > endingYear)
        {
         buildSelectModal();
         jQuery(".alert-success").addClass('alert-danger');
         jQuery(".alert-danger").removeClass('alert-success');
         jQuery("#selectMessage").html('Specify younger year after<br />Clicking the refresh button');
        }

      // Process user seasons
      //
      else
        {
         buildSelectModal();
         message  = ' startingSeason -> ' + startingSeason;
         message += ' startingYear -> ' + startingYear;
         message += ' endingSeason -> ' + endingSeason;
         message += ' endingYear -> ' + endingYear;
         console.log(message);
         requestGwChange(startingSeason, startingYear, endingSeason, endingYear);
        }
   });

   // Display refresh button clicked
   //
   jQuery('.refresh').click(function() {
       clearCustomLevels();
       clearSelectModal();
       setfilterGwHtml();
   });

  }


// Builds selected sites
//
function requestGwChange(startingSeason, startingYear, endingSeason, endingYear)
  {
   console.log("requestGwChange " + [startingSeason, startingYear, endingSeason, endingYear].join(" "));

   message = "Building groundwater level changemap";
   openModal(message);
     
    // Set seasons
    //
    var startingYear2 = parseInt(startingYear);
    //if(startingSeason === "Winter") { startingYear2 = startingYear + 1; }
    seasonOne = [ 
                 [startingYear,  SeasonIntervals[startingSeason][0]].join("-"), 
                 [startingYear2, SeasonIntervals[startingSeason][1]].join("-"),
                 SeasonIntervals[startingSeason][2] 
                ];
    seasonOne = [startingYear, SeasonIntervals[startingSeason]];
     
    var endingYear2 = parseInt(endingYear);
    //if(endingSeason === "Winter") { endingYear2 = endingYear + 1; }
    seasonTwo = [ 
                 [endingYear,  SeasonIntervals[endingSeason][0]].join("-"), 
                 [endingYear2, SeasonIntervals[endingSeason][1]].join("-"),
                 SeasonIntervals[endingSeason][2] 
                ];
    seasonTwo = [endingYear, SeasonIntervals[endingSeason]];

    gwLevelContent = [
                          'Groundwater Change Starting',
                          startingYear,
                          SeasonIntervals[startingSeason][0],
                          'to',
                          SeasonIntervals[startingSeason][SeasonIntervals[startingSeason].length - 2],
                          'Ending',
                          endingYear,
                          SeasonIntervals[endingSeason][0],
                          'to',
                          SeasonIntervals[endingSeason][SeasonIntervals[endingSeason].length - 2]
                         ]

    gwLevelContent = [
                          'Groundwater Change Starting',
                          startingSeason,
                          'of',
                          startingYear,
                          'Ending',
                          endingSeason,
                          'of',
                          endingYear
                         ]
    $(".gwLevelContent").html(gwLevelContent.join(" "));  

   // Reset buttons
   //
   jQuery("button#agency").val('All agencies');
   jQuery("button#agency").text('All agencies');
 
   jQuery("button#status").val('All wells');
   jQuery("button#status").text('All wells');
 
   jQuery("button#finder").val('All wells');
   jQuery("button#finder").text('All wells');
   $("#searchSites").val('');

   $(".gwLevelContent").html('');

   $('.monitoringAgency').hide();
   $('.monitoringStatus').hide();
   $('.siteFinder').hide();
   $('.sitesList').hide();
   $('#countsTable').hide();
     
    // Request for wells
    //
    var request_type = "GET";
    var script_http  = "/cgi-bin/klamath_wells/requestGwChange.py";
    var data_http    = "seasonOne=" + seasonOne.join(",");
    data_http       += "&seasonTwo=" + seasonTwo.join(",");
          
    var dataType     = "json";
          
    // Web request
    //
    webRequest(request_type, script_http, data_http, dataType, makeGwChangeMap);
   }

// Builds selected sites
//
function makeGwChangeMap(gwChanges)
  {
   console.log("makeGwChangeMap");

   var mySiteList   = [];
   var customList   = [];
   var siteCount    = 0;

   // Check if there are sites with value for change levels
   //
   if('message' in gwChanges)
     {
         $('#selectMessage').append('</br><div class="text-danger">Warning ' + gwChanges.message + "</div>");
         return;
     }

   var mapSiteSet =  buildSiteList();
   var mapSiteIDs =  mapSiteSet.map(item => item.site_id);
   console.log("mapSiteSet");
   console.log(mapSiteSet);

   // Remove existing custom sites
   //
   if(map.hasLayer(customLevels))
     {
      customLevels.clearLayers();
     }

   // Check for all sites
   //
   if(!map.hasLayer(allSites))
     {
      map.addLayer(allSites);
     }

   // Set the bounds 
   //
   map.fitBounds(allSites.getBounds());

   var mapBounds    = map.getBounds();

   // Build site list
   //
   allSites.eachLayer(function(site)
     {
      // Only process sites in mapview
      //
      if(map.hasLayer(site))
        {
         if(mapBounds.contains(site.getLatLng()))
           {
            // Attributes
            //
            var properties        = site.feature.properties;
            var site_id           = properties.site_id;
            var site_no           = properties.site_no;
            var coop_site_no      = properties.coop_site_no;
            var cdwr_id           = properties.cdwr_id;
            var station_nm        = properties.station_nm;
            var state_well_nmbr   = properties.state_well_nmbr;
            var site_tp_cd        = properties.site_tp_cd;
            var site_status       = 'Active';
               
      // Only process sites in mapview
      //
      if(mapSiteIDs.includes(site_id)) {

            // Set marker
            //                  
            myIcon                   = setIcon(site_id, site_tp_cd, site_status);
            mySiteInfo[site_id].icon = myIcon;
               
            // Groundwater change value for user-chosen interval
            //
            if(gwChanges[site_id])
              {
               var myTitle    = [];
               if(site_no)      { myTitle.push("USGS " + site_no); }
               if(coop_site_no) { myTitle.push("OWRD " + coop_site_no); }
               if(cdwr_id)      { myTitle.push("CDWR " + state_well_nmbr); }

               var latitude   = site.feature.geometry.coordinates[1];
               var longitude  = site.feature.geometry.coordinates[0];

               var gwValue    = gwChanges[site_id];
               var radius     = getRadius(Math.abs(parseFloat(gwValue)));
               var color      = getColor(gwValue);

               // Add selected
               //
               $('#tr_' + site_id).addClass('selected gwChange');

               // Text
               //
               if(gwValue > 0)
                 { 
                  table_txt = "Rise " + Math.abs(gwValue) + " feet";
                  myTitle.push(table_txt);
                  $('#tr_' + site_id).addClass('Rise');
                 }
               else if(gwValue < 0)
                 {
                  table_txt = "Decline " + Math.abs(gwValue) + " feet";
                  myTitle.push(table_txt);
                  $('#tr_' + site_id).addClass('Decline');
                 }
               else
                 {
                  table_txt = "No change";
                  myTitle.push(table_txt);
                 }
                  
               var circle     = L.circleMarker([latitude, longitude], 
                                               { 
                                                //site_no: coop_site_no,
                                                pane: 'gwChangePane',
                                                radius: radius,
                                                color: color,
                                                weight: 1,
                                                fillColor: color,
                                                fillOpacity: 0.15
               });

               // Bind tooltip to show value on hover
               //
               circle.bindTooltip(myTitle.join(" ")).openTooltip();

               // Add layer
               //
               customLevels.addLayer(circle);

               customList.push(site_id);
                         
               // Prepare list
               //
               mySiteList.push({
                      'site_id': site_id,
                      'site_no': site_no,
                      'coop_site_no': coop_site_no,
                      'cdwr_id': cdwr_id,
                      'state_well_nmbr': state_well_nmbr,
                      'station_nm': station_nm,
                      'site_status': site_status,
                      'site_icon': myIcon,
                  });
                  
               // Assign gw change data
               //
               gwChangeSites[site_id] = table_txt;
                  
               siteCount++;
              }
               
            // No groundwater change value for user-chosen interval
            //
            else
              {
               mySiteInfo[site_id].gw_change = null;
              }
           }
 
         // Add text to gw change column in table
         //
         if($('#gw_' + site_id).length > 0)
           {
            myTable.cell('#gw_' + site_id).data(table_txt);
           }
        }
        }
   });

   // Add layer of selected sites
   //
   console.log("CustomLevels count " + siteCount);
   if(siteCount > 0)
     {
      // Remove existing sites
      //
      if(map.hasLayer(allSites))
        {
         map.removeLayer(allSites);
        }

      // Remove existing sites
      //
      if(map.hasLayer(customSites))
        {
         map.removeLayer(customSites);
        }

      customLevels.addTo(map).bringToFront();

      // Add legend
      //
      $('.gwChangeLegend').show();

      // Build tables
      //
      var siteTable = createTable(mySiteList);
      $('#siteTable').html("");
      $('#siteTable').html(siteTable);
      $(".siteCount").text(siteCount);

      // Set table caption
      //
      $("#stationsCaption").html(gwLevelContent.join(" "));  
      $("#stationsCaption").append([" --", siteCount, "Sites with measurements"].join(" "));

      // Set table
      //
      DataTables ("#stationsTable")
         
      // Toggle the visibility of column
      //
      var myTable = $('#stationsTable').DataTable();
      var gwChangeColumn = 0
      myTable.columns().header().to$().each(function( index ) {
        //console.log( index + ": " + $( this ).text() );
        if($( this ).text() === 'Groundwater Change') {
            myTable.column([index]).visible( true );
            gwChangeColumn = index;
        }
      });

      // Assign row rise/no change/decline colors
      //
      var tableRows = $('.stations_table tr:contains(Decline)').addClass('Decline');
      var tableRows = $('.stations_table tr:contains(No change)').addClass('NoChange');
      var tableRows = $('.stations_table tr:contains(Rise)').addClass('Rise');
     }
      
   else
     {
      closeModal();
      var message = "No sites met the selection criteria";
      openModal(message);
      fadeModal(2000);
      clearCustomLevels()
      setfilterGwHtml();
     }

   // Close
   //
   fadeModal(2000);

   return customLevels;
  }

function clearCustomLevels()
  {
   console.log("clearCustomLevels");

   $(".gwLevelContent").html('');
   $(".gwChangeLegend").hide();

   // Remove existing groundwater change level
   //
   if(map.hasLayer(customLevels))
     {
      gwChangeSites = {};
      map.removeLayer(customLevels);
      customLevels.clearLayers();
     }

   // Set the bounds 
   //
   map.fitBounds(allSites.getBounds());
         
   // Clear gw change data
   //
   var myTable = $('#stationsTable').DataTable();
         
   // Toggle the visibility gw change column
   //
   var myTable = $('#stationsTable').DataTable();
   myTable.columns().header().to$().each(function( index ) {
       //console.log( index + ": " + $( this ).text() );
       if($( this ).text() === 'Groundwater Change') {
           myTable.column([index]).visible( false );
       }
   });
   //myTable.column([6]).visible( false );

   // Reset features
   //
   $('.monitoringAgency').show();
   $('.monitoringStatus').show();
   $('#countsTable').show();
   $('.siteFinder').show();
   $('.sitesList').show();

   // Build tables
   //
   var mySiteSet =  buildSiteList();
   leftPanel (mySiteSet);
   var siteTable = createTable (mySiteSet);
   $('#siteTable').html("");
   $('#siteTable').html(siteTable);
   $(".siteCount").text(mySiteSet.length);

   // Add table sorting
   //
   DataTables ("#stationsTable")
  }	

// Obtain values for selected sites
//
function sortByValue(myObject)
  {
   console.log("processCustomGwChanges");

   return Object.keys(obj).sort(function(a, b) {
     return obj[b] - obj[a];
   });

  }

// Builds select message
//
function buildSelectModal()
  {
   console.log("buildSelectModal ==> " + jQuery('#selectMessage').length);

   if(jQuery('#selectMessage').length > 0)
     {
      jQuery('#selectMessage').remove();
     }

      jQuery('<div id="selectMessage" class="alert alert-success">Click the refresh button<br /> when done</div>')
            .css({
                  position: "absolute",
                  width: "100%",
                  height: "100%",
                  top: 0,
                  left: 0,
                  background: "#ccc"
              }).appendTo($(".warningModal").css("position", "relative"));
  }

// Clears message
//
function clearSelectModal()
  {
   console.log("clearSelectModal ");

   if(jQuery('#selectMessage').length > 0)
     {
      jQuery('#selectMessage').remove();
     }
  }
