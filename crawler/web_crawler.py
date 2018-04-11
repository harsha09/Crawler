from requests import get
from bs4 import BeautifulSoup
from user_agent import generate_user_agent


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
        response = get(url, headers=self.header, timeout=10, verify=False)
        if response.status_code == 200:
            return BeautifulSoup(response.text, 'lxml')
        else:
            response.raise_for_status()

    @classmethod
    def get_output(cls, markup, return_type, attr):
        """Returns the innerHTMLText if attr is None. If attr is passed then returns the
        text of that respective html attribute.
        For Example: if attr=href returns href of all the attributes.
        if return_type is string then string is returned by joining the list else list is returned."""
        if attr == 'tags':
            return markup
        output = [dom[attr].strip() if attr else dom.text.strip() for dom in markup]

        if return_type == 'string':
            output = ''.join(output).encode(encoding='utf8', errors='ignore')

        return output

    def crawl(self, **kwargs):
        """Loops through selectors dictionary and returns all selectors."""

        url = kwargs.get('url')
        selectors = kwargs.get('selectors')

        output = {}
        selector = ''
        return_type = 'string'

        for key, value in selectors.items():
            if isinstance(value, dict):
                selector = value.get('selector')
                return_type = value.get('return_type', 'string')
                attr = value.get('attr')
            else:
                attr = None
                selector = value

            output[key] = WebCrawler.get_output(
                self._response(url).select(selector), return_type, attr)
            if isinstance(output[key], bytes):
                output[key] = output[key].decode('utf8')

        return output
