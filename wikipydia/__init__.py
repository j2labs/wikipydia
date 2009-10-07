#!/usr/bin/env python

"""
Interface to Wikipedia. Their API is in beta and subject to change.
As a result, this code is also in beta and subject to unexpected brokenness.

http://en.wikipedia.org/w/api.php
http://github.com/j2labs

jd@j2labs.net
"""

import urllib
import simplejson

api_url = 'http://%s.wikipedia.org/w/api.php'

def opensearch(query, format='json', language='en'):
    """
    action=opensearch
    """
    url = api_url % (language)
    query_args = urllib.urlencode({'action' : 'opensearch',
                                   'search': query,
                                   'format': format})
    search_results = urllib.urlopen(url, data=query_args)
    json = simplejson.loads(search_results.read())
    return json
    
def query_language_links(titles, format='json', language='en'):
    """
    action=query,prop=langlinks
    Accepts a titles argument, but appears to actually expect singular title
    """       
    url = api_url % (language)
    query_args = urllib.urlencode({'action': 'query',
                                   'prop': 'langlinks',
                                   'titles': titles,
                                   'format': format})
    search_results = urllib.urlopen(url, data=query_args)
    json = simplejson.loads(search_results.read())
    # Totally weird to return on the first iteration of a for loop...
    for page_id in json['query']['pages']:
        return dict([(l['lang'],l['*'])
                     for l in json['query']['pages'][page_id]['langlinks']])
        
    
def query_text_raw(titles, format='json', language='en'):
    """
    action=query
    Fetches the article in wikimarkup form
    """
    url = api_url % (language)
    query_args = urllib.urlencode({'action': 'query',
                                   'titles': titles,
                                   'rvprop': 'content',
                                   'prop': 'revisions',
                                   'format': format})
    search_results = urllib.urlopen(url, data=query_args)
    json = simplejson.loads(search_results.read())
    # Totally weird to return on the first iteration of a for loop...
    for page_id in json['query']['pages']:
        return json['query']['pages'][page_id]['revisions'][0]['*']

def query_text_rendered(page, format='json', language='en'):
    """
    action=parse
    Fetches the article in parsed html form
    """
    url = api_url % (language)
    query_args = urllib.urlencode({'action': 'parse',
                              #'page': 'Dennis',
                              'page': page,
                              'format': 'json'})
    search_results = urllib.urlopen(url, data=query_args)
    json = simplejson.loads(search_results.read())
    html = json['parse']['text']['*']
    return html
