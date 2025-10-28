#!/usr/bin/python
import sys
import cgi
import urllib
import json
import time
import pprint 
isPython2 = sys.hexversion < 0x03000000
if isPython2:
	import urllib2
else:
	import urllib.request
	import urllib.error

#	Python sample code for Siteliner Premium API
#	
#	Compatible with Python 2.4 or later
#	
#	You may install, use, reproduce, modify and redistribute this code, with or without
#	modifications, subject to the general Terms and Conditions on the Siteliner website.
#	
#	For any technical assistance please contact us via our website.
#	
#	5-Aug-2020: First version
#	
#	Siteliner (c) Indigo Stream Technologies 2020 - https://www.siteliner.com/
#
#
#	Instructions for use:
#	
#	1. Set the constants SITELINER_USERNAME and SITELINER_API_KEY below to your details.
#	2. Call the appropriate API function, following the examples below .
#	3. Use print_r to discover the structure of the output.
#	4. To run the example provided, please uncomment and edit the lines below.
#	   NOTE: Each scanned page and API request for scan results costs 1c

#SITELINER_RUN_EXAMPLES=True
#SITELINER_ROOT_URL="http://www.example.com/"
#SITELINER_MAX_PAGES=100

#	Error handling:
#	
#	* If a call failed completely (e.g. curl failed to connect), functions return false.
#	* If the API returned an error, the response array will contain an 'error' element.


# A. Constants you need to change

SITELINER_USERNAME = "your-copyscape-username"
SITELINER_API_KEY = "your-copyscape-api-key"

SITELINER_API_URL = "https://www.siteliner.com/api/"

#	B. Functions for you to use 

def siteliner_get_account_summary(count=100, start=1):
	return siteliner_api_call('account',{'count':count,'start':start})        
    
def siteliner_start_scan(rooturl, maxpages, parameters=None):
# any optional API parameters should be provided to the function in the format specified by the API documentation
# 
# Example:
# 
# siteliner_start_scan("http://www.example.com", 100, 
#                      {"scanmode":"excludedirs",
#                       "excludedirs":"sports/\nbusiness/banking/"
#                       })        
    params={'rooturl':rooturl,'maxpages':maxpages}
    if parameters is not None:
        for key in parameters:
            params[key] = parameters[key]

    return siteliner_api_call('start',params,True)
    
def siteliner_pause_scan(scan):
    return siteliner_api_call('pause',{'scan':scan},True)
    
def siteliner_resume_scan(scan):
	return siteliner_api_call('resume',{'scan':scan},True)
    
def siteliner_cancel_scan(scan):
	return siteliner_api_call('cancel',{'scan':scan},True)
    
def siteliner_get_scan_status(scan):
	return siteliner_api_call('status',{'scan':scan})
    
def siteliner_get_scan_summary(scan):
	return siteliner_api_call('sitesummary',{'scan':scan})       

def siteliner_get_analyzed_pages(scan, count=100, start=1):
	return siteliner_api_call('siteanalyzed',{'scan':scan,'count':count,'start':start})
    
def siteliner_get_skipped_pages(scan, count=100, start=1):
	return siteliner_api_call('siteskipped',{'scan':scan,'count':count,'start':start})    
        
def siteliner_get_duplicate_pages(scan, count=100, start=1):
	return siteliner_api_call('siteduplicate',{'scan':scan,'count':count,'start':start})    
    
def siteliner_get_broken_link_pages(scan, count=100, start=1):
	return siteliner_api_call('sitebroken',{'scan':scan,'count':count,'start':start}) 
    
def siteliner_get_related_domains(scan, count=100, start=1):
	return siteliner_api_call('siterelateddomain',{'scan':scan,'count':count,'start':start})   
            
def siteliner_get_page_duplicates(scan, page, count=100, start=1):
	return siteliner_api_call('pageduplicate',{'scan':scan,'page':page,'count':count,'start':start})       
    
