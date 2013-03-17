# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(
    name='mp3hash',
    version='0.0.1',
    description='Music file hasher',
    author='Javier Santacruz',
    author_email='javier.santacruz.lc@gmail.com',
    url='http://github.com/jvrsantacruz/mp3hash',
    packages=find_packages(),
    install_requires=[],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    platforms=['Any'],
    scripts=['scripts/mp3hash'],
)
