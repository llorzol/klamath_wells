/**
 * Namespace: WebRequest
 *
 * WebRequest is a JavaScript library to make a Ajax request.
 *
 $Id: /var/www/html/habs/javascripts/gages/webRequest.js, v 1.11 2026/01/27 20:02:16 llorzol Exp $
 $Revision: 1.11 $
 $Date: 2026/01/27 20:02:16 $
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

async function webRequest(urls) {

    const myData = [];
    for (const url of urls) { // Use for...of for clean iteration
        try {
            const response = await fetch(url); // Wait for the fetch
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json(); // Wait for JSON parsing
            results.push(data);
            console.log(`Fetched data for ${url}:`, data);
        } catch (error) {
            console.error(`Error fetching ${url}:`, error);
        }
    }
    return results; // The function will return a Promise that resolves with the final array
}

async function webRequests(urls, responseType, callBack) {
    // Create an array of Promises
    //
    const fetchPromises = urls.map(url => fetch(url));

    try {
        // Wait for all promises to resolve
        //
        const responses = await Promise.all(fetchPromises);

        // Map over the responses to parse them as JSON (each is an async operation)
        //
        const myPromises = responses.map(response => {
            if (!response.ok) {
                // You must handle non-ok statuses here
                throw new Error(`HTTP error! status: ${response.status} for ${response.url}`);
            }
            if (responseType == 'json') return response.json();
            else if (responseType == 'text') return response.text();
            else if (responseType == 'blob') return response.blob();
            else if (responseType == 'bytes') return response.bytes();
            else return response.text();
        });

        // Wait for all JSON parsing promises to resolve
        //
        const dataArray = await Promise.all(myPromises);
        //console.log("All concurrent fetches complete:", dataArray);
        //return dataArray;
        callBack(dataArray)

    } catch (error) {
        let message = `An error occurred during concurrent fetches: ${error}`
        console.error(message)
        updateModal(message);
        fadeModal(6000);
    }
}
