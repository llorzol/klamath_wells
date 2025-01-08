/**
 * Namespace: datatablesSupport
 *
 * datatablesSupport is a JavaScript library to provide a set of functions to build
 *  a table with buttons to export table content.
 *
 * version 3.08
 * February 14, 2024
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

var excelButton = 
  {
   exportOptions: {
       customize: function ( xlsx ) {
           var sheet = xlsx.xl.worksheets['sheet1.xml'];

           // Highlight table caption
           //
           $('row:first c', sheet).attr( 's', '42' );
       },
       format: {
           body: function ( data, row, column, node ) {

               // Strip href
               //
               if(!data) { data = '--'; }
               else if(data.length < 1) { data = '--'; }

               return data;
           }
       }
   }
  }

var excelButton2 = 
  {
   exportOptions: {
       format: {
           body: function ( data, row, column, node ) {

               // Strip href
               //
               //var data = column > 0 || column < 2 ? data.replace( /^<a\s+(?:[^>]*?\s+)?href=(["'])(.*?)/i, 'Yes' ) : data;
               //var data = column > 0 || column < 2 ? data.replace( /^(<a\s+(?:[^>]*?\s+)?href=(["'])(.*?)(\d+))/i, 'Yes' ) : data;
               //var data = column > 0 || column < 2 ? data.replace( /^(<a\s+(?:[^>]*?\s+)?href=(["'])(.*?)(\d+)*">)((\d+))<\/a>/i, $6 ) : data;
               var data = column > 0 || column < 3 ? data.replace( /^(<a\s+(?:[^>]*?\s+)?href=(["'])(.*?)(\d+)*">)/i, '' ) : data;
               data     = column > 0 || column < 3 ? data.replace( /(<\/a>)$/i, '' ) : data;
               data     = column === 0 ? data.replace( /^(<span class="site_no">)/i, '' ) : data;
               data     = column === 0 ? data.replace( /(<\/span>)$/i, '' ) : data;

               // Strip img tag
               //
               var data = column > 2 || column < 7 ? data.replace( /<img src="Symbols\/\w+\W\w+.gif">/, 'Yes' ) : data;

               return data;
         }
       }
     }
  }

var printButton = 
  {
   exportOptions: {
       format: {
           body: function (data, row, column, node ) {
               //jQuery('.stations_table > caption' ).remove();
               return data;
         }
       }
     }
  }

// Describes Excel structure
//
//    https://datatables.net/reference/button/excelHtml5#Customisation
//    https://docs.sheetjs.com/
//    http://officeopenxml.com/SSstyles.php
//
function fpsDataTable (tableSelector, myTitle, excelFileName) 
  {
     console.log("fpsDataTable");
     console.log("datatablesInit " + jQuery(tableSelector).length);

     // TableSorter - New Version with Fixed Headers
     //-------------------------------------------------
     jQuery(tableSelector).DataTable( {
        "paging":    false,
        "ordering":  true,
        "info":      false,
        "searching": false,
        "autoWidth": true,
        "stripeClasses": [],
        "fixedHeader": { header: true, footer: false },
        dom: 'Bfrtip',
        "order": [[0, 'asc' ]],
        buttons: [
            $.extend( true, {}, excelButton, {
                extend: 'excelHtml5',
                exportOptions: { columns: [0, 1, 2, 3, 4, 5, 6, 7] },
                title: '',
                messageTop: myTitle,
                sheetName: "FPS",
                filename: excelFileName,
                customize: function ( xlsx ) {
                    var sheet = xlsx.xl.worksheets['sheet1.xml'];

                    // Highlight table caption
                    //
                    $('row:first c', sheet).attr( 's', '42' );
 
                    // Left justify column A for all rows except row 1
                    //  [not working ??]
                    //
                    $('row:gt(0) c[r="A"]', sheet).attr( 's', '50' );
 
                    // Set column A to text for all rows except row 1
                    //
                    $('row:gt(0) c[r="A"]', sheet).attr( 's', '0' );
                }
            } ),
            $.extend( true, {}, printButton, {
                extend: 'print',
                title: myTitle,
                autoPrint: false
            } )
        ]
     });
  }

function DataTables (tableSelector) 
  {
     console.log("DataTables");
     console.log("datatablesInit " + jQuery(tableSelector).length);
     var myTitle = $('#stationsCaption').text();
     //console.log("myTitle " + myTitle);

     // TableSorter - New Version with Fixed Headers
     //-------------------------------------------------
     var table = jQuery(tableSelector).DataTable( {
         rowGroup: {dataSrc: 1 },
         "paging":    false,
         scrollCollapse: true,
         scrollY: '40vh',
         "ordering":  true,
         //"info":      false,
         //"searching": false,
         "autoWidth": true,
         "stripeClasses": [],
         "bAutoWidth": false,
         "columnDefs": [
            {
                "targets": [ 6 ],
                "visible": false,
                "searchable": false
            }],
         "order": [[2, 'asc' ]],
         dom: 'Bfrtip',
         buttons: [
            {
                extend: 'excelHtml5',
                text: 'Excel',
                sheetName: "KlamathWells",
                messageTop: myTitle,
                title: '',
                exportOptions: {
                    columns: [0, 2, 3, 4, 5, 6, 7],
                    rows: ':visible'
                },
                    customize: function ( xlsx ) {
                        var sheet = xlsx.xl.worksheets['sheet1.xml'];
                        $('row:first c', sheet).attr( 's', '17' );
                        
                        // Get unique values from rowGroup.dataSrc column
                        //
                        var groupNames = [... new Set( table.column(0).data().toArray() )];
                        //console.log('Groups:', groupNames);
        
                        // Loop over all cells in sheet
                        //
                        //$('row a', sheet).each( function () {
                        var skippedHeader = false;
                        $('row c', sheet).each( function () {
                            //console.log(" Row " + $(this).text());
                            
                            if (skippedHeader) {
                                
                                // If active
                                //
                                if ( $('is t', this).text().indexOf("Active") > -1 ) {
                                   $(this).attr('s', '37');
                               }
        
                               else if ( $('is t', this).text().indexOf("Inactive") > -1 ) {
                                   $(this).attr('s', '2');
                               }
                            }
                            else {
                                skippedHeader = true;
                            }
                        });
                    }
            },
            {
                extend: 'print',
                messageTop: myTitle,
                autoPrint: false,
                exportOptions: {
                    columns: [0, 2, 3, 4, 5, 6, 7],
                    rows: ':visible'
                },
                customize: function (doc) {
                    $(doc.document.body).find('h1').css('font-size', '16pt');
                    $(doc.document.body).find('h1').css('text-align', 'center');
                    $(doc.document.body).find('h1').css('font-weight:', 'bold');
                    $(doc.document.body).find('div').css('font-size', '14pt');
                    $(doc.document.body).find('div').css('text-align', 'center');
                    $(doc.document.body).find('div').css('font-weight:', 'bold');
                    $(doc.document.body).find('thead').css('font-size', '12pt');
                    $(doc.document.body).find('tbody').css('font-size', '10pt');
                }
            },
            {
                extend: 'pdfHtml5',
                messageTop: myTitle,
                autoPrint: false,
                exportOptions: {
                    columns: [0, 2, 3, 4, 5, 6, 7],
                    rows: ':visible'
                },
                customize: function (doc) {
                    doc.defaultStyle.fontSize = 8;
                    doc.styles.tableHeader.fontSize = 8;
                }
            },
            {
                text: 'Geojson',
                autoPrint: true,
                action: function ( e, dt, node, config ) {
                    message = 'Exporting sites in geojson format';
                    openModal(message);
                    fadeModal(3000);
                    var file = 'KlamathSites.geojson';
                      saveAs(new File([JSON.stringify(geojsonSites)], file, {
                        type: "text/plain;charset=utf-8"
                      }), file);
                }
            }
        ]
     });
  }

function DataTablesSave1 (tableSelector) 
  {
     console.log("datatablesInit " + jQuery(tableSelector).length);
     var myTitle = $('#stationsCaption').text();
     console.log("myTitle " + myTitle);

     // TableSorter - New Version with Fixed Headers
     //-------------------------------------------------
     var table = jQuery(tableSelector).DataTable( {
        "paging":    false,
         scrollCollapse: true,
         scrollY: '40vh',
         "ordering":  true,
        //"info":      false,
        //"searching": false,
        "autoWidth": true,
        "stripeClasses": [],
        "bAutoWidth": false,
        "columnDefs": [
            {
                "targets": [ 6 ],
                "visible": false,
                "searchable": false
            }],
        "order": [[2, 'asc' ]],
        dom: 'Bfrtip',
        buttons: [
            {
                extend: 'excelHtml5',
                exportOptions: { columns: [0, 2, 3, 4, 5, 6, 7] },
                title: '',
                messageTop: myTitle,
                sheetName: "Wells"
            },
            {
                extend: 'print',
                autoPrint: false
            }
        ]
     });
  }

function DataTablesSave2 (tableSelector) 
  {
     console.log("datatablesInit " + jQuery(tableSelector).length);
     var myTitle = $('#stationsCaption').text();
     console.log("myTitle " + myTitle);

     // TableSorter - New Version with Fixed Headers
     //-------------------------------------------------
     var table = jQuery(tableSelector).DataTable( {
        "paging":    false,
        "ordering":  true,
        "info":      false,
        "searching": false,
        "autoWidth": true,
        "stripeClasses": [],
        "fixedHeader": { header: true, footer: false },
        dom: 'Bfrtip',
        "bAutoWidth": false,
        "columnDefs": [
            {
                "targets": [ 6 ],
                "visible": false,
                "searchable": false
            }],
        "order": [[2, 'asc' ]],
        buttons: [
            {
                extend: 'excelHtml5',
                exportOptions: { columns: [0, 2, 3, 4, 5, 6, 7] },
                title: '',
                messageTop: myTitle,
                sheetName: "Wells"
            },
            {
                extend: 'print',
                autoPrint: false
            }
        ]
     });
  }

// https://regex101.com/r/eR2oH3/24
// https://datatables.net/reference/button/excelHtml5#Built-in-styles
// https://stackoverflow.com/questions/41485310/exporting-jquery-datatable-to-excel-with-additional-rows-is-not-working-ie
// https://stackoverflow.com/questions/61313581/jquery-datatable-export-to-excel-customization-make-first-row-bold
// https://stackoverflow.com/questions/40243616/jquery-datatables-export-to-excelhtml5-hyperlink-issue
// https://stackoverflow.com/questions/41230596/datatables-how-to-fill-a-column-with-a-hyperlink
// https://datatables.net/extensions/buttons/examples/html5/titleMessage.html
//
function exportCustomExcel (tableSelector, myTitle) 
  {
     console.log("exportCustomExcel");
     console.log("datatablesInit " + jQuery(tableSelector).length);

     // TableSorter - New Version with Fixed Headers
     //-------------------------------------------------
     jQuery(tableSelector).DataTable( {
        "paging":    false,
        "ordering":  true,
        "info":      false,
        "searching": false,
        "autoWidth": true,
        "stripeClasses": [],
        dom: 'Bfrtip',
        "order": [[1, 'asc' ]],
        buttons: [
            $.extend( true, {}, excelButton, {
                extend: 'excelHtml5',
                columns: [0, 1, 2, 3, 4, 5, 6, 7],
                title: '',
                messageTop: myTitle,
                sheetName: "FPS",
                customize: function ( xlsx ) {
                    var sheet = xlsx.xl.worksheets['sheet1.xml'];
                    $('row:first c', sheet).attr( 's', '42' );

                    // Loop over all cells in sheet
                    //
                    //$('row a', sheet).each( function () {
                    $('row href', sheet).each( function () {
                        console.log(" Row " + $(this).text());

                        // If cell starts with http
                        //
                        if ( $('is t', this).text().indexOf("<a href") === 0 ) {

                           // (2.) change the type to `str` which is a formula
                           //
                           $(this).attr('t', 'str');
                           
                           // Append the formula
                           //
                           $(this).append('<f>' + 'HYPERLINK("'+$('is t', this).text()+'","'+$('is t', this).text()+'")'+ '</f>');
                           
                           // Remove the inlineStr
                           //
                           $('is', this).remove();
                           
                           // (3.) underline
                           //
                           $(this).attr( 's', '4' );
                       }
                    });
                }
            } ),
            $.extend( true, {}, printButton, {
                extend: 'print',
                title: myTitle,
                autoPrint: false
            } )
        ]
     });
  }

// Select table rows that match text
//
function selectRows (tableSelector, selectText, selectClass) 
{
    // Find indexes of rows which have a value for groundwater change
    //
    var table   = $('#stationsTable').DataTable();
    var indexes = table.rows().eq( 0 ).filter( function (rowIdx) {
        return table.cell( rowIdx, gwChangeColumn ).data() === selectText ? true : false;
    } );                    //console.log(message);

    // Add a class to those rows using an index selector
    table.rows( indexes )
        .nodes()
        .to$()
        .addClass( selectClass );
  }
