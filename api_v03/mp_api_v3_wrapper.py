import datetime as dt
from os import environ
import requests
import logging


class AuthToken:
    def __init__(self, domain):
        self._creation_timestamp: dt.datetime = dt.datetime.now()
        self._expires_in: int = 0
        self._access_token: str = ''
        self._refresh_token: str = ''
        self._domain: str = domain
        logging.info('Object AuthToken initiated')
        
    def _set_properties(self, **kwargs):
        logging.info('Setting up properties')
        self._set_creation_time()
        if 'access_token' in kwargs.keys():
            self._access_token = kwargs['access_token']
        if 'expires_in' in kwargs.keys():
            self._expires_in = kwargs['expires_in']
        if 'refresh_token' in kwargs.keys():
            self._refresh_token = kwargs['refresh_token']
        
    def _set_creation_time(self):
        self._creation_timestamp = dt.datetime.now()
        logging.debug(f'Timestamp created {self._creation_timestamp}')
        
    def _request_token(self):
        logging.info('Requesting token')
        login = environ.get('mp_v3_lg')  # use environment variables to pass credentials
        password = environ.get('mp_v3_ps')
        logging.debug('Credentials retrieved')
        url = f'https://{self._domain}.megaplan.ru/api/v3/auth/access_token'
        payload = {'username': login, 'password': password, 'grant_type': 'password'}
        response = requests.request("POST", url, headers={}, data=payload, files=[])
        logging.debug(response.status_code)
        response_dict = response.json()
        self._set_properties(**response_dict)

    def _check_expiration(self):
        logging.info('Checking token expiration datetime')
        now = dt.datetime.now()
        safe_margin_minutes = dt.timedelta(minutes=120)
        expiration_datetime = self._creation_timestamp + dt.timedelta(seconds=self._expires_in) - safe_margin_minutes
        logging.debug(f'{now=} | {safe_margin_minutes.seconds=} | {expiration_datetime}')
        if now >= expiration_datetime:
            logging.info(f'Token has expired or is about to. Requesting new token')
            self._request_token()

    def return_token(self):
        logging.info('Returning token')
        self._check_expiration()
        return self._access_token


class MegaplanV3:
    def __init__(self, host):
        self._token: AuthToken = AuthToken(host)
        self.host: str = ''
        self._endpoint = f'https://{host}.megaplan.ru/api/v3/'
        logging.info('Object MegaplanV3 initiated')

    def get_method(self, uri, var_str=None, var_arg=None, **kwargs):
        ready_url = f'{self._endpoint}{uri}'
        if var_str and var_arg:
            ready_url.replace(var_str, var_arg)
        logging.debug(ready_url)
        headers = {
            'AUTHORIZATION': f'Bearer {self._token.return_token()}',
            'Content-Type': 'application/json'
        }
        response = requests.get(
            url=ready_url,
            headers=headers,
            params=kwargs['params'] if 'params' in kwargs.keys() else {},
        )
        logging.debug(response.text)
        return response
    
    def post_method(self, uri, var_str=None, var_arg=None, **kwargs):
        ready_url = f'{self._endpoint}{uri}'
        if var_str is not None and var_arg is not None:
            ready_url = ready_url.replace(var_str, str(var_arg))
        logging.debug(ready_url)
        headers = {
            'AUTHORIZATION': f'Bearer {self._token.return_token()}',
            'Content-Type': 'application/json'
        }
        response = requests.post(
            url=ready_url,
            headers=headers,
            data=kwargs['payload'] if 'payload' in kwargs.keys() else {},
        )
        logging.debug(response.text)
        return response


if __name__ == '__main__':
    DOMAIN = ''
    
    logging.basicConfig(
        filename='../logs/api_03_wrapper.log',
        level=logging.DEBUG,
        format='%(asctime)s;%(levelname)s;%(message)s'
    )
    
    api = MegaplanV3(DOMAIN)
    tasks = api.get_method('task/')
    print(tasks)
    