from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()


setup(name='drupal_download',
      version='0.0.1',
      description='Download data from Drupal using Python',
      long_description='This python 3 module will help you to extract data from a Drupal 7 or 8 web site. This data '
                       'can be later used for archiving or for migration to another CMS, such as Wagtail.',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet',
      ],
      keywords='drupal download data migration wagtail',
      url='https://github.com/zelenij/python-drupal-download',
      author="Andre Bar'yudin",
      author_email='andre.baryudin@gmail.com',
      license='MIT',
      packages=['drupal_download'],
      include_package_data=True,
      zip_safe=False)