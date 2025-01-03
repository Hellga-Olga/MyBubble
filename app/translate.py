import requests
from flask_babel import _
from app import current_app

def translate(text, source_language, dest_language):
    #  checks if there is a key for the translation service in the configuration
    if 'MS_TRANSLATOR_KEY' not in current_app.config or not current_app.config['MS_TRANSLATOR_KEY']:
        print(current_app.config['SECRET_KEY'])
        return _('Error: the translation service is not configured')
    auth = {
        'Ocp-Apim-Subscription-Key': current_app.config['MS_TRANSLATOR_KEY'],
        'Ocp-Apim-Subscription-Region': 'westeurope',
    }
    # sends an HTTP request with a POST method to the URL given as the first argument
    r = requests.post('https://api.cognitive.microsofttranslator.com'
                      '/translate?api-version=3.0&from={}&to={}'.format(source_language, dest_language), headers=auth, json=[{'Text': text}])
    if r.status_code != 200:
        return _('Error: the translation service failed')
    return r.json()[0]['translations'][0]['text']