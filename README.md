DavisWLL driver for weewx
=========================

This is (yet another) [weewx](https://www.weewx.com) driver for the
[Davis WeatherLink Live data logger](https://www.davisinstruments.com/pages/weatherlink-live).
Why another driver? Several reasons:

* Table-driven, making it easy to add/update without writing a lot of code.
* _Purely_ based off the [Davis WLL v4 API](), and doesn't use streaming packets, so it works even if multicast doesn't.
* Good support for easy sensor <-> transmitter mapping customization.

