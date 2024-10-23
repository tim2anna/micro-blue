#!/usr/bin/python3
# -*- coding: utf-8 -*-


from setuptools import setup, find_packages


setup(
    name='micro-blue',
    version='0.2.4',
    description=(
        'micro-blue is an extension for Raspberry Pi that collects a lot of sensor drivers.'
    ),
    long_description_content_type="text/markdown",
    long_description=open('README.md').read(),
    author='Anna',
    author_email='',
    license='BSD License',
    packages=find_packages(),
    platforms=["all"],
    url='https://github.com/tim2anna/micro-blue',
    install_requires=[
        # 'gpiozero>=2.0.1',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)