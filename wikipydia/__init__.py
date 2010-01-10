#!/usr/bin/env python

"""
Interface to Wikipedia. Their API is in beta and subject to change.
As a result, this code is also in beta and subject to unexpected brokenness.

http://en.wikipedia.org/w/api.php
http://github.com/j2labs/wikipydia

jd@j2labs.net
"""

import urllib
import simplejson

api_url = 'http://%s.wikipedia.org/w/api.php'

def _unicode_urlencode(params):
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
    data = _unicode_urlencode(args)
    search_results = urllib.urlopen(url, data=data)
    json = simplejson.loads(search_results.read())
    return json

def opensearch(query, language='en'):
    """
    action=opensearch
    """
    query_args = {
        'action': 'opensearch',
        'search': query,
        'format': 'json'
    }
    return _run_query(query_args, language)

def unnormalize_titles(titles, query_results):
   """
   Creates a map of  normalized titles from the query results
   back onto the titles that the user submitted
   """
   unnormalized_titles = dict([(t, t) for t in titles])
   if 'normalized' in query_results['query'].keys():
       for normalized in query_results['query']['normalized']:
           unnormalized_titles[normalized['to']] = normalized['from']
   return unnormalized_titles

def query_language_links(titles, language='en', lllimit=10):
   """
   action=query,prop=langlinks
   Accepts a list of titles and returns a map for each title
   that has an inter-language link, containing the lang abbreviation
   and the corresponding title in that language
   """
   url = api_url % (language)
   query_args = {
       'action': 'query',
       'prop': 'langlinks',
       'titles': '|'.join(titles),
       'format': 'json',
       'lllimit': lllimit
   }
   json = _run_query(query_args, language)
   titles_map = unnormalize_titles(titles, json)
   results = {}
   for page_id in json['query']['pages']:
       title = titles_map[json['query']['pages'][page_id]['title']]
       if 'langlinks' in json['query']['pages'][page_id].keys():
           lang_map = dict([(ll['lang'],ll['*']) for ll in json['query']['pages'][page_id]['langlinks']])
           results[title] = lang_map
   return results
    
def query_text_raw(titles, language='en'):
    """
    action=query
    Fetches the article in wikimarkup form
    """
    query_args = {
        'action': 'query',
        'titles': titles,
        'rvprop': 'content',
        'prop': 'info|revisions',
        'format': 'json',
        'redirects': ''
    }
    json = _run_query(query_args, language)
    for page_id in json['query']['pages']:
        response = {
            'text': json['query']['pages'][page_id]['revisions'][0]['*'],
            'revid': json['query']['pages'][page_id]['lastrevid'],
        }
        return response

def query_text_rendered(page, language='en'):
    """
    action=parse
    Fetches the article in parsed html form
    """
    query_args = {
        'action': 'parse',
        'page': page,
        'format': 'json',
        'redirects': ''
    }
    json = _run_query(query_args, language)
    response = {
        'html': json['parse']['text']['*'],
        'revid': json['parse']['revid'],
    }
    return response

def query_rendered_altlang(title, title_lang, target_lang):
    """
    Takes a title and the language the title is in, asks wikipedia for
    alternative language offerings and fetches the article hosted by
    wikipedia in the target language.
    """
    lang_links = query_language_links(title, title_lang, lllimit=100)
    if target_lang in lang_links:
        return query_text_rendered(lang_links[target_lang], language=target_lang)
    else:
        return ValueError('Language not supported')
