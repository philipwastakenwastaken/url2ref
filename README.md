# url2ref &ndash; create a reference from a web address

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Website](https://img.shields.io/website/https/url2ref.onrender.com?up_message=online&down_message=offline)](https://url2ref.onrender.com)

## Motivation

Manually citing a news article on the web in a thorough manner can be a tedious process. To do so, one has to write down the title, authors, publication date, work and other attributes. While there exists tools for converting a collection of attributes into a specific reference style, the manual collection of those attributes typically remains a chore. However, this application aims to make this process automatic for some web resources, namely those which have structured and annotated their content according to a semantic web format, such as [Microdata](https://developer.mozilla.org/en-US/docs/Web/HTML/Microdata), [RDFa](https://en.wikipedia.org/wiki/RDFa) or [JSON-LD](https://json-ld.org/), using the [Schema.org](https://schema.org/) vocabulary.

## Front end

The application [has a web front end](https://url2ref.onrender.com/) hosted by [Render](https://render.com), making it easy to retrieve a reference simply by pasting a URL into the query field. The front end is created with [Bootstrap via npm](https://getbootstrap.com/docs/5.0/getting-started/download/#npm).

## Local execution

### Script

The application can be executed as a script from the command-line after installing the required packages with ``pip install -r requirements.txt``. To generate a [wiki reference](https://en.wikipedia.org/wiki/Template:Cite_web) for a given URL, simply type:

```bash
python url2ref.py -u <URL>
```

### Flask app

To build and run the front end locally, first install the required Python packages by running ``pip install -r requirements.txt`` &ndash; preferably within a virtual environment &ndash; and then install the needed Bootstrap files with ``npm i bootstrap @popperjs/core`` from within the ``flaskapp/static/assets`` folder. Then, a Flask development server can be started locally with ``flask --app app --debug run``.

## License

The code in this project is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0).
