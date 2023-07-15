# url2ref &ndash; create a reference from a web address

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Website](https://img.shields.io/website/https/url2ref.onrender.com?up_message=online&down_message=offline)](https://url2ref.onrender.com)

## Motivation

Manually citing a news article on the web in a thorough manner can be a tedious process. To do so, one has to write down the title, authors, publication date, work and other attributes. While there exists tools for converting a collection of attributes into a specific reference style, the manual collection of those attributes typically remains a chore. However, this application aims to make this process automatic for some web resources, namely those which have structured and annotated their content according to a semantic web format, such as [Microdata](https://developer.mozilla.org/en-US/docs/Web/HTML/Microdata), [RDFa](https://en.wikipedia.org/wiki/RDFa) or [JSON-LD](https://json-ld.org/), using the [Schema.org](https://schema.org/) vocabulary.

## Front end

The application [has a web front end](https://url2ref.onrender.com/) hosted by [Render](https://render.com), making it easy to retrieve a reference simply by pasting a URL into the query field. The front end is created with [Bootstrap via npm](https://getbootstrap.com/docs/5.0/getting-started/download/#npm).

## Features

* Generate a [{{cite web}}](https://en.wikipedia.org/wiki/Template:Cite_web) Wikipedia markup reference for a given URL
* Locale-aware date format conversion and title translation
* Automatic insertion of an archived URL from the [Internet Archive](https://en.wikipedia.org/wiki/Internet_Archive) using the [Wayback Machine](http://web.archive.org/)
* Automatic title translation using the [DeepL API](https://www.deepl.com/en/docs-api/)

## Local execution

### Script

The application can be executed as a script from the command-line after installing the required packages with ``pip install -r requirements.txt``. To generate a [wiki reference](https://en.wikipedia.org/wiki/Template:Cite_web) for a given URL, simply type:

```bash
python url2ref.py -u <URL>
```

### Flask app

To build and run the front end locally, first install the required Python packages by running ``pip install -r requirements.txt`` &ndash; preferably within a virtual environment. Then, from within the ``flaskapp/static/assets`` folder, install the needed ``npm`` packages with the following command:

```bash
npm i bootstrap@5.3.0 @popperjs/core@2.11.8 bootstrap-icons@1.10.5
```

A Flask development server can then be started locally by running ``flask --app app --debug run`` from within the ``flaskapp`` directory.

## License

The code in this project is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0).

The ``lid.176.ftz`` model for language identification is [distributed by FastText](https://fasttext.cc/docs/en/language-identification.html) and licensed under [CC-BY-SA 3.0](http://creativecommons.org/licenses/by-sa/3.0/). See [fasttext/ATTRIBUTION.md](./fasttext) for more details.
