import setuptools


def readme():
    with open('README.rst') as f:
        return f.read()


setuptools.setup(name='drupal_download',
                 version='0.0.9',
                 description='Download data from Drupal using Python',
                 long_description=readme(),
                 classifiers=[
                     'Development Status :: 3 - Alpha',
                     'License :: OSI Approved :: MIT License',
                     'Programming Language :: Python :: 3',
                     'Topic :: Internet',
                 ],
                 keywords='drupal download data migration wagtail',
                 url='https://github.com/zelenij/python-drupal-download',
                 author="Andre Bar'yudin",
                 author_email='andre.baryudin@gmail.com',
                 license='MIT',
                 packages=setuptools.find_packages(),
                 include_package_data=True,
                 python_requires='>=3.6',
                 install_requires=["requests", "python-dateutil", "furl", "configargparse"],
                 tests_require=['requests_mock', 'pytest'],
                 zip_safe=False)
