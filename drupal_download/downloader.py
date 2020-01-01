#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from builtins import Exception
from enum import Enum, auto

from typing import Iterable, Callable

import requests
from requests.auth import HTTPBasicAuth

from furl import furl


class DrupalDownloadException(Exception):
    pass


class AuthType(Enum):
    HTTPBasic = auto()
    CookieSession = auto()


class DrupalDadaDownloader(object):
    def __init__(self,
                 base_url: str,
                 username: str,
                 password: str,
                 auth_type: AuthType,
                 on_node: Callable,
                 page_size = 10):
        super().__init__()
        self.initial_url: furl = furl(base_url)
        self.username = username
        self.password = password
        self.auth_type = auth_type
        self.on_node = on_node
        self.page_size = page_size

        self.nodes_count = 0
        self.pages_count = 0
        self.logged_in = False
        self.session = requests.Session()
        self.auth = None

    def get_url(self, url: str) -> requests.Response:
        if self.auth_type == AuthType.HTTPBasic:
            if self.auth is None:
                self.auth = HTTPBasicAuth(self.username, self.password)
            return self.session.get(url, auth=self.auth)
        elif self.auth_type == AuthType.CookieSession:
            if not self.logged_in:
                login = dict()
                login['name'] = self.username
                login['pass'] = self.password
                url = self.initial_url.set(path="user").add(dict(_format="json"))
                response = self.session.post(url.url, data=json.dumps(login))
                if not response.ok:
                    raise DrupalDownloadException(f"Failed to login: {response.reason}")
                self.logged_in = True
            return self.session.get(url)
        else:
            raise DrupalDownloadException(f"Unsupported authentication type {self.auth_type}")

    def load_data(self):
        self.nodes_count = 0
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
            for node in self.page_to_nodes(data):
                count += 1
                self.nodes_count += 1
                self.process_node(node)

            if len(data) > 0:
                self.pages_count += 1
            else:
                load_next = False

    def page_to_nodes(self, page_data) -> Iterable:
        return page_data

    def process_node(self, node):
        self.on_node(node)


class Drupal7DadaDownloader(DrupalDadaDownloader):
    def page_to_nodes(self, page_data) -> Iterable:
        for node_data in page_data:
            node = self.get_url(node_data["uri"])
            yield node
