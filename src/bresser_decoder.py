from struct import unpack

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

#
# Ported from rtl_433 project - https://github.com/merbanan/rtl_433/blob/master/src/util.c
#
def lfsr_digest16(message, num_bytes, gen, key):
    _sum = 0
    for k in range(num_bytes):
        data = message[k]
        for i in range(7, -1, -1):
            # if data bit is set then xor with key
            if data >> i & 1:
                _sum ^= key
            
            # roll the key right (actually the lsb is dropped here)
            # and apply the gen (needs to include the dropped lsb as msb)
            if key & 1:
                key = (key >> 1) ^ gen
            else:
                key = (key >> 1)
    return _sum

#
# Ported from rtl_433 project - https://github.com/merbanan/rtl_433/blob/master/src/util.c
#
def add_bytes(message, num_bytes):
    result = 0;
    
    for i in range(num_bytes):
        result += message[i]
    
    return result
    

#
# Ported from rtl_433 project - https://github.com/merbanan/rtl_433/blob/master/src/devices/bresser_6in1.c (20220608)
#
# - also Bresser Weather Center 7-in-1 indoor sensor.
# - also Bresser new 5-in-1 sensors.
# - also Froggit WH6000 sensors.
# - also rebranded as Ventus C8488A (W835)
# - also Bresser 3-in-1 Professional Wind Gauge / Anemometer PN 7002531
# 
# There are at least two different message types:
# - 24 seconds interval for temperature, hum, uv and rain (alternating messages)
# - 12 seconds interval for wind data (every message)
# 
# Also Bresser Explore Scientific SM60020 Soil moisture Sensor.
# https://www.bresser.de/en/Weather-Time/Accessories/EXPLORE-SCIENTIFIC-Soil-Moisture-and-Soil-Temperature-Sensor.html
# 
# Moisture:
# 
#     f16e 187000e34 7 ffffff0000 252 2 16 fff 004 000 [25,2, 99%, CH 7]
#     DIGEST:8h8h ID?8h8h8h8h STYPE:4h STARTUP:1b CH:3d 8h 8h8h 8h8h TEMP:12h ?2b BATT:1b ?1b MOIST:8h UV?~12h ?4h CHKSUM:8h
# 
# Moisture is transmitted in the humidity field as index 1-16: 0, 7, 13, 20, 27, 33, 40, 47, 53, 60, 67, 73, 80, 87, 93, 99.
# The Wind speed and direction fields decode to valid zero but we exclude them from the output.
# 
#     aaaa2dd4e3ae1870079341ffffff0000221201fff279 [Batt ok]
#     aaaa2dd43d2c1870079341ffffff0000219001fff2fc [Batt low]
# 
#     {206}55555555545ba83e803100058631ff11fe6611ffffffff01cc00 [Hum 96% Temp 3.8 C Wind 0.7 m/s]
#     {205}55555555545ba999263100058631fffffe66d006092bffe0cff8 [Hum 95% Temp 3.0 C Wind 0.0 m/s]
#     {199}55555555545ba840523100058631ff77fe668000495fff0bbe [Hum 95% Temp 3.0 C Wind 0.4 m/s]
#     {205}55555555545ba94d063100058631fffffe665006092bffe14ff8
#     {206}55555555545ba860703100058631fffffe6651ffffffff0135fc [Hum 95% Temp 3.0 C Wind 0.0 m/s]
#     {205}55555555545ba924d23100058631ff99fe68b004e92dffe073f8 [Hum 96% Temp 2.7 C Wind 0.4 m/s]
#     {202}55555555545ba813403100058631ff77fe6810050929ffe1180 [Hum 94% Temp 2.8 C Wind 0.4 m/s]
#     {205}55555555545ba98be83100058631fffffe6130050929ffe17800 [Hum 95% Temp 2.8 C Wind 0.8 m/s]
# 
#     2dd4  1f 40 18 80 02 c3 18 ff 88 ff 33 08 ff ff ff ff 80 e6 00 [Hum 96% Temp 3.8 C Wind 0.7 m/s]
#     2dd4  cc 93 18 80 02 c3 18 ff ff ff 33 68 03 04 95 ff f0 67 3f [Hum 95% Temp 3.0 C Wind 0.0 m/s]
#     2dd4  20 29 18 80 02 c3 18 ff bb ff 33 40 00 24 af ff 85 df    [Hum 95% Temp 3.0 C Wind 0.4 m/s]
#     2dd4  a6 83 18 80 02 c3 18 ff ff ff 33 28 03 04 95 ff f0 a7 3f
#     2dd4  30 38 18 80 02 c3 18 ff ff ff 33 28 ff ff ff ff 80 9a 7f [Hum 95% Temp 3.0 C Wind 0.0 m/s]
#     2dd4  92 69 18 80 02 c3 18 ff cc ff 34 58 02 74 96 ff f0 39 3f [Hum 96% Temp 2.7 C Wind 0.4 m/s]
#     2dd4  09 a0 18 80 02 c3 18 ff bb ff 34 08 02 84 94 ff f0 8c 0  [Hum 94% Temp 2.8 C Wind 0.4 m/s]
#     2dd4  c5 f4 18 80 02 c3 18 ff ff ff 30 98 02 84 94 ff f0 bc 00 [Hum 95% Temp 2.8 C Wind 0.8 m/s]
# 
#     {147} 5e aa 18 80 02 c3 18 fa 8f fb 27 68 11 84 81 ff f0 72 00 [Temp 11.8 C  Hum 81%]
#     {149} ae d1 18 80 02 c3 18 fa 8d fb 26 78 ff ff ff fe 02 db f0
#     {150} f8 2e 18 80 02 c3 18 fc c6 fd 26 38 11 84 81 ff f0 68 00 [Temp 11.8 C  Hum 81%]
#     {149} c4 7d 18 80 02 c3 18 fc 78 fd 29 28 ff ff ff fe 03 97 f0
#     {149} 28 1e 18 80 02 c3 18 fb b7 fc 26 58 ff ff ff fe 02 c3 f0
#     {150} 21 e8 18 80 02 c3 18 fb 9c fc 33 08 11 84 81 ff f0 b7 f8 [Temp 11.8 C  Hum 81%]
#     {149} 83 ae 18 80 02 c3 18 fc 78 fc 29 28 ff ff ff fe 03 98 00
#     {150} 5c e4 18 80 02 c3 18 fb ba fc 26 98 11 84 81 ff f0 16 00 [Temp 11.8 C  Hum 81%]
#     {148} d0 bd 18 80 02 c3 18 f9 ad fa 26 48 ff ff ff fe 02 ff f0
# 
# Wind and Temperature/Humidity or Rain:
# 
#     DIGEST:8h8h ID:8h8h8h8h STYPE:4h STARTUP:1b CH:3d WSPEED:~8h~4h ~4h~8h WDIR:12h ?4h TEMP:8h.4h ?2b BATT:1b ?1b HUM:8h UV?~12h ?4h CHKSUM:8h
#     DIGEST:8h8h ID:8h8h8h8h STYPE:4h STARTUP:1b CH:3d WSPEED:~8h~4h ~4h~8h WDIR:12h ?4h RAINFLAG:8h RAIN:8h8h UV:8h8h CHKSUM:8h
# 
# Digest is LFSR-16 gen 0x8810 key 0x5412, excluding the add-checksum and trailer.
# Checksum is 8-bit add (with carry) to 0xff.
#
# Notes on different sensors:
# 
# - 1910 084d 18 : RebeckaJohansson, VENTUS W835
# - 2030 088d 10 : mvdgrift, Wi-Fi Colour Weather Station with 5in1 Sensor, Art.No.: 7002580, ff 01 in the UV field is (obviously) invalid.
# - 1970 0d57 18 : danrhjones, bresser 5-in-1 model 7002580, no UV
# - 18b0 0301 18 : konserninjohtaja 6-in-1 outdoor sensor
# - 18c0 0f10 18 : rege245 BRESSER-PC-Weather-station-with-6-in-1-outdoor-sensor
# - 1880 02c3 18 : f4gqk 6-in-1
# - 18b0 0887 18 : npkap
# 
# Parameters:
# 
#  msg     - Pointer to message
#  msgSize - Size of message
# 
#  Returns:
# 
#  DECODE_OK      - OK - WeatherData will contain the updated information
#  DECODE_DIG_ERR - Digest Check Error
#  DECODE_CHK_ERR - Checksum Error
#
def decodeBresser6In1Payload(msg, msgSize):
    moisture_map = [0, 7, 13, 20, 27, 33, 40, 47, 53, 60, 67, 73, 80, 87, 93, 99] # scale is 20/3
    
    # LFSR-16 digest, generator 0x8810 init 0x5412
    chkdgst = (msg[0] << 8) | msg[1]
    digest  = lfsr_digest16(msg[2:], 15, 0x8810, 0x5412);

    if (chkdgst != digest):
        print("Digest check failed - [0x{:02x}] != [0x{:02x}]\n".format(chkdgst, digest))
        return DECODE_DIG_ERR

    # Checksum, add with carry
    # msg[2] to msg[17]
    _sum = add_bytes(msg[2:], 16)
    if ((_sum & 0xff) != 0xff):
        print("Checksum failed\n")
        return DECODE_CHK_ERR
    
    (sid, stype_ch) = unpack(">iB",msg[2:7])
    stype = (stype_ch & 0xf0) >> 4
    ch    = stype_ch & 3
    flags = msg[16] & 0x0f
    
    # temperature, humidity(, uv) - shared with rain counter
    temp_ok = humidity_ok = (flags == 0)
    if temp_ok:
        sign     = (msg[13] >> 3) & 1
        temp_raw = (msg[12] >> 4) * 100 + (msg[12] & 0x0f) * 10 + (msg[13] >> 4)
        temp     = (temp_raw - 1000) if (sign) else temp_raw * 0.1
        batt_ok  = (msg[13] >> 1) & 1
        humidity = (msg[14] >> 4) * 10 + (msg[14] & 0x0f)
        
        # apparently ff01 or 0000 if not available, ???0 if valid, inverted BCD
        uv_ok  = (~msg[15] & 0xff) <= 0x99 and (~msg[16] & 0xf0) <= 0x90
        if uv_ok:
            uv_raw    = ((~msg[15] & 0xf0) >> 4) * 100 + (~msg[15] & 0x0f) * 10 + ((~msg[16] & 0xf0) >> 4)

    msg12 = msg[12] ^ 0xff
    msg13 = msg[13] ^ 0xff
    msg14 = msg[14] ^ 0xff
    
    rain_ok = (flags == 1) and (stype == 1)
    if rain_ok:
        rain_raw  =   (msg12 >> 4) * 100000 + (msg12 & 0x0f) * 10000 \
                    + (msg13 >> 4) * 1000   + (msg13 & 0x0f) * 100 \
                    + (msg14 >> 4) * 10     + (msg14 & 0x0f)
        rain_mm   = rain_raw * 0.1
    
    msg7 = msg[7] ^ 0xff
    msg8 = msg[8] ^ 0xff
    msg9 = msg[9] ^ 0xff
    wind_gust  = (msg7 >> 4) * 100 + (msg7 & 0xf) * 10 + (msg8 >> 4)
    wind_gust *= 0.1
    wind_avg   = (msg9 >> 4) * 100 + (msg9 & 0xf) * 10 + (msg8 & 0xf)
    wind_avg  *= 0.1
    wind_dir   = ((msg[10] & 0xf0) >> 4) * 100 + (msg[10] & 0x0f) * 10 + (msg[11] & 0xf0) >> 4
    
    moisture_ok = 0
    
    # the moisture sensor might present valid readings but does not have the hardware
    if stype == 4:
        wind_ok = 0
        uv_ok   = 0

    
    if stype == 4 and temp_ok and humidity >= 1 and sensor[slot].humidity <= 16:
        moisture_ok = 1
        humidity_ok = 0
        moisture = moisture_map[humidity - 1]
    
    if moisture_ok:
       print("id: 0x{:02x} type: {:d} ch: {:d} batt_ok: {:d} temp: {:.1f} moist: {:d}\n".format(sid, stype, ch, batt_ok, temp, moisture))
    elif temp_ok:
        print("id: 0x{:02x} type: {:d} ch: {:d} batt_ok: {:d} temp: {:.1f} hum: {:d} w_gust: {:.1f} w_avg: {:.1f} w_dir: {:.1f}\n".format(sid, stype, ch, batt_ok, temp, humidity, wind_gust, wind_avg, wind_dir))
    else:
        print("id: 0x{:02x} type: {:d} ch: {:d} rain: {:.1f} w_gust: {:.1f} w_avg: {:.1f} w_dir: {:.1f}\n".format(sid, stype, ch, rain_mm, wind_gust, wind_avg, wind_dir))
    
    return DECODE_OK
    
