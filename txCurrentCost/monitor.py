#!/usr/bin/env python


import datetime
import logging
import os
import sys
import ConfigParser
import txCurrentCost
from twisted.internet import reactor
from twisted.python import usage




class MonitorConfig(object):
    """ Current Cost Configuration file """
    
    # secitons
    CURRENT_COST_SECTION = "current_cost"
    SECTIONS = [CURRENT_COST_SECTION]
    
    # fields
    LOGFILE = "logfile"
    LOGFORMAT = "logformat"
    LOGLEVEL = "loglevel"
    PORT = "port"
    BAUDRATE = "baudrate"
    CLAMP_COUNT = "clamp_count"
    USE_UTC_TIMESTAMPS = "use_utc_timestamps"

    FIELDS = [LOGFILE,
              LOGFORMAT,
              LOGLEVEL,
              PORT,
              BAUDRATE,
              CLAMP_COUNT,
              USE_UTC_TIMESTAMPS]

    
    def __init__(self, config_file):
        if not os.path.exists(config_file):
            raise Exception("Invalid configuration file path: %s" % config_file)
        self.config_file = config_file
        
        # attribute populated after config file parsing
        self.logfile = None
        self.loglevel = None
        self.port = None
        self.baudrate = None
        self.clamp_count = None

        self.parse(config_file)

        
    def parse(self, config_file):
        parser = ConfigParser.SafeConfigParser()
        parser.read(config_file)
        
        # current cost settings
        
        logfile = parser.get(MonitorConfig.CURRENT_COST_SECTION, MonitorConfig.LOGFILE)
        if logfile and logfile.lower() == "none":
            self.logfile = sys.stdout
        else:
            self.logfile = logfile
        
        self.logformat = parser.get(MonitorConfig.CURRENT_COST_SECTION, MonitorConfig.LOGFORMAT, raw=True)
        
        loglevel = parser.get(MonitorConfig.CURRENT_COST_SECTION, MonitorConfig.LOGLEVEL)
        DESCRIPTION_TO_LEVEL = {"debug" : logging.DEBUG,
                                "info" : logging.INFO,
                                "warning" : logging.WARNING,
                                "error" : logging.ERROR}
        if loglevel in DESCRIPTION_TO_LEVEL:
            self.loglevel = DESCRIPTION_TO_LEVEL[loglevel]
        else:
            # default to error level logging
            self.loglevel = logging.ERROR
        
        
        self.port = parser.get(MonitorConfig.CURRENT_COST_SECTION, MonitorConfig.PORT)
        self.baudrate = parser.getint(MonitorConfig.CURRENT_COST_SECTION, MonitorConfig.BAUDRATE)
        self.clamp_count = parser.getint(MonitorConfig.CURRENT_COST_SECTION, MonitorConfig.CLAMP_COUNT)
        self.use_utc_timestamps = parser.getboolean(MonitorConfig.CURRENT_COST_SECTION, MonitorConfig.USE_UTC_TIMESTAMPS)



  

