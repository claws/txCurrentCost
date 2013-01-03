#!/usr/bin/env python

'''
This module implements the Current Cost monitor class.
'''

import datetime
import logging
import os
import sys
import ConfigParser
import txcurrentcost
from twisted.internet import reactor
from twisted.python import usage



class MonitorOptions(usage.Options):
    optParameters = [['configfile', 'c', None, 'Configuration file path']]


class MonitorConfig(object):
    """
    Current Cost Monitor Configuration
    """
    
    # configuration sections
    CURRENT_COST_SECTION = "current_cost"
    SECTIONS = [CURRENT_COST_SECTION]
    
    # configuration fields
    PORT = "port"
    BAUDRATE = "baudrate"
    CLAMP_COUNT = "clamp_count"
    USE_UTC_TIMESTAMPS = "use_utc_timestamps"

    FIELDS = [PORT,
              BAUDRATE,
              CLAMP_COUNT,
              USE_UTC_TIMESTAMPS]

    
    def __init__(self, config_file):
        if not os.path.exists(config_file):
            raise Exception("Invalid configuration file path: %s" % config_file)
        self.config_file = config_file
        
        # attribute populated after config file parsing
        self.port = None
        self.baudrate = None
        self.clamp_count = None

        self.parse(config_file)

        
    def parse(self, config_file):
        parser = ConfigParser.SafeConfigParser()
        parser.read(config_file)
        
        self.port = parser.get(MonitorConfig.CURRENT_COST_SECTION, MonitorConfig.PORT)
        self.baudrate = parser.getint(MonitorConfig.CURRENT_COST_SECTION, MonitorConfig.BAUDRATE)
        self.clamp_count = parser.getint(MonitorConfig.CURRENT_COST_SECTION, MonitorConfig.CLAMP_COUNT)
        self.use_utc_timestamps = parser.getboolean(MonitorConfig.CURRENT_COST_SECTION, MonitorConfig.USE_UTC_TIMESTAMPS)



  

