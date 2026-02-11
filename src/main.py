# Bresser Weather Sensor Decoder Test
#
# https://github.com/matthias-bs/MicroPython-BresserWeatherSensorReceiver
#
from time import sleep, sleep_ms
import config
from cc1101 import CC1101
from bresser_decoder import (
    DECODE_INVALID, DECODE_OK, DECODE_PAR_ERR, DECODE_CHK_ERR, DECODE_DIG_ERR, DECODE_SKIP,
    decodeBresser6In1Payload, decodeBresser5In1Payload, decodeBresser7In1Payload,
    decodeBresserLightningPayload, decodeBresserLeakagePayload
)


def getMessage():
    decode_res = DECODE_INVALID
    
    # Receive data
    #     1. flush RX buffer
    #     2. switch to RX mode
    #     3. wait for expected RX packet or timeout [~500us in this configuration]
    #     4. flush RX buffer
    #     5. switch to standby
    (rcvState, data) = cc1101.receive(27)
    #print("\nData:  ", data)
    #rssi  = cc1101.getRSSI()
    #print("RSSI:  ", rssi)
    recvData = []
    
#    if len(data) > 0:
#        recvData = [int.from_bytes(data[0][i:i+1], "little") for i in range(len(data[0]))]
    #if len(data) > 0:
    #    recvData = [int.from_bytes(data[0][i:i+1], "little") for i in range(len(data))]
    
    #print("recvData: ", recvData)
    #if len(recvData) > 0:
    #    print("\n[{}]".format(' '.join(hex(x) for x in recvData)))
    
    recvData = data
    if rcvState == CC1101.ERR_NONE:
        # Verify last syncword is 1st byte of payload (see setSyncWord() above)
        if recvData[0] == 0xD4:

            print("[{:02X}] RSSI: {:0.1f}".format(recvData[0], cc1101.getRSSI()))
            
            # Try all decoders in sequence until one succeeds
            # Order: 7-in-1, 6-in-1, 5-in-1, Lightning, Leakage
            decoders = [
                decodeBresser7In1Payload,
                decodeBresser6In1Payload,
                decodeBresser5In1Payload,
                decodeBresserLightningPayload,
                decodeBresserLeakagePayload
            ]
            
            decode_res = DECODE_INVALID
            for decoder in decoders:
                decode_res = decoder(recvData[1:], 26)
                if decode_res == DECODE_OK or decode_res == DECODE_SKIP:
                    break
            
    elif rcvState == CC1101.ERR_RX_TIMEOUT:
        print("T", end='')
        
    else:
        # some other error occurred
        print("\nReceive failed: [{:d}]".format(rcvState))
        
    return decode_res


if __name__ == "__main__":
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
