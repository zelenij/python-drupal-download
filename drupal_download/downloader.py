#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from builtins import Exception
from enum import Enum, auto

from typing import Iterable, Callable, Set

import requests
from requests.auth import HTTPBasicAuth

from furl import furl


class DrupalDownloadException(Exception):
    """
    The exception this library uses to report problems
    """
    pass


class AuthType(Enum):
    """
    Authentication types for Drupal REST API
    """
    Anonymous = auto()
    HTTPBasic = auto()
    CookieSession = auto()


class DrupalDadaDownloader(object):
    """
    Download data from a Drupal REST API endpoint. This specific class assumes that each page carries all the
    information needed for each individual object, so it doesn't need to download anything else.
    """
    def __init__(self,
                 base_url: str,
                 username: str,
                 password: str,
                 auth_type: AuthType,
                 on_object: Callable,
                 page_size = 10,
                 skip_duplicates: bool = True):
        """
        Constructor of the class

        :param base_url: the base url of the API endpoint
        :param username: user for the API access. None if anonymous access is available
        :param password: password for the API access. None if anonymous access is available
        :param auth_type: authentication type, as defined in the endpoint configuration
        :param on_object: a callback to process each retrieved object
        :param page_size: how many items retrieve per page
        :param skip_duplicates: whether to skip the same data if seen more than once
        """
        super().__init__()
        self.initial_url: furl = furl(base_url)
        self.username = username
        self.password = password
        self.auth_type = auth_type
        self.on_object = on_object
        self.page_size = page_size
        self.skip_duplicates = skip_duplicates

        self.objects_count = 0
        self.pages_count = 0
        self.logged_in = False
        self.session = requests.Session()
        self.auth = None
        self.seen_objects: Set[int] = set()

    def get_url(self, url: str) -> requests.Response:
        if self.auth_type == AuthType.HTTPBasic:
            if self.auth is None:
                self.auth = HTTPBasicAuth(self.username, self.password)
            return self.session.get(url, auth=self.auth)
        elif self.auth_type == AuthType.Anonymous:
            return self.session.get(url)
        elif self.auth_type == AuthType.CookieSession:
            if not self.logged_in:
                login = dict()
                login['name'] = self.username
                login['pass'] = self.password
                login_url = self.initial_url.set(path="user").add(dict(_format="json"))
                response = self.session.post(login_url.url, data=json.dumps(login))
                if not response.ok:
                    raise DrupalDownloadException(f"Failed to login: {response.reason}")
                self.logged_in = True
            return self.session.get(url)
        else:
            raise DrupalDownloadException(f"Unsupported authentication type {self.auth_type}")

    def load_data(self):
        """
        Load the objects from the API endpoint. On each valid object the on_object callback is invoked.
        """
        self.objects_count = 0
        self.pages_count = 0
        load_next = True
        page = -1
        url = self.initial_url.copy()
        while load_next:
            page += 1
            if page > 0:
                url.args["page"] = page
            elif "page" in url.args:
                del url.args["page"]
            url.args["pagesize"] = self.page_size
            response = self.get_url(url.url)
            if not response.ok:
                raise DrupalDownloadException(f"Failed to get the data: {response.reason}")
            data = response.json()

            count = 0
            if self.skip_duplicates:
                filtered_data = [n for n in data if self.get_object_id(n) not in self.seen_objects]
            else:
                filtered_data = data
            for obj in self.page_to_objects(filtered_data):
                obj_id = self.get_object_id(obj)
                self.seen_objects.add(obj_id)
                count += 1
                self.objects_count += 1
                self.process_object(obj)

            if len(data) > 0:
                self.pages_count += 1
            else:
                load_next = False

    def page_to_objects(self, page_data) -> Iterable:
        return page_data

    def process_object(self, obj):
        self.on_object(obj)

    @staticmethod
    def get_object_id(node) -> int:
        return int(node["nid"])


class Drupal7DadaDownloader(DrupalDadaDownloader):
    """
    A refinement of the downloader class, applicable to the standard service REST APIs in Drupal 7. Their default
    implementation provides only basic data on the index page. To get full data, this class uses the provided uri
    attribute for each individual object.
    """
    def page_to_objects(self, page_data) -> Iterable:
        for obj_data in page_data:
            obj = self.get_url(obj_data["uri"])
            yield obj
