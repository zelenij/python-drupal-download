#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from builtins import Exception
from enum import Enum, auto

from typing import Iterable, Callable, Set, Optional, Dict

import logging

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

    logger = logging.getLogger("DrupalDownload")

    def __init__(self,
                 base_url: str,
                 username: str,
                 password: str,
                 auth_type: AuthType,
                 on_object: Callable,
                 page_size: Optional[int] = None,
                 skip_duplicates: bool = True,
                 id_name: Optional[str] = None):
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
        self.id_name: Optional[str] = id_name

        if self.page_size is not None and self.page_size <= 0:
            raise DrupalDownloadException(f"Page size must be positive or None")

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
                self.logger.info(f"Not logged in, login into Drupal session for {self.username}")
                login = dict()
                login['name'] = self.username
                login['pass'] = self.password
                login_url = self.get_login_url()
                headers = {'Content-type': 'application/json'}
                response = self.session.post(login_url.url, json=login, headers=headers)
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
        self.logger.info(f"Starting data extraction from {self.initial_url}")
        while load_next:
            page += 1
            if page > 0:
                url.args["page"] = page
            elif "page" in url.args:
                del url.args["page"]
            if self.page_size is not None:
                url.args["pagesize"] = self.page_size
            response = self.get_url(url.url)
            if not response.ok:
                raise DrupalDownloadException(f"Failed to get the data from {url}: {response.reason}")
            if response.encoding is None:
                response.encoding = "utf-8"
            data = response.json()

            count = 0
            if self.skip_duplicates:
                filtered_data = self.filter_out_duplicates(data)
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
                self.logger.debug(f"Loaded page {page + 1} with {count:,} objects on it")
            else:
                load_next = False
        self.logger.info(
            f"Finished data extraction from {self.initial_url}; pages={self.pages_count:,}, objects={self.objects_count:,}")

    def page_to_objects(self, page_data) -> Iterable:
        pass

    def process_object(self, obj):
        self.on_object(obj)

    def get_object_id(self, obj) -> int:
        pass

    def get_login_url(self) -> furl:
        pass

    def filter_out_duplicates(self, data) -> Iterable:
        return [n for n in data if self.get_object_id(n) not in self.seen_objects]


class Drupal7DadaDownloader(DrupalDadaDownloader):
    """
    A refinement of the downloader class, applicable to the standard service REST APIs in Drupal. This module
    implementation provides only basic data on the index page. To get full data, this class uses the provided uri
    attribute for each individual object.
    """

    ids_sequence = ["cid", "tid", "vid", "nid"]

    def page_to_objects_list(self, page_data) -> Iterable:
        for obj_data in page_data:
            url = obj_data["uri"]
            response = self.get_url(url)
            if not response.ok:
                raise DrupalDownloadException(f"Failed to get the data for node from {url}: {response.reason}")
            yield response.json()

    def page_to_objects(self, page_data) -> Iterable:
        return self.page_to_objects_list(page_data)

    def get_login_url(self):
        res = self.initial_url.copy().set(path="user")
        if "_format" not in res.args:
            return res.add(dict(_format="json"))
        else:
            return res

    def get_object_id(self, obj) -> int:
        if self.id_name is None:
            for id_name in self.ids_sequence:
                if id_name in obj:
                    self.id_name = id_name
                    break
            if self.id_name is None:
                raise DrupalDownloadException("Unable to find an object id")
        return int(obj[self.id_name])


class Drupal8DadaDownloader(DrupalDadaDownloader):
    """
    A refinement of the downloader class, applicable to Drupal 8. In this version you must use the built in REST
    services, which will expose all the data on one page, without the need to refer to additional resources.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.id_name is None:
            raise DrupalDownloadException("id_name is mandatory for Drupal 8")

    def page_to_objects(self, page_data) -> Iterable:
        for obj in  page_data:
            yield self.simplify_object(obj)

    def simplify_object(self, obj: Dict) -> Dict:
        for key, val in list(obj.items()):
            if isinstance(val, list):
                if len(val) == 1:
                    val = val[0]
                    if isinstance(val, dict) and len(val) == 1:
                        val = next(iter(val.values()))
                    obj[key] = val
                elif len(val) == 0:
                    obj[key] = None
        return obj

    def get_login_url(self):
        res = self.initial_url.copy().set(path="user/login")
        if "_format" in res.args:
            del res.args["_format"]
        return res.add(dict(_format="json"))

    def get_object_id(self, obj) -> int:
        res = obj[self.id_name]
        if isinstance(res, list):
            res = res[0]["value"]
        return int(res)
