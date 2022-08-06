import requests
import hashlib
import hmac
import base64
from urllib.parse import urlencode
import datetime as dt
from email import utils


class MegaplanAuth:
    __slots__ = [
        'login', 'password', 'host',
        '__proto', 'accessid', 'secretkey', 'domain'
    ]
    
    def __init__(self, host: str, proto='https://'):
        self.host, self.__proto = host, proto
        self.domain = f"{self.__proto}{self.host}.megaplan.ru"
    
    def __password_crypt(self, password: str) -> str:
        return hashlib.md5(password.encode()).hexdigest()
    
    def __get_otk(self, login: str, encrypt_password: str):
        response = requests.post(
            url=f'{self.domain}/BumsCommonApiV01/User/createOneTimeKeyAuth.api',
            headers={'Accept': 'application/json'},
            data={'Login': login, 'Password': encrypt_password})
        resp_json = response.json()
        data = resp_json.get("data")
        status = resp_json.get("status")
        code = status.get("code")
        if code == "error":
            raise ValueError(status.get("message"))
        else:
            return data
    
    def get_key(self, login: str, password: str):
        encrypt_password = self.__password_crypt(password)
        # encrypt_password = password
        response = requests.post(
            url=f'{self.domain}/BumsCommonApiV01/User/authorize.api',
            headers={'Accept': 'application/json'},
            data={'Login': login, 'Password': encrypt_password, 'OneTimeKey': self.__get_otk(login, encrypt_password)})
        resp_json = response.json()
        _AccessId = resp_json["data"]["AccessId"]
        _SecretKey = resp_json["data"]["SecretKey"]
        return _AccessId, _SecretKey


class MegaplanApi:
    __slots__ = [
        '_today', 'AccessId', 'SecretKey',
        'host', '__proto', 'domain', '_today'
    ]
    
    def __init__(self, access_id: str, secret_key: str, host: str, proto='https://'):
        self.host, self.__proto = host, proto
        self.domain = f"{self.__proto}{self.host}.megaplan.ru"
        self.AccessId, self.SecretKey = access_id, secret_key.encode()
    
    def query_hasher(self, request_type, uri, payload=None):
        self._today = utils.format_datetime(dt.datetime.now().astimezone())
        if payload:
            uri = f"{uri}?{urlencode(payload, doseq=True)}"
        query = f"{request_type}\n\napplication/x-www-form-urlencoded\n{self._today}\n{self.host}.megaplan.ru{uri}"
        hash_query = base64.b64encode(hmac.new(
            self.SecretKey,
            query.encode(),
            hashlib.sha1).hexdigest().encode()
                                      ).decode()
        auth_header = {
            'Date': self._today,
            'Accept': 'application/json',
            'X-Authorization': f"{self.AccessId}:{hash_query}",
            'Content-Type': 'application/x-www-form-urlencoded',
            'accept-encoding': 'gzip, deflate, br'
        }
        return auth_header
    
    def get_query(self, uri_query: str, payload=None):
        head = self.query_hasher('GET', uri_query, payload)
        params = urlencode(payload, doseq=True) if payload else None
        response = requests.get(
            url=f"{self.domain}{uri_query}",
            headers=head,
            params=params, timeout=60)
        resp_json = response.json()
        status = resp_json.get("status")
        if status and status.get("code") == "error":
            raise ValueError(status["message"])
        return resp_json.get("data")
    
    def post_query(self, uri_query: str, payload: dict):
        head = self.query_hasher('POST', uri_query, None)
        print(payload)
        response = requests.post(
            url=f"{self.domain}{uri_query}",
            headers=head,
            data=payload)
        resp_json = response.json()
        status = resp_json.get("status")
        if status and status.get("code") == "error":
            raise ValueError(status["message"])
        return response
    
    def __repr__(self):
        return f"<API [{self.domain}]>"


if __name__ == '__main__':
    pass
