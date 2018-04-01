from requests import get
from bs4 import BeautifulSoup
from user_agent import generate_user_agent


class WebCrawler(object):
    """Crawls web page for the url provided.
    args: header, url, selectors.
    optional args: header"""

    def __init__(self, **kwargs):

        header = {'User-Agent': generate_user_agent(device_type='desktop', os=('linux', 'mac'))}
        self.header = kwargs.get('header', header)
        self.url = kwargs.get('url')
        self.selectors = kwargs.get('selectors')

        if self.url is None:
            raise KeyError('Give a url to scrape.')

        if self.selectors is None:
            raise KeyError('Provide Selectors to extract the content.')

        if not isinstance(self.selectors, dict):
            raise ValueError('Selectors should be of type key value pairs.')

    @classmethod
    def get_text(cls, args):
        return [arg.text for arg in args]
    
    def _response(self):
        response = get(self.url, headers=self.header, timeout=10)
        if response.status_code == 200:
            return BeautifulSoup(response.text, 'lxml')
        else:
            response.raise_for_status()

    def crawl(self):
        output = {}
        for key, value in self.selectors.items():
            output[key] = ". ".join([dom.text.strip() for dom in self._response().select(value)])
        return output

if __name__ == '__main__':
    kwargs = {
    'url': 'https://www.fnlondon.com/articles/uk-seeks-to-soothe-fund-managers-delegation-fears-20180329',
    'selectors': {
    'header': '.article_header .wsj-article-headline',
    'author': '.author .name',
    'date': '.op-modified'
    }
    }
    print(WebCrawler(**kwargs).crawl())

