from setuptools import setup

setup(
    name='phant',
    version='0.4',
    author='Matthias Vogelgesang',
    description='Client library for Sparkfun\'s Phant',
    author_email='matthias.vogelgesang@gmail.com',
    url='http://github.com/matze/python-phant',
    py_modules=['phant'],
    install_requires=['requests'],
)
