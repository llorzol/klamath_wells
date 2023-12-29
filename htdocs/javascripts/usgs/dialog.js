/* Javascript modal window library for jQuery and flot.
 *
 * Dialog is a JavaScript library to display modal windows.
 *
 * version 1.12
 * October 18, 2021
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

function get_dialog_dimensions() 
  {
   var window_height  = jQuery(window).height();
   var html_height    = jQuery(document).height();
   var dialog_height  = html_height * 0.30;
   if(window_height < html_height) { dialog_height = window_height * 0.30; }
    
   var window_width   = jQuery(window).width();
   var html_width     = jQuery(document).width();
   var dialog_width   = html_width * 0.70;
   if(window_width < html_width) { dialog_width = window_width * 0.70; }
   
   return { 'dialog_height': dialog_height, 'dialog_width': dialog_width }
  }

function openModal(message) 
  {
    //console.log("openModal " + jQuery('#messageDialog').length);
    if(jQuery('#messageDialog').length > 0)
      {
       jQuery('#message').text(message);
       //closeModal();
       return;
      }

    jQuery('body').append('<div id="messageDialog"><div><img src="' + imageSrc + 'ajax-loader.gif" alt="Loading"><div id="message">'+message+'</div></div><div class="bg"></div></div>');

    jQuery('#messageDialog').css({
                                  'width':'100%',
                                  'height':'100%',
                                  'position':'fixed',
                                  'z-index':'10000000',
                                  'top':'0',
                                  'left':'0',
                                  'right':'0',
                                  'bottom':'0',
                                  'margin':'auto'
    });
  
    jQuery('#messageDialog .bg').css({
                                  'background':'#000000',
                                  'opacity':'0.7',
                                  'width':'100%',
                                  'height':'100%',
                                  'position':'absolute',
                                  'top':'0'
    });
  
    jQuery('#messageDialog>div:first').css({
                                  'width': '250px',
                                  'height':'75px',
                                  'text-align': 'center',
                                  'position': 'fixed',
                                  'top':'0',
                                  'left':'0',
                                  'right':'0',
                                  'bottom':'0',
                                  'margin':'auto',
                                  'font-size':'16px',
                                  'z-index':'10',
                                  'color':'#ffffff'
  
    });
  
    jQuery('#messageDialog .bg').height('100%');
    jQuery('#messageDialog').fadeIn(300);
    //jQuery('body').css('cursor', 'wait');
  }; 

function closeModal() 
  {
   //jQuery("#messageDialog").fadeOut(200).remove();
   jQuery("#messageDialog").fadeOut(200);
  }

function fadeModal(fadeTime) 
  {
   //console.log("Fading message");
   setTimeout(function() {
     closeModal();
   }, fadeTime);  
  }
