from enum import Enum
from collections import defaultdict
from w3lib.html import get_base_url
from babel.dates import format_date
from translate import Translator

import dateutil.parser
import extruct
import requests
import pprint
import re
import wayback
import fasttext
import os

input_url = None

Attribute = Enum('Attribute', ['URL', 'TITLE', 'AUTHORS', 'DATE', 'WORK', 'PUBLISHER', 'ACCESS', 'LOCALE'])

# TODO: Move lookup list information to separate file
# Lookup lists for each format to use for attribute fetching
#
# For instance, ['author', 'name'] under 'json-ld' means 
# attempting to fetch the author attribute using
#       jsonld.get('author').get('name')
# There are multiple possible fetching paths within a format for each attribute
lookup_formats = ['json-ld', 'dublincore', 'microdata', 'microformat', 'opengraph', 'rdfa']
lookup_url = [('opengraph', ['og:url']), 
              ('rdfa', ['@id'])]
lookup_author = [('json-ld', ['author', 'name']),
                 ('json-ld', ['creator', 'name']),
                 ('opengraph', ['article:author']),
                 ('rdfa', ['http://ogp.me/ns/article#author'])]
lookup_title = [('json-ld', ['headline']), 
                ('opengraph', ['og:title']),
                ('opengraph', ['og:site_name'])]
lookup_date = [('json-ld', ['datePublished']),
               ('opengraph', ['article:published_time']),
               ('opengraph', ['og:article:published_time']),
               ('microdata', ['datePublished']),
               # The modification time is useful for content
               # without an explicit publication date:
               ('opengraph', ['article:modified_time']),
               ('opengraph', ['og:article:modified_time'])]
lookup_work = [('opengraph', ['og:site_name'])]
lookup_publisher = [('json-ld', ['publisher', 'name'])]
lookup_access = [('json-ld', ['isAccessibleForFree']),
                 ('json-ld', ['hasPart', 'isAccessibleForFree']),
                 ('rdfa', ['lp:type'])]
lookup_locale = [('opengraph', ['og:locale'])]  

def fetch_attribute(lookup_dict, metadata):
    """Returns a value associated with the metadata item in the given lookup dictionary.
    
    Args:
        lookup_dict: Dictionary of paths to certain information for different metadata formats.
        data: Metadata dictionary in the format returned by extruct.extract(uniform=True).

    Returns:
        item: String retrieved from the metadata using the lookup dictionary 
    """
    def collect_item(path, dic):
        if (len(path) > 1):
            return collect_item(path[1:], dic.get(path[0], {}))
        if isinstance(dic, list): dic = dic[0]
        return dic.get(path[0])

    for format, path in lookup_dict:
        if metadata[format]:
            item = collect_item(path, metadata[format][0])
            if item: # Return first non-empty result
                return item
    return None

def get_reference_attributes(metadata):
    """Returns a dictionary of reference attributes based on the given metadata.

    Args: 
        metadata: Metadata dictionary in the format returned by extruct.extract(uniform=True).

    Returns:
        attributes: Reference attributes to construct a citation.
    """
    attributes = defaultdict(lambda: '')
    attributes[Attribute.URL]       = fetch_attribute(lookup_url, metadata)
    attributes[Attribute.TITLE]     = fetch_attribute(lookup_title, metadata)
    attributes[Attribute.AUTHORS]   = fetch_attribute(lookup_author, metadata)
    attributes[Attribute.DATE]      = fetch_attribute(lookup_date, metadata)
    attributes[Attribute.WORK]      = fetch_attribute(lookup_work, metadata)
    attributes[Attribute.PUBLISHER] = fetch_attribute(lookup_publisher, metadata)
    attributes[Attribute.ACCESS]    = fetch_attribute(lookup_access, metadata)
    attributes[Attribute.LOCALE]    = fetch_attribute(lookup_locale, metadata)

    return attributes

def extract_metadata(url):
    """Return extruct metadata dictionary for the given URL.

    Args:
        url: URL of a website from which to scrape the metadata.

    Returns:
        metadata: Dictionary containing entries for each metadata style present in the website.
    """
    # Using custom header as some websites, such as The New York Times, 
    # reject requests from the standard header used by the 'requests' library
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36'}
    
    r = requests.get(url, headers=headers)
    base_url = get_base_url(r.text, r.url)
    metadata = extruct.extract(r.text, base_url=base_url, uniform=True)

    return metadata

