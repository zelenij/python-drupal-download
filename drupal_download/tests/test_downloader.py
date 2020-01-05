import json
from typing import Dict

import pytest
import requests
import requests_mock

from drupal_download.downloader import AuthType, DrupalDownloadException, Drupal7DadaDownloader, Drupal8DadaDownloader


class TestDownloader:
    website = "https://www.example.com"
    base_url = website + "/export"

    def test_authentication_anonymous(self):
        with requests_mock.Mocker() as mock:
            mock.get(self.base_url, text='[]')
            dl = Drupal7DadaDownloader(self.base_url, None, None, AuthType.Anonymous, lambda x: x)
            dl.load_data()
            assert dl.pages_count == 0
            assert dl.objects_count == 0

    def test_authentication_session(self):
        with requests_mock.Mocker() as mock:
            mock.get(self.base_url, text='[]')
            mock.post(self.website + "/user?_format=json", text='')

            dl = Drupal7DadaDownloader(self.base_url, "john", "123", AuthType.CookieSession, lambda x: x)
            dl.load_data()
            assert dl.pages_count == 0
            assert dl.objects_count == 0

    def test_authentication_session_fails(self):
        with requests_mock.Mocker() as mock:
            mock.post(self.website + "/user?_format=json", text='', status_code=403)

            dl = Drupal7DadaDownloader(self.base_url, "john", "123", AuthType.CookieSession, lambda x: x)
            with pytest.raises(DrupalDownloadException):
                dl.load_data()

    def test_authentication_basic(self):
        with requests_mock.Mocker() as mock:
            mock.get(self.base_url, text='[]')

            dl = Drupal7DadaDownloader(self.base_url, "john", "123", AuthType.HTTPBasic, lambda x: x)
            dl.load_data()
            assert dl.pages_count == 0
            assert dl.objects_count == 0

    def validate_object_id(self, data: Dict, expected: int):
        dl = Drupal7DadaDownloader(self.base_url, None, None, AuthType.Anonymous, None)
        assert dl.get_object_id(data) == expected

    def test_get_object_id(self):
        self.validate_object_id(dict(cid="2", nid="30"), 2)
        self.validate_object_id(dict(tid="2", nid="30"), 2)
        self.validate_object_id(dict(vid="2", nid="30"), 2)
        self.validate_object_id(dict(xxtid="2", nid="30"), 30)

    def test_get_object_id_captures_id_name(self):
        dl = Drupal7DadaDownloader(self.base_url, None, None, AuthType.Anonymous, None)
        data = dict(cid="2", nid="30")
        assert dl.get_object_id(data) == 2
        assert dl.get_object_id(dict(cid=70)) == 70

    def test_get_object_id_drupal8(self):
        dl = Drupal8DadaDownloader(self.base_url, None, None, AuthType.Anonymous, None, id_name="nid")
        data = dict(cid="2", nid=[{"value": "30"}])
        assert dl.get_object_id(data) == 30

    def test_download(self):
        count = 0

        def incr(x):
            nonlocal count
            count += 1

        data = [dict(nid=i, uri=self.base_url + f"?node={i}") for i in range(20)]
        with requests_mock.Mocker() as mock:
            mock.register_uri('GET', url=self.base_url, text=json.dumps(data), complete_qs=True)
            mock.register_uri('GET', url=self.base_url + "?page=1", text="[]", complete_qs=True)
            mock.post(self.website + "/user?_format=json", text='')

            dls = [Drupal8DadaDownloader(self.base_url, None, None, AuthType.Anonymous, incr, id_name="nid")]
            for dl in dls:
                count = 0
                dl.load_data()
                assert dl.pages_count == 1
                assert dl.objects_count == 20
                assert count == 20

    def test_download_drupal7(self):
        count = 0

        def incr(x):
            nonlocal count
            count += 1

        data = [dict(nid=i, uri=self.base_url + f"?node={i}") for i in range(20)]
        with requests_mock.Mocker() as mock:
            mock.register_uri('GET', url=self.base_url, text=json.dumps(data), complete_qs=True)
            mock.register_uri('GET', url=self.base_url + "?page=1", text="[]", complete_qs=True)
            for node in data:
                mock.register_uri('GET', url=self.base_url + "?node=" + str(node["nid"]),
                                  text=json.dumps(node), complete_qs=True)
            mock.post(self.website + "/user?_format=json", text='')
            mock.post(self.website + "/user/login?_format=json", text='')

            dls = [Drupal8DadaDownloader(self.base_url, "john", "123", AuthType.CookieSession, incr, id_name="nid"),
                   Drupal7DadaDownloader(self.base_url, None, None, AuthType.Anonymous, incr)]
            for dl in dls:
                count = 0
                dl.load_data()
                assert dl.pages_count == 1
                assert dl.objects_count == 20
                assert count == 20
