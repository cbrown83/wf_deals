import requests
import json
from urllib import parse
from bs4 import BeautifulSoup
import us

state_abbreviations = None

wf_states = []
LANDING_PAGE_LINK = 'https://www.wholefoodsmarket.com/sales-flyer'
sale_items = {}

def scrape(): 
    state = 'Washington'
    city = 'Redmond'
    street = ''

    store_sales_url = _get_store_sale_page(state, city, street)

    #once you have the sales_flyer page, turn it into soup
    soup = BeautifulSoup(requests.get(store_sales_url).text, 'html.parser')

    _get_sale_item_data(soup)
    _print_all_sale_items()



def _get_store_sale_page(state, city, street): 
    global state_abbreviations
    initial_page = requests.get(LANDING_PAGE_LINK)
    soup = BeautifulSoup(initial_page.text, 'html.parser')
    
    state_abbreviation = state_abbreviations[state]

    states_with_stores = soup.find(class_ = 'store-select form-select')

    #current html labels stores by <state_abbrev><city> 
    #e.g. WARedmond for store in Redmond, WA
    label = state_abbreviation + city
    city_stores = states_with_stores.findAll('optgroup', 
            {'label': label})

    city_store = None

    if len(city_stores) < 1: #No store found in given city
        raise StoreNotFoundException('No store in ' + city + ', ' + state 
                + ' exists.')
        
    #TODO make sure a street was given
    elif len(city_stores) > 1: #multiple stores in given city
        city_stores = city_stores.find(label_ = street)

    else: #just one store in given city
        city_store = city_stores[0]


    #get the unique store id for the store in the given state, city, and street
    store_id = city_store.find('option').attrs['value']

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
