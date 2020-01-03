# Python Drupal download module

This python 3 module will help you to extract data from a Drupal 7 or 8 web site.  This data can be later used for 
archiving or for migration to another CMS, such as Wagtail.

## Motivation

[Drupal](https://www.drupal.org/) is an open source CMS, written in PHP.  It has a long history and many followers. A 
large number of web sites
run on Drupal and there is a substantial development community.  The product is extendable, there are plenty of useful
modules available to enhance functionality of Drupal web sites.

Over the years there has been a number of major releases of Drupal. At the time of writing the most recent is Drupal 8.
In the past migration from one major version to another was done in-place.  However, in order to move from an earlier 
version to 8, the user must follow a process of migration, involving creating a basic deployment of Drupal 8 first and
then using additional tools to copy the data from the old web site to the new.  While this should work in theory, the
reality seems a bit different.

I own a few very straightforward Drupal 7 web sites. They use a number of modules from the standard repository, but no
custom code.  The vast majority of the content are simple stories.  Nonetheless, the migration was rather ugly - a lot
of content didn't make it over.  What did, looked rather puny and definitely didn't match the look and feel of my old 
web sites.  Blocks were missing.  In short, the result needed a lot of extra work to make it right.

I decided to revert to the old Drupal 7 deployment, which was, admittedly, easy, thanks to the fact that the migration
did involve a fresh instance of Drupal.  This was the short term fix.  Given the effort of migration, I decided to move
all my web sites to [Django](https://www.djangoproject.com/) + [Wagtail](https://wagtail.io/), which would give me much 
more freedom in managing my data and, hopefully, will 
prove a good long term solution.  To be fair, Drupal has lasted me more than 10 years, so it wasn't a bad journey 
overall.  But I do hate to code in PHP, so getting rid of it for good fills my heart with joy.

To achieve this move from Drupal to Django I need to extract the data from the former in some readable format.  Luckily,
there are simple export facilities built into the CMS.  This Python package uses them in order to download the data.
There is a generic API to handle each downloaded object, such as node, comment, vocabulary term etc, or to simply dump
everything as JSON into files.  The task of shaping this extracted data into something suitable for Django or any other
target you might have in mind is entirely yours.

## Usage

### Python support

Only Python 3 is supported at the moment.  Let Python 2 die in quiet dignity!

### Drupal support

Currently Drupal 7 and 8 are supported.  In theory this module could work with previous versions of Drupal and it might
work with some future ones as well.  Your mileage can vary.

### Installation

This package is available on PyPi. Simply use pip to install (assuming you are running in a Python 3 virtual environment):

        pip install drupal_download

### On a Drupal web site

First, you must enable a JSON-based REST API in Drupal. Follow the correct link for your version of Drupal:

* Drupal 7 - https://www.drupal.org/project/services
* Drupal 8 - https://www.drupal.org/docs/8/api/restful-web-services-api/restful-web-services-api-overview

Enable the relevant services and take node of the APIs endpoints. Make sure you configure the desired authentication 
controls. At the moment, the model supports these methods:

* Anonymous - no authentication is needed. This also means that anyone can access you endpoint and download the data
* HTTP Basic - the standard basic authentication
* Session - cookie-driven authentication, the same in fact, that you use when accessing a Drupal site interactively

*NB:* I very strongly recommend using HTTPS for all these communications. If you don't have an SSL certificate yet and
can't afford one, get one for free from [Letsencrypt](https://letsencrypt.org/).

### In a script

You can use the API from this module directly, in this manner:

        def data_callback(obj):
            # process the data

        dl = DrupalDadaDownloader("https://www.example.com/export/node.json", "john", "123", AuthType.CookieSession, data_callback)
        dl.load_data()

### From the command line

Alternatively, there is a simple command line tool shipped with this module.  You can invoke it like this:

        python3 -m download_drupal --help
        
This will display some help information.  Calling it like this:

        python3 -m download_drupal -b https://www.example.com/export/$i.json --username jane --password secret --auth-type CookieSession -o example_node.json --drupal-version 7
        
