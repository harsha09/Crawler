from web_crawler import WebCrawler
import yaml
import pandas as pd
import os

def get_from_naviscapital(data, mapping):
    items = split_list(data[1:], 'hr')

    for item in items:
        temp = {}
        name = item[0].select('strong')[0].text.strip()
        designation = item[0].select('span')[0].text.strip()
        bio = "".join([bio_tag.text for bio_tag in item[2:]])

        yield {
            mapping['Name']: name,
            mapping['BIO']: bio,
            mapping['Title']: designation
        }

def get_from_jll_bod(data, mapping):
    items = split_list1(data, 'h3')
    import pdb
    pdb.set_trace()
    for item in items:
        temp = {}
        name = item[0].select('h3').text.strip()
        # designation = item[]
    import pdb
    pdb.set_trace()

def split_list1(l, cond):
    output = []
    temp = []
    first = True
    for i in l:
        if first:
            temp += [i]
        if i.name == cond:
            if not first:
                output.append(temp)
                temp = []
            else:
                first = False
        if not first:
            temp += [i]
    output.append(temp)
    return output

def split_list(l, cond):
    output = []
    temp = []
    for i in l:
        if i.name == cond:
            output.append(temp)
            temp = []
        else:
            temp += [i]
    return output

def write_to_file(data):
    data = pd.DataFrame.from_dict(data, orient='index').T
    output_data = pd.DataFrame()
    if os.path.exists('output.csv'):
        output_data = pd.read_csv('output.csv')

    pd.concat([output_data, data]).to_csv('output.csv', index=False)

class BioCrawler(WebCrawler):
    def __init__(self, **kwargs):
        super().__init__()

        self.config = kwargs.get('config')

        if not self.config:
            raise KeyError('Expecting config file path.')

        url = self.config.get('url')

        if not url:
            raise KeyError('Give a url to scrape.')

        selectors = BioCrawler._get_selectors(self.config)

        if isinstance(selectors, list):
            link = self.crawl(url=url, selectors=selectors[0])
            link = link.get('base_links')[0]
            base_link = selectors[1].get('base_links').get('base_url')
            links = self.crawl(url='{}{}'.format(base_link, link), selectors=selectors[1])
        else:
            links = self.crawl(url=url, selectors=selectors)

        if self.config.get('function'):
            func = self.config.get('function').get('func_name')
            func = eval(compile(func, 'temp.txt', mode='eval'))
            output = func(links.get('Data', []), self.config.get('function'))
            for i in output:
                write_to_file(i)
        else:
            count = 0

            for link in links.get('base_links', []):
                url = '{}{}'.format(self.config.get('bio_selectors').get('base_url', ''), link)
                selectors = BioCrawler._get_selectors(self.config.get('bio_selectors'))

                replacer = {key: val for key, val in selectors.items() if val.find('{{') > -1}

                output = self.crawl(url=url, selectors={key: val for key, val in selectors.items() if val.find('{{') == -1})
                if replacer:
                    for replacer_key in replacer:
                        replacer_vals = links.get(replacer[replacer_key].replace('{{', '').replace('}}', '').strip(), [])
                        if len(replacer_vals) == 1:
                            replacer_val = replacer_vals[0]
                        else:
                            replacer_val = replacer_vals[count]

                        output.update({replacer_key: replacer_val})

                write_to_file(output)                
                count += 1

    @classmethod
    def _get_selectors(cls, config):
        selectors = config.get('selectors')
        if selectors is None:
            raise KeyError('Provide Selectors to extract the content.')

        return selectors        

if __name__ == '__main__':
    with open('seerconfig.yaml') as file_handler:
        configs = yaml.load(file_handler)

    for config in configs:
        BioCrawler(config=config['stories_link'])