def get_sub_dictionary(dictionary, target_key, target_value):
    """Return a dictionary containing the specified key-value pair. 
    
    Args:
        dictionary: Metadata dictionary containing lists of other dictionaries
        target_key: Target key to search for within a dictionary inside a list.
        target_value: Target value to search for within a dictionary inside a list
    
    Returns:
        target_dictionary: Target dictionary that contains target key value pair. 
    """
    
    for key in dictionary:
        if len(dictionary[key]) > 0:
            for item in dictionary[key]:
                if item[target_key] == target_value:
                    return item

def create_wiki_reference(attributes):
    """Return a string reference in Wiki markup using the {{Cite web}} template from English Wikipedia.

    Args:
        attributes: Dictionary of attribute-value pairs for title, author etc.

    Returns:
        wiki_ref: {{Cite web}} string reference in Wiki markup
    """
    locale = attributes[Attribute.LOCALE]
    if not locale:
        locale = 'en_US'

    # Formatting date
    try:
        parsed_date = dateutil.parser.parse(attributes[Attribute.DATE])
        date = format_date(parsed_date, format='long', locale=locale)
    except dateutil.parser.ParserError:
        date = ''

    # TODO: Parse authors (support multiple authors), format string and insert it within larger citation string
    author_reg = re.compile('(?P<first>[\w\s]*) (?P<last>\w*)')
    authors = attributes[Attribute.AUTHORS]
    if authors:
        if type(authors) == list:
            matches = author_reg.findall(authors[0])
        else:
            matches = author_reg.findall(authors)
        if matches:
            last  = matches[0][1]
            first = matches[0][0]
    else:
        last = ''
        first = ''

    # Use wayback to construct an archive URL and date
    client = wayback.WaybackClient()
    mementos = list(client.search(url=attributes[Attribute.URL]))
    archive_url = ''
    archive_date = ''
    if mementos:
        memento = client.get_memento(mementos[0])
        archive_url = memento.memento_url
        archive_date = format_date(memento.timestamp, format='long', locale=locale)
    client.close()

    # Predict title language
    model_loc = os.path.join(os.path.dirname(__file__), 'fasttext/lid.176.ftz')
    lang_detector = fasttext.load_model(model_loc)
    prediction = lang_detector.predict(attributes[Attribute.TITLE], k=1)
    # Grab the language label and remove the '__label__' prefix
    src_lang = prediction[0][0][9:]
    pred_confidence = prediction[1][0]

    # Translate the title if article language differs from user language
    dst_lang = 'en'
    trans_ext = ''
    if (dst_lang != src_lang and pred_confidence >= 0.85):
        translator = Translator(dst_lang, src_lang)
        translation = translator.translate(attributes[Attribute.TITLE])
        trans_ext = '|language={lang} |trans-title={title}'.format(lang=src_lang, title=translation)
    
    # Check access
    # TODO: Instead of assuming subscription is required, instead ask
    # the user to specify the type of access (limited, registration, or subscription)
    # if free access is 'False'
    access_ext = ''
    if attributes[Attribute.ACCESS] == 'False':
        access_ext = '|url-access=subscription'

    wiki_ref = '{{{{cite web |last={last} |first={first} |title={title} |url={url} ' \
          '|date={date} |work={work} |publisher={publisher} ' \
          '|archive-url={archive_url} |archive-date={archive_date} |url-status=live {transtitle} {access} }}}}'
    wiki_ref = wiki_ref.format(title=attributes[Attribute.TITLE], url=attributes[Attribute.URL], date=date, work=attributes[Attribute.WORK], 
                           publisher=attributes[Attribute.PUBLISHER], last=last, first=first, 
                           archive_url=archive_url, archive_date=archive_date, transtitle=trans_ext, access=access_ext)
    # Remove redundant and trailing spaces
    wiki_ref = ' '.join(wiki_ref.split())

    return wiki_ref

def url2ref(url):
    metadata = extract_metadata(url)
    attributes = get_reference_attributes(metadata)
    wiki_ref = create_wiki_reference(attributes)

    return wiki_ref

def main():
    wiki_ref = url2ref(input_url)

    pprint.pprint(wiki_ref)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-u",
        "--url",
        type=str,
        default='',
        help="URL to create a reference from",
    )

    args = parser.parse_args()

    if args.url:
        input_url = args.url
    
    main()