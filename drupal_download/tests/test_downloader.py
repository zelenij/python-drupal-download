import pytest
import requests
import requests_mock

from drupal_download.downloader import DrupalDadaDownloader, AuthType


class TestDownloader:
    base_url = "https://www.example.com/export"

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
            mock.post("https://www.example.com/user?_format=json", text='')

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