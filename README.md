# MicroPython-BresserWeatherSensorReceiver
Bresser 5-in-1/6-in-1 868 MHz Weather Sensor Radio Receiver for MicroPython

Work in progress...

Current status:
* CC1101 initialization :heavy_check_mark: -- Compared register contents with [BresserWeatherSensorReceiver](https://github.com/matthias-bs/BresserWeatherSensorReceiver)

* Radio Message Reception :x: -- Seems to fail to detect start of frame

* 6-in-1 Protocol Decoder :heavy_check_mark: -- Fully ported from [rtl_433](https://github.com/merbanan/rtl_433)
  * Supports weather stations (temperature, humidity, UV, wind, rain)
  * Supports soil moisture sensors
  * Supports pool/spa thermometers
  * Includes LFSR-16 digest validation
  * Tested with sample payloads
    
* 5-in-1 Protocol Decoder :hourglass: -- Not ported yet
