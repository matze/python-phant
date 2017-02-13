from setuptools import setup, find_packages
from os import path

# Read version
from phant.version import __version__

here = path.abspath(path.dirname(__file__))


setup(
    name='phant',
    version=__version__,
    author='Matthias Vogelgesang <matthias.vogelgesang@gmail.com>, Pablo Manuel Garcia Corzo <pablo.garcia.corzo@gmail.com>',
    description='Client library for Sparkfun\'s Phant',
    author_email='matthias.vogelgesang@gmail.com',
    url='http://github.com/matze/python-phant',
    packages=['phant', 'phant.encoders'],
    install_requires=['requests'],
    test_suite="tests",
)
