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

import calendar
import datetime

import re

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

def query_page_view_stats(title, language='en', start_date=(datetime.date.today()-datetime.timedelta(1)), end_date=datetime.date.today()):
    """
    Queries stats.grok.se for the daily page views for wikipedia articles
    """
    stats_api_url = 'http://stats.grok.se/json/%s/%s/%s'
    earliest_date = datetime.date(2007, 01, 01)
    query_date = max(start_date, earliest_date)
    end_date = min(end_date, datetime.date.today())
    total_views = 0
    stats = {}
    stats['monthly_views'] = {}
    while(query_date < end_date):
        query_date_str = query_date.strftime("%Y%m")
        url = stats_api_url % (language, query_date_str, urllib.quote(title.encode('utf-8')))
        search_results = urllib.urlopen(url)
        json = simplejson.loads(search_results.read())
        total_views += json['total_views']
        stats['monthly_views'][query_date_str] = json
        days_in_month = calendar.monthrange(query_date.year, query_date.month)[1]
        query_date = query_date + datetime.timedelta(days_in_month)        
    stats['total_views'] = total_views
    return stats

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


def get_page_id(title, query_results):
   """
   Extracts the title's pageid from the query results.
   Assumes queries of the form query:pages:id, 
   and properly handle the normalized method.
   Returns -1 if it cannot find the page id
   """
   if 'normalized' in query_results['query'].keys():
       for normalized in query_results['query']['normalized']:
           if title == normalized['from']:
              title = normalized['to']
              break

   for page in query_results['query']['pages']:
       if title == query_results['query']['pages'][page]['title']:
          return query_results['query']['pages'][page]['pageid']
   return -1


def query_language_links(title, language='en', lllimit=10):
   """
   action=query,prop=langlinks
   returns a dict of inter-language links, containing the lang abbreviation
   and the corresponding title in that language
   """
   url = api_url % (language)
   query_args = {
       'action': 'query',
       'prop': 'langlinks',
       'titles': title,
       'format': 'json',
       'lllimit': lllimit
   }
   json = _run_query(query_args, language)
   page_id = get_page_id(title, json)
   lang_links = {}
   if 'langlinks' in json['query']['pages'][page_id].keys():
       lang_links = dict([(ll['lang'],ll['*']) for ll in json['query']['pages'][page_id]['langlinks']])
   return lang_links

def query_categories(title, language='en'):
   """
   action=query,prop=categories
   Returns a full list of categories for the title
   """
   url = api_url % (language)
   query_args = {
       'action': 'query',
       'prop': 'categories',
       'titles': title,
       'format': 'json',
   }
   categories = []
   while True:
      json = _run_query(query_args, language)
      for page_id in json['query']['pages']:
          if 'categories' in json['query']['pages'][page_id].keys():
              for category in json['query']['pages'][page_id]['categories']:
                  categories.append(category['title'])
      if 'query-continue' in json:
          continue_item = json['query-continue']['categories']['clcontinue']
          query_args['clcontinue'] = continue_item
      else:
          break
   return categories


def query_category_members(category, language='en', limit=100):
   """
   action=query,prop=categories
   Returns all the members of a category up to the specified limit
   """
   url = api_url % (language)
   query_args = {
       'action': 'query',
       'list': 'categorymembers',
       'cmtitle': category,
       'format': 'json',
       'cmlimit': min(limit, 500)
   }
   members = []
   while True:
      json = _run_query(query_args, language)
      for member in json['query']['categorymembers']:
          members.append(member['title'])
      if 'query-continue' in json and len(members) <= limit:
          continue_item = json['query-continue']['categorymembers']['cmcontinue']
          query_args['cmcontinue'] = continue_item
      else:
          break
   return members[0:limit]


def query_text_raw(title, language='en'):
    """
    action=query
    Fetches the article in wikimarkup form
    """
    query_args = {
        'action': 'query',
        'titles': title,
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


def get_sections(wikified_text):
    """
    Parses the wikipedia markup for a page and returns
    two arrays, one containing section headers and one
    containing the (marked up) text of the section.
    """
    title_pattern = re.compile('==.*?==')
    iterator = title_pattern.finditer(wikified_text)
    headers = []
    contents = []
    header = ''
    content_start = 0
    for match in iterator:
        headers.append(header)
        content = wikified_text[content_start:match.start()]
        contents.append(content)
        header = wikified_text[match.start()+2:match.end()-2]
        content_start = match.end()
    headers.append(header)
    content = wikified_text[content_start:len(wikified_text)-1]
    contents.append(content)
    return dict([('headers', headers), ('contents', contents)])



def get_links(wikified_text):
    """
    Parses the wikipedia markup for a page and returns
    a dict of rendered link text onto underlying wiki links
    """
    link_pattern = re.compile('\[\[.*?\]\]')
    linked_text = {}
    iterator = link_pattern.finditer(wikified_text)
    for match in iterator:
        link = wikified_text[match.start()+2:match.end()-2].split('|', 1)
        linked_text[link[-1]] = link[0]
    return linked_text

