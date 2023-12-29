/**
 * Namespace: leftPanel
 *
 * leftPanel is a JavaScript library to set of functions to build
 *  a list of sites in a left panel that is linked to the sites on
 *  on the web map.
 *
 * version 3.12
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
var sortColuumn = 'site_id';
var sortType    = 'number';
 
// Enable selection of agency and reset sites visible
//
$("#monitoringAgency").on( "change", function( evt ) {
   console.log("Click monitoringAgency");
   console.log($("#monitoringAgency").prop('value'));
 
   // Remove existing custom levels
   //
   clearCustomLevels()
   clearSelectModal();
   setfilterGwHtml();
 
   // Build tables
   //
   var mySiteSet =  buildSiteList();
   leftPanel(mySiteSet);
   var siteTable = createTable (mySiteSet);
   $('#siteTable').html("");
   $('#siteTable').html(siteTable);
   $(".siteCount").text(mySiteSet.length);
 
   // Add table sorting
   //
   DataTables ("#stationsTable")
   $(".dt-buttons").css('width', '100%');
 
});
 
// Enable selection of measuring status and reset sites visible
//
$("#monitoringStatus").on( "change", function( evt ) {
 
   // Remove existing custom levels
   //
   clearCustomLevels()
   clearSelectModal();
   setfilterGwHtml();
 
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
   DataTables ("#stationsTable")
   $(".dt-buttons").css('width', '100%');
 
});
 
// Enable selection by USGS, OWRD, or CDWR Id 
//
$("#finderLinks").on( "click", function( evt ) {
 
   $("#searchSites").val('');
 
   // Build tables
   //
   var mySiteSet =  setFinderFilter();
   leftPanel(mySiteSet);
   var siteTable = createTable(mySiteSet);
   $('#siteTable').html("");
   $('#siteTable').html(siteTable);
   $(".siteCount").text(mySiteSet.length);
 
   // Add table sorting
   //
   DataTables ("#stationsTable")
   $(".dt-buttons").css('width', '100%');
 
});

// Read parameter codes from NwisWeb
//
function leftPanel(mySiteList)
  {
   console.log("leftPanel");
   //console.log(mySiteList);
   //console.log(sortColuumn);

   var siteSelection  = [];
   var newList        = [];
   var siteCount      = 0;

   // Check what the agency currently set to
   //
   var myAgency = $("#monitoringAgency").prop('value');
   //console.log("myAgency " + myAgency);

   // Check what the network type currently set to
   //
   var myStatus = $("#monitoringStatus").prop('value');
   //console.log("myStatus " + myStatus);
   
   // Close popup
   //
   map.closePopup();
   
   // Remove refresh button
   //
   $(".selectButton").html('');
   
   // Reset list of visible sites for left panel
   //
   $('#siteLinks').html("");
    
   // Sort list content
   //
   if(mySiteList.length > 0)
     {
      mySiteList = sorting(mySiteList, sortColuumn, sortType)
     }

   // Build list of visible sites for left panel
   //
   for(var i = 0; i < mySiteList.length; i++)
     {
      //console.log(mySiteList[i]);
      var site_id         = mySiteList[i].site_id;
      var site_no         = mySiteInfo[site_id].site_no;
      var coop_site_no    = mySiteInfo[site_id].coop_site_no;
      var state_well_nmbr = mySiteInfo[site_id].state_well_nmbr;
      var cdwr_id         = mySiteInfo[site_id].cdwr_id;
      var agency_cd       = mySiteInfo[site_id].agency_cd;
      var station_nm      = mySiteInfo[site_id].station_nm;
      var site_tp_cd      = mySiteInfo[site_id].site_tp_cd;
      var loc_web_ds      = mySiteInfo[site_id].loc_web_ds;
      var coordinates     = mySiteInfo[site_id].coordinates;
      var gw_status       = mySiteInfo[site_id].gw_status;
      var myIcon          = setIcon(site_id, site_tp_cd, gw_status);

      var myTitle         = [];
      if(site_no) { myTitle.push("USGS " + site_no); }
      if(coop_site_no) { myTitle.push("OWRD " + coop_site_no); }
      if(cdwr_id) { myTitle.push("CDWR " + cdwr_id); }

      mySite              = station_nm;
      if(/^site_id/i.test(sortColuumn)) { mySite = station_nm; sortType = 'other';}
      else if(/^site_no/i.test(sortColuumn)) { mySite = site_no;  sortType = 'number';}
      else if(/^coop_site_no/i.test(sortColuumn)) { mySite = coop_site_no; }
      else if(/^cdwr_id/i.test(sortColuumn)) { mySite = cdwr_id; }
      else { mySite = 'Not available'; }

      if(!mySite) { mySite = 'Not available'; }

      //var paneName        = 'allSites';
      //if(!/^all/i.test(myAgency) || !/^all/i.test(myStatus)) { paneName = 'customSites'; }

      //var newLayer        = L.marker(coordinates, {pane : 'customPane', icon: myIcon, title: myTitle.join(" "), siteID: site_id } );

      var wellList        = '<li>';
      wellList           += '<a href="javascript:void(0)"';
      wellList           += ' id="' + site_id + '"';
      wellList           += ' title="' + myTitle.join(" ") + '"';
      wellList           += ' class="site_link list-group-item"';
      wellList           += '>' + mySite + '</a></li>';
             
      siteSelection.push(wellList);
     }
   
   // Update list of visible sites for left panel
   //
   $('#siteLinks').html(siteSelection);
   $('#siteCount').html(' (' + mySiteList.length + ')');
   //$('#TotalStations').text(mySiteList.length);

   // Highlight the marker icon based on text link hover
   //
   $("#siteLinks").delegate( "a.site_link", "mouseenter", function( evt ) {

     if($("a.site_link").hasClass('active')) { $("a.site_link").blur(); }

     var siteID  = evt.target.id;
     //console.log("Highlight site " + siteID);
       	
     // Build highlight marker
     //
     customSite = highlightSites([siteID]);
   });

   // Unhighlight the marker icon based on text link hover
   //
   $("#siteLinks").delegate( "a.site_link", "mouseout", function( evt ) {

     if($("a.site_link").hasClass('active')) { $("a.site_link").blur(); }

     var siteID  = evt.target.id;
     //console.log("Unhighlight site " + siteID);
       	
     // Remove highlight marker
     //
    if(map.hasLayer(customSite))
      {
       map.removeLayer(customSite);
      }

     // Remove highlight entry
     //
     unhighlightList(siteID);
   });

   // Open popup based on sidebar link click
   //
   $("#siteLinks").delegate( "a.site_link", "click", function( evt ) {

     if($("a.site_link").hasClass('active')) { $("a.site_link").removeClass('active'); }

     var siteID      = evt.target.id;
     //console.log("Clicked " + siteID);

     var target  = "#" + siteID;
     $(target).toggleClass("active", true);
       	
     // Zoom to selected site
     //
     //customSites = zoomToSite([siteID]);
       	
     // PopUp of selected site
     //
     createPopUp(evt.target, siteID);
   });

   // Search list of sites
   //
   $("#searchSites").keyup(function() {
      var searchText = $(this).val();
      $("#siteLinks li").each(function() {
         //console.log($(this).text());
         var string = $(this).text();
         if(string.indexOf(searchText)!=-1) {
           $(this).show();
         } else {
           $(this).hide();
         }
      });
   });
  }

// Builds selected sites
//
function buildSiteList()
  {
   console.log("buildSiteList");

   var mySiteList   = [];
   var customList   = [];
   var siteCount    = 0;

   var mapBounds    = map.getBounds();
   presentMapExtent = mapBounds;

   // Check for all sites
   //
   if(!map.hasLayer(allSites))
     {
      map.addLayer(allSites);
     }

   // Remove existing custom sites
   //
   if(map.hasLayer(customSites))
     {
      map.removeLayer(customSites);
      customSites.clearLayers();
     }

   // Remove existing custom site
   //
   if(map.hasLayer(customSite))
     {
      map.removeLayer(customSite);
      customSite.clearLayers();
     }

   // Check what the agency currently set to
   //
   var myAgency = $("#monitoringAgency").prop('value');
   console.log("myAgency " + myAgency);

   // Check what the network type currently set to
   //
   var myStatus = $("#monitoringStatus").prop('value');
   console.log("myStatus " + myStatus);

   // Check what the agency currently set to
   //
   var QueryOption = $("button#finder").prop('value');
   //console.log("setFinderFilter --> " + QueryOption);

   console.log("buildSiteList myAgency " + myAgency + " myStatus " + myStatus + " Search Column " + QueryOption);
        
   // Check sites
   //
   allSites.eachLayer(function (site)
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
               
            var gw_status         = properties.gw_status;
            var gw_agency_cd      = properties.gw_agency_cd;
            var rc_agency_cd      = properties.rc_agency_cd;
            var rc_status         = properties.rc_status;
 
            var usgs_status       = properties.usgs_status;
            var usgs_agency_cd    = properties.usgs_agency_cd;
            var usgs_rc_status    = properties.usgs_rc_status;
            var usgs_rc_agency_cd = properties.usgs_rc_agency_cd;
 
            var owrd_status       = properties.owrd_status;
            var owrd_agency_cd    = properties.owrd_agency_cd;
            var owrd_rc_status    = properties.owrd_rc_status;
            var owrd_rc_agency_cd = properties.owrd_rc_agency_cd;
 
            var cdwr_status       = properties.cdwr_status;
            var cdwr_agency_cd    = properties.cdwr_agency_cd;
            var cdwr_rc_status    = properties.cdwr_rc_status;
            var cdwr_rc_agency_cd = properties.cdwr_rc_agency_cd;
              
            var latitude          = site.feature.geometry.coordinates[1];
            var longitude         = site.feature.geometry.coordinates[0];
            var myIcon            = properties.icon;
 
            var icon_status       = gw_status;
 
            //console.log("Site " + siteID);
            //console.log(gw_agency_cd);

            var siteFlag        = false;

            site.setOpacity(0.1);

            // All monitoring agency and check status
            //
            if(/^all/i.test(myAgency))
              {   
               //console.log(" ");
               //console.log("Site " + site_id + " myAgency " + myAgency + " myStatus " + myStatus);
               //console.log("Periodic " + gw_status + " Recorder " + rc_status + " siteFlag " + siteFlag);
               if(/all/i.test(myStatus))
                 {
                     if(myStatus.toLowerCase().includes('inactive'))
                     {
                         if(gw_status.toLowerCase() == 'inactive') { icon_status = 'Inactive'; siteFlag = true; }
                     }
                     else if(myStatus.toLowerCase().includes('active'))
                     {
                         if(gw_status.toLowerCase() == 'active') { siteFlag = true; }
                         if(rc_status.toLowerCase() == 'active') { siteFlag = true; }
                     }
                     else { siteFlag = true; }
                 }
               else if(/periodic/i.test(myStatus))
                 {
                     if(myStatus.toLowerCase().includes('inactive'))
                     {
                         if(gw_status.toLowerCase() == 'inactive') { icon_status = 'Inactive'; siteFlag = true; }
                     }
                     else if(myStatus.toLowerCase().includes('active'))
                     {
                         if(gw_status.toLowerCase() == 'active') { siteFlag = true; }
                     }
                     else { siteFlag = true; }
                 }
               else if(/recorders/i.test(myStatus))
                 {
                     if(myStatus.toLowerCase().includes('inactive'))
                     {
                         if(rc_status.toLowerCase() == 'inactive') { icon_status = 'Inactive'; siteFlag = true; }
                     }
                     else if(myStatus.toLowerCase().includes('active'))
                     {
                         if(rc_status.toLowerCase() == 'active') { siteFlag = true; }
                     }
                     else
                     {
                         if(rc_agency_cd)
                         {
                             if(rc_status.toLowerCase() == 'inactive') { icon_status = 'Inactive'; }
                             else if(rc_status.toLowerCase() == 'active')
                             {
                                 icon_status = 'Active';
                             }
                             siteFlag = true;
                         }
                     }
                 }
               else
                 {
                  siteFlag = true;
                 }
               //console.log("Periodic " + gw_status + " Recorder " + rc_status + " siteFlag " + siteFlag);
              }

            // Check monitoring agency then check status
            //
            else if(jQuery.inArray(myAgency,gw_agency_cd) > -1 || jQuery.inArray(myAgency,rc_agency_cd) > -1)
               {
               var agency_gw_status = properties[myAgency.toLowerCase() + '_status']
               var agency_rc_cd     = properties[myAgency.toLowerCase() + '_rc_agency_cd']
               var agency_rc_status = properties[myAgency.toLowerCase() + '_rc_status']
               //console.log(" ");
               //console.log("Site " + site_id + " myAgency " + myAgency + " myStatus " + myStatus);
               //console.log("Periodic " + gw_status + " Recorder " + rc_status);
               //console.log("Agency gw agency |" + agency_gw_status + "|");
               //console.log("Agency rc agency |" + agency_rc_status + "|");
                   
               if(/all/i.test(myStatus))
                 {
                     if(agency_gw_status.toLowerCase() == 'active') { siteFlag = true; }
                     else if(agency_gw_status.toLowerCase() == 'inactive') { icon_status = 'Inactive'; siteFlag = true; }
                     else { siteFlag = true; }

                     if(agency_rc_status.toLowerCase() == 'active') { siteFlag = true; }
                     else if(agency_rc_status.toLowerCase() == 'inactive') { icon_status = 'Inactive'; siteFlag = true; }
                     else { siteFlag = true; }
                 }
               else if(myStatus.toLowerCase().includes('periodic'))
                 {
                     if(jQuery.inArray(myAgency,gw_agency_cd) > -1)
                     {
                         if(myStatus.toLowerCase().includes('inactive'))
                         {
                             if(agency_gw_status.toLowerCase() == 'inactive') { icon_status = 'Inactive'; siteFlag = true; }
                         }
                         else if(myStatus.toLowerCase().includes('active'))
                         {
                             if(agency_gw_status.toLowerCase() == 'active') { siteFlag = true; }
                         }
                         else
                         {
                             if(agency_gw_status.toLowerCase() == 'inactive') { icon_status = 'Inactive'; }
                             else if(agency_gw_status.toLowerCase() == 'active') { icon_status = 'Active'; }
                             siteFlag = true;
                         }
                     }
                 }
               else if(myStatus.toLowerCase().includes('recorders'))
                 {
                     if(jQuery.inArray(myAgency,rc_agency_cd) > -1)
                     {
                         if(myStatus.toLowerCase().includes('inactive'))
                         {
                             if(agency_rc_status.toLowerCase() == 'inactive') { icon_status = 'Inactive'; siteFlag = true; }
                         }
                         else if(myStatus.toLowerCase().includes('active'))
                         {
                             if(agency_rc_status.toLowerCase() == 'active') { siteFlag = true; }
                         }
                         else
                         {
                             if(agency_rc_status.toLowerCase() == 'inactive') { icon_status = 'Inactive'; }
                             else if(agency_rc_status.toLowerCase() == 'active') { icon_status = 'Active'; }
                             siteFlag = true;
                         }
                     }
                 }
               else
                 {
                  siteFlag = true;
                 }
              }

            // Add site
            //
            if(siteFlag)
              {   
               // Build marker title
               //
               var myTitle = [];
               if(site_no)         { myTitle.push("USGS " + site_no); }
               if(coop_site_no)    { myTitle.push("OWRD " + coop_site_no); }
               if(cdwr_id)         { myTitle.push("CDWR " + cdwr_id); }

               // Add layer
               //                  
               myIcon = setIcon(site_id, site_tp_cd, icon_status);

               // Add layer
               //
               var latlng = L.latLng({ lat: latitude, lng: longitude });
               var layer  = L.marker(latlng, {pane: 'customSites', icon: myIcon, title: myTitle.join(" "), siteID: site_id } );

               // Popup and highlight/unhighlight site in list of left panel
               //
               layer.on({
                   click: (function(evt) { createPopUp(evt.target, site_id); }),
                   mouseover: (function(evt) { highlightList(site_id); }),
                   mouseout: (function(evt) { unhighlightList(site_id); })
               });

               customList.push(layer);
                         
                  mySiteList.push({
                      'site_id': site_id,
                      'station_nm': station_nm,
                      'site_no': site_no,
                      'coop_site_no': coop_site_no,
                      'cdwr_id': cdwr_id,
                      'site_status': icon_status,
                      'site_icon': myIcon
                  });
               
               siteCount++;
              }

            // Skip site
            //
            else
              {   
               site.unbindPopup();
               site.off({
                   click: (function(evt) { nothing = 'nothing'; }),
                   mouseover: (function(evt) { nothing = 'nothing'; }),
                   mouseout: (function(evt) { nothing = 'nothing'; })
               });
              }
 
           }
        }
     });

   // Add layer of selected sites
   //
   if(customList.length > 0)
     {
      console.log("customSites --> " + customList.length);

      customSites = new L.FeatureGroup(customList);

      customSites.addTo(map).bringToFront();
     }

   return mySiteList;
  }

// Builds site filter content
//
function setFinderFilter()
  {
   console.log("setFinderFilter");

   // Check what the agency currently set to
   //
   var QueryOption = $("button#finder").prop('value');
   console.log("setFinderFilter --> " + QueryOption);
        
   // Set
   //
   var newList    = [];
   sortColuumn    = 'site_id';
   sortType       = 'number';
        
   // Set list
   //
   var mySiteList = buildSiteList();

   // Build list of visible sites for left panel
   //
   for(var i = 0; i < mySiteList.length; i++)
     {
      //console.log(mySiteList[i]);
      var site_id         = mySiteList[i].site_id;
      var site_no         = mySiteInfo[site_id].site_no;
      var coop_site_no    = mySiteInfo[site_id].coop_site_no;
      var state_well_nmbr = mySiteInfo[site_id].state_well_nmbr;
      var cdwr_id         = mySiteInfo[site_id].cdwr_id;
      var station_nm      = mySiteInfo[site_id].station_nm;

      var siteFlag        = false;

      if(/^All/i.test(QueryOption))
        {
         if(site_id) { siteFlag = true; }
         //else if(site_no.length > 0) { siteCount = 1; }
        }

      else if(/^USGS/i.test(QueryOption))
        {
         if(site_no) { siteFlag = true; }
         sortColuumn = 'site_no';
        }

      else if(/^Station/i.test(QueryOption))
        {
         if(station_nm) { siteFlag = true; }
         sortColuumn = 'station_nm';
         sortType    = 'other';
         //else if(station_nm.length > 0) { siteCount = 1; }
        }

      else if(/^OWRD/i.test(QueryOption))
        {
         if(coop_site_no) { siteFlag = true; }
         sortColuumn = 'coop_site_no';
         sortType    = 'other';
         //else if(coop_site_no.length > 0) { siteCount = 1; }
        }

      else
        {
         if(cdwr_id) { siteFlag = true; }
         sortColuumn = 'cdwr_id';
         sortType    = 'other';
         //else if(state_well_nmbr.length > 0) { siteCount = 1; }
        }

      if(siteFlag)
        {
         newList.push({'site_id': site_id, 'station_nm': station_nm, 'site_no': site_no, 'coop_site_no': coop_site_no, 'cdwr_id': cdwr_id});
         //console.log("Site " + coop_site_no + " on map");
        }
    }
    
   // No sites
   //
   if(newList.length < 1)
     {
      message = "No sites found matching search";
      openModal(message);
     }
 
   // Return
   //
   return newList;
   
  }

// Highlight selected sites
//
function highlightSites(mySiteList)
  {
   //console.log("highlightSites");

   var customList   = [];
   var siteCount    = 0;

   var mapBounds    = map.getBounds();

   // Remove existing custom list
   //
   if(map.hasLayer(customSite))
     {
      map.removeLayer(customSite);
     }

   if($("a.site_link").hasClass('active')) { $("a.site_link").removeClass('active'); }

   // Build layer of selected sites
   //
   allSites.eachLayer(function (site)
     {
      // Only process sites in mapview
      //
      if(map.hasLayer(site))
        {
         if(mapBounds.contains(site.getLatLng()))
           {
            var site_id = site.feature.properties.site_id;

            if(jQuery.inArray(site_id,mySiteList) > -1)
              {   
               var site_no      = mySiteInfo[site_id].site_no;
               var coop_site_no = mySiteInfo[site_id].coop_site_no;
               var cdwr_id      = mySiteInfo[site_id].cdwr_id;
               var agency_cd    = mySiteInfo[site_id].agency_cd;
               var station_nm   = mySiteInfo[site_id].station_nm;
               var site_tp_cd   = mySiteInfo[site_id].site_tp_cd;
                        
               // Build marker title
               //
               var myTitle = [];
               if(site_no)      { myTitle.push("USGS " + site_no); }
               if(coop_site_no) { myTitle.push("OWRD " + coop_site_no); }
               if(cdwr_id)      { myTitle.push("CDWR " + cdwr_id); }
   
               // Build layer
               //
               var myIcon       = setIcon(site_id, site_tp_cd, 'highlight');
               var latlng       = site._latlng;
               var layer        = L.marker(latlng, {pane : 'customPane', icon: myIcon, title: myTitle.join(" "), site_id: site_id } );
         
               // Create popup
               //
               layer.on('click', function(evt) {
                         createPopUp(evt.target, site_id);
                         //clickPopup = true;
               });
      
               // Bind tooltip to show value on hover
               //
               customList.push(layer);
            
               siteCount++;
              }
           }
        }
     });

   // Add layer of selected sites
   //
   if(customList.length > 0)
     {
      //console.log("CustomSites " + siteCount);
      customSite = new L.FeatureGroup(customList);

      customSite.addTo(map).bringToFront();

      //var customZoom = map.getBoundsZoom(customSites.getBounds(), true);
      //console.log("customZoom " + customZoom);
     }

   return customSite;
  }	

// Set highlight
//
function highlightList(siteID)
  {
   //console.log("highlightList");

   if($("a.site_link").hasClass('active')) { $("a.site_link").removeClass('active'); }

   //var layer  = evt.target;
   //var siteID = layer.feature.properties.site_id;

   var target = "a#" + siteID;
   //$(target).toggleClass("active");
   if(!$(target).hasClass('active')) { $(target).addClass('active'); }

  }	

function unhighlightList(siteID)
  {
   //console.log("unhighlightList");

   if($("a.site_link").hasClass('active')) { $("a.site_link").removeClass('active'); }

   //var layer   = evt.target;
   //var site_id = layer.feature.properties.site_id;
   //console.log("unhighlightList " + site_id);

   //var target  = "#" + site_id;
   //$(target).toggleClass("active", false);
  }	

// Monitoring agency
//
function monitoringLeftPanel(evt)
  {
   console.log("monitoringLeftPanel");

   var buttonID = evt.target.id
   console.log("monitoringLeftPanel " + buttonID);

   // Check what the agency currently set to
   //
   var myAgency = $("#monitoringAgency").prop('value');
   console.log("myAgency " + myAgency);

   // Check what the network type currently set to
   //
   var myStatus = $("#monitoringStatus").prop('value');
   console.log("myStatus " + myStatus);

   // Check what the period type currently set to
   //
   //var myPeriod = $("button#periodofrecord").prop('value');
  }	

function clearCustomLayer(customPane, customLayer)
  {
   console.log("clearCustomLayer");

   // Remove existing custom sites
   //
   if(map.hasLayer(customLayer))
     {
      customLayer.clearLayers();

      map.getPane(customPane).style.pointerEvents = 'none';

      map.getPane(customPane).style.zIndex = 590;
     }
  }	

function sorting(tmpObject, column, typeSort)
  {
   if(typeSort === "number")
     {
      sortedObject = tmpObject.sort(function(a,b) {return (parseFloat(a[column]) > parseFloat(b[column])) ? 1 : ((parseFloat(b[column]) > parseFloat(a[column])) ? -1 : 0);} );
     }
   else
     {
      sortedObject = tmpObject.sort(function(a,b) {return (a[column] > b[column]) ? 1 : ((b[column] > a[column]) ? -1 : 0);} );
     }

  return sortedObject;
}

// Builds selected sites
//
function zoomToSite(mySiteList)
  {
   //console.log("zoomToSite");

   var customList   = [];
   var siteCount    = 0;

   var mapBounds    = map.getBounds();

   // Remove existing custom list
   //
   if(map.hasLayer(customSites))
     {
      map.removeLayer(customSites);
     }

   // Build layer of selected sites
   //
   allSites.eachLayer(function (site)
     {
      // Only process sites in mapview
      //
      if(map.hasLayer(site))
        {
         var site_id       = site.feature.properties.site_id;

         if(jQuery.inArray(siteID,mySiteList) > -1)
           {   
            var site_no      = mySiteInfo[site_id].site_no;
            var coop_site_no = mySiteInfo[site_id].coop_site_no;
            var cdwr_id      = mySiteInfo[site_id].cdwr_id;
            var agency_cd    = mySiteInfo[site_id].agency_cd;
            var station_nm   = mySiteInfo[site_id].station_nm;
                        
            // Build marker title
            //
            var myTitle = [];
            if(site_no)      { myTitle.push("USGS " + site_no); }
            if(coop_site_no) { myTitle.push("OWRD " + coop_site_no); }
            if(cdwr_id)      { myTitle.push("CDWR " + cdwr_id); }
   
            // Build layer
            //
            var myIcon       = setIcon(site_id, "GW", 'highlight');
            var latlng       = site._latlng;
            var layer        = L.marker(latlng, {icon: myIcon, title: myTitle.join(" "), siteID: siteID } );
         
            // Create popup
            //
            layer.on('click', function(evt) {
                      createPopUp(evt.target, site_no);
            });
      
            // Bind tooltip to show value on hover
            //
            customList.push(layer);
            
            siteCount++;
           }
        }
     });

   // Add layer of selected sites
   //
   if(customList.length > 0)
     {
      //console.log("CustomSites " + siteCount);
      customSites = new L.FeatureGroup(customList);

      customSites.addTo(map);

      map.fitBounds(customSites.getBounds());

      //var customZoom = map.getBoundsZoom(customSites.getBounds(), true);
      //console.log("customZoom " + customZoom);
     }

   return customSites;
  }	
