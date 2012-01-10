

try:
    from xml.etree import cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree
import logging
from twisted.internet.serialport import SerialPort
from twisted.protocols.basic import LineReceiver


version = (0,0,1)


# Define the kinds of messages that can be received from the CurrentCost device
#
PeriodicUpdateMsg = 'periodic_update_msg'
HistoryUpdateMsg = 'history_update_msg'
MessageKinds = [PeriodicUpdateMsg,
                HistoryUpdateMsg]


class Sensors(object):
    """ Define Current Cost sensor kinds """

    # Defines the maximum number of sensors available.
    # 0 - Whole House sensor 
    # 1-9 Appliance sensors
    Maximum = 10
    
    WholeHouseSensorId = 0
    IndividualApplicanceMonitor1Id = 1
    IndividualApplicanceMonitor2Id = 2
    IndividualApplicanceMonitor3Id = 3
    IndividualApplicanceMonitor4Id = 4
    IndividualApplicanceMonitor5Id = 5
    IndividualApplicanceMonitor6Id = 6
    IndividualApplicanceMonitor7Id = 7
    IndividualApplicanceMonitor8Id = 8
    IndividualApplicanceMonitor9Id = 9

    
    # Sensor Types
    TemperatureSensor = 0 # A psuedo kind used for realtime updates
    ElectricitySensor = 1 # Whole House unit, IAM's, etc
    OptiSmartSensor = 2   # Impulse sensor
    
    Types = [TemperatureSensor,
             ElectricitySensor,
             OptiSmartSensor]
    
    Names = {TemperatureSensor : "Temperature",
             ElectricitySensor : "Electricity",
             OptiSmartSensor : "OptiSmart"}

    Units = {TemperatureSensor : "C",
             ElectricitySensor : "Watts",
             OptiSmartSensor : "ipu"}

    @classmethod
    def nameForType(cls, sensor_type):
        if sensor_type in Sensors.Types:
            return Sensors.Names[sensor_type]
        else:
            logging.warning("Invalid sensor type \'%s\' not in %s - can't return name" % (sensor_type, Sensors.Types))
            return "Unknown"
        
    @classmethod
    def unitsForKind(cls, sensor_type):
        if sensor_type in Sensors.Kinds:
            return Sensors.Units[sensor_type]
        else:
            logging.warning("Invalid sensor type \'%s\' not in %s - can't return units" % (sensor_type, Sensors.Kinds))
            return "Unknown"
        



