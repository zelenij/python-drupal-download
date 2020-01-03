import json
import sys

import datetime as dt
import configargparse
import logging

import dateutil.parser as dp
from furl import furl

from drupal_download.downloader import AuthType, DrupalDownloadException, DrupalDadaDownloader, Drupal7DadaDownloader


def download_main():
    logging.getLogger('urllib3').setLevel(logging.INFO)
    logging.getLogger('requests').setLevel(logging.INFO)
    log = logging.getLogger('')
    log.setLevel(logging.DEBUG)
    format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)-4s - %(message)s")
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(format)
    log.addHandler(ch)

    data = list()

    def collector(obj):
        nonlocal data
        data.append(obj)

    parser = configargparse.ArgumentParser(description='Drupal download dump utility. Download data from a Drupal site'
                                                       ' and write it to a json file')
    parser.add_argument('-c', '--config', required=False, is_config_file=True, help='config file path')
    parser.add_argument('-b', '--base-url',
                        help='Base url for the Drupal site')
    parser.add_argument('--auth-type', choices=[x.name for x in AuthType],
                        help='The authentication type')
    parser.add_argument('--username', required=False,
                        help='The user name')
    parser.add_argument('--password', required=False,
                        help='Password')
    parser.add_argument('-o', '--output',
                        help='Output file')
    parser.add_argument('--drupal-version', choices=[7, 8], type=int,
                        help='Drupal version')
    parser.add_argument('--page-size', type=int,
                        help='Page size')

    args = parser.parse_args()
    auth_type = [x for x in AuthType if x.name == args.auth_type][0]
    if auth_type != AuthType.Anonymous:
        if args.username is None or args.password is None:
            raise DrupalDownloadException(f"Username and password required for auth type {auth_type}")

    if args.drupal_version == 7:
        downloader = Drupal7DadaDownloader
    elif args.drupal_version == 8:
        downloader = DrupalDadaDownloader
    else:
        raise DrupalDownloadException(f"Unsupported Drupal version {args.drupal_version}")
    dl = downloader(args.base_url, args.username, args.password, auth_type, collector, page_size=args.page_size)
    dl.load_data()

    with open(args.output, 'w') as fs:
        json.dump(data, fs, indent=4)
