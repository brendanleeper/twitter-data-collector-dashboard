import requests
from .auth import create_headers

class request(object):
    def __init__(self, url, params, endpoint):
        self.url = url
        self.params = params
        self.endpoint = endpoint
    
    def connect_to_endpoint(self, pagination_token = None):
        if pagination_token:
            self.params['pagination_token'] = pagination_token
        print('Executing API request: {}'.format(self.url))
        response = requests.request("GET", self.url, headers = create_headers(), params = self.params)
        print("Endpoint Response Code: " + str(response.status_code))
        if response.status_code != 200:
            raise Exception(response.status_code, response.text)
        return response.json()

    def __str__(self):
        return self.endpoint + ' :: ' + self.url
