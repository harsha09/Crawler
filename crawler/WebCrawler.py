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
        self.url = kwargs.get('url')
        self.selectors = kwargs.get('selectors')

        if not self.url:
            raise KeyError('Give a url to scrape.')

        if self.selectors is None:
            raise KeyError('Provide Selectors to extract the content.')

        if not isinstance(self.selectors, dict):
            raise ValueError('Selectors should be of type key value pairs.')
    
    def _response(self):
        response = get(self.url, headers=self.header, timeout=10)
        if response.status_code == 200:
            return BeautifulSoup(response.text, 'lxml')
        else:
            response.raise_for_status()

    @classmethod
    def get_output(cls, scraped, return_type, attr):

        output = [dom[attr].strip() for dom in scraped] if attr else [dom.text.strip() for dom in scraped]

        if return_type == 'string':
            output = '. '.join(output)

        return output


    def crawl(self):
        output = {}
        selector = ''
        return_type = 'string'
        attr = None

        for key, value in self.selectors.items():

            if isinstance(value, dict):
                selector = value.get('selector')
                return_type = value.get('return_type', 'string')
                attr = value.get('attr')
            else:
                selector = value

            output[key] = WebCrawler.get_output(
                self._response().select(selector), return_type, attr)

        return output

