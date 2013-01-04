
'''
This module defines common Current Cost classes such as
Sensors, History data store and the protocol used to
communicate with the Current Cost device.

The Current Cost message defintion is defined at:
http://www.currentcost.com/cc128/xml.htm
'''

import json
import logging
try:
    from xml.etree import cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree
from twisted.internet.serialport import SerialPort
from twisted.protocols.basic import LineReceiver


version = (0, 0, 3)


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
    TemperatureSensor = 0  # A psuedo kind used for periodic updates
    ElectricitySensor = 1  # Whole House unit, IAM's, etc
    OptiSmartSensor = 2    # Impulse sensor

    Types = [TemperatureSensor,
             ElectricitySensor,
             OptiSmartSensor]

    Names = {TemperatureSensor: "Temperature",
             ElectricitySensor: "Electricity",
             OptiSmartSensor: "OptiSmart"}

    Units = {TemperatureSensor: "C",
             ElectricitySensor: "Watts",
             OptiSmartSensor: "ipu"}

    @classmethod
    def nameForType(cls, sensor_type):
        if sensor_type in Sensors.Types:
            name = Sensors.Names[sensor_type]
        else:
            logging.warning("Invalid sensor type \'%s\' not in %s - can't return name" % (sensor_type, Sensors.Types))
            name = "Unknown"
        return name

    @classmethod
    def unitsForType(cls, sensor_type):
        if sensor_type in Sensors.Types:
            _type = Sensors.Units[sensor_type]
        else:
            logging.warning("Invalid sensor type \'%s\' not in %s - can't return units" % (sensor_type, Sensors.Types))
            _type = "Unknown"
        return _type