def main():
    # Test data
    msg1     = bytes([0xD4, 0x2A, 0xAF, 0x21, 0x10, 0x34, 0x27, 0x18, 0xFF, 0xAA, 0xFF, 0x29, 0x28, 0xFF, 0xBB, 0x89, 0xFF, 0x01, 0x1F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    msg1_err = bytes([0xD4, 0x2A, 0xAF, 0x21, 0x10, 0x34, 0x28, 0x18, 0xFF, 0xAA, 0xFF, 0x29, 0x28, 0xFF, 0xBB, 0x89, 0xFF, 0x01, 0x1F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    msg2     = bytes([0xD4, 0x54, 0x1B, 0x21, 0x10, 0x34, 0x27, 0x18, 0xFF, 0x88, 0xFF, 0x29, 0x28, 0x06, 0x42, 0x87, 0xFF, 0xF0, 0xC6, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    msg3     = bytes([0xD4, 0x65, 0xA7, 0x79, 0x28, 0x82, 0xA2, 0x18, 0xFF, 0x66, 0xFF, 0x25, 0x68, 0xFF, 0xEA, 0xBF, 0xFF, 0x01, 0x89, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    recv     = bytes([0xd4, 0x3d, 0x91, 0x39, 0x58, 0x58, 0x23, 0x76, 0x18, 0xff, 0xff, 0xff, 0x31, 0x28, 0x05, 0x16, 0x89, 0xff, 0xf0, 0xd4, 0xaa, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    decodeBresser6In1Payload(msg1[1:], 26)
    
    decodeBresser6In1Payload(msg1_err[1:], 26)
    
    decodeBresser6In1Payload(msg2[1:], 26)

    decodeBresser6In1Payload(msg3[1:], 26)

if __name__ == "__main__":
    main()
