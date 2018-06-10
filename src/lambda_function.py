import time

import logging

from scraper import scrape_all_deals
from scraper import scrape_for_category
from scraper import scrape_for_brand

from webdriver_wrapper import WebDriverWrapper

SALE_PREFIX = 'This week at your local Whole Foods, '
NO_STORE_FOUND = 'I\'m sorry. There were no stores found in '
HELP_MESSAGE = 'To find out the weekly deals at your local Whole Foods, say \'tell me the deals in\' followed by your city and state. If there are multiple stores in your city, say the street name after your city and state.'
FALLBACK_MESSAGE = 'Please say your city and state. If there are multiple stores in your city, say the street name after your city and state.'

# *********** ALEXA ENDPOINT **********
def lambda_handler(event, context):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    request = event['request']
    request_type = request['type']

    if event['session']['new']: 
        print('New session initiated')

    if request_type == 'LaunchRequest':
        return on_launch(request)
    elif request_type == 'IntentRequest': 
        return on_intent(request, event['session'])
    elif request_type == 'SessionEndedRequest': 
        return on_session_ended()


# *********** REQUESTS ***************
def on_intent(request, session): 
    intent_name = request['intent']['name']

    if 'dialogState' in request: 
        #delegate to Alexa until dialog sequence is complete
        if request['dialogState'] == 'STARTED' or request['dialogState'] == 'IN_PROGRESS':
            return dialog_response('', False)

    if intent_name == 'GetDeals': 
        return get_all_deals_response(request)
    elif intent_name == 'GetDealsByCategory': 
        return get_deals_by_category_response(request)
    elif intent_name == 'GetDealsByBrand': 
        return get_deals_by_brand_response(request)
    elif intent_name == 'AMAZON.HelpIntent': 
        return get_help_response()
    elif intent_name == 'AMAZON.StopIntent': 
        return get_stop_response()
    elif intent_name == 'AMAZON.CancelIntent': 
        return get_stop_response()
    elif intent_name == 'AMAZON.FallbackIntent': 
        return get_fallback_response(request)
    else: 
        return get_help_response()

def get_all_deals_response(request): 
    logger.info('get all deals request')
    #TODO could update this to fetch location 
    city, state, street = extract_location(request)
    sale_items = scrape_all_deals(state, city, street)

    #interpret scrape response
    speech_output = SALE_PREFIX + how_to_say(sale_items)
    return response(speech_response(speech_output, True))

def get_deals_by_category_response(request): 
    logger.info('get deals by category request')
    city, state, street = extract_location(request) 
    category = get_slot_value('category', request)
    sale_items_by_category = scrape_for_category(category, state, city, street)

    speech_output = SALE_PREFIX + how_to_say(sale_items_by_category)
    return response(speech_response(speech_output, True))

def get_deals_by_brand_response(request): 
    logger.info('get deals by brand request')
    city, state, street = extract_location(request) 
    brand = get_slot_value('brand', request)
    sale_items_by_brand = scrape_for_brand(brand, state, city, street)

    speech_output = SALE_PREFIX + how_to_say(sale_items_by_brand)
    return response(speech_response(speech_output, True))

def get_launch_response(request): 
    return get_all_deals_response(request)

def get_fallback_response(request): 
    speech_output = FALLBACK_MESSAGE
    return response(speech_response(speech_output, True))

def get_stop_response(): 
    speech_output = ''
    return response(speech_response(speech_output, True))

def get_help_response(): 
    speech_output = HELP_MESSAGE
    return response(speech_response(speech_output, True))

def on_launch(request): 
    return get_launch_response(request)

def on_session_ended(): 
    print('on_session_ended')


# ******* SPEECH RESPONSE HANDLERS **********
def speech_response(output, endsession): 
    return {
        'outputSpeech': {
            'type': 'PlainText', 
            'text': output
        },
        'shouldEndSession': endsession
    }

def dialog_response(attributes, endsession): 
    return {
        'version': '1.0', 
        'sessionAttributes': attributes,
        'response':{
            'directives': [
                {
                    'type': 'Dialog.Delegate'
                }
            ], 
            'shouldEndSession': endsession
        }
    }

def response(speech_message): 
    return {
        'version': '1.0', 
        'response': speech_message
    }


# ********* STRING FORMATTER *********
def how_to_say(item_dict): 
    '''dict structure: 
    key: product type
    value: (brand, product type, sale price, regular price)
    '''
    sales_string = ''
    for item in item_dict.keys(): 
        brand, product, sale_price, reg_price = item_dict[item]
        sales_string += (str(brand) + ' ' + str(product) + ' is on sale for ' + 
                str(sale_price) + '. ')

    return sales_string

# ********* FUNCTIONAL HELPERS **********
def extract_location(request): 
    city = get_slot_value('city', request)
    state = get_slot_value('state', request)

    street = None
    try: 
        street = get_slot_value('street', request)
    except KeyError: 
        street = ''

    return city, state, street

def get_slot_value(slot, request): 
    return request['intent']['slots'][slot]['value']
