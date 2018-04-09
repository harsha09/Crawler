from web_crawler import WebCrawler
import yaml
import pandas as pd
import os


class ArticleCrawler(WebCrawler):
    def __init__(self, **kwargs):
        super().__init__()

        self.config = kwargs.get('config')

        if not self.config:
            raise KeyError('Expecting config file path.')

        url = self.config.get('url')

        if not url:
            raise KeyError('Give a url to scrape.')

        selectors = ArticleCrawler._get_selectors(self.config)

        if isinstance(selectors, list):
            link = self.crawl(url=url, selectors=selectors[0])
            link = link.get('base_links')[0]
            base_link = selectors[1].get('base_links').get('base_url')
            links = self.crawl(url='{}{}'.format(base_link, link), selectors=selectors[1])
        else:
            links = self.crawl(url=url, selectors=selectors)
        import pdb
        pdb.set_trace()
        for link in links.get('base_links', []):
            url = '{}{}'.format(self.config.get('articles').get('base_url', ''), link)
            output = self.crawl(url=url, selectors=ArticleCrawler._get_selectors(self.config.get('articles')))
            data = pd.DataFrame.from_dict(output, orient='index').T
            output_data = pd.DataFrame()
            if os.path.exists('output.csv'):
                output_data = pd.read_csv('output.csv')
            
            pd.concat([output_data, data]).to_csv('output.csv', index=False)

    @classmethod
    def _get_selectors(cls, config):
        selectors = config.get('selectors')
        if selectors is None:
            raise KeyError('Provide Selectors to extract the content.')

        return selectors        


with open('seerconfig.yaml') as file_handler:
    configs = yaml.load(file_handler)

for config in configs:
    ArticleCrawler(config=config['stories_link'])
