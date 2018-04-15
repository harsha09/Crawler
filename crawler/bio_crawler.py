from web_crawler import WebCrawler
import yaml
import pandas as pd
import os
import pyodbc
import logging

server = 'KOMARRAJU\SQLEXPRESS'
database = 'finacplus'

data_lable_mapping = {
    'URL': 1, 'Name': 2, 'Title': 3, 'Bio': 4, 'Division': 5,
    'Phone-1': 6, 'Phone-2': 7, 'Email': 8
}

vistara_division = {
    'f_1': 'Executive Committee', 'f_6': 'Alternative Investments',
    'f_3': 'Company Formation', 'f_5': 'Corporate Clients',
    'f_4': 'International Expansion', 'f_2': 'Private Clients',
    'f_7': 'Group Functions'
}

row_num = 1
logger = logging.getLogger('bio_crawler_logger')
logger.setLevel(logging.DEBUG)

file_logger = logging.FileHandler('log.log')
file_logger.setLevel(logging.ERROR)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_logger.setFormatter(formatter)

logger.addHandler(file_logger)

def get_from_naviscapital(data, mapping):
    items = split_list(data[1:], 'hr')

    for item in items:
        temp = {}
        name = item[0].select('strong')[0].text.strip()
        designation = item[0].select('span')[0].text.strip()
        bio = "".join([bio_tag.text for bio_tag in item[2:]])

        yield {
            mapping['Name']: name.replace('\u200b', ''),
            mapping['Bio']: bio.replace('\u200b', ''),
            mapping['Title']: designation.replace('\u200b', '')
        }

def get_from_jll_bod(data, mapping):
    import re

    data = [i for i in data if i.name in ['p', 'h3']]

    items = split_list1(data, 'h3')
    for item in items:
        temp = {}
        name = item[0].text.strip()
        name = name.replace('\u200b', '')
        name = re.sub(r'(\w)([A-Z])', r'\1 \2', name).strip()

        bio = item[-1].text
        bio = bio.replace('\u200b', '')

        if len(item) == 2:
            title_array = [i.text for i in item[-1].select('strong')]
            title = ", ".join(title_array)
            bio = bio.replace(''.join(title_array), '')
        else:
            title = BioCrawler._content_delimited(item[1:-1][0], delimiter=', ')

        yield {
            mapping['Name']: name.replace('\u200b', ''),
            mapping['Bio']: bio.replace('\u200b', ''),
            mapping['Title']: title.replace('\u200b', ''),
            mapping['Division']: 'Board of Directors'
        }

def get_from_jll_corporate(data, mapping):
    import re

    names = [i.select('strong') for i in data]
    names = [''.join([i.text for i in name]) for name in names if len(name)]
    names = [re.sub('\W+', ' ', i.strip()) for i in names if len(i.strip())]

    title = [BioCrawler._content_delimited(i, delimiter=' ') for i in data]
    title = [re.sub('\W+', ' ', i.strip()) for i in title]
    title = [i.strip() for i in title if len(i.strip())]

    title = [re.sub(r'(\w)([A-Z])', r'\1 \2', title[i].replace(name.lstrip(), '')).strip() for i, name in enumerate(names)]

    division = ['Additional Corporate Officers'] * len(names)
    for i in zip(names, title, division):
        yield {
            mapping['Name']: i[0].replace('\u200b', ''),
            mapping['Title']: i[1].replace('\u200b', ''),
            mapping['Division']: i[2].replace('\u200b', '')
        }

def split_list1(l, cond):
    output = []
    temp = []
    first = True

    for i in l:
        if i.name == cond:
            if not first:
                output.append(temp)
                temp = []
            else:
                first = False
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
    output.append(temp)
    return output

def write_to_file(data):
    data = pd.DataFrame.from_dict(data, orient='index').T
    output_data = pd.DataFrame()
    if os.path.exists('output.csv'):
        output_data = pd.read_csv('output.csv')

    pd.concat([output_data, data]).to_csv('output.csv', index=False)

def write_to_database(data, link_num):
    global row_num, server, database
    global data_lable_mapping, logger
    con = pyodbc.connect('Trusted_Connection=yes', driver = '{SQL Server}',server = server, database = database)
    try:
        cur = con.cursor()
        querylog="insert into PECCLinkLog1(PECCLinkID,RunDateTime,StatusCode) values({}, getdate(), {})".format(link_num, 1)
        cur.execute(querylog)
        con.commit()
        # print(querylog)
        name = data.get('Name')
        name = name.replace("'", "''")
        for data_label in data.keys():
            data_value = data[data_label].replace("'", "''")
            querystring = "insert into PECCLinkData1 (PECCLinkLogID,RowNum,DataLabelID,DataLabel,DataValue,DownloadDate,BackChFlagID,UniIdentifier) values({}, {}, {}, '{}', '{}', getdate(), '{}', '{}')".format(get_log_num(), row_num, data_lable_mapping[data_label], data_label, data_value, 'New', name)
            # print(querystring)
            cur.execute(querystring)
        con.commit()
    except Exception as e:
        logger.error(data.get('URL'))
        logger.error(data.get('Name'))
        logger.error(data.get('Bio'))
        logger.error(e)
    finally:
        con.close()
    row_num += 1

def get_log_num():
    global server, database
    con = pyodbc.connect('Trusted_Connection=yes', driver = '{SQL Server}',server = server, database = database)
    cur = con.cursor()
    querylog="select ISNULL(max(PECCLinkLogID), 1) as cnt from PECCLinkLog1"
    cur.execute(querylog)
    log_num = cur.fetchone()

    return log_num[0]

link_num = 0

class BioCrawler(WebCrawler):
    def __init__(self, **kwargs):
        super().__init__()
        global row_num
        row_num = 1
        self.config = kwargs.get('config')
        global link_num
        link_num += 1

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
                i.update({'URL': url})
                write_to_database(i, link_num)
                # write_to_file(i)
        else:
            count = 0

            for link in links.get('base_links', []):
                url = '{}{}'.format(self.config.get('bio_selectors').get('base_url', ''), link)
                selectors = BioCrawler._get_selectors(self.config.get('bio_selectors'))

                replacer = {key: val for key, val in selectors.items() if val.find('{{') > -1}

                try:
                    output = self.crawl(url=url, selectors={key: val for key, val in selectors.items() if val.find('{{') == -1})
                    if replacer:
                        for replacer_key in replacer:
                            replacer_vals = links.get(replacer[replacer_key].replace('{{', '').replace('}}', '').strip(), [])
                            if len(replacer_vals) == 1:
                                replacer_val = replacer_vals[0]
                            else:
                                replacer_val = replacer_vals[count]

                            output.update({replacer_key: replacer_val})
                except Exception as e:
                    print(e)

                output.update({'URL': url})
                write_to_database(output, link_num)
                # write_to_file(output)                
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
