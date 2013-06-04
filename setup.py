"""
Django Fixie setup.
"""

from setuptools import setup, find_packages

setup( name='django-fixie',
       version='0.1',
       description='Django app for manipulating fixtures.',
       author='Brantley Harris',
       author_email='brantley.harris@gmail.com',
       packages = find_packages(),
       include_package_data = False,
       zip_safe = True
      )
