#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Davis WeatherLink Live (WLL) driver for WeeWX
#
# Copyright 2021 Ethan L. Miller
#
# Based on wll.py, Copyright 2020 Jon Otaegi
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.
#
# See http://www.gnu.org/licenses/

""" WeeWX driver for Davis WeatherLink Live (WLL) devices.

The Davis WeatherLink Live (WLL) has an HTTP interface that returns current weather
data in JSON format, described at https://weatherlink.github.io/weatherlink-live-local-api/.
This driver polls the interface and creates a packet with current weather conditions,
and returns it to WeeWX.

The driver supports a WLL that reports information for multiple sensors of the same
type; weewx.conf can specify which sensors are reported for each field.

Requires:
* Python3
* requests module (install with apt/yum/pkg or pip)

++++++ IMPORTANT: this driver is *only* compatible with Python3. ++++++

"""

import time
import requests
from collections import namedtuple
import unittest

import weewx
import weewx.drivers

DRIVER_NAME = 'DavisWLL'
DRIVER_VERSION = '0.1'

MM_TO_INCH = 0.0393701
rain_collector_scale = {
    1: 0.01,
    2: 0.2 * MM_TO_INCH,
    3: 0.1,
    4: 0.001 * MM_TO_INCH,
}

def track_total_rain (drvr, data, annual_rain):
    """
    Return the amount of rain that's fallen since the last call to this function.
    If this is the first call to the function, return zero and set annual rain to current annual rain total.
    If the annual rain total decreased, we must have wrapped around a year, so set the "last rainfall" to 0.
    Track total rain amount in absolute units.
    """
    # Scale rain *first* so all stored amounts are in absolute units
    annual_rain_scaled = scale_rain (drvr, data, annual_rain)
    if drvr.annual_rain_scaled == None:
        drvr.annual_rain_scaled = annual_rain_scaled
    elif annual_rain_scaled < drvr.annual_rain_scaled:
        drvr.annual_rain_scaled = 0
    rain_amt = annual_rain_scaled - drvr.annual_rain_scaled
    drvr.annual_rain_scaled = annual_rain_scaled
    return rain_amt

def scale_rain (drvr, data, amt):
    """
    Scale rainfall by the current scale.
    """
    return amt * drvr.rain_scale_factor

# Table of sensor information.
# Includes Davis WLL name (from JSON), default scale, sensor "group" (for mappings), sensor type, and function to generate value (if any).
SensorInfo = namedtuple ('SensorInfo', ['wllname', 'factor', 'metric_type', 'txid_group', 'function'])

try:
    # WeeWX 4 logging
    import weeutil.logger
    import logging

    log = logging.getLogger(__name__)

    def log_dbg(msg):
        log.debug(msg)

    def log_inf(msg):
        log.info(msg)

    def log_err(msg):
        log.error(msg)

except ImportError:
    # Old-style WeeWX logging
    import syslog

    def log_msg(level, msg):
        syslog.syslog(level, 'DavisWLL: %s' % msg)

    def log_dbg(msg):
        log_msg(syslog.LOG_DEBUG, msg)

    def log_inf(msg):
        log_msg(syslog.LOG_INFO, msg)

    def log_err(msg):
        log_msg(syslog.LOG_ERR, msg)


def loader(config_dict, engine):
    return DavisWLL(**config_dict['DavisWLL'])

