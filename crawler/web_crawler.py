from requests import get
from bs4 import BeautifulSoup
import bs4.element
from user_agent import generate_user_agent
from urllib.parse import urlparse


class WebCrawler(object):
    """Crawls web page for the url provided.
    args: header, url, selectors.
    optional args: header
    Example:
    kwargs = {
    'url': 'https://www.fnlondon.com/articles/uk-seeks-to-soothe-fund-managers-delegation-fears-20180329',
    'selectors': {
    'header': '.article_header .wsj-article-headline',
    'author': '.author .name',
    'date': '.op-modified'
    }
    }
    kwargs = {
    'url': 'https://www.bloomberg.com/markets',
    'selectors':{
        'stories_link': {
            'selector': '.top-news-v3__stories .top-news-v3-story-view .top-news-v3-story-headline a',
            'return_type': 'list',
            'attr': 'href'
            }
        }
    }
    print(WebCrawler(**kwargs).crawl())
    """

    def __init__(self, **kwargs):

        header = {'User-Agent': generate_user_agent(device_type='desktop', os=('linux', 'mac'))}
        self.header = kwargs.get('header', header)
    
    def _response(self, url):
        url = urlparse(url)
        if not url.scheme:
            url = url._replace(scheme='https')

        response = get(url.geturl(), headers=self.header, timeout=20, verify=False)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            for script in soup(['script', 'style']):
                script.extract()
            return soup
        else:
            response.raise_for_status()

    @classmethod
    def _content_delimited(cls, tag, delimiter):
        if isinstance(tag, str) or isinstance(tag, bs4.element.NavigableString):
            return tag

        return '{}'.format(delimiter).join(
            [i.strip() if isinstance(i, bs4.element.NavigableString) else i.text.strip() for i in tag.contents])

    @classmethod
    def get_output(cls, markup, return_type, attr, delimiter):
        """Returns the innerHTMLText if attr is None. If attr is passed then returns the
        text of that respective html attribute.
        For Example: if attr=href returns href of all the attributes.
        if return_type is string then string is returned by joining the list else list is returned."""

        if attr == 'tags':
            return markup
        output = [dom[attr].strip().replace('\u200b', '') if attr else WebCrawler._content_delimited(dom, delimiter).replace('\u200b', '') for dom in markup]

        if return_type == 'string':
            output = ' '.join([i for i in output if i])
            output = output.replace('\u200b', '')

        return output

    def crawl(self, **kwargs):
        """Loops through selectors dictionary and returns all selectors."""

        url = kwargs.get('url')
        selectors = kwargs.get('selectors')

        output = {}
        selector = ''
        return_type = 'string'
        delimiter = '\r\n'

        for key, value in selectors.items():
            if isinstance(value, dict):
                selector = value.get('selector')
                return_type = value.get('return_type', 'string')
                attr = value.get('attr')
                delimiter = value.get('delimiter', '\r\n')
            else:
                attr = None
                selector = value

            if selector.find('{%') == -1:
                dom_selectors = self._response(url).select(selector)
                if 'subselector' in value:
                    dom_selectors = [i.select(value.get('subselector'))[0].text.strip() for i in dom_selectors]
                output[key] = WebCrawler.get_output(dom_selectors, return_type, attr, delimiter)
            else:
                output[key] = value.replace('{%', '').replace('%}', '').strip()

            if 'replacer' in value and 'replacee' in value:
                replacer = value.get('replacer')
                replacee = value.get('replacee')

                if isinstance(output[key], str):
                    output[key] = output[key].replace(replacee, replacer).strip()
                if isinstance(output[key], list):
                    output[key] = [i.replace(replacee, replacer).strip() for i in output[key]]

        return output
