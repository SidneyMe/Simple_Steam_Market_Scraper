import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from lxml import etree
import pandas as pd

class Steam:

 
    def __init__(self, urls) -> None:
        self.steam_urls = urls
        self.timer_delay_time = 0
        self.items_list = []
        self.drivers = []
        self.queue = []
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        path_to_chromedriver = r'chromedriver/chromedriver.exe'
        service = Service(executable_path=path_to_chromedriver)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)


    def ulr_processor(self):
        for url in self.steam_urls:
            self.get_all_items(url)


    def get_page(self, current_page):        
        self.driver.get(current_page)
        time.sleep(self.timer_delay_time)
        page = etree.HTML(self.driver.page_source)
        return page


    def get_num_pages(self, url):
        page = self.get_page(url)
        num_items = int(page.xpath('//*[@id="searchResults_total"]')[0].text.replace(',', ''))
        num_of_pages = (num_items // 10) + (1 if num_items % 10 != 0 else 0)
        return num_of_pages + 1


    def get_all_items(self, url):
        self.timer_delay_time = 5
        num_of_items = self.get_num_pages(url)
        base_url = url.split('#')[0]
        for i in range(1, num_of_items):
            current_url = f'{base_url}#p{i}_price_asc'
            page = self.get_page(current_url)
            for market_listing in page.xpath('//*[@id="searchResultsRows"]/a[contains(@class, "market_listing_row")]'):
                href = market_listing.get('href')
                name = market_listing.xpath('.//div[contains(@class, "market_listing_item_name_block")]/span/text()')[0]
                qty = market_listing.xpath('.//span[@class="market_listing_num_listings_qty"]/@data-qty')[0]
                price = market_listing.xpath('.//span[@class="normal_price"]/text()')[0]
                self.items_list.append({
                    'name': name,
                    'url': href,
                    'qty': qty,
                    'price': price,
                })


    def get_sales(self):
        self.ulr_processor()
        self.timer_delay_time = 2
        for item in self.items_list:
            item['ulr'] = item['url'].replace('https://steamcommunity.com/market/listings/730/', 'https://steamfolio.com/Item?name=')
            page = self.get_page(item['url'])
            item.update({
                'sales_w' : page.xpath('//*[@id="item-container"]/div/div/div/div[2]/div[2]/div/div[2]/div[1]/div/div/table/tbody/tr[2]/td/text()')[0],
                'sales_m' : page.xpath('//*[@id="item-container"]/div/div/div/div[2]/div[2]/div/div[2]/div[1]/div/div/table/tbody/tr[3]/td/text()')[0],
                'sales_y': page.xpath('//*[@id="item-container"]/div/div/div/div[2]/div[2]/div/div[2]/div[1]/div/div/table/tbody/tr[4]/td/text()')[0],         
            })
        print(self.items_list)


    def generate_xml(self):
        self.get_sales()
        root = etree.Element('Items')
        for item in self.items_list:
            item_element = etree.SubElement(root, 'Item')
            for key, value in item.items():
                sub_element = etree.SubElement(item_element, key)
                sub_element.text = value       
        tree = etree.ElementTree(root)
        with open('test.xml', 'wb') as f:
            tree.write(f, pretty_print=True, xml_declaration=True, encoding='UTF-8')


    def generate_exel(self): 
        df = pd.DataFrame(self.items_list)
        df.to_excel('steam_items_table.xlsx', index=False)
        print('Exel has been generated')


    def close(self):
        try:
            self.driver.quit()
        except Exception as ex:
            print(f'Failed to close webdriver {ex}')


if __name__ == '__main__':        
    steam_urls = ['']
    s = Steam(steam_urls)
    try:
        s.generate_xml()
        s.generate_exel()
    finally:
        s.close()