class SensorHistoryData(object):
    """ Store history data for a single Current Cost sensor """

    Hour_Data = 'hour'
    Day_Data = 'day'
    Month_Data = 'month'
    Year_Data = 'year'

    Hour_Data_Prefix = 'h'
    Day_Data_Prefix = 'd'
    Month_Data_Prefix = 'm'
    Year_Data_Prefix = 'y'

    Prefixes = [Hour_Data_Prefix,
                Day_Data_Prefix,
                Month_Data_Prefix,
                Year_Data_Prefix]

    Prefix_To_Data_Kind_Map = {Hour_Data_Prefix: Hour_Data,
                               Day_Data_Prefix: Day_Data,
                               Month_Data_Prefix: Month_Data,
                               Year_Data_Prefix: Year_Data}

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

        # This flag declares that this sensor has non-zero data. CurrentCost
        # history messages contain a full complement of hour, day, month,
        # year entries even when the content is entirely zeros. If any value
        # is non-zero this flag is set. This can be useful if we only want to
        # process history data for a sensor that actually contains data.
        self.dataPresent = False

    def _getDataPointKind(self, tag):
        """
        Detect the kind of history data point by inspecting the tag.
        Examples of tags are: (h,018), (d,054), (m,002), (y,001)
        """
        tag_prefix = tag[0]
        if tag_prefix in SensorHistoryData.Prefixes:
            history_data_kind = SensorHistoryData.Prefix_To_Data_Kind_Map[tag_prefix]
            return history_data_kind
        else:
            logging.error("Unknown tag prefix \'%s\', can't resolve to history data kind" % (tag_prefix))

    def _getData(self, dataDict):
        """
        Return a list of tuples containing the data in ascending tag order.
        Each tuple in the list contains the data tag (itself a 2-tuple of
        tag prefix and index) and the value.
        The data key is kept associated with the value (rather than simply a
        list of values) so that the value can't be misinterpreted as belonging
        to a different tag in cases where intervening tags are missing.
        """
        # Sort the data keys using the integer value of the key index which
        # is the second field in the data key tuple.
        dataKeys = dataDict.keys()
        dataKeys.sort(key=lambda x: int(x[1]))
        sortedData = []
        for dataKey in dataKeys:
            datapoint = (dataKey, dataDict[dataKey])
            sortedData.append(datapoint)
        return sortedData

    def _checkForActualData(self, value):
        """
        Set a flag on this sensor if non-zero data is observed.
        """
        if not self.dataPresent:
            if float(value) > 0:
                self.dataPresent = True

    def getHourData(self):
        """
        Return a list of tuples containing hour data in ascending tag order.
        """
        return self._getData(self.hourData)

    def getDayData(self):
        """
        Return a list of tuples containing day data in ascending tag order.
        """
        return self._getData(self.dayData)

    def getMonthData(self):
        """
        Return a list of tuples containing month data in ascending tag order.
        """
        return self._getData(self.monthData)

    def getYearData(self):
        """
        Return a list of tuples containing year data in ascending tag order.
        """
        return self._getData(self.yearData)

    def storeHourData(self, key, value):
        """
        Store an hour datapoint
        """
        self.hourData[key] = value
        self._checkForActualData(value)

    def storeDayData(self, key, value):
        """
        Store a day datapoint
        """
        self.dayData[key] = value
        self._checkForActualData(value)

    def storeMonthData(self, key, value):
        """
        Store a month datapoint
        """
        self.monthData[key] = value
        self._checkForActualData(value)

    def storeYearData(self, key, value):
        """
        Store a year datapoint
        """
        self.yearData[key] = value
        self._checkForActualData(value)

    def storeDataPoints(self, timestamp, datapoints):
        """
        Store any kind of historical datapoints. History entries might exist
        for hour, day, month, year. Handle all variants of datapoint kind.

        @param timestamp: timestamp of the last history update received
        @type timestamp: datetime
        @param datapoints: A list of 2-tuples containing the history tag and value
        @type datapoints: list of 2-tuples
        """
        self.last_update = timestamp
        for tag, value in datapoints:
            history_data_kind = self._getDataPointKind(tag)

            if history_data_kind == SensorHistoryData.Hour_Data:
                self.storeHourData(tag, value)

            elif history_data_kind == SensorHistoryData.Day_Data:
                self.storeDayData(tag, value)

            elif history_data_kind == SensorHistoryData.Month_Data:
                self.storeMonthData(tag, value)

            elif history_data_kind == SensorHistoryData.Year_Data:
                self.storeYearData(tag, value)

            else:
                logging.warning("Don't know how to handle historical tag %s with value %s" % (tag, value))

    def toJson(self):
        """
        Return a JSON format encoding of this sensor's historical data.
        """
        d = {}
        d['type'] = self.type
        d['instance'] = self.instance
        d['timestamp'] = str(self.last_update)
        d['units'] = self.units
        d['data'] = {'hour': self.getHourData(),
                     'day': self.getDayData(),
                     'month': self.getMonthData(),
                     'year': self.getYearData()}
        return json.dumps(d)

    def __str__(self):
        """
        Return a string representation of this object
        """
        o = []

        if self.dataPresent:
            o.append("Sensor: %s [%s]" % (self.instance, Sensors.nameForType(self.type)))
            o.append("Last update: %s" % (self.last_update))
            if self.hourData:
                o.append("Hour Data:")
                for hourKey, hourValue in self.getHourData():
                    o.append("\t%s %s %s" % (hourKey, hourValue, self.units))
            else:
                o.append("No hour data history available")

            if self.dayData:
                o.append("Day Data:")
                for dayKey, dayValue in self.getDayData():
                    o.append("\t%s %s %s" % (dayKey, dayValue, self.units))
            else:
                o.append("No day data history available")

            if self.monthData:
                o.append("Month Data:")
                for monthKey, monthValue in self.getMonthData():
                    o.append("\t%s %s %s" % (monthKey, monthValue, self.units))
            else:
                o.append("No month data history available")

            if self.yearData:
                o.append("Year Data:")
                for yearKey, yearValue in self.getMonthData():
                    o.append("\t%s %s %s" % (yearKey, yearValue, self.units))
            else:
                o.append("No year data history available")

        else:
            o.append("Sensor: %s - No history data" % self.instance)

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
        Parse the string into an ElementTree element and inspect
        for which of the two message variants has been received
        then dispatch to the handler.
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