class HistoricalSensorData(object):
    """ Store historical data for a single Current Cost sensor """
    
    Historic_Hour_Data = 'hour'
    Historic_Day_Data = 'day'
    Historic_Month_Data = 'month'
    Historic_Year_Data = 'year'    
    
    Historic_Hour_Data_Prefix = 'h'
    Historic_Day_Data_Prefix = 'd'
    Historic_Month_Data_Prefix = 'm'
    Historic_Year_Data_Prefix = 'y'
    
    Historic_Data_Prefixes = [Historic_Hour_Data_Prefix,
                              Historic_Day_Data_Prefix,
                              Historic_Month_Data_Prefix,
                              Historic_Year_Data_Prefix]
    
    Prefix_To_Data_Kind_Map = {Historic_Hour_Data_Prefix : Historic_Hour_Data,
                               Historic_Day_Data_Prefix : Historic_Day_Data,
                               Historic_Month_Data_Prefix : Historic_Month_Data,
                               Historic_Year_Data_Prefix : Historic_Year_Data}
    
    def __init__(self, sensor_type, sensor_instance, sensor_units):
        
        self.instance = sensor_instance
        self.type = sensor_type
        self.units = sensor_units
        self.last_update = None
        
        # historical data stores
        self.hourData = {}
        self.dayData = {}
        self.monthData = {}
        self.yearData = {}
        
        # A flag to declare that this sensor has non-zero data. CurrentCost
        # history messages contain a full complement of hour, day, month,
        # year entries even when the content is entirely zeros. If any value
        # is non-zero this flag is set. This can be useful if we only want to 
        # process historical sensor data that actually contains data.
        self.nonZeroDataPresent = False


    def _getDataPointKind(self, tag):
        """ Detect the kind of history data point kind of the tag """
        tag_prefix = tag[0]
        if tag_prefix in HistoricalSensorData.Historic_Data_Prefixes:
            history_data_kind = HistoricalSensorData.Prefix_To_Data_Kind_Map[tag_prefix]
            return history_data_kind
        else:
            logging.error("Unknown tag prefix \'%s\', can't resolve to history data kind" % (tag_prefix)) 


    def storeHourData(self, key, value):
        self.hourData[key] = value
        
    def storeDayData(self, key, value):
        self.dayData[key] = value
        
    def storeMonthData(self, key, value):
        self.monthData[key] = value

    def storeYearData(self, key, value):
        self.yearData[key] = value

    def storeDataPoints(self, timestamp, datapoints):
        """
        Store any kind of historical data point. History entries might exist
        for hour, day, month, year. Handle all variants of data point kind.
        
        @param timestamp: timestamp of the last history update received 
        @type timestamp: datetime
        @param datapoints: A list of 2-tuples containing the history tag and value
        @type datapoints: list of 2-tuples
        """
        self.last_update = timestamp
        for tag, value in datapoints:
            history_data_kind = self._getDataPointKind(tag)
            
            if float(value) > 0:
                self.nonZeroDataPresent = True
            
            if history_data_kind == HistoricalSensorData.Historic_Hour_Data:
                self.storeHourData(tag, value)
                
            elif history_data_kind == HistoricalSensorData.Historic_Day_Data:
                self.storeDayData(tag, value)
                
            elif history_data_kind == HistoricalSensorData.Historic_Month_Data:
                self.storeMonthData(tag, value)
                
            elif history_data_kind == HistoricalSensorData.Historic_Year_Data:
                self.storeYearData(tag, value)
                
            else:
                logging.warning("Don't know how to handle historical tag %s with value %s" % (tag, value))  
                  
        
    def __str__(self):
        o = []
        
        if self.last_update is None:
            o.append("Sensor: %s - No historical data" % self.instance)
        else:        
            o.append("Sensor: %s [%s]" % (self.instance, Sensors.nameForKind(self.type)))

            if self.hourData:
                o.append("Historical Hour Data:")
                hourDataKeys = self.hourData.keys()
                for hourDataKey in hourDataKeys:
                    hourDataValue = self.hourData[hourDataKey]
                    o.append("\t%s %s %s" % (hourDataKey, hourDataValue, self.units))
            else:
                o.append("No historical hour data available")
                
            if self.dayData:
                o.append("Historical Day Data:")
                dayDataKeys = self.dayData.keys()
                for dayDataKey in dayDataKeys:
                    dayDataValue = self.dayData[dayDataKey]
                    o.append("\t%s %s %s" % (dayDataKey, dayDataValue, self.units))
            else:
                o.append("No historical day data available")
                
            if self.monthData:
                o.append("Historical Month Data:")
                monthDataKeys = self.monthData.keys()
                for monthDataKey in monthDataKeys:
                    monthDataValue = self.monthData[monthDataKey]
                    o.append("\t%s %s %s" % (monthDataKey, monthDataValue, self.units))
            else:
                o.append("No historical month data available")
                
            if self.yearData:
                o.append("Historical Year Data:")
                yearDataKeys = self.yearData.keys()
                for yearDataKey in yearDataKeys:
                    yearDataValue = self.yearData[hourDataKey]
                    o.append("\t%s %s %s" % (yearDataKey, yearDataValue, self.units))
            else:
                o.append("No historical year data available")
                        
        return "\n".join(o)
    



class FixedSerialPort(SerialPort):
    '''
    My current Cost EnviR is connected to my computer using 
    a serial over USB connection. USB devices can be 
    disconnected or reset at any time. Ensure the delivery
    of the connectionLost event.
    
    See: http://stackoverflow.com/questions/3678661/twisteds-serialport-and-disappearing-serial-port-devices
    '''
    def connectionLost(self, reason):
        super(FixedSerialPort, self).connectionLost(reason)
        self.protocol.connectionLost(reason)
        
    def close(self):
        """ Close the serial port """
        if self.protocol.transport:
            self.protocol.transport.loseConnection()
            
             
class CurrentCostDataProtocol(LineReceiver):
    """
    The CurrentCost device sends messages using a new line as a delimiter
    between messages.
    """

    delimiter = "\n"

    def __init__(self, msgHandler):
        self.msgHandler = msgHandler

    def connectionMade(self):
        logging.debug("%s connection made!" % self.__class__.__name__)

    def connectionLost(self, reason):
        logging.debug("%s connection lost!" % self.__class__.__name__)
        self.clearLineBuffer()
  
    def lineReceived(self, line):
        """ 
        Handle a CurrentCost message line from the serial port.
        """
        logging.debug("Received a CurrentCost message with %i bytes" % (len(line)))
        
        try:
            msg = etree.fromstring(line)
            history = msg.find("hist")
            if history is not None:
                kind = HistoryUpdateMsg
            else:
                kind = PeriodicUpdateMsg
                
            self.msgHandler(kind, msg)
            
        except etree.ParseError, ex:
            logging.error("Error parsing msg xml: %s\n%s\n" % (ex, line))
            return
        
