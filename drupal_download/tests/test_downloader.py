import json

import pytest
import requests
import requests_mock

from drupal_download.downloader import DrupalDadaDownloader, AuthType


class TestDownloader:
    website = "https://www.example.com"
    base_url = website + "/export"

    def test_authentication_anonymous(self):
        with requests_mock.Mocker() as mock:
            mock.get(self.base_url, text='[]')
            dl = DrupalDadaDownloader(self.base_url, None, None, AuthType.Anonymous, lambda x: x)
            dl.load_data()
            assert dl.pages_count == 0
            assert dl.objects_count == 0

    def test_authentication_session(self):
        with requests_mock.Mocker() as mock:
            mock.get(self.base_url, text='[]')
            mock.post(self.website + "/user?_format=json", text='')

            dl = DrupalDadaDownloader(self.base_url, "john", "123", AuthType.CookieSession, lambda x: x)
            dl.load_data()
            assert dl.pages_count == 0
            assert dl.objects_count == 0

    def test_authentication_basic(self):
        with requests_mock.Mocker() as mock:
            mock.get(self.base_url, text='[]')

            dl = DrupalDadaDownloader(self.base_url, "john", "123", AuthType.HTTPBasic, lambda x: x)
            dl.load_data()
            assert dl.pages_count == 0
            assert dl.objects_count == 0

    def test_download(self):
        data = [dict(nid=i, uri=self.base_url + f"?node={i}") for i in range(20)]
        with requests_mock.Mocker() as mock:
            mock.register_uri('GET', url=self.base_url, text=json.dumps(data), complete_qs=True)
            mock.register_uri('GET', url=self.base_url + "?page=1", text="[]", complete_qs=True)
            mock.post(self.website + "/user?_format=json", text='')
            dls = [DrupalDadaDownloader(self.base_url, "john", "123", AuthType.CookieSession, lambda x: x),
                   DrupalDadaDownloader(self.base_url, None, None, AuthType.Anonymous, lambda x: x)]
            for dl in dls:
                dl.load_data()
                assert dl.pages_count == 1
                assert dl.objects_count == 20
