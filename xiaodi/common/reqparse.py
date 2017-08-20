# coding=utf-8
import re
import six
from enum import Enum
from tornado.httputil import HTTPFile
from xiaodi.api.abc import Namespace
from xiaodi.common.utils import xss_filter
from xiaodi.api.errors import invalid_argument_error
from xiaodi.api.errors import internal_server_error


__all__ = ['RequestParser']


def handle_validation_error(error):
    error_str = six.text_type(error)

    return invalid_argument_error(error_str)


class ArgumentSources(Enum):
    BODY = 'body'
    QUERY = 'query'
    FILE = 'file'


class Argument(object):
    def __init__(self, name, required=False, default=None,
                 ignore=False, type=six.text_type, filter=None,
                 choices=(), case_sensitive=True, strip=True,
                 source=None):
        self.name = name
        self.default = default
        self.required = required
        self.ignore = ignore
        self.type = type
        self.choices = choices
        self.case_sensitive = case_sensitive
        self.strip = strip
        self.source = source
        self.filter = filter

    def convert(self, value):
        if value is None:
            return None
        elif isinstance(value, HTTPFile) and self.type == HTTPFile:
            return value

        if callable(self.type):
            try:
                return self.type(value)
            except Exception as e:
                return internal_server_error(str(e))
        return value

    def parse(self, req):
        if self.source == ArgumentSources.BODY.value:
            value = xss_filter(req.get_body_argument(self.name, default=self.default, strip=self.strip))
        elif self.source == ArgumentSources.QUERY.value:
            value = xss_filter(req.get_query_argument(self.name, default=self.default, strip=self.strip))
        elif self.source == ArgumentSources.FILE.value:
            value = req.request.files.get(self.name)
            if isinstance(value, list) and len(value):
                value = value[0]
        else:
            return internal_server_error('no such params source: %s' % self.source)
        try:
            value = self.convert(value)
        except ValueError as error:
            if not self.ignore:
                return handle_validation_error(error)
        if value is None:
            if self.required:
                return handle_validation_error('missing required argument: %s' % self.name)
            elif self.default:
                return self.default

        if self.filter:
            if isinstance(value, six.string_types) and \
                    re.match(self.filter, value) is None:
                return handle_validation_error('invalid argument: %s, must satisfy %s' % (self.name, self.filter))
            elif isinstance(value, six.integer_types) and \
                    re.match(self.filter, str(value)) is None:
                return handle_validation_error('invalid argument: %s, must satisfy %s' % (self.name, self.filter))

        if hasattr(value, "lower") and not self.case_sensitive:
            value = value.lower()

            if hasattr(self.choices, "__iter__"):
                self.choices = [choice.lower()
                                for choice in self.choices]

        if self.choices and value not in self.choices:
            return handle_validation_error('invalid argument: %s, must choice from %s' % (self.name, str(self.choices)))

        return value


class RequestParser(object):
    def __init__(self, namespace_class=Namespace, argument_class=Argument):
        self.args = []
        self.namespace_class = namespace_class
        self.argument_class = argument_class

    def _add_argument(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], self.argument_class):
            self.args.append(args[0])
        else:
            self.args.append(self.argument_class(*args, **kwargs))

        return self

    def add_body_argument(self, *args, **kwargs):
        kwargs['source'] = ArgumentSources.BODY.value
        return self._add_argument(*args, **kwargs)

    def add_query_argument(self, *args, **kwargs):
        kwargs['source'] = ArgumentSources.QUERY.value
        return self._add_argument(*args, **kwargs)

    def add_file_argument(self, *args, **kwargs):
        kwargs['source'] = ArgumentSources.FILE.value
        return self._add_argument(*args, **kwargs)

    def parse_args(self, request=None):
        if request is None:
            return

        namespace = self.namespace_class()
        for arg in self.args:
            value = arg.parse(request)
            namespace[arg.name] = value

        return namespace
