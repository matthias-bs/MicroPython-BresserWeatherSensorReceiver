# Bresser Weather Sensor Decoder Test
#
# https://github.com/matthias-bs/MicroPython-BresserWeatherSensorReceiver
#
from time import sleep_ms
import config
from cc1101 import CC1101
from BresserDecoder import (
    DECODE_INVALID, DECODE_OK, DECODE_SKIP,
    LOG_LEVEL_ERROR, set_log_level,
    BresserDecoder
)


def print_sensor_data(data):
    """
    Print decoded sensor data from a dictionary.
    
    Args:
        data: Dictionary with decoded sensor data
    """
    if data is None:
        return
    
    # Print common fields
    sensor_id = data.get('sensor_id')
    sensor_type = data.get('sensor_type')
    if sensor_id is not None:
        # Prepend sensor type name
        sensor_type_name = BresserDecoder.get_sensor_type_name(sensor_type)
        print(f"{sensor_type_name}: ", end='')
        
        if sensor_id <= 0xFF:
            print(f"ID: 0x{sensor_id:02x}  Type: {sensor_type if sensor_type is not None else 'N/A'}", end='')
        elif sensor_id <= 0xFFFF:
            print(f"ID: 0x{sensor_id:04x}  Type: {sensor_type if sensor_type is not None else 'N/A'}", end='')
        else:
            print(f"ID: 0x{sensor_id:08x}  Type: {sensor_type if sensor_type is not None else 'N/A'}", end='')
        
        if 'channel' in data:
            print(f"  Channel: {data['channel']}", end='')
        
        batt_ok = data.get('battery_ok', False)
        print(f"  Battery: {'OK' if batt_ok else 'Low'}", end='')
        
        startup = data.get('startup', False)
        print(f"  Startup: {'Yes' if startup else 'No'}")
    
    # Print temperature and humidity/moisture
    if 'moisture' in data:
        print(f"  Temperature: {data.get('temp_c', 0):.1f}°C  Moisture: {data['moisture']}%")
    elif 'temp_c' in data and 'humidity' in data:
        print(f"  Temperature: {data['temp_c']:.1f}°C  Humidity: {data['humidity']}%")
    elif 'temp_c' in data:
        print(f"  Temperature: {data['temp_c']:.1f}°C")
    
    # Print UV index
    if 'uv_index' in data and 'light_lux' not in data:
        print(f"  UV Index: {data['uv_index']:.1f}")
    
    # Print wind data
    if 'wind_gust_meter_sec' in data:
        print(f"  Wind: Gust={data['wind_gust_meter_sec']:.1f}m/s  " +
              f"Avg={data['wind_avg_meter_sec']:.1f}m/s  " +
              f"Dir={data['wind_direction_deg']:.1f}°")
    
    # Print rain
    if 'rain_mm' in data:
        print(f"  Rain: {data['rain_mm']:.1f}mm")
    
    # Print light and UV for 7-in-1
    if 'light_lux' in data:
        print(f"  Light: {data['light_lux']:.0f}lux  UV Index: {data.get('uv_index', 0):.1f}")
    
    # Print globe temperature for 8-in-1
    if 'globe_temp_c' in data:
        print(f"  Globe Temperature: {data['globe_temp_c']:.1f}°C")
    
    # Print air quality data
    if 'pm_1_0' in data:
        print(f"  PM1.0: {data['pm_1_0']} µg/m³  " +
              f"PM2.5: {data['pm_2_5']} µg/m³  " +
              f"PM10: {data['pm_10']} µg/m³")
    
    # Print CO2 data
    if 'co2_ppm' in data:
        print(f"  CO2: {data['co2_ppm']} ppm")
    
    # Print HCHO/VOC data
    if 'hcho_ppb' in data:
        print(f"  HCHO: {data['hcho_ppb']} ppb  VOC Level: {data.get('voc_level', 0)}")
    
    # Print lightning data
    if 'strike_count' in data:
        print(f"  Strike Count: {data['strike_count']}  Distance: {data['distance_km']} km")
    
    # Print leakage alarm
    if 'alarm' in data:
        print(f"  Alarm: {'YES' if data['alarm'] else 'NO'}")


