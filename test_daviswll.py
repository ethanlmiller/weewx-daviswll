#
# Test code for daviswll.py
#
# Run tests using pytest (pip3 install pytest)
#
# IMPORTANT: must set PYTHONPATH so that weewx can be imported properly.
# For example:
# export PYTHONPATH=/home/weewx/bin

from daviswll import DavisWLL
from math import isclose

readings = (
    ({'did': '001D0A71262A',
      'ts': 1634925911,
      'conditions': [{'lsid': 330316, 'data_structure_type': 1, 'txid': 5, 'temp': 57.9, 'hum': 97.6,
                    'dew_point': 57.2, 'wet_bulb': 57.5, 'heat_index': 58.7, 'wind_chill': 57.9,
                    'thw_index': 58.7, 'thsw_index': 64.4, 'wind_speed_last': 2.0, 'wind_dir_last': 200,
                    'wind_speed_avg_last_1_min': 1.18, 'wind_dir_scalar_avg_last_1_min': 360,
                    'wind_speed_avg_last_2_min': 1.5, 'wind_dir_scalar_avg_last_2_min': 360,
                    'wind_speed_hi_last_2_min': 2.0, 'wind_dir_at_hi_speed_last_2_min': 360,
                    'wind_speed_avg_last_10_min': 1.56, 'wind_dir_scalar_avg_last_10_min': 360,
                    'wind_speed_hi_last_10_min': 5.0, 'wind_dir_at_hi_speed_last_10_min': 180,
                    'rain_size': 1, 'rain_rate_last': 0, 'rain_rate_hi': 0, 'rainfall_last_15_min': 0,
                    'rain_rate_hi_last_15_min': 0, 'rainfall_last_60_min': 0, 'rainfall_last_24_hr': 44,
                    'rain_storm': 73, 'rain_storm_start_at': 1634730060,
                    'solar_rad': 378, 'uv_index': 1.8, 'rx_state': 0, 'trans_battery_flag': 0,
                    'rainfall_daily': 44, 'rainfall_monthly': 77, 'rainfall_year': 986,
                    'rain_storm_last': 4, 'rain_storm_last_start_at': 1634521081, 'rain_storm_last_end_at': 1634648461},
                   {'lsid': 330311, 'data_structure_type': 4, 'temp_in': 70.9, 'hum_in': 57.4, 'dew_point_in': 55.1,
                    'heat_index_in': 70.1}, {'lsid': 330310, 'data_structure_type': 3, 'bar_sea_level': 30.074,
                    'bar_trend': 0.054, 'bar_absolute': 29.755}]
    },
    {
        'outTemp': 57.9, 'outHumidity': 97.6,
        'windSpeed': 2.0, 'windDir': 200, 'windGust': 5.0, 'windGustDir': 180,
        'rain': 0, 'rainRate': 0,
        'radiation': 378, 'UV': 1.8, 'txBatteryStatus': 0,    }),
    ({'did': '001D0A71262A',
          'ts': 1634926765,
          'conditions': [{'lsid': 330316, 'data_structure_type': 1, 'txid': 5, 'temp': 57.7, 'hum': 97.2,
                        'dew_point': 56.9, 'wet_bulb': 57.2, 'heat_index': 58.4, 'wind_chill': 57.7,
                        'thw_index': 58.4, 'thsw_index': 64.5, 'wind_speed_last': 2.0, 'wind_dir_last': 352,
                        'wind_speed_avg_last_1_min': 0.5, 'wind_dir_scalar_avg_last_1_min': 360,
                        'wind_speed_avg_last_2_min': 0.93, 'wind_dir_scalar_avg_last_2_min': 360,
                        'wind_speed_hi_last_2_min': 2.0, 'wind_dir_at_hi_speed_last_2_min': 360,
                        'wind_speed_avg_last_10_min': 1.56, 'wind_dir_scalar_avg_last_10_min': 360,
                        'wind_speed_hi_last_10_min': 4.0, 'wind_dir_at_hi_speed_last_10_min': 15,
                        'rain_size': 1, 'rain_rate_last': 2, 'rain_rate_hi': 0, 'rainfall_last_15_min': 0,
                        'rain_rate_hi_last_15_min': 0, 'rainfall_last_60_min': 0, 'rainfall_last_24_hr': 44,
                        'rain_storm': 73, 'rain_storm_start_at': 1634730060,
                        'solar_rad': 445, 'uv_index': 2.1, 'rx_state': 0, 'trans_battery_flag': 0,
                        'rainfall_daily': 45, 'rainfall_monthly': 78, 'rainfall_year': 987,
                        'rain_storm_last': 4, 'rain_storm_last_start_at': 1634521081, 'rain_storm_last_end_at': 1634648461},
                       {'lsid': 330311, 'data_structure_type': 4, 'temp_in': 70.8, 'hum_in': 57.6, 'dew_point_in': 55.1,
                        'heat_index_in': 70.0}, {'lsid': 330310, 'data_structure_type': 3, 'bar_sea_level': 30.076,
                        'bar_trend': 0.052, 'bar_absolute': 29.757}]
    },
    {'outTemp': 57.7, 'outHumidity': 97.2, 'heatindex': 58.4, 'windchill': 57.7,
     'windSpeed': 2.0, 'windDir': 352, 'windGust': 4.0, 'windGustDir': 15,
     'rain': 0.01, 'rainRate': 0.02,
     'radiation': 445, 'UV': 2.1, 'txBatteryStatus': 0,
    }
    )
)

def test_packet_handler ():
    config = {
        'host' : '10.203.213.224',
        'weather_transmitter_id' : 5,
        'soil_transmitter_id' : 5,
    }
    drvr = DavisWLL (**config)

    for r in readings:
        rsp, desired = r
        pkt = drvr.parse_packet (rsp)
        for k in desired.keys():
            assert isclose (desired[k], pkt[k], rel_tol=1e-6)
