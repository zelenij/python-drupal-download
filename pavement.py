"""paver config file"""

from paver.easy import sh
from paver.tasks import task, needs


@task
def pytest():
    """unit testing"""
    sh('pytest')

@task
def pylint():
    """pyltin"""
    sh('pylint ./drupal_download/')

@task
def pypi():
    """Instalation on PyPi"""
    sh('python setup.py sdist')
    sh('twine upload dist/*')

@task
def local():
    """local install"""
    sh("pip uninstall drupal_download")
    sh("python setup.py install develop")


@task
def sphinx():
    """Document creation using Shinx"""
    sh('cd docs; make html; cd ..')

@needs('pytest', 'pylint', 'sphinx')
@task
def default():
    """default"""
    pass
