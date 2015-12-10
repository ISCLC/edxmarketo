import os
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='edxmarketo',
    version='0.2',
    packages=find_packages(),
    include_package_data=True,
    license='BSD License',  # example license
    description='A Django app to communicate events from edX to Marketo',
    long_description=README,
    url='http://www.appsembler.com/',
    author='Bryan Wilson, Appsembler',
    author_email='bryan@appsembler.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',  # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        # Replace these appropriately if you are stuck on Python 2.
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=[
        'pythonmarketo',
        'mock_django == 0.6.9'
    ],
)
