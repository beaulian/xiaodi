'''
@author: gavin.guan
'''
from tornado.web import HTTPError

INTERNAL_SERVER_ERROR = 'internal_server_error'
BAD_REQUEST_ERROR = 'bad_request_error'

NOT_AUTHORIZED_ERROR = 'not_authorized_error'
EXCEED_MAX_ATTEMPTS_ERROR = 'exceed_max_attempts_error'
FORBIDDEN_ERROR = 'forbidden_error'
NOT_FOUND_ERROR = 'not_found_error'
ALREADY_EXIST_ERROR = 'already_exist_error'
EMAIL_ERROR = 'email_error'

INVALID_ARGUMENT = 'invalid_argument_error'
PAY_ERROR = 'pay_error'


class HTTPAPIError(HTTPError):
    def __init__(self, error_id, message, code=500):
        self.message = message
        self.error_id = error_id
        self.code = code
        super(HTTPAPIError, self).__init__(code, **self.__dict__)

    def __str__(self):
        import json

        attrs = ['message', 'error_id', 'code']
        return json.dumps({attr: self.__getattribute__(attr) for attr in attrs})


def forbidden_error(message):
    raise HTTPAPIError(FORBIDDEN_ERROR, message, 403)


def not_authorized_error(message):
    raise HTTPAPIError(NOT_AUTHORIZED_ERROR, message, 401)


def exceed_max_attempts_error(message):
    raise HTTPAPIError(EXCEED_MAX_ATTEMPTS_ERROR, message, 401)


def not_found_error(message):
    raise HTTPAPIError(NOT_FOUND_ERROR, message, 404)


def already_exist_error(message):
    raise HTTPAPIError(ALREADY_EXIST_ERROR, message, 400)


def invalid_argument_error(message):
    raise HTTPAPIError(INVALID_ARGUMENT, message, 400)


def bad_request_error(message):
    raise HTTPAPIError(BAD_REQUEST_ERROR, message, 400)


def pay_error(message):
    raise HTTPAPIError(PAY_ERROR, message, 400)


def internal_server_error(message):
    raise HTTPAPIError(INTERNAL_SERVER_ERROR, message, 500)



