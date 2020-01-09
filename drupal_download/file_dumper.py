import json
import sys
import io

import datetime as dt
import configargparse
import logging

import dateutil.parser as dp
from furl import furl

from drupal_download.downloader import AuthType, DrupalDownloadException, Drupal7DadaDownloader, Drupal8DadaDownloader


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
    parser.add_argument('--id-name', required=False,
                        help='ID name of the data being downloaded. For node it will be nid, for comment cid etc.')

    args = parser.parse_args()
    auth_type = [x for x in AuthType if x.name == args.auth_type][0]
    if auth_type != AuthType.Anonymous:
        if args.username is None or args.password is None:
            raise DrupalDownloadException(f"Username and password required for auth type {auth_type}")

    if args.drupal_version == 7:
        downloader = Drupal7DadaDownloader
    elif args.drupal_version == 8:
        downloader = Drupal8DadaDownloader
    else:
        raise DrupalDownloadException(f"Unsupported Drupal version {args.drupal_version}")
    dl = downloader(args.base_url,
                    args.username,
                    args.password,
                    auth_type,
                    collector,
                    page_size=args.page_size,
                    id_name=args.id_name)
    dl.load_data()

    with io.open(args.output, 'w', encoding='utf-8') as fs:
        json.dump(data, fs, ensure_ascii=False, indent=4)
