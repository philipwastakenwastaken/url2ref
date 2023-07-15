from enum import Enum
from collections import defaultdict
from w3lib.html import get_base_url
from datetime import datetime
from babel.dates import format_date
from translate import Translator
from nameparser import HumanName

import difflib
import dateutil.parser
import extruct
import requests
import pprint
import re
import wayback
import wayback.exceptions
import fasttext
import os
import deepl
import tldextract

# Supress FastText warning
# See: https://stackoverflow.com/a/66401601
fasttext.FastText.eprint = lambda x: None

input_url = None

Attribute = Enum('Attribute', ['URL', 'TITLE', 'AUTHORS', 'DATE', 'WEBSITE', 'PUBLISHER', 'ACCESS', 'LANGUAGE'])

# TODO: Move lookup list information to separate file
# Lookup lists for each format to use for attribute fetching
#
# For instance, ['author', 'name'] under 'json-ld' means 
# attempting to fetch the author attribute using
#       jsonld.get('author').get('name')
# There are multiple possible fetching paths within a format for each attribute
lookup_formats = ['json-ld', 'dublincore', 'microdata', 'microformat', 'opengraph', 'rdfa']
lookup_url = [('opengraph', ['og:url'])]
lookup_author = [('json-ld', ['author', 'name']),
                 ('json-ld', ['creator', 'name']),
                 ('opengraph', ['article:author']),
                 ('rdfa', ['http://ogp.me/ns/article#author'])]
lookup_title = [('json-ld', ['headline']), 
                ('opengraph', ['og:title']),
                ('json-ld', ['alternativeHeadline'])]
lookup_date = [('json-ld', ['datePublished']),
               ('opengraph', ['article:published_time']),
               ('opengraph', ['og:article:published_time']),
               ('microdata', ['datePublished']),
               # The modification time is useful for content
               # without an explicit publication date:
               ('opengraph', ['article:modified_time']),
               ('opengraph', ['og:article:modified_time'])]
lookup_website = [('opengraph', ['og:site_name']),
                  ('json-ld', ['sourceOrganization', 'name']),
                  ('json-ld', ['copyrightHolder', 'name'])]
lookup_publisher = [('json-ld', ['publisher', 'name'])]
lookup_access = [('json-ld', ['isAccessibleForFree']),
                 ('json-ld', ['hasPart', 'isAccessibleForFree']),
                 ('rdfa', ['lp:type'])]
lookup_language = [('json-ld', ['inLanguage']),
                   ('opengraph', ['og:locale'])]

def find_attribute_values(lookup_dict, json_data):
    """Returns a list of values within the metadata for the attributes in the lookup dictionary.
    
    Args:
        lookup_dict: Dictionary of potential paths to attribute values within the metadata
        data: Metadata dictionary in the format returned by extruct.extract(uniform=True)

    Returns:
        values: List of values retrieved from the metadata using the lookup dictionary
    """
    def collect_item(path, dic):
        if (len(path) > 1):
            return collect_item(path[1:], dic.get(path[0], {}))
        if isinstance(dic, list): dic = dic[0]
        return dic.get(path[0])

    def find_rec(json_data, attribute_path, values):
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                if key == attribute_path[0]:
                    if len(attribute_path) > 1:
                        find_rec(json_data[key], attribute_path[1:], values)
                    else: # Item can be retrieved
                        if isinstance(value, list):
                            for subitem in value:
                                if subitem not in values:
                                    values.append(subitem)
                        elif value not in values:
                            values.append(value)
                elif isinstance(value, (dict, list)):
                    find_rec(value, attribute_path, values)
        elif isinstance(json_data, list):
            for item in json_data:
                find_rec(item, attribute_path, values)
                
    values = []
    for format, attribute_path in lookup_dict:
        if json_data[format]:
            find_rec(json_data, attribute_path, values)
    return values

