import requests
import json
from urllib import parse
from bs4 import BeautifulSoup
import us
import string

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException

state_abbreviations = None

wf_states = []
LANDING_PAGE_LINK = 'https://www.wholefoodsmarket.com/sales-flyer'
sale_items = {}

def scrape(): 
    state = 'California'
    city = 'Los Angeles'
    street = 'national blvd'

    store_sales_url = _get_store_sale_page(state, city, street)

    #once you have the sales_flyer page, turn it into soup
    soup = BeautifulSoup(requests.get(store_sales_url).text, 'html.parser')

    _get_sale_item_data(soup)
    _print_all_sale_items()



def _get_store_sale_page(state, city, street): 
    global state_abbreviations
    state_abbreviation = state_abbreviations[state]

    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    driver = webdriver.Chrome(chrome_options=options)

    driver.get(LANDING_PAGE_LINK)
    sel = Select(driver.find_element_by_id('edit-state'))
    try: 
        sel.select_by_value(state_abbreviation)
    except NoSuchElementException: #no stores found in state
        exit(1)
        #raise StoreNotFoundException('No store in ' + state 
        #        + ' exists.')


    sel_cities = Select(driver.find_element_by_id('edit-store'))
    city_stores = None
    try: 
        city_stores = driver.find_element_by_xpath('//optgroup[@label="'+city+'"]').find_elements_by_tag_name('option')
    except NoSuchElementException: #no stores found in city
        exit(1)
        #raise StoreNotFoundException('No store in ' + city + ', ' + state 
        #       + ' exists.')

    store = None

    #TODO make sure a street was given
    if len(city_stores) > 1: #multiple stores in given city
        street_keywords = street.split(' ')
        #for each store in the city
        for city_store in city_stores: 
            store_address = city_store.get_attribute('label').split('-')[1]
            address_keywords = store_address.split(' ')[2:]#strip street number

            #strip punctuation
            trans = str.maketrans('','', string.punctuation)
            address_keywords = list(map(lambda x : x.translate(trans).lower(), address_keywords)) 

            is_match = True
            i = 0
            while is_match and i < len(address_keywords): 
                if address_keywords[i] not in street_keywords: 
                    is_match = False
                i += 1

            if is_match: 
                store = city_store

    else: #just one store in given city
        store = city_stores[0]


    #get the unique store id for the store in the given state, city, and street
    store_id = store.get_attribute('value')

    #get the url to the weekly sales for the store
    values = {'state': state_abbreviation, 
            'store': store_id
            }
    data = parse.urlencode(values)
    r = requests.get(LANDING_PAGE_LINK, params=data)
    return r.url


def _get_sale_item_data(sale_flyer_page): 
    #Get all the items for sale
    global sale_items
    sales = sale_flyer_page.find_all(class_='views-row views-row-odd')

    #add entry for each sale item to global sale_items dict
    for sale in sales: 
        brand = _get_brand_name(sale)
        product = _get_product_name(sale)
        sale_price, reg_price = _get_item_price_info(sale)

        sale_items[product] = (brand, product, sale_price, reg_price)


def _get_brand_name(sale_item): 
    sale_data = sale_item.find(class_='views-field-field-flyer-brand-name')
    brand_text = sale_data.find(class_='field-content').string

    return brand_text if brand_text else ''


def _get_product_name(sale_item): 
    item_data = sale_item.find(class_='views-field-field-flyer-product-name')
    product_text = item_data.find(class_='field-content').string

    return product_text


def _get_item_price_info(sale_item): 
    item_data = sale_item.find(class_='views-field-nothing')
    price_data = item_data.find(class_='prices-text')

    #Get sale price
    sale_price_text = price_data.find(class_='sale_line')

    if sale_price_text.string is None: #Price format has some modifier like '/lb'
        price = sale_price_text.find(class_='my_price').string
        suffix = sale_price_text.find(class_='sub_price').string
        sale_price_text = price + ' ' + suffix
    else: 
        sale_price_text = sale_price_text.string

    #Get regular price
    reg_price_text = price_data.find(class_='reg_line').string

    return sale_price_text, reg_price_text


def _get_all_sale_items(): 
    return sale_items

def _print_all_sale_items(): 
    for item in sale_items.keys(): 
        brand, product, sale_price, reg_price = sale_items[item]
        print('Item: ' + brand + ' ' + product + 
            '\nSale Price: ' + sale_price + 
            '\nRegular Price: ' + reg_price + '\n')

def _init_abbreviations(): 
    global state_abbreviations
    state_abbreviations = us.states.mapping('name', 'abbr')
    state_abbreviations['British Columbia'] = 'BC'
    state_abbreviations['Ontario'] = 'ON'
    state_abbreviations['United Kingdom'] = 'UK'


class StoreNotFoundException(Exception): 
    def __init__(self, value): 
        self.value = value

    def __str__(self): 
        return repr(self.value)
    
if __name__ == '__main__': 
    _init_abbreviations()
    scrape()
