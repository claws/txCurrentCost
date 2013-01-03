#!/usr/bin/env python
#
'''
This script implements a demonstration Current Cost monitor.

Modify the monitor.cfg file to define the correct port
for the monitor to use then run the demo script using:

$ python demo.py --configfile=monitor.cfg 
'''

from twisted.internet import reactor
from twisted.python import log
import logging
try:
    import txcurrentcost
    from txcurrentcost.monitor import MonitorOptions, MonitorConfig, Monitor
except ImportError:
    print "Unable to import txcurrentcost. Install the package or make is visible using PYTHONPATH"
    import sys
    sys.exit(1)



class DemoMonitor(Monitor):
    """
    Extends the txcurrentcost.monitor.Monitor by implementing periodic 
    and history update handlers to simply display the data received 
    from the current cost monitor. 
    """
    
    def periodicUpdateReceived(self, timestamp, temperature, sensor_type, sensor_instance, sensor_data):
        """ 
        Called upon receiving a periodic update message. 
        """
        print "Periodic Update => timestamp=%s, temperature=%s, sensor_type=%s, sensor_instance=%s, sensor_data=%s" % (timestamp,
                                                                                                                       temperature, 
                                                                                                                       txcurrentcost.Sensors.nameForType(sensor_type), 
                                                                                                                       sensor_instance, 
                                                                                                                       sensor_data)

    def historyUpdateReceived(self, sensor_type, sensorHistoryData):
        """
        Called upon receiving a history update message after the completion of
        a history update message cycle. 
        """
        print "History Update => sensor_type=%s" % (txcurrentcost.Sensors.nameForType(sensor_type))
        for sensor_id, sensorHistoricalData in sensorHistoryData.items():
            print "History for sensor id: %s" % sensor_id
            print sensorHistoricalData
            
            
            
if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s [%(funcName)s] %(message)s")

    # Send Twisted log messages to logging logger
    _observer = log.PythonLoggingObserver()
    _observer.start()

    o = MonitorOptions()
    try:
        o.parseOptions()
    except usage.UsageError, errortext:
        print "%s: %s" % (sys.argv[0], errortext)
        print "%s: Try --help for usage details." % (sys.argv[0])
        raise SystemExit, 1

 
    config = MonitorConfig(o.opts['configfile'])
    monitor = DemoMonitor(config)
    reactor.callWhenRunning(monitor.start)
    reactor.run()
