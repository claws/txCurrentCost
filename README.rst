txCurrentCost
=============

txCurrentCost is a Python Twisted package that allows you to monitor your CurrentCost device. 
The serial communication with the CurrentCost device uses the Twisted networking framework.
Use it to integrate non blocking access to CurrentCost devices into your Python Twisted application.

**txCurrentCost is currently under development**

Software Dependencies
---------------------

* Python
* pyserial
* Twisted

  - zope.interface
  
* Serial-to-USB driver. Typically the common way to communicate with CurrentCost devices on
  modern computers is through a serial to USB adaptor. After trying a few without success I 
  found that this one worked: https://github.com/failberg/osx-pl2303.




Install
=======

1. Download txCurrentCost archive::

    $ git clone git://github.com/claws/txCurrentCost.git
    
For other download options (zip, tarball) visit the github web page of `txCurrentCost <https://github.com/claws/txCurrentCost>`_.

2. Install txCurrentCost module into your Python distribution::
  
    sudo python setup.py install
    
3. Test::

    $ python
    >>> import txCurrentCost
    >>>


Example
=======

A simple demonstration script exists in the examples directory of the repository. It contains
an example of how a developer would use the Monitor object to obtain periodic and history
update message data from the CurrentCost device.

To run it you must update update the 'port' setting in the examples/monitor.cfg file to point
to the actual serial port your current cost device is connected to.


Run it as follows (Ctrl+c will stop the script running)::

    $ cd examples
    $ python demo.py
    
Expected output::

    Periodic Update => timestamp=2012-01-10 09:55:59.997599, temperature=21.7, sensor_type=Electricity, sensor_instance=0, sensor_data=['00504']
    Periodic Update => timestamp=2012-01-10 09:56:06.098980, temperature=21.8, sensor_type=Electricity, sensor_instance=0, sensor_data=['00508']
    Periodic Update => timestamp=2012-01-10 09:56:12.202030, temperature=21.8, sensor_type=Electricity, sensor_instance=0, sensor_data=['00516']

History updates will be displayed also if they are encountered while running the demo script, however these are only sent at about 1 minute
past the hour. 


        
Todo
====

* N/A


