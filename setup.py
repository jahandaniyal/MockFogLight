import os
from setuptools import setup, find_packages
from agent import __version__

setup(
	name='MockFogLoadAgent',
	version = __version__,
	packages=find_packages(exclude=('docs', 'tests', 'env', 'index.py'))
)