def siteliner_get_page_int_links_in(scan, page, count=100, start=1):
	return siteliner_api_call('pagelinkin',{'scan':scan,'page':page,'count':count,'start':start})       
    
def siteliner_get_page_int_links_out(scan, page, count=100, start=1):
	return siteliner_api_call('pagelinkout',{'scan':scan,'page':page,'count':count,'start':start})       
    
def siteliner_get_page_ext_links_out(scan, page, count=100, start=1):
	return siteliner_api_call('pageexternal',{'scan':scan,'page':page,'count':count,'start':start})       

def siteliner_get_related_links_in(scan, url, count=100, start=1):
	return siteliner_api_call('relatedlinkin',{'scan':scan,'url':url,'count':count,'start':start})        


# C. Functions used internally

def siteliner_api_call(operation, params={}, post=False):
    urlparams={}
    urlparams['user'] = SITELINER_USERNAME
    urlparams['key'] = SITELINER_API_KEY
    if post:
        urlparams['command'] = operation
    else:	
        urlparams['report'] = operation

    if post:    
        if isPython2:
            postdata = urllib.urlencode(params)
        else:
            postdata = urllib.parse.urlencode(params)
    else:	 
        postdata = None  
        urlparams.update(params)
	
    uri = SITELINER_API_URL + '?'

    request = None
    if isPython2:
        uri += urllib.urlencode(urlparams)
        if postdata is None:
            request = urllib2.Request(uri)
        else:
            request = urllib2.Request(uri, postdata.encode("UTF-8"))
    else:
        uri += urllib.parse.urlencode(urlparams)    
        if postdata is None:
            request = urllib.request.Request(uri) 
        else:
            request = urllib.request.Request(uri, postdata.encode("UTF-8"))
	
    try: 
        response = None
        if isPython2:
            response = urllib2.urlopen(request)
        else:
            response = urllib.request.urlopen(request)
        res = response.read()
        result = json.loads(res)	
        if 'error' in result.keys(): 
            print("API returned error: "+result['error'])
            return None
        return result
    except Exception:
        e = sys.exc_info()[1]
        print(e.args[0])
		
    return None

def format_plural_string(count,text):
    result='No '+text+'s'                   
    if count > 0:
        if count==1:
            result='1 ' + text
        else:
            result=str(count) + ' ' + text + 's'                    
    return result

#	E. Example

def siteliner_run_example(rooturl, maxpages):    

    print("\nStarting scan for "+rooturl)

    scan_info=siteliner_start_scan(rooturl,maxpages)
    if scan_info is None:
        sys.exit()

    scan=scan_info['scan']
    print("Scan successfully started, scan ID: "+scan)

    while(scan_info['status'] != 'completed'):
        time.sleep(10)
        scan_info=siteliner_get_scan_status(scan)        
        if scan_info is None:
            sys.exit()
        print(format_plural_string(scan_info['found'],"page")+" found so far, "+format_plural_string(scan_info['retrieved'],"page")+" retrieved")

    summary=siteliner_get_scan_summary(scan)
    if summary is None:
        sys.exit()

    print("\nScan completed successfully, summary:")
    print(json.dumps(summary, indent=4))

    analyzed=siteliner_get_analyzed_pages(scan,5)
    if analyzed is None:
        sys.exit()

    print("\n"+format_plural_string(len(analyzed['results']), 'most prominent page'))
    print(json.dumps(analyzed, indent=4))

    home_links_in=siteliner_get_page_int_links_in(scan,"/",5)
    if home_links_in is None:
        sys.exit()

    if home_links_in['resultcount'] > 0:
        print("\n"+format_plural_string(len(home_links_in['results']), 'most prominent page')+" with most links to home page:")
        print(json.dumps(home_links_in, indent=4))
    else:
        print("\nNo pages found with links to home page");        
    print("\n")


if 'SITELINER_RUN_EXAMPLES' in globals() and SITELINER_RUN_EXAMPLES:
    siteliner_run_example(SITELINER_ROOT_URL,SITELINER_MAX_PAGES)