class DavisWLL(weewx.drivers.AbstractDevice):
    @property
    def default_stanza(self):
        return """
[DavisWLL]
    # This section is for Davis WeatherLink Live reporters.

    # The hostname or ip address of the WeatherLink Live device in the local network.
    # For the driver to work, the WeatherLink Live and the computer running WeeWX have to be on the same local network.
    # For details on programmatically finding WeatherLink Live devices on the local network,
    # see https://weatherlink.github.io/weatherlink-live-local-api/discovery.html
    host = 10.0.0.1

    # How often to poll the weather data (in seconds).
    # The interface can support continuous requests as often as every 10 seconds.
    poll_interval = 10

    # The default transmitter ID (1-8).
    weather_transmitter_id = 1

    # Default soil sensor transmitter ID (1-8):
    soil_transmitter_id = 2

    # More detailed mappings of sensors to transmitter IDs.
    # Only specify cases where the default transmitter ID isn't correct.
    # Mappings are for temp (includes humidity), wind, rain, uv, solar, and battery.
    # Mappings are also for soil temp (soil1, soil2, soil3, soil4) and soil moisture (moist1, moist2, moist3, moist4)
    # If no transmitter is specified for a measurement (either globally as above, or locally in mappings),
    # the lowest-number transmitter with that measurement is used.
    # mappings = temp:1, wind:4, soil1:2, soil2:3 moist1:3

    # The driver to use:
    driver = user.daviswll

"""

    def __init__(self, **stn_dict):
        self.sensor_info = {
            'outTemp'           : SensorInfo ('temp', 1, 'temp', 'W', None),
            'outHumidity'       : SensorInfo ('hum', 1, 'temp', 'W', None),
            'dewpoint'          : SensorInfo ('dew_point', 1, 'temp', 'W', None),
            'heatindex'         : SensorInfo ('heat_index', 1, 'temp', 'W', None),
            'windchill'         : SensorInfo ('wind_chill', 1, 'wind', 'W', None),
            'windSpeed'         : SensorInfo ('wind_speed_last', 1, 'wind', 'W', None),
            'windDir'           : SensorInfo ('wind_dir_last', 1, 'wind', 'W', None),
            'windGust'          : SensorInfo ('wind_speed_hi_last_10_min', 1, 'wind', 'W', None),
            'windGustDir'       : SensorInfo ('wind_dir_at_hi_speed_last_10_min', 1, 'wind', 'W', None),
            'rain'              : SensorInfo ('rainfall_year', 1, 'rain', 'W', track_total_rain),
            'rainRate'          : SensorInfo ('rain_rate_last', 1, 'rain', 'W', scale_rain),
            'radiation'         : SensorInfo ('solar_rad', 1, 'solar', 'W', None),
            'UV'                : SensorInfo ('uv_index', 1, 'uv', 'W', None),
            'txBatteryStatus'   : SensorInfo ('trans_battery_flag', 1, 'battery', 'W', None),
            'soilTemp1'         : SensorInfo ('temp_1', 1, 'soil1', 'S', None),
            'soilTemp2'         : SensorInfo ('temp_2', 1, 'soil2', 'S', None),
            'soilTemp3'         : SensorInfo ('temp_3', 1, 'soil3', 'S', None),
            'soilTemp4'         : SensorInfo ('temp_4', 1, 'soil4', 'S', None),
            'soilMoist1'        : SensorInfo ('moist_soil_1', 1, 'moist1', 'S', None),
            'soilMoist2'        : SensorInfo ('moist_soil_2', 1, 'moist2', 'S', None),
            'soilMoist3'        : SensorInfo ('moist_soil_3', 1, 'moist3', 'S', None),
            'soilMoist4'        : SensorInfo ('moist_soil_4', 1, 'moist4', 'S', None),
            'barometer'         : SensorInfo ('bar_sea_level', 1, 'bar', 'B', None),
            'pressure'          : SensorInfo ('bar_absolute', 1, 'bar', 'B', None),
            'inTemp'            : SensorInfo ('temp_in', 1, 'indoor', 'I', None),
            'inHumidity'        : SensorInfo ('hum_in', 1, 'indoor', 'I', None),
            'inDewpoint'        : SensorInfo ('dew_point_in', 1, 'indoor', 'I', None),
        }
        self.host = stn_dict.get('host')
        if not self.host:
            log_err("The WeatherLink Live hostname or ip address is required.")
        self.service_url = "http://{0}:80/v1/current_conditions".format (self.host)
        self.poll_interval = float(stn_dict.get('poll_interval', 10))
        if self.poll_interval < 10:
            log_err("The `poll_interval` parameter must be 10 or greater (found {0}).".format (poll_interval))
        self.hardware = stn_dict.get('hardware')
        self.annual_rain_scaled = None
        # Default is rain collector type 1
        self.rain_scale_factor = self.get_rain_scale_factor (1)
        self.all_txids = list (range(1,9))
        self.all_txids += ['B', 'I']
        self.txids = dict()
        self.default_weather_txid = int(stn_dict.get ('weather_transmitter_id', 1))
        self.default_soil_txid = int (stn_dict.get ('soil_transmitter_id', 2))
        self.mappings = stn_dict.get ('mappings')
        self.init_txids (self.mappings)

    def hardware_name(self):
        return self.hardware

    def init_txids (self, mappings):
        # Initialize default txids by large-scale group
        default_txids = {'W': self.default_weather_txid, 'S': self.default_soil_txid, 'B': 'B', 'I': 'I'}
        for c in self.sensor_info.values():
            self.txids[c.wllname] = default_txids[c.txid_group]
        # Set up different txids for individual mappings
        if mappings:
            for m in mappings.lower().split ():
                try:
                    (metric_type, txid) = m.split (':')
                    txid = int (txid)
                    for c in self.sensor_info.values():
                        if c.metric_type == metric_type:
                            self.txids[c.wllname] = txid
                except:
                    continue

    def get_rain_scale_factor (self, collector_type):
        return rain_collector_scale.get (collector_type, None)

    def get_condition (self, data, condition):
        if (self.txids[condition], condition) in data.keys ():
            return data[self.txids[condition],condition]
        for tx in self.all_txids:
            if (tx,condition) in data.keys():
                return data[tx,condition]
        return None

    def parse_packet (self, json_data):
        # Create the new packet
        pkt = {
            'dateTime': json_data['ts'],
            'usUnits': weewx.US
        }

        # Store JSON data into a normal dictionary for later processing
        # This allows us to pick the "best" transmitter ID
        data = dict()
        # Read packet into data array
        for c in json_data['conditions']:
            record_type = c['data_structure_type']
            if record_type in (1,2):
                txid = c['txid']
            elif record_type == 3:
                txid = 'B'
            elif record_type == 4:
                txid = 'I'
            for k,v in c.items():
                # For rain_size in packet, calculate rain scale and place it into driver object
                if k == 'rain_size' and txid == self.txids["rainfall_year"]:
                    r = self.get_rain_scale_factor (v)
                    if r:
                        self.rain_scale_factor = r
                    continue
                data[txid,k] = v

        for metric, info in self.sensor_info.items():
            value = self.get_condition (data, info.wllname)
            if value != None:
                value *= info.factor
                if info.function:
                    value = info.function(self, data, value)
                pkt.update ({metric : value})
        return pkt

    def genLoopPackets (self):
        while True:
            try:
                try:
                    response = requests.get(self.service_url)
                except Exception as exception:
                    log_err("Error connecting to the WeatherLink Live device at {0}.".format(self.host))
                    log_err(str (exception))
                    time.sleep(2)
                    continue  # Continue without exiting.
                rsp = response.json ()
                _packet = self.parse_packet (rsp['data'])
                yield _packet
            except Exception as exception:
                log_err("Error parsing the WeatherLink Live json data.")
                log_err("%s" % exception)
            time.sleep(self.poll_interval)

# daviswll = DavisWLL()
# daviswll.genLoopPackets()


