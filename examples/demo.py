#!/usr/bin/env python
#
# Run using:
# $python demo.py 
#

from twisted.internet import reactor
try:
    import txCurrentCost
except ImportError:
    # cater for situation where txCurrentCost is not installed into Python distribution
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import txCurrentCost
from txCurrentCost.monitor import MonitorConfig, Monitor





class BasicMonitor(Monitor):
    """
    Extends the txCurrentCost.monitor.Monitor by implementing periodic and history update
    handlers to simply displays the data received from the current cost monitor. 
    """
    
    def periodicUpdateReceived(self, timestamp, temperature, sensor_type, sensor_instance, sensor_data):
        """ 
        Called to notify receipt of a periodic update message after parsing important 
        information from the message xml. 
        
        @param timestamp: A computer generated utc timestamp generated on receipt of message
        @type timestamp: datetime.datetime
        @param temperature: The temperature reported by the display unit
        @type temperature: string
        @param sensor_type: The sensor type that triggered the periodic message
        @type sensor_type:
        @param sensor_instance: The sensor instance that triggered the periodic message
        @type sensor_instance: 
        @param sensor_data: sensor specific periodic data. This can vary depending on the 
                            sensor type and instance.
        
        Implement this method to handle data in the way you want. For example you may
        want to update it to Pachube. Perhaps you want to store it for a while, average
        it and then post it to Pachube. Whatever!
        """
        print "Periodic Update => timestamp=%s, temperature=%s, sensor_type=%s, sensor_instance=%s, sensor_data=%s" % (timestamp,
                                                                                                                       temperature, 
                                                                                                                       txCurrentCost.Sensors.nameForType(sensor_type), 
                                                                                                                       sensor_instance, 
                                                                                                                       sensor_data)
        
        
    def historyUpdateReceived(self, sensor_type, sensorHistoryData):
        """
        Called to notify receipt of a history update message after the completion of
        a history update message cycle. 
        
        @param sensor_type: The sensor that reported the history update
        @type sensor_type: A Sensors.Types item
        @param sensorHistoryData: A dict keyed by sensor identifier with values of
                                  HistoricalSensorData objects.
        @type sensorHistoryData: dict
        
        Implement this method to handle data in the way you want. For example you may
        want to store it to a database. Whatever!
        """
        print "History Update => sensor_type=%s" % (txCurrentCost.Sensors.nameForType(sensor_type))
        for sensor_id, sensorHistoricalData in sensorHistoryData.items():
            print "History for sensor id: %s" % sensor_id
            print sensorHistoricalData
            
            
            
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)

    monitorConfig = MonitorConfig('monitor.cfg')
    monitor = BasicMonitor(monitorConfig)
    reactor.callWhenRunning(monitor.start)
    reactor.run()
