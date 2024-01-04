/**
 * Namespace: gwFilter
 *
 * parameterData is a JavaScript library to provide a set of functions to manage
 *  the data exploration tool.
 *
 * version 3.21
 * January 4, 2024
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
var SeasonsList = ['Winter','Spring','Summer','Fall'];

var selectedSeasonIntervals;
var prepareGwChangeMap = true;
   
var SeasonAgruments = [];
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
filterGroundwater.push('    <div class="section text-xs-left">');
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
var content      = '<ul class="no-bullets">';
content         += '<li>';
//content         += ' <img class="symbols lineSymbol" src="icons/red_gw.png" />';
content         += ' <span class="gwDecliningCircle" style="vertical-align:middle; width: ' + 2*circleRadius +'px; height: ' + 2*circleRadius + 'px"></span>';
content         += ' <span class="vertical-centered-text">Groundwater Level Decline</span>';
content         += '</li>';
content         += '<li>';
//content         += ' <img class="symbols lineSymbol" src="icons/blue_gw.png" />';
content         += ' <span class="gwRisingCircle" style="vertical-align:middle; width: ' + 2*circleRadius +'px; height: ' + 2*circleRadius + 'px"></span>';
content         += ' <span class="vertical-centered-text">Groundwater Level Rise</span>';
content         += '</li>';
content         += '<li>';
//content         += ' <img class="symbols lineSymbol" src="icons/violet_gw.png" />';
content         += ' <span class="gwNeutralCircle" style="vertical-align:middle; width: ' + 2*circleRadius +'px; height: ' + 2*circleRadius + 'px"></span>';
content         += ' <span class="vertical-centered-text">No Change</span>';
content         += '</li>';

for(var i = 0; i < interval.length-1; i++)
  {
   content += '<li><span class="circleBase" style="vertical-align:middle; width: ' + 2*circleRadius +'px; height: ' + 2*circleRadius +'px"></span>';
   content += '    <span>' + interval[i].toFixed(1) + (interval[i + 1].toFixed(1) ? '&ndash;' + interval[i + 1].toFixed(1) + '</span>' : '+');
   content += '</li>';

   circleRadius += 5;
  }
content         += '<li>';
content         += ' <span class="circleBase text-left" style="vertical-align:middle; width: ' + 2*circleRadius +'px; height: ' + 2*circleRadius +'px"></span>';
content         += ' <span>>' + interval[i].toFixed(1) + '</span>';
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
   var content = '<div class="sectionHead">Select a Year then Season</div>';
   content    += '<div class="warningModal">';
   content    += ' <div class="dlist">Choose an Older Year and Season:';
   content    += "  <div class='row'>";
        
   // Define oldest year and season
   //
   content    += "   <select id='startingYear'>";
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

   content    += "   <select id='startingSeason'>";
   var selectedOption = "None";
   jQuery.each(SeasonsList, function(index, seasonOption) 
     {
      if(selectedSeasonIntervals[firstYear].includes(seasonOption))
        {
         if(selectedOption === "None")
           {
            content += "    <option value='" + seasonOption + "' selected='selected'>" + seasonOption + "</option>";
            selectedOption = true;
           }
         else
           {
            content += "    <option value='" + seasonOption + "'>" + seasonOption + "</option>";
           }
        }
     });
   content    += "   </select>";

   content    += "  </div>";
   content    += " </div>";

   // Define youngest year and season
   //
   content    += ' <div class="dlist">Choose a Younger Year and Season:';
   content    += "  <div class='row'>";
   content    += "   <select id='endingYear'>";
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

   content    += "   <select id='endingSeason'>";
   var selectedOption = "None";
   jQuery.each(SeasonsList, function(index, seasonOption) 
     {
      if(selectedSeasonIntervals[firstYear].includes(seasonOption))
        {
         if(selectedOption === "None")
           {
            content += "    <option value='" + seasonOption + "' selected='selected'>" + seasonOption + "</option>";
            selectedOption = true;
           }
         else
           {
            content += "    <option value='" + seasonOption + "'>" + seasonOption + "</option>";
           }
        }
     });
   content    += "   </select>";
   content    += "  </div>";
   content    += " </div>";
   content    += "</div>";

   content    += ' <div><button type="button" class="btn btn-primary makeList" data-toggle="button">Display Selection</button></div>';
   content    += ' <div><button type="button" class="btn-default refresh" data-toggle="button">Refresh Map</button></div>';
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
      var startingYear = "";
      jQuery("#startingYear option:selected").each(function() {
         startingYear = jQuery( this ).val();
      });
      jQuery("#startingSeason").empty();
      var content = "";
      jQuery.each(SeasonsList, function(index, seasonOption) 
        {
         if(selectedSeasonIntervals[startingYear].includes(seasonOption))
           {
            content    += "    <option value='" + season + "'>" + seasonOption + "</option>";
           }
      });
      jQuery("#startingSeason").append(content);

     });

   jQuery('#endingYear').change(function() 
     {
      //console.log("Handler for .change() called." );

      // Set available season for selected year
      //
      var endingYear = "";
      jQuery("#endingYear option:selected").each(function() {
         endingYear = jQuery( this ).val();
      });
      jQuery("#endingSeason").empty();
      var content = "";
      jQuery.each(SeasonsList, function(index, seasonOption) 
        {
         if(selectedSeasonIntervals[startingYear].includes(seasonOption))
           {
            content    += "    <option value='" + season + "'>" + seasonOption + "</option>";
           }
      });
      jQuery("#endingSeason").append(content);

     });

   // Display selection button clicked
   //
   jQuery('.makeList').click(function() {

      console.log("makeGwChange clicked");

      // Ensure starting season has been selected
      //
      jQuery("#startingYear option:selected").each(function() {
         startingYear = jQuery( this ).val();
      });
      jQuery("#startingSeason option:selected").each(function() {
         startingSeason = jQuery( this ).val();
      });

      // Ensure ending season has been selected
      //
      jQuery("#endingYear option:selected").each(function() {
         endingYear = jQuery( this ).val();
      });
      jQuery("#endingSeason option:selected").each(function() {
         endingSeason = jQuery( this ).val();
      });

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

    var gwLevelContent = [
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

    var gwLevelContent = [
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

   // Check for all sites
   //
   if(!map.hasLayer(allSites))
     {
      map.addLayer(allSites);
     }

   // Set the bounds 
   //
   map.fitBounds(allSites.getBounds());

    // Build tables
    //
    var mySiteSet =  buildSiteList();
    leftPanel(mySiteSet);
    var siteTable = createTable(mySiteSet);
    $('#siteTable').html("");
    $('#siteTable').html(siteTable);
    $(".siteCount").text(mySiteSet.length);

    // Set table caption
    //
    $("#stationsCaption").html(gwLevelContent.join(" "));  

    // Set table
    //
    DataTables ("#stationsTable")
    $(".dt-buttons").css('width', '100%');
     
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
   console.log("gwChanges");
   console.log(gwChanges);
   console.log("gwChanges");

   // Check if there are sites with value for change levels
   //
   if('message' in gwChanges)
     {
         $('#selectMessage').append('</br><div class="text-danger">Warning ' + gwChanges.message + "</div>");
         return;
     }

   var customList   = [];
   var siteCount    = 0;

   var mapBounds    = map.getBounds();
   presentMapExtent = mapBounds;

   // Remove existing custom sites
   //
   if(map.hasLayer(customLevels))
     {
      customLevels.clearLayers();
     }
         
    // Toggle the visibility of column
    //
    var myTable = $('#stationsTable').DataTable();
      
    myTable.column([6]).visible( true );

   // Build site list
   //
   allSites.eachLayer(function(site) {
      if(map.hasLayer(site))
        {
         var table_txt       = 'No measurement';
               
         var properties      = site.feature.properties;
         var site_id         = properties.site_id;

         //console.log("Site " + site_id);
         if($('#gw_' + site_id).length > 0)
           {
            myTable.cell('#gw_' + site_id).data(table_txt);
           }

         if(mapBounds.contains(site.getLatLng()))
           {
            var site_no         = properties.site_no;
            var coop_site_no    = properties.coop_site_no;
            var cdwr_id         = properties.cdwr_id;
            var station_nm      = properties.station_nm;
            var state_well_nmbr = properties.state_well_nmbr;

            var siteID          = site_id;
               
            var site_txt        = [];
            if(site_no > 0) { site_txt.push("USGS " + site_no); }
            if(coop_site_no > 0) { site_txt.push("OWRD " + coop_site_no); }
            if(cdwr_id > 0)      { site_txt.push("CDWR " + state_well_nmbr); }

            // Groundwater change value for user-chosen interval
            //
            if(typeof gwChanges[siteID] !== "undefined")
              {
               var latitude   = site.feature.geometry.coordinates[1];
               var longitude  = site.feature.geometry.coordinates[0];

               var gwValue    = gwChanges[siteID];
               var radius     = getRadius(Math.abs(parseFloat(gwValue)));
               var color      = getColor(gwValue);

               // Text
               //
               if(gwValue > 0)
                 { 
                  table_txt = "Rise " + Math.abs(gwValue) + " feet";
                  site_txt.push(table_txt);
                 }
               else if(gwValue < 0)
                 {
                  table_txt = "Decline " + Math.abs(gwValue) + " feet";
                  site_txt.push(table_txt);
                 }
               else
                 {
                  table_txt = "No change";
                  site_txt.push(table_txt);
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
               circle.bindTooltip(site_txt.join(" ")).openTooltip();

               // Add layer
               //
               customLevels.addLayer(circle);

               siteCount++;
              }

            // Hide row No measurement for user-chosen interval
            //
            else
              {
                  $('#tr_' + site_id).css('display','none');
              }
           }
 
         // Add text to gw change column in table
         //
         if($('#gw_' + site_id).length > 0)
           {
            myTable.cell('#gw_' + site_id).data(table_txt);
           }
        }
   });

   // Add layer of selected sites
   //
   console.log("CustomLevels count " + siteCount);
   if(siteCount > 0)
     {
      // Set table caption
      //
      $("#stationsCaption").append([" --", siteCount, "Sites with measurements"].join(" "));

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
      map.removeLayer(customLevels);
      customLevels.clearLayers();
     }
         
   // Toggle the visibility
   //
   var myTable = $('#stationsTable').DataTable();
 
   myTable.column([6]).visible( false );

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
   $(".dt-buttons").css('width', '100%');
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
