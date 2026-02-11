# MicroPython-BresserWeatherSensorReceiver
Bresser 5-in-1/6-in-1 868 MHz Weather Sensor Radio Receiver for MicroPython

Work in progress...

Current status:
* CC1101 initialization :heavy_check_mark: -- Compared register contents with [BresserWeatherSensorReceiver](https://github.com/matthias-bs/BresserWeatherSensorReceiver)

* Radio Message Reception :x: -- Seems to fail to detect start of frame

* Protocol Decoders:
  * **6-in-1 Decoder** :heavy_check_mark: -- Fully ported from [rtl_433](https://github.com/merbanan/rtl_433)
    * Supports weather stations (temperature, humidity, UV, wind, rain)
    * Supports soil moisture sensors
    * Supports pool/spa thermometers
    * Includes LFSR-16 digest validation
    * Tested with sample payloads
    
  * **5-in-1 Decoder** :heavy_check_mark: -- Fully ported from [rtl_433](https://github.com/merbanan/rtl_433)
    * Supports Bresser 5-in-1 weather sensors
    * Supports Bresser Professional Rain Gauge
    * Includes parity and checksum validation
    
  * **7-in-1 Decoder** :heavy_check_mark: -- Fully ported from [rtl_433](https://github.com/merbanan/rtl_433)
    * Supports Bresser 7-in-1/8-in-1 weather sensors
    * Supports Air Quality (PM) sensors
    * Supports CO2 sensors
    * Supports HCHO/VOC sensors
    * Includes data de-whitening and LFSR-16 digest validation
    
  * **Lightning Sensor Decoder** :heavy_check_mark: -- Fully ported
    * Supports Bresser Lightning sensor
    * Includes data de-whitening and LFSR-16 digest validation
    * Tested with sample payloads
    
  * **Leakage Sensor Decoder** :heavy_check_mark: -- Fully ported
    * Supports Bresser Water Leakage sensor
    * Includes CRC16/XMODEM validation
    * Tested with sample payloads

* **Sequential Decoder Fallback** :heavy_check_mark: -- main.py tries all decoders in sequence until one succeeds
