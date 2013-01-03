txCurrentCost
=============

txCurrentCost is a Python Twisted package that allows you to monitor your CurrentCost device. 
The serial communication with the CurrentCost device uses the Twisted networking framework.
Use it to integrate non blocking access to CurrentCost devices into your Python Twisted application.


Software Dependencies
---------------------

* Python
* pyserial
* Twisted

  - zope.interface
  
* Serial-to-USB driver. Typically the common way to communicate with CurrentCost devices on
  modern computers is through a serial to USB adaptor. Do a Google search for 'pl2303 driver' and your platform.

  One example is: https://github.com/mpepping/osx-pl2303
  
  Additionally, there is a kernel extension at: http://xbsd.nl/2011/07/pl2303-serial-usb-on-osx-lion.html
  Installing the kext file can be done in a few easy steps:

      Download and extract
      $ cd /path/to/osx-pl2303.kext
      $ sudo cp -R osx-pl2303.kext /System/Library/Extensions/
      Next you need to fix permissions and execute bits:
      $ cd /System/Library/Extensions
      $ sudo chmod -R 755 osx-pl2303.kext
      $ sudo chown -R root:wheel osx-pl2303.kext
      $ cd /System/Library/Extensions
      $ sudo kextload ./osx-pl2303.kext
      $ sudo kextcache -system-cache
  
  The kernel extension worked fine for me, didn't even need to unplug the USB dongle. Just updated the /dev/cu.  XXXXX port in the config file and started demo.


Install
=======

A number of methods are available to install this package::

* Using pip with PyPI as source::

  $ [sudo] pip install txcurrentcost

* Using pip with github source::

  $ [sudo] pip install git+git://github.com/claws/txCurrentCost.git

* Manually download and install the txCurrentCost archive::

  $ git clone git://github.com/claws/txCurrentCost.git
    
  For other download options (zip, tarball) visit the github web page of `txCurrentCost <https://github.com/claws/txCurrentCost>`_.

  $ cd txCurrentCost
  $ [sudo] python setup.py install
    
Test
====

    $ python
    >>> import txcurrentcost
    >>>


Example
=======

A simple demonstration script exists in the examples directory of the repository. It contains
an example of how a developer would use the Monitor object to obtain periodic and historic
update message data from the CurrentCost device.

To run it you must update update the 'port' setting in the examples/monitor.cfg file to point
to the actual serial port your current cost device is connected to.


Run it as follows (Ctrl+c will stop the script running)::

    $ cd examples
    $ python demo.py --configfile=monitor.cfg
    
Expected output::

    Periodic Update => timestamp=2012-01-10 09:55:59.997599, temperature=21.7, sensor_type=Electricity, sensor_instance=0, sensor_data=['00504']
    Periodic Update => timestamp=2012-01-10 09:56:06.098980, temperature=21.8, sensor_type=Electricity, sensor_instance=0, sensor_data=['00508']
    Periodic Update => timestamp=2012-01-10 09:56:12.202030, temperature=21.8, sensor_type=Electricity, sensor_instance=0, sensor_data=['00516']

History updates may be displayed if they are encountered while running the demo script. 
However these are only sent at about 1 minute past every odd hour. 


        
Todo
====

* N/A


