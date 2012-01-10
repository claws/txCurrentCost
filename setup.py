#!/usr/bin/env python

"""
A distutils installation script for txCurrentCost.
"""

from distutils.core import setup
import txCurrentCost


long_description = """txCurrentCost is a Python Twisted package that allows you to monitor your CurrentCost device. 
The serial communication with the CurrentCost device uses the Twisted networking framework.
Use txCurrentCost to integrate non blocking access to CurrentCost devices into your Python Twisted application."""


setup(name='txCurrentCost',
      version='.'.join(txCurrentCost.version),
      description='txCurrentCost is a Python Twisted package that allows you to monitor your CurrentCost device.',
      long_description=long_description,
      author='Chris Laws',
      author_email='clawsicus@gmail.com',
      license='http://www.opensource.org/licenses/mit-license.php',
      url='https://github.com/claws/txPachube',
      download_url='https://github.com/claws/txCurrentCost/tarball/master',
      packages=['txCurrentCost'],
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'Intended Audience :: End Users/Desktop',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Framework :: Twisted']
      )




