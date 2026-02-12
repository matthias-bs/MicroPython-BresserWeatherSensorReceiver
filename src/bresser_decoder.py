import sys

if sys.implementation.name != "micropython":
    const = lambda x: x

DECODE_INVALID  = const(0)
DECODE_OK       = const(1)
DECODE_PAR_ERR  = const(2)
DECODE_CHK_ERR  = const(3)
DECODE_DIG_ERR  = const(4)
DECODE_SKIP     = const(5)
DECODE_FULL     = const(6)

# Log levels - MicroPython-compatible
LOG_LEVEL_NONE = const(0)
LOG_LEVEL_ERROR = const(1)
LOG_LEVEL_WARNING = const(2)
LOG_LEVEL_INFO = const(3)
LOG_LEVEL_DEBUG = const(4)

# Global log level
log_level = LOG_LEVEL_ERROR

def set_log_level(level):
    """Set the global log level."""
    global log_level
    log_level = level

def log_message(level, msg):
    """Print a log message if the log level is sufficient."""
    if level <= log_level:
        print(msg)


class BresserDecoder:
    """
    Bresser Weather Sensor Decoder class.
    
    This class provides methods to decode various Bresser weather sensor payloads,
    including 5-in-1, 6-in-1, 7-in-1, Lightning, and Leakage sensors.
    """
    
    MOISTURE_MAP = [0, 7, 13, 20, 27, 33, 40, 47, 53, 60, 67, 73, 80, 87, 93, 99]
    
    @staticmethod
    def lfsr_digest16(message, num_bytes, gen, key):
        """
        Calculate LFSR-16 digest.
        
        Ported from rtl_433 project:
        https://github.com/merbanan/rtl_433/blob/master/src/util.c
        
        Args:
            message: Message buffer
            num_bytes: Number of bytes to process
            gen: Generator polynomial
            key: Initial key value
            
        Returns:
            LFSR-16 digest
        """
        _sum = 0
        for k in range(num_bytes):
            data = message[k]
            for i in range(7, -1, -1):
                # if data bit is set then xor with key
                if (data >> i) & 1:
                    _sum ^= key
                
                # roll the key right (actually the lsb is dropped here)
                # and apply the gen (needs to include the dropped lsb as msb)
                if key & 1:
                    key = (key >> 1) ^ gen
                else:
                    key = (key >> 1)
        return _sum
    
    @staticmethod
    def add_bytes(message, num_bytes):
        """
        Calculate sum of message bytes.
        
        Ported from rtl_433 project:
        https://github.com/merbanan/rtl_433/blob/master/src/util.c
        
        Args:
            message: Message buffer
            num_bytes: Number of bytes to sum
            
        Returns:
            Sum of all bytes
        """
        result = 0
        
        for i in range(num_bytes):
            result += message[i]
        
        return result
    
    @staticmethod
    def crc16(message, num_bytes, polynomial, init):
        """
        Calculate CRC16 of message bytes.
        
        Ported from rtl_433 project:
        https://github.com/merbanan/rtl_433/blob/master/src/util.c
        
        Args:
            message: Message buffer
            num_bytes: Number of bytes
            polynomial: Polynomial
            init: Initial value
            
        Returns:
            CRC16 of all message bytes
        """
        remainder = init
        
        for byte_idx in range(num_bytes):
            remainder ^= message[byte_idx] << 8
            for bit in range(8):
                if remainder & 0x8000:
                    remainder = (remainder << 1) ^ polynomial
                else:
                    remainder = (remainder << 1)
                # Keep it 16-bit
                remainder &= 0xFFFF
        
        return remainder
    
    @staticmethod
    def get_sensor_type_name(sensor_type):
        """
        Get human-readable sensor type name from sensor type number.
        
        Args:
            sensor_type: Numeric sensor type value
            
        Returns:
            str: Human-readable sensor type name
        """
        if sensor_type is None:
            return "Unknown"
        
        sensor_type_map = {
            1: "Weather Station",
            3: "Pool/Spa Thermometer",
            4: "Soil Moisture Sensor",
            5: "Leakage Sensor",
            8: "Air Quality (PM) Sensor",
            9: "Lightning Sensor",
            10: "CO2 Sensor",
            11: "HCHO/VOC Sensor",
            12: "Weather Station (3-in-1)",
            13: "Weather Station (8-in-1)",
            # Professional Rain Gauge can have sensor types 0x39, 0x3A, or 0x3B
            # (see bresser_5in1 decoder line 415-417)
            0x39: "Professional Rain Gauge",
            0x3A: "Professional Rain Gauge",
            0x3B: "Professional Rain Gauge"
        }
        return sensor_type_map.get(sensor_type, f"Unknown (Type {sensor_type})")
    
    @staticmethod
    def decodeBresser6In1Payload(msg, _msgSize):
        """
        Decode Bresser 6-in-1 weather sensor payload.
        
        Based on rtl_433 decoder:
        https://github.com/merbanan/rtl_433/blob/master/src/devices/bresser_6in1.c
        
        Supports:
        - Bresser Weather Center 7-in-1 indoor sensor
        - Bresser new 5-in-1 sensors
        - Froggit WH6000 sensors
        - Ventus C8488A (W835)
        - Bresser 3-in-1 Professional Wind Gauge / Anemometer PN 7002531
        - Bresser Pool / Spa Thermometer PN 7009973
        - Bresser Soil Moisture Sensor
        
        Returns:
            tuple: (status_code, data_dict or None)
                status_code: DECODE_OK, DECODE_DIG_ERR, or DECODE_CHK_ERR
                data_dict: Dictionary with decoded data if successful, None otherwise
        """
        # Sensor type constants
        SENSOR_TYPE_WEATHER1 = 1
        SENSOR_TYPE_POOL_THERMO = 3
        SENSOR_TYPE_SOIL = 4
        
        # LFSR-16 digest, generator 0x8810 init 0x5412
        chkdgst = (msg[0] << 8) | msg[1]
        digest  = BresserDecoder.lfsr_digest16(msg[2:], 15, 0x8810, 0x5412)

        if (chkdgst != digest):
            log_message(LOG_LEVEL_WARNING, f"Digest check failed - [0x{chkdgst:04x}] vs [0x{digest:04x}] (0x{chkdgst ^ digest:04x})")
            return (DECODE_DIG_ERR, None)

        # Checksum, add with carry
        # msg[2] to msg[17]
        _sum = BresserDecoder.add_bytes(msg[2:], 16)
        if ((_sum & 0xff) != 0xff):
            log_message(LOG_LEVEL_WARNING, "Checksum failed")
            return (DECODE_CHK_ERR, None)
        
        sid   = (msg[2] << 24) | (msg[3] << 16) | (msg[4] << 8) | msg[5]
        stype = msg[6] >> 4
        ch    = msg[6] & 7
        startup = ((msg[6] & 0x8) == 0)
        flags = msg[16] & 0x0f
        
        # Per-message status flags
        temp_ok = False
        humidity_ok = False
        uv_ok = False
        wind_ok = False
        rain_ok = False
        moisture_ok = False
        
        # Initialize variables
        humidity = 0
        uv = 0.0
        batt_ok = False
        wind_gust = 0.0
        wind_avg = 0.0
        wind_dir = 0.0
        moisture = 0
        
        # Check for 3-in-1 Professional Wind Gauge
        # Temperature below -50°C indicates incorrect sign bit interpretation
        f_3in1 = False
        
        # temperature, humidity(, uv) - shared with rain counter
        temp_ok = (flags == 0)
        humidity_ok = (flags == 0)
        if temp_ok:
            sign     = (msg[13] >> 3) & 1
            temp_raw = (msg[12] >> 4) * 100 + (msg[12] & 0x0f) * 10 + (msg[13] >> 4)
            temp     = ((temp_raw - 1000) * 0.1) if sign else (temp_raw * 0.1)
            
            # Correction for Bresser 3-in-1 Professional Wind Gauge / Anemometer
            # The temperature range is -40...+60°C
            # If temperature is below -50°C, the sign bit is inverted
            if temp < -50.0:
                temp = temp_raw * 0.1
                f_3in1 = True
                
            batt_ok  = (msg[13] >> 1) & 1
            humidity = (msg[14] >> 4) * 10 + (msg[14] & 0x0f)
            
            # apparently ff01 or 0000 if not available, ???0 if valid, inverted BCD
            uv_ok  = ((~msg[15] & 0xff) <= 0x99) and ((~msg[16] & 0xf0) <= 0x90) and (not f_3in1)
            if uv_ok:
                uv_raw = ((~msg[15] & 0xf0) >> 4) * 100 + (~msg[15] & 0x0f) * 10 + ((~msg[16] & 0xf0) >> 4)
                uv     = uv_raw * 0.1
        
        # invert 3 bytes wind speeds
        msg7 = msg[7] ^ 0xff
        msg8 = msg[8] ^ 0xff
        msg9 = msg[9] ^ 0xff
        
        wind_ok = (msg7 <= 0x99) and (msg8 <= 0x99) and (msg9 <= 0x99)
        if wind_ok:
            gust_raw = (msg7 >> 4) * 100 + (msg7 & 0x0f) * 10 + (msg8 >> 4)
            wavg_raw = (msg9 >> 4) * 100 + (msg9 & 0x0f) * 10 + (msg8 & 0x0f)
            wind_dir_raw = ((msg[10] & 0xf0) >> 4) * 100 + (msg[10] & 0x0f) * 10 + ((msg[11] & 0xf0) >> 4)
            
            wind_gust = gust_raw * 0.1
            wind_avg  = wavg_raw * 0.1
            wind_dir  = float(wind_dir_raw)
        
        # rain counter, inverted 3 bytes BCD - shared with temp/hum
        msg12 = msg[12] ^ 0xff
        msg13 = msg[13] ^ 0xff
        msg14 = msg[14] ^ 0xff
        
        rain_ok = (flags == 1) and (stype == SENSOR_TYPE_WEATHER1)
        if rain_ok:
            rain_raw  =   (msg12 >> 4) * 100000 + (msg12 & 0x0f) * 10000 \
                        + (msg13 >> 4) * 1000   + (msg13 & 0x0f) * 100 \
                        + (msg14 >> 4) * 10     + (msg14 & 0x0f)
            rain_mm   = rain_raw * 0.1
        
        # Pool / Spa thermometer
        if stype == SENSOR_TYPE_POOL_THERMO:
            humidity_ok = False
        
        # the moisture sensor might present valid readings but does not have the hardware
        if stype == SENSOR_TYPE_SOIL:
            wind_ok = False
            uv_ok   = False
        
        if stype == SENSOR_TYPE_SOIL and temp_ok and humidity >= 1 and humidity <= 16:
            moisture_ok = True
            humidity_ok = False
            moisture = BresserDecoder.MOISTURE_MAP[humidity - 1]
        
        # Build result dictionary
        result = {
            'sensor_id': sid,
            'sensor_type': stype,
            'channel': ch,
            'battery_ok': batt_ok,
            'startup': startup
        }
        
        if temp_ok:
            result['temp_c'] = temp
        if humidity_ok:
            result['humidity'] = humidity
        if moisture_ok:
            result['moisture'] = moisture
        if uv_ok:
            result['uv_index'] = uv
        if wind_ok:
            result['wind_gust_meter_sec'] = wind_gust
            result['wind_avg_meter_sec'] = wind_avg
            result['wind_direction_deg'] = wind_dir
        if rain_ok:
            result['rain_mm'] = rain_mm
        
        return (DECODE_OK, result)
    
    @staticmethod
    def decodeBresser5In1Payload(msg, msgSize):
        """
        Decode Bresser 5-in-1 weather sensor payload.
        
        Based on rtl_433 decoder:
        https://github.com/merbanan/rtl_433/blob/master/src/devices/bresser_5in1.c
        
        Supports:
        - Bresser 5-in-1 weather sensors
        - Bresser Professional Rain Gauge
        
        Returns:
            tuple: (status_code, data_dict or None)
                status_code: DECODE_OK, DECODE_PAR_ERR, or DECODE_CHK_ERR
                data_dict: Dictionary with decoded data if successful, None otherwise
        """
        # First 13 bytes need to match inverse of last 13 bytes
        for col in range(msgSize // 2):
            if (msg[col] ^ msg[col + 13]) != 0xff:
                log_message(LOG_LEVEL_WARNING, f"Parity wrong at column {col}")
                return (DECODE_PAR_ERR, None)
        
        # Verify checksum (number bits set in bytes 14-25)
        bits_set = 0
        expected_bits_set = msg[13]
        
        for p in range(14, msgSize):
            current_byte = msg[p]
            while current_byte:
                bits_set += (current_byte & 1)
                current_byte >>= 1
        
        if bits_set != expected_bits_set:
            log_message(LOG_LEVEL_WARNING, f"Checksum wrong - actual [0x{bits_set:02X}] != [0x{expected_bits_set:02X}]")
            return (DECODE_CHK_ERR, None)
        
        sid = msg[14]
        stype = msg[15] & 0x7F
        startup = ((msg[15] & 0x80) == 0)
        batt_ok = not (msg[25] & 0x80)
        
        # Temperature in BCD format
        temp_raw = (msg[20] & 0x0f) + ((msg[20] & 0xf0) >> 4) * 10 + (msg[21] & 0x0f) * 100
        if msg[25] & 0x0f:
            temp_raw = -temp_raw
        temp_c = temp_raw * 0.1
        
        # Humidity in BCD format
        humidity = (msg[22] & 0x0f) + ((msg[22] & 0xf0) >> 4) * 10
        humidity_ok = (msg[22] & 0x0f) <= 9
        temp_ok = (msg[20] & 0x0f) <= 9
        
        # Wind direction and speed
        wind_direction_raw = ((msg[17] & 0xf0) >> 4) * 225
        wind_direction_deg = wind_direction_raw * 0.1
        gust_raw = ((msg[17] & 0x0f) << 8) + msg[16]
        wind_gust = gust_raw * 0.1
        wind_raw = (msg[18] & 0x0f) + ((msg[18] & 0xf0) >> 4) * 10 + (msg[19] & 0x0f) * 100
        wind_avg = wind_raw * 0.1
        
        # Rain in BCD format
        rain_raw = (msg[23] & 0x0f) + ((msg[23] & 0xf0) >> 4) * 10 + (msg[24] & 0x0f) * 100 + ((msg[24] & 0xf0) >> 4) * 1000
        rain_mm = rain_raw * 0.1
        
        # Check if the message is from a Bresser Professional Rain Gauge
        # The sensor type for the Rain Gauge can be either 0x39, 0x3A, or 0x3B
        wind_ok = True
        if (stype >= 0x39) and (stype <= 0x3b):
            # Rescale the rain sensor readings
            rain_mm *= 2.5
            humidity_ok = False
            wind_ok = False
        
        # Build result dictionary
        result = {
            'sensor_id': sid,
            'sensor_type': stype,
            'battery_ok': batt_ok,
            'startup': startup,
            'rain_mm': rain_mm
        }
        
        if temp_ok:
            result['temp_c'] = temp_c
        if humidity_ok:
            result['humidity'] = humidity
        if wind_ok:
            result['wind_gust_meter_sec'] = wind_gust
            result['wind_avg_meter_sec'] = wind_avg
            result['wind_direction_deg'] = wind_direction_deg
        
        return (DECODE_OK, result)
    
    @staticmethod
    def decodeBresser7In1Payload(msg, msgSize):
        """
        Decode Bresser 7-in-1 weather sensor payload.
        
        Based on rtl_433 decoder:
        https://github.com/merbanan/rtl_433/blob/master/src/devices/bresser_7in1.c
        
        Supports:
        - Bresser 7-in-1 weather sensors
        - Bresser 8-in-1 weather sensors (with globe temperature)
        - Air Quality (PM) sensors
        - CO2 sensors
        - HCHO/VOC sensors
        
        Returns:
            tuple: (status_code, data_dict or None)
                status_code: DECODE_OK or DECODE_DIG_ERR
                data_dict: Dictionary with decoded data if successful, None otherwise
        """
        # Sensor type constants (from rtl_433 bresser_7in1.c)
        SENSOR_TYPE_WEATHER1 = 1
        SENSOR_TYPE_AIR_PM = 8
        SENSOR_TYPE_CO2 = 10
        SENSOR_TYPE_HCHO_VOC = 11
        SENSOR_TYPE_WEATHER3 = 12
        SENSOR_TYPE_WEATHER8 = 13
        
        # Sanity check
        if msg[21] == 0x00:
            log_message(LOG_LEVEL_WARNING, "Warning: Data sanity check failed (msg[21] == 0x00)")
        
        # Extract sensor type, startup flag, and channel from RAW data (before de-whitening)
        stype = msg[6] >> 4
        startup = (msg[6] & 0x08) == 0x00
        ch = msg[6] & 0x07
        
        # Data de-whitening
        msgw = bytearray(msgSize)
        for i in range(msgSize):
            msgw[i] = msg[i] ^ 0xaa
        
        # LFSR-16 digest, generator 0x8810 key 0xba95 final xor 0x6df1
        chkdgst = (msgw[0] << 8) | msgw[1]
        digest = BresserDecoder.lfsr_digest16(msgw[2:], 23, 0x8810, 0xba95)
        if (chkdgst ^ digest) != 0x6df1:
            log_message(LOG_LEVEL_WARNING, f"Digest check failed - [0x{chkdgst:04X}] vs [0x{digest:04X}] (0x{chkdgst ^ digest:04X})")
            return (DECODE_DIG_ERR, None)
        
        sid = (msgw[2] << 8) | msgw[3]
        
        flags = msgw[15] & 0x0f
        batt_ok = not ((flags & 0x06) == 0x06)
        
        # Build result dictionary with common fields
        result = {
            'sensor_id': sid,
            'sensor_type': stype,
            'channel': ch,
            'battery_ok': batt_ok,
            'startup': startup
        }
        
        if (stype == SENSOR_TYPE_WEATHER1) or (stype == SENSOR_TYPE_WEATHER3) or (stype == SENSOR_TYPE_WEATHER8):
            # Weather sensor data
            wind_light_ok = (stype != SENSOR_TYPE_WEATHER3)
            
            wdir = (msgw[4] >> 4) * 100 + (msgw[4] & 0x0f) * 10 + (msgw[5] >> 4)
            wgst_raw = (msgw[7] >> 4) * 100 + (msgw[7] & 0x0f) * 10 + (msgw[8] >> 4)
            wavg_raw = (msgw[8] & 0x0f) * 100 + (msgw[9] >> 4) * 10 + (msgw[9] & 0x0f)
            rain_raw = (msgw[10] >> 4) * 100000 + (msgw[10] & 0x0f) * 10000 + \
                       (msgw[11] >> 4) * 1000 + (msgw[11] & 0x0f) * 100 + \
                       (msgw[12] >> 4) * 10 + (msgw[12] & 0x0f)
            rain_mm = rain_raw * 0.1
            
            temp_raw = (msgw[14] >> 4) * 100 + (msgw[14] & 0x0f) * 10 + (msgw[15] >> 4)
            temp_c = temp_raw * 0.1
            if temp_raw > 600:
                temp_c = (temp_raw - 1000) * 0.1
            
            humidity = (msgw[16] >> 4) * 10 + (msgw[16] & 0x0f)
            
            lght_raw = (msgw[17] >> 4) * 100000 + (msgw[17] & 0x0f) * 10000 + \
                       (msgw[18] >> 4) * 1000 + (msgw[18] & 0x0f) * 100 + \
                       (msgw[19] >> 4) * 10 + (msgw[19] & 0x0f)
            light_lux = float(lght_raw)
            
            uv_raw = (msgw[20] >> 4) * 100 + (msgw[20] & 0x0f) * 10 + (msgw[21] >> 4)
            uv_index = uv_raw * 0.1
            
            result['temp_c'] = temp_c
            result['humidity'] = humidity
            result['rain_mm'] = rain_mm
            
            if wind_light_ok:
                wind_gust = wgst_raw * 0.1
                wind_avg = wavg_raw * 0.1
                result['wind_gust_meter_sec'] = wind_gust
                result['wind_avg_meter_sec'] = wind_avg
                result['wind_direction_deg'] = float(wdir)
                result['light_lux'] = light_lux
                result['uv_index'] = uv_index
            
            # 8-in-1 sensor has globe temperature
            if stype == SENSOR_TYPE_WEATHER8:
                if (msgw[23] >> 4) < 10:
                    tglobe_c = (msgw[22] >> 4) * 10 + (msgw[22] & 0x0f) + (msgw[23] >> 4) * 0.1
                    result['globe_temp_c'] = tglobe_c
        
        elif stype == SENSOR_TYPE_AIR_PM:
            # Air Quality (Particulate Matter) sensor
            pm_1_0 = (msgw[8] & 0x0f) * 1000 + (msgw[9] >> 4) * 100 + (msgw[9] & 0x0f) * 10 + (msgw[10] >> 4)
            pm_2_5 = (msgw[10] & 0x0f) * 1000 + (msgw[11] >> 4) * 100 + (msgw[11] & 0x0f) * 10 + (msgw[12] >> 4)
            pm_10 = (msgw[12] & 0x0f) * 1000 + (msgw[13] >> 4) * 100 + (msgw[13] & 0x0f) * 10 + (msgw[14] >> 4)
            result['pm_1_0'] = pm_1_0
            result['pm_2_5'] = pm_2_5
            result['pm_10'] = pm_10
        
        elif stype == SENSOR_TYPE_CO2:
            # CO2 sensor
            co2_ppm = ((msgw[4] & 0xf0) >> 4) * 1000 + (msgw[4] & 0x0f) * 100 + \
                      ((msgw[5] & 0xf0) >> 4) * 10 + (msgw[5] & 0x0f)
            result['co2_ppm'] = co2_ppm
        
        elif stype == SENSOR_TYPE_HCHO_VOC:
            # HCHO/VOC sensor
            hcho_ppb = ((msgw[4] & 0xf0) >> 4) * 1000 + (msgw[4] & 0x0f) * 100 + \
                       ((msgw[5] & 0xf0) >> 4) * 10 + (msgw[5] & 0x0f)
            voc_level = msgw[22] & 0x0f
            result['hcho_ppb'] = hcho_ppb
            result['voc_level'] = voc_level
        
        return (DECODE_OK, result)
    
    @staticmethod
    def decodeBresserLightningPayload(msg, msgSize):
        """
        Decode Bresser Lightning sensor payload.
        
        The data has a whitening of 0xaa.
        LFSR-16 digest, generator 0x8810 key 0xabf9 with a final xor 0x899e
        
        Returns:
            tuple: (status_code, data_dict or None)
                status_code: DECODE_OK or DECODE_DIG_ERR
                data_dict: Dictionary with decoded data if successful, None otherwise
        """
        # Extract sensor type and startup from RAW data (before de-whitening)
        stype = msg[6] >> 4
        startup = (msg[6] & 0x8) == 0x00
        
        # Data de-whitening
        msgw = bytearray(msgSize)
        for i in range(msgSize):
            msgw[i] = msg[i] ^ 0xaa
        
        # LFSR-16 digest, generator 0x8810 key 0xabf9 with a final xor 0x899e
        chk = (msgw[0] << 8) | msgw[1]
        digest = BresserDecoder.lfsr_digest16(msgw[2:], 8, 0x8810, 0xabf9)
        if ((chk ^ digest) != 0x899e):
            log_message(LOG_LEVEL_WARNING, f"Digest check failed - [0x{chk:04X}] vs [0x{digest:04X}] (0x{chk ^ digest:04X})")
            return (DECODE_DIG_ERR, None)
        
        sid = (msgw[2] << 8) | msgw[3]
        
        # Counter encoded as BCD with most significant digit counting up to 15!
        # Maximum value: 1599
        strike_count = (msgw[4] >> 4) * 100 + (msgw[4] & 0xf) * 10 + (msgw[5] >> 4)
        batt_ok = not ((msgw[5] & 0x08) == 0x00)
        distance_km = msgw[7]
        
        result = {
            'sensor_id': sid,
            'sensor_type': stype,
            'battery_ok': batt_ok,
            'startup': startup,
            'strike_count': strike_count,
            'distance_km': distance_km
        }
        
        return (DECODE_OK, result)
    
    @staticmethod
    def decodeBresserLeakagePayload(msg, _msgSize):
        """
        Decode Bresser Water Leakage sensor payload.
        
        Uses CRC16/XMODEM for validation.
        
        Returns:
            tuple: (status_code, data_dict or None)
                status_code: DECODE_OK, DECODE_CHK_ERR, or DECODE_INVALID
                data_dict: Dictionary with decoded data if successful, None otherwise
        """
        SENSOR_TYPE_LEAKAGE = 5
        
        # Verify CRC (CRC16/XMODEM)
        crc_act = BresserDecoder.crc16(msg[2:], 5, 0x1021, 0x0000)
        crc_exp = (msg[0] << 8) | msg[1]
        if crc_act != crc_exp:
            log_message(LOG_LEVEL_WARNING, f"CRC16 check failed - [0x{crc_act:04X}] vs [0x{crc_exp:04X}]")
            return (DECODE_CHK_ERR, None)
        
        sid = ((msg[2] << 24) | (msg[3] << 16) | (msg[4] << 8) | msg[5])
        stype = msg[6] >> 4
        ch = msg[6] & 0x7
        startup = (msg[6] & 0x8) == 0x00
        alarm = (msg[7] & 0x80) == 0x80
        no_alarm = (msg[7] & 0x40) == 0x40
        batt_ok = (msg[7] & 0x30) != 0x00
        
        # Sanity checks
        if (stype != SENSOR_TYPE_LEAKAGE) or (alarm == no_alarm) or (ch == 0):
            return (DECODE_INVALID, None)
        
        result = {
            'sensor_id': sid,
            'sensor_type': stype,
            'channel': ch,
            'battery_ok': batt_ok,
            'startup': startup,
            'alarm': alarm and not no_alarm
        }
        
        return (DECODE_OK, result)

#
# Ported from rtl_433 project - https://github.com/merbanan/rtl_433/blob/master/src/util.c
#
def lfsr_digest16(message, num_bytes, gen, key):
    """Module-level wrapper for backward compatibility."""
    return BresserDecoder.lfsr_digest16(message, num_bytes, gen, key)

#
# Ported from rtl_433 project - https://github.com/merbanan/rtl_433/blob/master/src/util.c
#
def add_bytes(message, num_bytes):
    """Module-level wrapper for backward compatibility."""
    return BresserDecoder.add_bytes(message, num_bytes)

#
# Ported from rtl_433 project - https://github.com/merbanan/rtl_433/blob/master/src/util.c
#
def crc16(message, num_bytes, polynomial, init):
    """Module-level wrapper for backward compatibility."""
    return BresserDecoder.crc16(message, num_bytes, polynomial, init)
    

def get_sensor_type_name(sensor_type):
    """Module-level wrapper for backward compatibility."""
    return BresserDecoder.get_sensor_type_name(sensor_type)


def decodeBresser6In1Payload(msg, _msgSize):
    """Module-level wrapper for backward compatibility."""
    return BresserDecoder.decodeBresser6In1Payload(msg, _msgSize)

def decodeBresser5In1Payload(msg, msgSize):
    """Module-level wrapper for backward compatibility."""
    return BresserDecoder.decodeBresser5In1Payload(msg, msgSize)

def decodeBresser7In1Payload(msg, msgSize):
    """Module-level wrapper for backward compatibility."""
    return BresserDecoder.decodeBresser7In1Payload(msg, msgSize)

def decodeBresserLightningPayload(msg, msgSize):
    """Module-level wrapper for backward compatibility."""
    return BresserDecoder.decodeBresserLightningPayload(msg, msgSize)

def decodeBresserLeakagePayload(msg, _msgSize):
    """Module-level wrapper for backward compatibility."""
    return BresserDecoder.decodeBresserLeakagePayload(msg, _msgSize)
    
def _print_test_sensor_data(data):
    """
    Simplified print function for test purposes only.
    For production use, import print_sensor_data from main.py.
    
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
        sensor_type_name = get_sensor_type_name(sensor_type)
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
    
    # Print UV index (only if not part of 7-in-1 with light)
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
        alarm_status = "YES" if data["alarm"] else "NO"
        print(f"  Alarm: {alarm_status}")


def main():
    """
    Simple main function for testing decoder functionality.
    For comprehensive testing, use pytest with the tests in the tests/ directory.
    """
    # Enable warning and error log messages for testing
    set_log_level(LOG_LEVEL_WARNING)
    
    print("Bresser Weather Sensor Decoder")
    print("For full test suite, run: pytest tests/")
    print()
    print("Running basic decoder test...")
    
    # Basic sanity check with 6-in-1 decoder
    msg_6in1 = bytes([0x54, 0x1B, 0x21, 0x10, 0x34, 0x27, 0x18, 0xFF, 0x88, 0xFF, 
                     0x29, 0x28, 0x06, 0x42, 0x87, 0xFF, 0xF0, 0xC6, 0x00, 0x00, 
                     0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    
    print("Testing 6-in-1 Decoder...")
    status, data = decodeBresser6In1Payload(msg_6in1, 26)
    if status == DECODE_OK:
        print("✓ 6-in-1 decoder working")
    else:
        print("✗ 6-in-1 decoder test failed")
    print()
    
    print("All decoders have comprehensive tests in tests/ directory")
    print("Run 'pytest tests/' for full test coverage")

if __name__ == "__main__":
    main()