def get_reference_attributes(metadata):
    """Returns a dictionary of reference attributes based on the given metadata.

    Args: 
        metadata: Metadata dictionary in the format returned by extruct.extract(uniform=True).

    Returns:
        attributes: Reference attributes to construct a citation.
    """
    attributes = defaultdict(lambda: [])
    attributes[Attribute.URL]       = find_attribute_values(lookup_url, metadata)
    attributes[Attribute.TITLE]     = find_attribute_values(lookup_title, metadata)
    attributes[Attribute.AUTHORS]   = find_attribute_values(lookup_author, metadata)
    attributes[Attribute.DATE]      = find_attribute_values(lookup_date, metadata)
    attributes[Attribute.WEBSITE]   = find_attribute_values(lookup_website, metadata)
    attributes[Attribute.PUBLISHER] = find_attribute_values(lookup_publisher, metadata)
    attributes[Attribute.ACCESS]    = find_attribute_values(lookup_access, metadata)
    attributes[Attribute.LANGUAGE]  = find_attribute_values(lookup_language, metadata)

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
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    r = requests.get(url, headers=headers)
    base_url = get_base_url(r.text, r.url)
    encoded_content = r.text.encode('utf-8')
    metadata = extruct.extract(encoded_content, encoding='utf-8', base_url=base_url, uniform=True)

    return metadata

def translate(text, target_lang, source_lang=None):
    """Return a translated text given a text and a target language.
    
    Args:
        text: A text string
        target_lang: An ISO 639-1 code specifying the target language

    Returns:
        translation: The translated text
    """
    def predict_lang(text):
        # Predict language of text
        model_loc = os.path.join(os.path.dirname(__file__), 'fasttext/lid.176.ftz')
        lang_detector = fasttext.load_model(model_loc)
        prediction = lang_detector.predict(text, k=1)
        # Grab the language label and remove the '__label__' prefix
        pred_lang = prediction[0][0][9:]
        pred_conf = prediction[1][0]

        return pred_lang, pred_conf

    # Predict source language if not specified
    if not source_lang:
        pred_lang, pred_conf = predict_lang(text)
        if pred_conf >= .5:
            source_lang = pred_lang
        #else:
            # TODO: source_lang = HTML lang attribute

    translation = ''
    # Translate if text differs from target language
    # with certain confidence
    if (source_lang and target_lang != source_lang):
        translator = None

        # If DeepL API key is available, use DeepL for translation.
        # Otherwise fall back to default translator.
        DEEPL_API_KEY = os.getenv('DEEPL_API_KEY')
        if DEEPL_API_KEY:
            translator = deepl.Translator(DEEPL_API_KEY, send_platform_info=False)
            limit_reached = translator.get_usage().any_limit_reached
        if translator and not limit_reached:
            translator.set_app_info("url2ref", "0.1")
            # Converting to a target language string accepted by DeepL
            language_codes = [language.code for language in translator.get_target_languages()]
            # Upper-case to achieve sensible results with difflib
            # as the language codes are in upper case
            target_lang = target_lang.upper()
            language_match = difflib.get_close_matches(target_lang, language_codes, n=1, cutoff=0)[0]
            translation = translator.translate_text(text=text,
                                                    source_lang=source_lang,
                                                    target_lang=language_match).text
        else:
            translator = Translator(target_lang, source_lang)
            translation = translator.translate(text)

    return translation, source_lang

