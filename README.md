DavisWLL driver for weewx
=========================

This is (yet another) [weewx](https://www.weewx.com) driver for the
[Davis WeatherLink Live data logger](https://www.davisinstruments.com/pages/weatherlink-live).
Why another driver? Several reasons:

* Table-driven, making it easy to add/update without writing a lot of code.
* _Purely_ based off the [Davis WLL v4 API](https://weatherlink.github.io/weatherlink-live-local-api/), and doesn't use streaming packets, so it works even if multicast doesn't.
* Good support for easy sensor <-> transmitter mapping customization.

Installing the driver
---------------------



Configuring the driver
----------------------

Testing the driver
------------------

Driver self-tests are in `test_daviswll.py`, and may be run using `pytest`. If `pytest` isn't installed
yet, it can be installed using `pip`.

License
-------

Licensed under the BSD 3-clause license. See the `LICENSE` file in the repository.
