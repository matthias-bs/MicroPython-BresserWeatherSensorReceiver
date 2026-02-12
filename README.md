# MicroPython-BresserWeatherSensorReceiver
Bresser 5-in-1/6-in-1/7-in-1 868 MHz Weather Sensor Radio Receiver for MicroPython

## Example Console Output

```
TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
--- RSSI: -82.0 dBm ---
TTTTTTTTTTTTTTTTT
--- RSSI: -72.5 dBm ---
Soil Moisture Sensor: ID: 0x52828827  Type: 4  Channel: 1  Battery: OK  Startup: No
  Temperature: 24.5°C  Moisture: 0%
TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
```

* Each 'T' marks a message reception timeout
* RSSI: Received Signal Strength Indicator
* Common sensor data and sensor type specific measurement values
* Only an RSSI value without subsequent data: unknown or invalid message (message integrity check failed)

## Supported Bresser Sensor Protocols

* **6-in-1 Decoder**
  * Supports weather stations (temperature, humidity, UV, wind, rain)
  * Supports soil moisture sensors
  * Supports pool/spa thermometers
    
* **5-in-1 Decoder**
  * 5-in-1 weather sensors
  * Professional Rain Gauge
    
* **7-in-1 Decoder**
  * 7-in-1/8-in-1 weather sensors
  * Air Quality (PM) sensor
  * CO2 sensor
  * HCHO/VOC sensor
    
* **Lightning Sensor Decoder**
  * Lightning sensor
    
* **Leakage Sensor Decoder** :heavy_check_mark: -- Fully ported
  * Water Leakage sensor


**Sequential Decoder Fallback** -- main.py tries all decoders in sequence until one succeeds