def create_wiki_reference(attributes, src_lang, targ_lang):
    """Return a string reference in Wiki markup using the {{Cite web}} template from English Wikipedia.

    Args:
        attributes: Dictionary of attribute-value pairs for title, author etc.

    Returns:
        wiki_ref: {{Cite web}} string reference in Wiki markup
    """
    url = attributes[Attribute.URL]
    if url:
        url = url[0]

    locale = attributes[Attribute.LANGUAGE]
    if locale:
        locale = locale[0]
    else:
        locale = 'en_US'

    # Formatting date
    date = attributes[Attribute.DATE]
    date_ext = ''
    access_date_ext = ''
    # TODO: Add this as function parameter
    user_locale = 'en_US'
    if date:
        date = date[0]
        try:
            parsed_date = dateutil.parser.parse(date)
            date_ext = '|date={}'.format(format_date(parsed_date, format='long', locale=user_locale))
        except dateutil.parser.ParserError:
            date_ext = '' 
    # Setting access-date if date of publication isn't found
    if date_ext == '':
        now = datetime.now()
        access_date_ext = '|access-date={}'.format(format_date(now, format='long', locale=user_locale))

    # Authors
    authors = attributes[Attribute.AUTHORS]
    author_ext = ''
    names = []
    if authors:
        for author in authors:
            name = HumanName(author)
            names.append(name)
        for i in range(len(names)):
            name = names[i]
            if name.first and name.last:
                first_name = ' '.join('{first} {middle}'.format(first=name.first, middle=name.middle).split())
                number = i+1 if len(names) > 1 else ''
                author_ext += '|last{n}={last} |first{n}={first}'.format(n=number, first=first_name, last=name.last)
            else:
                author_ext += '|author{n}={name}'.format(n=i+1, name=name.first)

    # Use wayback to construct an archive URL and date
    client = wayback.WaybackClient()
    archive_url = ''
    archive_date = ''
    try:
        target_window = 62208000 # Two years expressed in seconds
        memento = client.get_memento(url=url, timestamp=datetime.now(), exact=False, target_window=target_window)
        archive_url = memento.memento_url
        archive_date = format_date(memento.timestamp, format='long', locale=locale)
    except wayback.exceptions.MementoPlaybackError:
        pass
    client.close()

    # Website
    website = attributes[Attribute.WEBSITE]
    if website:
        website = website[0]
    if not website:
        try:
            results = tldextract.extract(url)
            website = '.'.join(results[-2:])
        except:
            website = ''

    # Publisher
    publisher = attributes[Attribute.PUBLISHER]
    publisher_ext = ''
    if publisher:
        publisher = publisher[0]
        publisher_ext = '|publisher={}'.format(publisher)

    # Title language detection and translation
    title = attributes[Attribute.TITLE]
    trans_ext = ''
    if title:
        title = title[0]
        translation, detected_lang = translate(text=title, source_lang=src_lang, target_lang=targ_lang)
        if detected_lang == targ_lang or not translation:
            trans_ext = ''
        else:
            trans_ext = '|language={lang} |trans-title={title}'.format(lang=detected_lang, title=translation)
    
    # Check access
    # TODO: Instead of assuming subscription is required, instead ask
    # the user to specify the type of access (limited, registration, or subscription)
    # if free access is 'False'
    access_ext = ''
    access = attributes[Attribute.ACCESS]
    if access:
        access = access[0]
    if access == 'False':
        access_ext = '|url-access=subscription'

    wiki_ref = '<ref>{{{{cite web {authors} |title={title} |url={url} ' \
          '{date} {access_date} |website={website} {publisher} ' \
          '|archive-url={archive_url} |archive-date={archive_date} |url-status=live {trans_title} {access} }}}}</ref>'
    wiki_ref = wiki_ref.format(title=title, url=url, date=date_ext, 
                               access_date=access_date_ext, website=website, publisher=publisher_ext, 
                               authors=author_ext, archive_url=archive_url, archive_date=archive_date, 
                               trans_title=trans_ext, access=access_ext)
    # Remove redundant and trailing spaces
    wiki_ref = ' '.join(wiki_ref.split())

    return wiki_ref

def url2ref(url, src_lang=None, targ_lang='en'):
    metadata = extract_metadata(url)
    attributes = get_reference_attributes(metadata)
    wiki_ref = create_wiki_reference(attributes, 
                                     src_lang=src_lang, 
                                     targ_lang=targ_lang)

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