def getMessage():
    decode_res = DECODE_INVALID
    
    # Receive data
    #     1. flush RX buffer
    #     2. switch to RX mode
    #     3. wait for expected RX packet or timeout [~500us in this configuration]
    #     4. flush RX buffer
    #     5. switch to standby
    (rcvState, data) = cc1101.receive(27)
    recvData = []
    
    recvData = data
    if rcvState == CC1101.ERR_NONE:
        # Verify last syncword is 1st byte of payload (see setSyncWord() above)
        if recvData[0] == 0xD4:

            print(f"[{recvData[0]:02X}] RSSI: {cc1101.getRSSI():0.1f}")
            
            # Try all decoders in sequence until one succeeds
            # Order: 7-in-1, 6-in-1, 5-in-1, Lightning, Leakage
            decoders = [
                BresserDecoder.decodeBresser7In1Payload,
                BresserDecoder.decodeBresser6In1Payload,
                BresserDecoder.decodeBresser5In1Payload,
                BresserDecoder.decodeBresserLightningPayload,
                BresserDecoder.decodeBresserLeakagePayload
            ]
            
            decode_res = DECODE_INVALID
            sensor_data = None
            for decoder in decoders:
                decode_res, sensor_data = decoder(recvData[1:], 26)
                if decode_res == DECODE_OK or decode_res == DECODE_SKIP:
                    break
            
            # Print the decoded sensor data
            if decode_res == DECODE_OK:
                print_sensor_data(sensor_data)
            
    elif rcvState == CC1101.ERR_RX_TIMEOUT:
        print("T", end='')
        
    else:
        # some other error occurred
        print(f"\nReceive failed: [{rcvState:d}]")
        
    return decode_res


if __name__ == "__main__":
    # Set log level to ERROR (only show errors, not warnings)
    set_log_level(LOG_LEVEL_ERROR)
    
    # Demo the connection to a CC1101 by reading values from the chip

    cc1101 = CC1101(config.SPI_ID, config.SS_PIN, config.GDO0_PIN, config.GDO2_PIN)

    # Read status byte
    status = cc1101.write_command(CC1101.SNOP)
    print("Status byte", hex(status), bin(status))

    # Read version
    version = cc1101.read_register(CC1101.VERSION, CC1101.STATUS_REGISTER)
    print("VERSION", hex(version))
    
    # Configuration
    state = cc1101.config()
    print("config():", state)
    
    state = cc1101.setFrequency(868.3)
    print("setFrequency():", state)
    
    state = cc1101.setBitRate(8.21)
    print("setBitrate():", state)
    
    state = cc1101.setRxBandwidth(270.0)
    print("setRxBandwidth():", state)
    
    state = cc1101.setFrequencyDeviation(57.136417)
    print("setFrequencyDeviation():", state)
    
    state = cc1101.setOutputPower(10)
    print("setOutputPower():", state)
    
    state = cc1101.setPreambleLength(32)
    print("setPreambleLength():", state)
    
    state = cc1101.setCrcFiltering(False)
    print("setCrcFiltering():", state)
    
    state = cc1101.fixedPacketLengthMode(27)
    print("fixedPacketLengthMode():", state)
    
    state = cc1101.setSyncWord(0xAA, 0x2D, 0, False)
    print("setSyncWord():", state)
    
    # Read all configuration registers (for debugging)
    regs = {
        "IOCFG0": CC1101.IOCFG0,
        "IOCFG1": CC1101.IOCFG1,
        "IOCFG2": CC1101.IOCFG2,
        "FREQ0": CC1101.FREQ0,
        "FREQ1": CC1101.FREQ1,
        "FREQ2": CC1101.FREQ2,
        "MDMCFG0": CC1101.MDMCFG0,
        "MDMCFG1": CC1101.MDMCFG1,
        "MDMCFG2": CC1101.MDMCFG2,
        "MDMCFG3": CC1101.MDMCFG3,
        "MDMCFG4": CC1101.MDMCFG4,
        "DEVIATN": CC1101.DEVIATN,
        "PKTCTRL0": CC1101.PKTCTRL0,
        "PKTCTRL1": CC1101.PKTCTRL1,
        "PKTLEN": CC1101.PKTLEN,
        "SYNC0": CC1101.SYNC0,
        "SYNC1": CC1101.SYNC1,
        "MCSM0": CC1101.MCSM0,
        "FIFOTHR": CC1101.FIFOTHR
    }
    
    for name, addr in regs.items():
        print(name, hex(cc1101.read_register(addr)))
    
    # Try to receive and decode sensor data
    while True:
        res = getMessage()
        sleep_ms(10)
