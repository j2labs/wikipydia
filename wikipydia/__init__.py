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

def unicode_urlencode(params):
        """
        A unicode aware version of urllib.urlencode.
        Borrowed from pyfacebook :: http://github.com/sciyoshi/pyfacebook/
        """
        if isinstance(params, dict):
            params = params.items()
        return urllib.urlencode([(k, isinstance(v, unicode) and v.encode('utf-8') or v)
                                 for k, v in params])

def _run_query(args, language):
    """
    takes arguments and optional language argument and runs query on server
    """
    url = api_url % (language)
    data = unicode_urlencode(args)
    search_results = urllib.urlopen(url, data=data)
    return simplejson.loads(search_results.read())
    

def opensearch(query, language='en'):
    """
    action=opensearch
    """
    query_args = {'action': 'opensearch',
                  'search': query,
                  'format': 'json'}
    return _run_query(query_args, language)
    
def query_language_links(titles, language='en'):
    """
    action=query,prop=langlinks
    Accepts a titles argument, but appears to actually expect singular title
    """       
    url = api_url % (language)
    query_args = {'action': 'query',
                  'prop': 'langlinks',
                  'titles': titles,
                  'format': 'json'}
    json = _run_query(query_args, language)
    # Totally weird to return on the first iteration of a for loop...
    for page_id in json['query']['pages']:
        return dict([(l['lang'],l['*'])
                     for l in json['query']['pages'][page_id]['langlinks']])
        
    
def query_text_raw(titles, language='en'):
    """
    action=query
    Fetches the article in wikimarkup form
    """
    query_args = {'action': 'query',
                  'titles': titles,
                  'rvprop': 'content',
                  'prop': 'revisions',
                  'format': 'json'}
    json = _run_query(query_args, language)
    for page_id in json['query']['pages']:
        return json['query']['pages'][page_id]['revisions'][0]['*']

def query_text_rendered(page, language='en'):
    """
    action=parse
    Fetches the article in parsed html form
    """
    query_args = {'action': 'parse',
                  'page': page,
                  'format': 'json'}
    json = _run_query(query_args, language)
    html = json['parse']['text']['*']
    return html

def fetch_rendered_article(title, title_lang, target_lang):
    """
    Takes a title and it's source language and fetches the article using
    wikipedia's mapping of the title translated to the target language.
    """
    if title_lang == target_lang:
        return query_text_rendered(title, language=title_lang)
    else:
        lang_links = query_language_links(title, title_lang)
        if target_lang in lang_links:
            return query_text_rendered(lang_links[target_lang], language=target_lang)
        else:
            return "Error :: target_lang:%s not supported" % (target_lang)
