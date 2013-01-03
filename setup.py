#!/usr/bin/env python

"""
A distutils installation script for txcurrentcost.
"""

from distutils.core import setup
import txcurrentcost


long_description = """txcurrentcost is a Python Twisted package that allows you to monitor your CurrentCost device. 
The serial communication with the CurrentCost device uses the Twisted networking framework.
Use txcurrentcost to integrate non blocking access to CurrentCost devices into your Python Twisted application."""


setup(name='txcurrentcost',
      version='.'.join([str(x) for x in txcurrentcost.version]),
      description='txcurrentcost is a Python Twisted package that allows you to monitor your CurrentCost device.',
      long_description=long_description,
      author='Chris Laws',
      author_email='clawsicus@gmail.com',
      license='http://www.opensource.org/licenses/mit-license.php',
      url='https://github.com/claws/txCurrentCost',
      download_url='https://github.com/claws/txCurrentCost/tarball/master',
      packages=['txcurrentcost'],
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'Intended Audience :: End Users/Desktop',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Framework :: Twisted',
                   'Topic :: Communications',
                   'Topic :: Home Automation',
                   'Topic :: System :: Monitoring',
                   'Topic :: Software Development :: Libraries :: Python Modules'],
      requires=['pyserial', 'Twisted']
      )




