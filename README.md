# txCurrentCost

txCurrentCost is a Python Twisted package that lets you monitor your CurrentCost device. Use the txcurrentcost package to integrate non blocking access to CurrentCost devices into your Python Twisted application.

## Software Dependencies

### Python Dependencies

* Python
* pyserial
* Twisted

  - zope.interface

### Non-Python Dependencies
* Serial-to-USB driver. Typically the common way to communicate with CurrentCost devices on modern computers is through a serial to USB adaptor. Do a Google search for 'pl2303 driver' and your platform.

  Here is one [example](https://github.com/mpepping/osx-pl2303) that seems more up to date that the original [failberg](http://github.com/downloads/failberg/osx-pl2303) version I was running.

  Additionally, there is a kernel extension at http://xbsd.nl/2011/07/pl2303-serial-usb-on-osx-lion.html that can be installed by following the easy steps listed there. The kernel extension method worked fine for me, didn't even need to unplug the USB dongle. I just updated the /dev/cu.XXXXX port in the config file and started demo.


## Install

A number of methods are available to install this package.

* Using pip with PyPI as source:

```bash
$ [sudo] pip install txcurrentcost
```

* Using pip with github source:

```bash
$ [sudo] pip install git+git://github.com/claws/txCurrentCost.git
```

* Manually download and install the txCurrentCost archive. For other manual download options (zip, tarball) visit the github web page of [txCurrentCost](https://github.com/claws/txCurrentCost):

```bash
$ git clone git://github.com/claws/txCurrentCost.git
$ cd txCurrentCost
$ [sudo] python setup.py install
```

### Test Installation

```bash
$ python
>>> import txcurrentcost
>>>
```

## Example

A simple demonstration script exists in the examples directory of this repository showing how a developer would use the Monitor to obtain periodic and historic update message data from the CurrentCost device.

To run it you must first update update the 'port' setting in the examples/monitor.cfg file to point to the actual serial port your current cost device is connected to.

Then run the example script as follows (Ctrl+c will stop the script running):
```bash
$ cd examples
$ python demo.py --configfile=monitor.cfg
```

Example output:
```python
Periodic Update => timestamp=2012-01-10 09:55:59.997599temperature=21.7, sensor_type=Electricity, sensor_instance=0sensor_data=['00504']
Periodic Update => timestamp=2012-01-10 09:56:06.098980temperature=21.8, sensor_type=Electricity, sensor_instance=0sensor_data=['00508']
Periodic Update => timestamp=2012-01-10 09:56:12.202030temperature=21.8, sensor_type=Electricity, sensor_instance=0sensor_data=['00516']
```

History updates may be displayed if they are encountered while running the demo script. However, these are only sent at intervals of approximately 1 minute past every odd hour so this is unlikely.