class Monitor(object):
    """ 
    Monitor a current cost device.
    
    The monitor expects a MonitorConfig object passed to it as the config
    argument but any object providing the port, baudrate, clamp_count and 
    use_utc_timestamps attributes will suffice.
    """
    
    def __init__(self, config):
        """
        @param config: A MonitorConfig instance holding configuration settings
        @type config: a MonitorConfig instance
        """ 
        self.config = config
        self.serialPort = None
        self.protocol = None
        
        self.source = None
        self.days_since_birth = None
        self.days_since_wiped = None
        
        self.historicSensorData = {}
        self.historicDataMessageTimeout = 20.0  # seconds
        self.historicalDataUpdateCompleteForSensorType = {}
        
        
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
        want to send an update to Cosm. Perhaps you want to store it for a while, average
        it and then post it to Cosm. Whatever! 
        """
        pass
        
        
    def historyUpdateReceived(self, sensor_type, sensorHistoryData):
        """
        Called to notify receipt of a history update message after the completion of
        a history update message cycle and parsing important information from the 
        message xml. 
        
        @param sensor_type: The sensor that reported the history update
        @type sensor_type: A Sensors.Types item
        @param sensorHistoryData: A dict keyed by sensor identifier with values of
                                  HistoricalSensorData objects.
        @type sensorHistoryData: dict

        Implement this method to handle data in the way you want. For example you may
        want to store it to a database. Whatever!
        """
        pass
        
                
    def start(self):
        """
        Start the CurrenCost monitor
        """
        logging.info('CurrentCostMonitor starting')
        logging.info('Attempting to open port %s at %dbps' % (self.config.port, self.config.baudrate))
        self.protocol = txcurrentcost.CurrentCostDataProtocol(self._messageHandler)
        self.serialPort = txcurrentcost.FixedSerialPort(self.protocol, 
                                                        self.config.port, 
                                                        reactor,
                                                        baudrate=self.config.baudrate)
       

    def stop(self):
        """
        Stop the CurrenCost monitor
        """
        logging.info('CurrentCostMonitor stopping')
        if self.protocol and self.protocol.transport:
            self.protocol.transport.loseConnection()
        self.serialPort.close()


    def _messageHandler(self, kind, message):
        """ 
        Handle a CurrentCost message from the protocol and dispatch it to
        the appropriate handler. This method get passed to the protocol 
        during its construction so that it can pass messages back to the
        monitor. 
        
        @param kind: The kind of message received
        @type kind: string
        @param message: An XML message string
        @type message: string
        """
        if kind not in txcurrentcost.MessageKinds:
            logging.error("Invalid message kind \'%s\' not in kinds: %s" % txcurrentcost.MessageKinds)
            return
        
        if kind == txcurrentcost.PeriodicUpdateMsg:
            self._parsePeriodicUpdate(message)
            
        elif kind == txcurrentcost.HistoryUpdateMsg:
            self._parseHistoryUpdate(message)

        
        
    def _parsePeriodicUpdate(self, msg):
        """
        Parse a periodic update message for important information and
        pass to the user implemented handlePeriodicUpdate method.
        """
        logging.debug("Parsing a periodic update message")
        try:
            self.source = msg.findtext("src")
            self.days_since_birth = msg.findtext("dsb")
            # Ignore the unit timestamp in preference for a
            # computer generated timestamp that can more
            # easily be used when updating data points at
            # sites like Cosm.
            #timestamp = msg.findtext("time")
            if self.config.use_utc_timestamps:
                timestamp = datetime.datetime.utcnow()
            else:
                timestamp = datetime.datetime.now()
            
            temperature = msg.findtext("tmpr")
            
            sensor_instance = int(msg.findtext("sensor"))
            identifier = msg.findtext("id")
            sensor_type = int(msg.findtext("type"))

            if sensor_type == txcurrentcost.Sensors.ElectricitySensor:
                
                # channel indexes start from 1, not zero.
                if sensor_instance == txcurrentcost.Sensors.WholeHouseSensorId:
                    # The whole house sensor supports multiple channels.
                    channels = range(1, self.config.clamp_count+1)
                else:
                    # All other sensors only support 1 channel
                    channels = range(1, 2)
                    
                watts_on_channel = []
                for channel_number in channels:
                    channel = msg.find("ch%i" % channel_number)
                    if channel is not None:
                        watts = channel.findtext("watts")
                        watts_on_channel.append(watts)
                sensor_data = watts_on_channel
                    
            elif sensor_type == txcurrentcost.Sensors.OptiSmartSensor:
                imp = msg.findtext("imp")
                imu = msg.findtext("ipu")
                sensor_data = (imp, imu)

            else:
                logging.warning("Don't know how to handle sensor type: %s" % sensor_type)
                return
                
            
            # pass message data on to user implemented method
            self.periodicUpdateReceived(timestamp,
                                        temperature,
                                        sensor_type,
                                        sensor_instance,
                                        sensor_data)
           
        except Exception, ex:
            logging.exception(ex)
            logging.error("Problem processing periodic update")
            return        



                       
    def _parseHistoryUpdate(self, msg):
        """
        Parse a history update message for important information and
        store it until the complete history message update cycle is 
        completed. A history update is one message among many that 
        form the history update cycle set of messages.
        
        The Current Cost device begins emitting set of history 
        messages about 1 minute past every odd hour.
        
        On receipt of the first history message a callback timer is 
        started and the timer is extended upon receipt of each
        subsequent history message. The expiry of the timer signifies
        the completion of the history message cycle at which point
        the accumulated history message data is passed to the user
        implemented historyUpdateReceived method.
        """
        logging.debug("Parsing a history update message")

        try:
            self.source = msg.findtext("src")
            self.days_since_birth = msg.findtext("dsb")
            # Ignore the unit timestamp in preference for a
            # computer generated timestamp that can more
            # easily be used when updating data points at
            # sites like Cosm.
            #timestamp = msg.findtext("time")
            if self.config.use_utc_timestamps:
                timestamp = datetime.datetime.utcnow()
            else:
                timestamp = datetime.datetime.now()

        
            history = msg.find("hist")
            self.days_since_wiped = history.findtext("dsw")
            sensor_type = int(history.findtext("type"))


            # Add a new key for the sensor type if one does not yet exist.
            if sensor_type not in self.historicSensorData:
                self.historicSensorData[sensor_type] = {}
                
            # Add a new key for the timeout handler
            if sensor_type not in self.historicalDataUpdateCompleteForSensorType:
                self.historicalDataUpdateCompleteForSensorType[sensor_type] = None            

            # Start a callback timer, for this particular sensor type, that will be 
            # used to detect the completion of the historic data message cycle and
            # pass the collected historic data to the handleHistoryUpdate method.
            # If a message is received within the timeout window then delay the 
            # timer and additional timeout period.
            #
            if self.historicalDataUpdateCompleteForSensorType[sensor_type] is None:
                self.historicalDataUpdateCompleteForSensorType[sensor_type] = reactor.callLater(self.historicDataMessageTimeout, 
                                                                                                self._historicalDataUpdateCompleted,
                                                                                                sensor_type)
            else:
                # delay history data completed job another timeout period.
                self.historicalDataUpdateCompleteForSensorType[sensor_type].delay(self.historicDataMessageTimeout)


            
            sensor_units = history.findtext("units")
            
            for data_element in history.findall("data"):
                sensor_instance = int(data_element.findtext("sensor"))
                
                if sensor_instance not in self.historicSensorData[sensor_type]:
                    sensorHistoricalData = txcurrentcost.SensorHistoryData(sensor_type, sensor_instance, sensor_units)
                    self.historicSensorData[sensor_type][sensor_instance] = sensorHistoricalData
                    
                logging.debug("Processing historical data for sensor %s" % sensor_instance)
                
                datapoints = []   
                for historical_element in data_element:
                    tag = historical_element.tag
                    value = historical_element.text
                    if tag == "sensor":
                        # ignore the sensor element that has already been inspected.
                        continue
                    datapoints.append((tag, value))
                    
                historicalSensorData = self.historicSensorData[sensor_type][sensor_instance]
                historicalSensorData.storeDataPoints(timestamp, datapoints)
                
        except Exception, ex:
            logging.exception(ex)
            logging.error("Problem processing history update message")
            return                    


    def _historicalDataUpdateCompleted(self, sensor_type):
        """
        Callback called to notify that a history update message cycle has completed
        for the specified sensor type.
        
        @param sensor_type: The sensor type that has completed it's history cycle.
        @type sensor_type: A Sensors.Types item
        """
        logging.debug("History update cycle completed for sensor type: %s" % sensor_type)
        
        self.historicalDataUpdateCompleteForSensorType[sensor_type] = None
        historicDataForSensorType = self.historicSensorData[sensor_type]
        
        # Only pass on sensor historical data for sensors that actually contain data.
        sensorsWithHistoricalData = {}
        for sensor_id, sensorHistoricalData in historicDataForSensorType.items():
            if sensorHistoricalData.dataPresent:
                sensorsWithHistoricalData[sensor_id] = sensorHistoricalData
        
        self.historyUpdateReceived(sensor_type, sensorsWithHistoricalData)


    
    
