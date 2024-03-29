from setuptools import setup, find_packages
import os

version = '1.0'

setup(name='redomino.wpimport',
      version=version,
      description="Import your Wordpress site in Plone.",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        ],
      keywords='',
      author='Giacomo Spettoli, Luca Cipriani',
      author_email='giacomo.spettoli@redomino.com',
      url='http://redomino.com',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['redomino'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'collective.transmogrifier',
          'plone.app.transmogrifier',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
