/* Javascript modal window library for jQuery and flot.
 *
 * Dialog is a JavaScript library to display modal windows.
 *
 * version 1.10
 * February 27, 2019
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
var modalDialog = [];

//modalDialog.push('<!-- Modal -->');
modalDialog.push('<div class="modal fade" id="messageDialog" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel" aria-hidden="true">');
modalDialog.push('  <div class="modal-dialog" role="document">');
modalDialog.push('    <div class="modal-content">');
//modalDialog.push('      <div class="modal-header">');
//modalDialog.push('        <button type="button" class="close" data-dismiss="modal" aria-label="Close">');
//modalDialog.push('          <span aria-hidden="true">&times;</span>');
//modalDialog.push('        </button>');
//modalDialog.push('      </div>');
modalDialog.push('      <div class="modal-body">');
modalDialog.push('       <div><img src="images/ajax-loader.gif"></div>');
modalDialog.push('       <span id="message"</span>');
modalDialog.push('      </div>');
modalDialog.push('    </div>');
modalDialog.push('  </div>');
modalDialog.push('</div>');

function openModal(message) {
    //console.log("openModal " + jQuery('#messageDialog').length);
    if (jQuery('#messageDialog').length < 1) {
        jQuery('body').append(modalDialog.join('\n'));
        //console.log("append openModal " + jQuery('#messageDialog').length);
    }

    jQuery('#message').text(message);

    jQuery('#messageDialog').modal('show');
};

function closeModal() {
    jQuery("#messageDialog").modal('hide');
}

function fadeModal(fadeTime) {
    // console.log("Fading message");
    setTimeout(function() {
        jQuery("#messageDialog").modal('hide');
    }, fadeTime);
}

function updateModal(message) {
    jQuery('#message').text(message);
}