class Monitor(object):
    """ Monitor a current cost device. """
    
    def __init__(self, config_file):
        
        self.config = MonitorConfig(config_file)
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
        want to update it to Pachube. Perhaps you want to store it for a while, average
        it and then post it to Pachube. Whatever! 
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
        """ Start the CurrenCost monitor """
        logging.info('CurrentCostMonitor starting')
        logging.info('Attempting to open port %s at %dbps' % (self.config.port, self.config.baudrate))
        self.protocol = txCurrentCost.CurrentCostDataProtocol(self._messageHandler)
        self.serialPort = txCurrentCost.FixedSerialPort(self.protocol, 
                                                      self.config.port, 
                                                      reactor,
                                                      baudrate=self.config.baudrate)
       

    def stop(self):
        """ Stop the CurrenCost monitor """
        logging.info('CurrentCostMonitor stopping')
        if self.protocol.transport:
            self.protocol.transport.loseConnection()
        self.serialPort.close()


    def _messageHandler(self, kind, message):
        """ 
        Handle a CurrentCost message from the protocol. This method is passed
        to the protocol as a message callback handler. 
        
        @param kind: The kind of message received
        @type kind: string
        @param message: An XML message string
        @type message: string
        """
        if kind not in txCurrentCost.MessageKinds:
            logging.error("Invalid message kind \'%s\' not in kinds: %s" % txCurrentCost.MessageKinds)
            return
        
        if kind == txCurrentCost.PeriodicUpdateMsg:
            self._parsePeriodicUpdate(message)
            
        elif kind == txCurrentCost.HistoryUpdateMsg:
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
            # sites like pachube.
            #timestamp = msg.findtext("time")
            if self.config.use_utc_timestamps:
                timestamp = datetime.datetime.utcnow()
            else:
                timestamp = datetime.datetime.now()
            
            temperature = msg.findtext("tmpr")
            
            sensor_instance = int(msg.findtext("sensor"))
            identifier = msg.findtext("id")
            sensor_type = int(msg.findtext("type"))

            if sensor_type == txCurrentCost.Sensors.ElectricitySensor:
                
                # channel indexes start from 1, not zero.
                if sensor_instance == txCurrentCost.Sensors.WholeHouseSensorId:
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
                    
            elif sensor_type == txCurrentCost.Sensors.OptiSmartSensor:
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
            logging.error("Problem processing periodic update: %s" % ex)
            return        



                       
    def _parseHistoryUpdate(self, msg):
        """
        Parse a historic update message for important information and
        store it until the history message update cycle is completed.
        A cycle of history messages begins about 1 minute past every
        hour.
        A callback timer is started on receipt of the first history
        message and the timer is extended upon receipt of each
        subsequent history message. If no history message is received 
        within the timeout period  to the user implemented handlePeriodicUpdate method.
        """
        logging.debug("Parsing a history update message")

        try:
            self.source = msg.findtext("src")
            self.days_since_birth = msg.findtext("dsb")
            # Ignore the unit timestamp in preference for a
            # computer generated timestamp that can more
            # easily be used when updating data points at
            # sites like pachube.
            #timestamp = msg.findtext("time")
            if self.config.use_utc_timestamps:
                timestamp = datetime.datetime.utcnow()
            else:
                timestamp = datetime.datetime.now()

        
            history = msg.find("hist")
            self.days_since_wiped = history.findtext("dsw")
            sensor_type = int(history.findtext("type"))


            # 
            if sensor_type not in self.historicSensorData:
                self.historicSensorData[sensor_type] = {}
                
            

            # Start a callback timer, for this particular sensor type, that will be 
            # used to detect the completion of the historic data message cycle and
            # pass the collected historic data to the handleHistoryUpdate method.
            # If a message is received within the timeout window then the reset.
            #
            if self.historicalDataUpdateCompleteForSensorType[sensor_type] is None:
                self.historicalDataUpdateCompleteForSensorType[sensor_type] = reactor.callLater(self.historicDataMessageTimeout, 
                                                                             self._historicalDataUpdateCompleted,
                                                                             sensor_type)
            else:
                # delay history data completed job another timeout period.
                self.historicalDataUpdateCompleteForSensorType[sensor_type].delay(self.historicalDataMessageTimeout)


            
            sensor_units = history.findtext("units")
            
            for data_element in history.findall("data"):
                sensor_instance = int(data_element.findtext("sensor"))
                
                if sensor_instance not in self.historicSensorData[sensor_type]:
                    sensorHistoricalData = txCurrentCost.HistoricalSensorData(sensor_type, sensor_instance, sensor_units)
                    self.historicSensorData[sensor_type][sensor_instance] = sensorHistoricalData
                    
                logging.debug("Processing historical data for sensor %s" % sensor_instance)
                
                datapoints = []   
                for historical_element in data_element.iter():
                    tag = historical_element.tag
                    value = historical_element.text
                    if tag == "sensor":
                        # ignore the sensor element that has already been inspected.
                        continue
                    datapoints.append((tag, value))
                    
                historicalSensorData = self.historicSensorData[sensor_type][sensor_instance]
                historicalSensorData.storeDataPoints(timestamp, datapoints)
                
        except Exception, ex:
            logging.error("Problem processing history update message: %s" % ex)
            return                    


    def _historicalDataUpdateCompleted(self, sensor_type):
        """
        Callback called to notify that a history update message cycle has completed
        for the specified sensor type.
        
        @param sensor_type: The sensor type that has completed it's history cycle.
        @type sensor_type: A Sensors.Types item
        """
        self.historicalDataUpdateCompleteForSensorType[sensor_type] = None
        historicDataForSensorType = self.historicSensorData[sensor_type]
        
        # Only pass on sensor historical data for sensors that actually contain data.
        sensorsWithHistoricalData = {}
        for sensor_id, sensorHistoricalData in historicDataForSensorType.items():
            if sensorHistoricalData.nonZeroDataPresent:
                sensorsWithHistoricalData[sensor_id] = sensorHistoricalData
        
        self.historyUpdateReceived(sensor_type, sensorsWithHistoricalData)








class MonitorOptions(usage.Options):
    optParameters = [['configfile', 'c', None, 'Configuration file path']]





if __name__ == "__main__":


    # Run using:
    # $python monitor.py --configfile=currentcost.cfg 

    from twisted.python import log
    
    o = MonitorOptions()
    try:
        o.parseOptions()
    except usage.UsageError, errortext:
        print "%s: %s" % (sys.argv[0], errortext)
        print "%s: Try --help for usage details." % (sys.argv[0])
        raise SystemExit, 1

    # Send Twisted log messages to logging logger
    _observer = log.PythonLoggingObserver()
    _observer.start()

    config_file = o.opts['configfile']
    monitor = Monitor(config_file)
    logging.basicConfig(level=monitor.config.loglevel,
                        format=monitor.config.logformat,
                        logfile=monitor.config.logfile)    
    reactor.callWhenRunning(monitor.start)
    reactor.run()
    
    
