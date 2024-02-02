/**
 * Namespace: About_Content
 *
 * About_Content is a JavaScript library to provide instructions and general information.
 *
 * version 2.01
 * December 21, 2023
*/

/*
###############################################################################
# Copyright (c) 2017 Oregon Water Science Center
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

// Set files for About text
//-----------------------------------------------
var aboutFiles          = {
                            "welcome" : "welcome.txt",
                            "mapFeatures" : "mapFeatures.txt",
                            "dataExploration" : "dataExploration.txt",
                            "contacts" : "contacts.txt"
                          };

// Help text
//
//setHelpTip("#aboutHelp", "Click this for information about this web site.", "right");

// Monitor About click
//-----------------------------------------------
jQuery('.aboutButtons').click(function() {

    var div_id   = jQuery(this).prop("id");
    var file     = aboutFiles[div_id];
    var InfoText = loadText(file);

    jQuery("#aboutContent").html(InfoText);
   
});

// Load text
//
function loadText(file_name) 
  {
    var myInfo = "";

    // Check file name
    //
    if(file_name.length < 1)
      {
        var message = "No file specified";
        openModal(message);
        return false;
      }

    // Load file
    //
    jQuery.ajax( 
                { url: file_name + "?_="+(new Date()).valueOf(),
                  dataType: "text",
                  async: false
                })
      .done(function(data)
            {
              myInfo = data;
            })
      .fail(function() 
            { 
              var message = "No file specified";
              openModal(message);
              return false;
            });

    return myInfo;
  }

function capitalizeEachWord(str) {
    return str.replace(/\w\S*/g, function(txt) {
        return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
    });
}
