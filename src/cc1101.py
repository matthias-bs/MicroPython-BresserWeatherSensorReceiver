# MicroPython CC1101 driver
#
# Inspired by the CC1101 drivers written in C from:
# https://github.com/letscontrolit/ESPEasyPluginPlayground/
# https://github.com/arjenhiemstra/IthoEcoFanRFT/blob/master/Master/Itho/CC1101.cpp
# https://github.com/SpaceTeddy/CC1101/blob/master/cc1100_raspi.cpp
# https://github.com/SpaceTeddy/CC1101/blob/master/cc1100_raspi.h
#
# Copyright 2021 (c) Erik de Lange
# Released under MIT license

import time
from time import sleep_ms, sleep_us

import machine
from machine import SPI, Pin
from micropython import const

import config  # hardware dependent configuration


class CC1101:
    # from RadioLib/TypeDef.h
    ERR_NONE                        = const(0)
    ERR_UNKNOWN                     = const(-1)
    ERR_PACKET_TOO_LONG             = const(-4)
    ERR_TX_TIMEOUT                  = const(-5)
    ERR_RX_TIMEOUT                  = const(-6)
    ERR_CRC_MISMATCH                = const(-7)
    ERR_INVALID_BANDWIDTH           = const(-8)
    ERR_INVALID_BIT_RANGE           = const(-11)
    ERR_INVALID_FREQUENCY           = const(-12)
    ERR_INVALID_OUTPUT_POWER        = const(-13)
    ERR_INVALID_PREAMBLE_LENGTH     = const(-18)
    ERR_INVALID_FREQUENCY_DEVIATION = const(-102)
    ERR_INVALID_RX_BANDWIDTH        = const(-104)
    ERR_INVALID_SYNC_WORD           = const(-105)
    
    # from RadioLib/CC1101.h
    CC1101_MAX_PACKET_LENGTH       = const(255)
    CC1101_CRYSTAL_FREQ            = const(26.0)
    
    # CC1101_REG_IOCFG2 + REG_IOCFG1 + REG_IOCFG0
    CC1101_GDOX_RX_FIFO_FULL_OR_PKT_END = const(0x01) # 0x01 //  5     0     Rx FIFO full or above threshold or reached packet end
    CC1101_GDOX_HIGH_Z                  = const(0x2e) # 0x2E //  5     0     high impedance state (default for GDO1)
    
    # CC1101_REG_FIFOTHR
    CC1101_FIFO_THR_TX_61_RX_4     = const(0x00) # 0b00000000  //  3     0     TX fifo threshold: 61, RX fifo threshold: 4
    
    # CC1101_REG_MCSM1
    CC1101_RXOFF_IDLE              = const(0x00) # 0b00000000  //  3     2     next mode after packet reception: idle (default)
    
    # CC1101_REG_MDMCFG1
    CC1101_NUM_PREAMBLE_2          = const(0x00) # 0b00000000  //  6     4     number of preamble bytes: 2
    CC1101_NUM_PREAMBLE_3          = const(0x10) # 0b00010000  //  6     4                               3
    CC1101_NUM_PREAMBLE_4          = const(0x20) # 0b00100000  //  6     4                               4 (default)
    CC1101_NUM_PREAMBLE_6          = const(0x30) # 0b00110000  //  6     4                               6
    CC1101_NUM_PREAMBLE_8          = const(0x40) # 0b01000000  //  6     4                               8
    CC1101_NUM_PREAMBLE_12         = const(0x50) # 0b01010000  //  6     4                               12
    CC1101_NUM_PREAMBLE_16         = const(0x60) # 0b01100000  //  6     4                               16
    CC1101_NUM_PREAMBLE_24         = const(0x70) # 0b01110000  //  6     4                               24
    
    # CC1101_REG_MDMCFG2
    CC1101_SYNC_MODE_NONE          = const(0x00) # 0b00000000  //  2     0 synchronization: no preamble/sync
    CC1101_SYNC_MODE_15_16         = const(0x01) # 0b00000001  //  2     0                  15/16 sync word bits
    CC1101_SYNC_MODE_16_16         = const(0x02) # 0b00000010  //  2     0                  16/16 sync word bits (default)
    CC1101_SYNC_MODE_30_32         = const(0x03) # 0b00000011  //  2     0                  30/32 sync word bits
    CC1101_SYNC_MODE_NONE_THR      = const(0x04) # 0b00000100  //  2     0                  no preamble sync, carrier sense above threshold
    CC1101_SYNC_MODE_15_16_THR     = const(0x05) # 0b00000101  //  2     0                  15/16 sync word bits, carrier sense above threshold
    CC1101_SYNC_MODE_16_16_THR     = const(0x06) # 0b00000110  //  2     0                  16/16 sync word bits, carrier sense above threshold
    CC1101_SYNC_MODE_30_32_THR     = const(0x07) # 0b00000111  //  2     0                  30/32 sync word bits, carrier sense above threshold
    CC1101_MOD_FORMAT_2_FSK        = const(0x00) # 0b00000000  //  6     4     modulation format: 2-FSK (default)
    CC1101_MOD_FORMAT_ASK_OOK      = const(0x30) # 0b00110000  //  6     4                        ASK/OOK


    # CC1101_REG_PKTCTRL0
    CC1101_WHITE_DATA_OFF          = const(0x00) # 0b00000000  //  6     6     data whitening: disabled
    CC1101_PKT_FORMAT_NORMAL       = const(0x00) # 0b00000000  //  5     4     packet format: normal (FIFOs)
    CC1101_CRC_OFF                 = const(0x00) # 0b00000000  //  2     2     CRC disabled
    CC1101_CRC_ON                  = const(0x04) # 0b00000100  //  2     2     CRC enabled (default)
    CC1101_LENGTH_CONFIG_FIXED     = const(0x00) # 0b00000000  //  1     0     packet length: fixed
    CC1101_LENGTH_CONFIG_VARIABLE  = const(0x01) # 0b00000001  //  1     0                    variable (default)
    
    # CC1101_REG_PKTCTRL1
    CC1101_CRC_AUTOFLUSH_OFF       = const(0x00) # 0b00000000  //  3     3     automatic Rx FIFO flush on CRC check fail: disabled (default)
    CC1101_APPEND_STATUS_ON        = const(0x04) # 0b00000100  //  2     2                                      enabled (default)
    CC1101_ADR_CHK_NONE            = const(0x00) # 0b00000000  //  1     0     address check: none (default)
  
    # CC1101_REG_MCSM0
    CC1101_FS_AUTOCAL_IDLE_TO_RXTX = const(0x10) # 0b00010000  //  5     4                            every transition from idle to Rx/Tx
    
    # CC1101_REG_PKTSTATUS
    CC1101_CRC_OK                  = const(0x80) # 0b10000000  //  7     7     CRC check passed
    CC1101_CRC_ERROR               = const(0x00) # 0b00000000  //  7     7     CRC check failed
    
    FIFO_BUFFER_SIZE               = const(64)
    
    # Transfer types
    WRITE_SINGLE_BYTE = const(0x00)
    WRITE_BURST = const(0x40)
    READ_SINGLE_BYTE = const(0x80)
    READ_BURST = const(0xC0)

    # Register types
    CONFIG_REGISTER = const(0x80)
    STATUS_REGISTER = const(0xC0)

    # PATABLE and FIFO address
    PATABLE = const(0x3E)
    TXFIFO = const(0x3F)
    RXFIFO = const(0x3F)
    PA_LowPower = const(0x60)
    PA_LongDistance = (0xC0)

    # FIFO Commands
    TXFIFO_BURST = const(0x7F)  # Burst access to TX FIFO
    TXFIFO_SINGLE_BYTE = const(0x3F)  # Single byte access to TX FIFO
    RXFIFO_BURST = const(0xFF)  # Burst access to RX FIFO
    RXFIFO_SINGLE_BYTE = const(0xBF)  # Single byte access to RX FIFO
    PATABLE_BURST = const(0x7E)  # Power control read/write
    PATABLE_SINGLE_BYTE = const(0xFE)  # Power control read/write

    # Configuration registers
    IOCFG2 = const(0x00)  # GDO2 output pin configuration
    IOCFG1 = const(0x01)  # GDO1 output pin configuration
    IOCFG0 = const(0x02)  # GDO0 output pin configuration
    FIFOTHR = const(0x03)  # RX FIFO and TX FIFO thresholds
    SYNC1 = const(0x04)  # Sync word, high byte
    SYNC0 = const(0x05)  # Sync word, low byte
    PKTLEN = const(0x06)  # Packet length
    PKTCTRL1 = const(0x07)  # Packet automation control
    PKTCTRL0 = const(0x08)  # Packet automation control
    ADDR = const(0x09)  # Device address
    CHANNR = const(0x0A)  # Channel number
    FSCTRL1 = const(0x0B)  # Frequency synthesizer control
    FSCTRL0 = const(0x0C)  # Frequency synthesizer control
    FREQ2 = const(0x0D)  # Frequency control word, high byte
    FREQ1 = const(0x0E)  # Frequency control word, middle byte
    FREQ0 = const(0x0F)  # Frequency control word, low byte
    MDMCFG4 = const(0x10)  # Modem configuration
    MDMCFG3 = const(0x11)  # Modem configuration
    MDMCFG2 = const(0x12)  # Modem configuration
    MDMCFG1 = const(0x13)  # Modem configuration
    MDMCFG0 = const(0x14)  # Modem configuration
    DEVIATN = const(0x15)  # Modem deviation setting
    MCSM2 = const(0x16)  # Main Radio Cntrl State Machine configuration
    MCSM1 = const(0x17)  # Main Radio Cntrl State Machine configuration
    MCSM0 = const(0x18)  # Main Radio Cntrl State Machine configuration
    FOCCFG = const(0x19)  # Frequency Offset Compensation configuration
    BSCFG = const(0x1A)  # Bit Synchronization configuration
    AGCCTRL2 = const(0x1B)  # AGC control
    AGCCTRL1 = const(0x1C)  # AGC control
    AGCCTRL0 = const(0x1D)  # AGC control
    WOREVT1 = const(0x1E)  # High byte Event 0 timeout
    WOREVT0 = const(0x1F)  # Low byte Event 0 timeout
    WORCTRL = const(0x20)  # Wake On Radio control
    FREND1 = const(0x21)  # Front end RX configuration
    FREND0 = const(0x22)  # Front end TX configuration
    FSCAL3 = const(0x23)  # Frequency synthesizer calibration
    FSCAL2 = const(0x24)  # Frequency synthesizer calibration
    FSCAL1 = const(0x25)  # Frequency synthesizer calibration
    FSCAL0 = const(0x26)  # Frequency synthesizer calibration
    RCCTRL1 = const(0x27)  # RC oscillator configuration
    RCCTRL0 = const(0x28)  # RC oscillator configuration
    FSTEST = const(0x29)  # Frequency synthesizer calibration control
    PTEST = const(0x2A)  # Production test
    AGCTEST = const(0x2B)  # AGC test
    TEST2 = const(0x2C)  # Various test settings
    TEST1 = const(0x2D)  # Various test settings
    TEST0 = const(0x2E)  # Various test settings

    # Status registers
    PARTNUM = const(0x30)  # Part number
    VERSION = const(0x31)  # Current version number
    FREQEST = const(0x32)  # Frequency offset estimate
    LQI = const(0x33)  # Demodulator estimate for link quality
    RSSI = const(0x34)  # Received signal strength indication
    MARCSTATE = const(0x35)  # Control state machine state
    WORTIME1 = const(0x36)  # High byte of WOR timer
    WORTIME0 = const(0x37)  # Low byte of WOR timer
    PKTSTATUS = const(0x38)  # Current GDOx status and packet status
    VCO_VC_DAC = const(0x39)  # Current setting from PLL calibration module
    TXBYTES = const(0x3A)  # Underflow and number of bytes in TXFIFO
    RXBYTES = const(0x3B)  # Overflow and number of bytes in RXFIFO
    RCCTRL1_STATUS = const(0x3C)  # Last RC oscillator calibration result
    RCCTRL0_STATUS = const(0xF3)  # Last RC oscillator calibration result

    # Command strobes
    SRES = const(0x30)  # Reset chip
    SFSTXON = const(0x31)  # Enable/calibrate frequency synthesizer
    SXOFF = const(0x32)  # Turn off crystal oscillator
    SCAL = const(0x33)  # Calibrate frequency synthesizer and disable
    SRX = const(0x34)  # Enable RX. Perform calibration first if coming from IDLE and MCSM0.FS_AUTOCAL=1.
    STX = const(0x35)  # Enable TX
    SIDLE = const(0x36)  # Exit RX / TX
    SAFC = const(0x37)  # AFC adjustment of freq synthesizer
    SWOR = const(0x38)  # Start automatic RX polling sequence
    SPWD = const(0x39)  # Enter power down mode when CSn goes high
    SFRX = const(0x3A)  # Flush the RX FIFO buffer. Only issue SFRX in IDLE or RXFIFO_OVERFLOW states.
    SFTX = const(0x3B)  # Flush the TX FIFO buffer. Only issue SFTX in IDLE or TXFIFO_UNDERFLOW states.
    SWORRST = const(0x3C)  # Reset real time clock to Event1 value
    SNOP = const(0x3D)  # No operation. May be used to get access to the chip status byte.

    # Bit fields for chip status byte
    STATUS_CHIP_RDYn = const(0x80)  # Should be low when using SPI interface
    STATUS_STATE = const(0x70)
    STATUS_FIFO_BYTES_AVAILABLE = const(0x0F)  # Bytes available in RX FIFO or bytes free in TX FIFO

    # Masks to retrieve status bit
    BITS_TX_FIFO_UNDERFLOW = const(0x80)
    BITS_RX_BYTES_IN_FIFO = const(0x7F)
    BITS_MARCSTATE = const(0x1F)

    # Marc states
    MARCSTATE_SLEEP = const(0x00)
    MARCSTATE_IDLE = const(0x01)
    MARCSTATE_XOFF = const(0x02)
    MARCSTATE_VCOON_MC = const(0x03)
    MARCSTATE_REGON_MC = const(0x04)
    MARCSTATE_MANCAL = const(0x05)
    MARCSTATE_VCOON = const(0x06)
    MARCSTATE_REGON = const(0x07)
    MARCSTATE_STARTCAL = const(0x08)
    MARCSTATE_BWBOOST = const(0x09)
    MARCSTATE_FS_LOCK = const(0x0A)
    MARCSTATE_IFADCON = const(0x0B)
    MARCSTATE_ENDCAL = const(0x0C)
    MARCSTATE_RX = const(0x0D)
    MARCSTATE_RX_END = const(0x0E)
    MARCSTATE_RX_RST = const(0x0F)
    MARCSTATE_TXRX_SWITCH = const(0x10)
    MARCSTATE_RXFIFO_OVERFLOW = const(0x11)
    MARCSTATE_FSTXON = const(0x12)
    MARCSTATE_TX = const(0x13)
    MARCSTATE_TX_END = const(0x14)
    MARCSTATE_RXTX_SWITCH = const(0x15)
    MARCSTATE_TXFIFO_UNDERFLOW = const(0x16)

    # Bit masks for chip status state
    STATE_IDLE = const(0x00)  # IDLE state
    STATE_RX = const(0x10)  # Receive mode
    STATE_TX = const(0x20)  # Transmit mode
    STATE_FSTXON = const(0x30)  # Fast TX ready
    STATE_CALIBRATE = const(0x40)  # Frequency synthesizer calibration is running
    STATE_SETTLING = const(0x50)  # PLL is settling
    STATE_RXFIFO_OVERFLOW = const(0x60)  # RX FIFO has overflowed
    STATE_TXFIFO_UNDERFLOW = const(0x70)  # TX FIFO has underflowed

    # Defaults
    CC1101_DEFAULT_FREQ        = const(434.0)
    CC1101_DEFAULT_BR          = const(4.8)
    CC1101_DEFAULT_FREQDEV     = const(5.0)
    CC1101_DEFAULT_RXBW        = const(135.0)
    CC1101_DEFAULT_POWER       = const(10)
    CC1101_DEFAULT_PREAMBLELEN = const(16)
    CC1101_DEFAULT_SW          = [0x12, 0xAD]
    CC1101_DEFAULT_SW_LEN      = const(2)

    def __init__(self, spi_id, ss, gdo0, gdo2):
        """ Create a CC1101 object connected to a microcontroller SPI channel

        This class assumes the usage of SPI hardware channels and the
        corresponding (hardwired) pins. Software SPI is not supported.
        Pin gd02 is only used when receiving messages, not when sending.

        :param int spi_id: microcontroller SPI channel id
        :param int ss: microcontroller pin number used for slave select (SS)
        :param int gd02: microcontroller pin number connected to port GD02 of the CC1101
        """
        if spi_id not in config.SPI_ID_LIST:
            raise ValueError(f"invalid SPI id {spi_id} for {config.BOARD}")

        self._freq       = CC1101.CC1101_DEFAULT_FREQ
        self._br         = CC1101.CC1101_DEFAULT_BR
        self._rawRSSI    = None
        self._rawLQI     = 0
        self._modulation = CC1101.CC1101_MOD_FORMAT_2_FSK

        self._packetLength        = 0
        self._packetLengthQueried = False
        self._packetLengthConfig  = CC1101.CC1101_LENGTH_CONFIG_VARIABLE

        self._promiscuous = False
        self._crcOn       = False  # Default to CRC disabled to match Bresser sensor RadioLib config
        self._directMode  = False # True?

        self._power = CC1101.CC1101_DEFAULT_POWER

        self.miso = Pin(config.MISO_PIN_PER_SPI_ID[str(spi_id)])
        self.ss = Pin(ss, mode=Pin.OUT)
        self.gdo0 = Pin(gdo0, mode=Pin.IN)
        self.gdo2 = Pin(gdo2, mode=Pin.IN)

        self.deselect()
#        self.spi = SPI(spi_id, baudrate=8000000, polarity=0, phase=0, bits=8,
#                       firstbit=SPI.MSB)  # use default pins for mosi, miso and sclk
        self.spi = SPI(spi_id, baudrate=1000000, polarity=0, phase=0, bits=8,
                       firstbit=SPI.MSB)  # use default pins for mosi, miso and sclk
        self.reset()
        self._freq = 868.3

    def select(self):
        """ CC1101 chip select """
        self.ss.value(0)

    def deselect(self):
        """ CC1101 chip deselect """
        self.ss.value(1)

    def spi_wait_miso(self):
        """ Wait for CC1101 SO to go low """
        while self.miso.value() != 0:
            pass

    def reset(self):
        """ CC1101 reset """
        self.deselect()
        time.sleep_us(5)
        self.select()
        time.sleep_us(10)
        self.deselect()
        time.sleep_us(45)
        self.select()

        self.spi_wait_miso()
        self.write_command(CC1101.SRES)
        time.sleep_ms(10)
        # self.spi_wait_miso()
        self.deselect()

    def write_command(self, command):
        """ Write command strobe

        Command strobes share addresses with the status registers
        (address 0x30 to 0x3F). A command strobe must have the
        burst bit set to 0.

        :param int command: strobe byte
        :return int: status byte
        """
        buf = bytearray((command,))
        self.select()
        self.spi_wait_miso()
        self.spi.write(buf)
        self.deselect()
        return buf[0]

    def write_register(self, address, data):
        """ Write single byte to configuration register

        Note that status registers cannot be written to (as that would be
        a command strobe).

        :param int address: byte address of register
        :param int data: byte to write to register
         """
        buf = bytearray(2)
        buf[0] = address | CC1101.WRITE_SINGLE_BYTE
        buf[1] = data
        self.select()
        self.spi_wait_miso()
        self.spi.write(buf)
        self.deselect()

    def read_register(self, address, register_type=0x80):
        """ Read value from configuration or status register

        Status registers share addresses with command strobes (address 0x30
        to 0x3F). To access a status register the burst bit must be set to 1.
        This is handled by the mask in parameter register_type.

        :param int address: byte address of register
        :param int register_type: C1101.CONFIG_REGISTER (default) or STATUS_REGISTER
        :return int: register value (byte)
        """
        read_buf = bytearray(2)
        write_buf = bytearray(2)
        write_buf[0] = address | register_type
        self.select()
        self.spi_wait_miso()
        self.spi.write_readinto(write_buf, read_buf)

        # CC1101 SPI/26 Mhz synchronization bug - see CC1101 errata
        # When reading the following registers two consecutive reads
        # must give the same result to be OK.
        if address in [CC1101.FREQEST, CC1101.MARCSTATE, CC1101.RXBYTES,
                       CC1101.TXBYTES, CC1101.WORTIME0, CC1101.WORTIME1]:
            value = read_buf[1]
            while True:
                self.spi.write_readinto(write_buf, read_buf)
                if value == read_buf[1]:
                    break
                value = read_buf[1]

        self.deselect()
        return read_buf[1]

    def read_register_median_of_3(self, address):
        """ Read register 3 times and return median value """
        lst = list()
        for _ in range(3):
            lst.append(self.read_register(address))
        lst.sort()
        return lst[1]

    def read_burst(self, address, length):
        """ Read values from consecutive configuration registers

        :param int address: start register address
        :param int length: number of registers to read
        :return bytearray: values read (bytes)
        """
        buf = bytearray(length + 1)
        buf[0] = address | CC1101.READ_BURST
        self.select()
        self.spi_wait_miso()
        self.spi.write_readinto(buf, buf)
        self.deselect()
        return buf[1:]

    def write_burst(self, address, data):
        """ Write data to consecutive registers

        :param int address: start register address
        :param bytearray data: values to write (full array is written)
        """
        buf = bytearray(1)
        buf[0] = address | CC1101.WRITE_BURST
        buf[1:1] = data  # append data
        self.select()
        self.spi_wait_miso()
        self.spi.write(buf)
        self.deselect()

    def receive_data(self, _length):
        """ Read available bytes from the FIFO

        :param int length: max number of bytes to read
        :return bytearray: bytes read (can have len() of 0)
        """
        rx_bytes = self.read_register(CC1101.RXBYTES, CC1101.STATUS_REGISTER) & CC1101.BITS_RX_BYTES_IN_FIFO

        # Check for
        if (self.read_register(CC1101.MARCSTATE, CC1101.STATUS_REGISTER) & CC1101.BITS_MARCSTATE) == CC1101.MARCSTATE_RXFIFO_OVERFLOW:
            buf = bytearray()  # RX FIFO overflow: return empty array
        else:
            buf = self.read_burst(CC1101.RXFIFO, rx_bytes)

        self.write_command(CC1101.SIDLE)
        self.write_command(CC1101.SFRX)  # Flush RX buffer
        self.write_command(CC1101.SRX)   # Switch to RX state

        return buf

    def receive(self, length):
        # calculate timeout (500 ms + 400 full max-length packets at current bit rate)
        timeout = 500000 + (1.0/(self._br*1000.0))*(CC1101.CC1101_MAX_PACKET_LENGTH*400.0)
        
        # start reception
        self.startReceive()
        # FIXME
        #RADIOLIB_ASSERT(state);

        # wait for packet or timeout
        start = time.ticks_us()
        while self.gdo0.value() == 0:
            #machine.idle()
            #sleep_us(10)
            #_mod->yield();

            if (time.ticks_us() - start) > timeout:
                self.write_command(CC1101.SIDLE)
                self.write_command(CC1101.SFRX)
                return CC1101.ERR_RX_TIMEOUT, []

        # read packet data
        return self.readData(length)
    
    # FIXME
    def readData(self, length):
        # get packet length
        _length = self.getPacketLength()
        if (length != 0) and (length < _length):
            # user requested less data than we got, only return what was requested
            _length = length

        # check address filtering
        _filter = self.SPIgetRegValue(CC1101.PKTCTRL1, 1, 0)
        if (_filter != CC1101.CC1101_ADR_CHK_NONE):
            self.read_register(CC1101.RXFIFO)
        

        bytesInFIFO = self.SPIgetRegValue(CC1101.RXBYTES, 6, 0)
        readBytes = 0
        lastPop = time.ticks_ms()

        data = []
        # keep reading from FIFO until we get all the packet.
        while readBytes < _length:
            if bytesInFIFO == 0:
                if (time.ticks_ms() - lastPop) > 5:
                    # readData was required to read a packet longer than the one received.
                    #RADIOLIB_DEBUG_PRINTLN(F("No data for more than 5mS. Stop here."));
                    break
                else:
                    sleep_ms(1)
                    bytesInFIFO = self.SPIgetRegValue(CC1101.RXBYTES, 6, 0)
                    continue

            # read the minimum between "remaining length" and bytesInFifo
            bytesToRead = min((_length - readBytes), bytesInFIFO)
            # self.SPIreadRegisterBurst(CC1101.FIFO, bytesToRead, &(data[readBytes]));
            #data.append(self.read_burst(CC1101.RXFIFO_BURST, bytesToRead))
            #readBytes += bytesToRead
            data.append(self.read_register(CC1101.RXFIFO))
            readBytes += 1
            lastPop = time.ticks_ms()

            # Get how many bytes are left in FIFO.
            bytesInFIFO = self.SPIgetRegValue(CC1101.RXBYTES, 6, 0)

        
        # check if status bytes are enabled (default: RADIOLIB_CC1101_APPEND_STATUS_ON)
        isAppendStatus = (self.SPIgetRegValue(CC1101.PKTCTRL1, 2, 2) != 0)
        
        # for some reason, we need this delay here to get the correct status bytes
        sleep_ms(3)

        # If status byte is enabled at least 2 bytes (2 status bytes + any following packet) will remain in FIFO.
        if (isAppendStatus):
            # read RSSI byte
            self._rawRSSI = self.SPIgetRegValue(CC1101.RXFIFO)
        
            # read LQI and CRC byte
            val = self.SPIgetRegValue(CC1101.RXFIFO)
            self._rawLQI = val & 0x7F
        
            # check CRC
            if (self._crcOn and (val & CC1101.CC1101_CRC_OK) == CC1101.CC1101_CRC_ERROR):
                self._packetLengthQueried = False
                return CC1101.ERR_CRC_MISMATCH, []
            

        # clear internal flag so getPacketLength can return the new packet length
        self._packetLengthQueried = False

        # Flush then standby according to RXOFF_MODE (default: RADIOLIB_CC1101_RXOFF_IDLE)
        if self.SPIgetRegValue(CC1101.MCSM1, 3, 2) == CC1101.CC1101_RXOFF_IDLE:
            # flush Rx FIFO
            self.write_command(CC1101.SFRX)

            # set mode to standby
            self.write_command(CC1101.SIDLE)
    

        return CC1101.ERR_NONE, data

        
    def startReceive(self):
        # Reset RSSI to ensure we don't use stale values
        self._rawRSSI = None
        
        # set mode to standby
        self.write_command(CC1101.SIDLE)

        # flush Rx FIFO
        self.write_command(CC1101.SFRX)

        # GDO0 and FIFOTHR are already configured in config()
        # No need to reconfigure them here

        # set RF switch (if present)
        #_mod->setRfSwitchState(Module::MODE_RX);

        # set mode to receive
        self.write_command(CC1101.SRX)

        return CC1101.ERR_NONE

    def getPacketLength(self, update = True):
        if not(self._packetLengthQueried) and update:
            if self._packetLengthConfig == CC1101.CC1101_LENGTH_CONFIG_VARIABLE:
                self._packetLength = self.read_register(CC1101.RXFIFO)
            else:
                self._packetLength = self.read_register(CC1101.PKTLEN)

            self._packetLengthQueried = True

        return self._packetLength

    def send_data(self, data):
        """ Send data

        :param bytearray data: bytes to send (len(data) may exceed FIFO size)
        """
        DATA_LEN = CC1101.FIFO_BUFFER_SIZE - 3

        self.write_command(CC1101.SIDLE)

        # Clear TX FIFO if needed
        if self.read_register(CC1101.TXBYTES, CC1101.STATUS_REGISTER) & CC1101.BITS_TX_FIFO_UNDERFLOW:
            self.write_command(CC1101.SIDLE)
            self.write_command(CC1101.SFTX)

        self.write_command(CC1101.SIDLE)

        length = len(data) if len(data) <= DATA_LEN else DATA_LEN

        self.write_burst(CC1101.TXFIFO, data[:length])

        self.write_command(CC1101.SIDLE)
        self.write_command(CC1101.STX)  # Start sending packet

        index = 0

        if len(data) > DATA_LEN:
            # More data to send
            index += length

            while index < len(data):
                while True:
                    tx_status = self.read_register_median_of_3(CC1101.TXBYTES | CC1101.STATUS_REGISTER) & CC1101.BITS_RX_BYTES_IN_FIFO
                    if tx_status <= (DATA_LEN - 2):
                        break

                length = DATA_LEN - tx_status
                length = len(data) - index if (len(data) - index) < length else length

                for i in range(length):
                    self.write_register(CC1101.TXFIFO, data[index + i])

                index += length

        # Wait until transmission is finished (TXOFF_MODE is expected to be set to 0/IDLE or TXFIFO_UNDERFLOW)
        while True:
            marcstate = self.read_register(CC1101.MARCSTATE, CC1101.STATUS_REGISTER) & CC1101.BITS_MARCSTATE
            if marcstate in [CC1101.MARCSTATE_IDLE, CC1101.MARCSTATE_TXFIFO_UNDERFLOW]:
                break

    def SPIsetRegValue(self, reg, value, msb = 7, lsb = 0):
        if (msb > 7) or (lsb > 7) or (lsb > msb):
            return CC1101.ERR_INVALID_BIT_RANGE

        currentValue = self.read_register(reg)
        mask = ~((0b11111111 << (msb + 1)) | (0b11111111 >> (8 - lsb)))
        newValue = (currentValue & ~mask) | (value & mask)
        self.write_register(reg, newValue)
        return CC1101.ERR_NONE

    def SPIgetRegValue(self, reg, msb = 7, lsb = 0):
        if (msb > 7) or (lsb > 7) or (lsb > msb):
            return CC1101.ERR_INVALID_BIT_RANGE

        rawValue = self.read_register(reg)
        maskedValue = rawValue & ((0xFF << lsb) & (0xFF >> (7 - msb)))
        return maskedValue >> lsb

    def config(self):
        # Reset the radio. Registers may be dirty from previous usage.
        self.write_command(CC1101.SRES)

        # Wait a ridiculous amount of time to be sure radio is ready.
        sleep_ms(150)

        # enable automatic frequency synthesizer calibration
        state = self.SPIsetRegValue(CC1101.MCSM0, CC1101.CC1101_FS_AUTOCAL_IDLE_TO_RXTX, 5, 4)
        # RADIOLIB_ASSERT(state);

        # set gdo2 to high impedance
        state |= self.SPIsetRegValue(CC1101.IOCFG2, CC1101.CC1101_GDOX_HIGH_Z)
        
        # Configure GDO0 for packet reception: Asserted when RX FIFO > threshold or packet end
        state |= self.SPIsetRegValue(CC1101.IOCFG0, CC1101.CC1101_GDOX_RX_FIFO_FULL_OR_PKT_END)
        state |= self.SPIsetRegValue(CC1101.FIFOTHR, CC1101.CC1101_FIFO_THR_TX_61_RX_4, 3, 0)
        
        # set packet mode
        state |= self.packetMode()

        return state

    def setFrequency(self, freq):
        # check allowed frequency range
        if not(((freq > 300.0) and (freq < 348.0)) or
               ((freq > 387.0) and (freq < 464.0)) or
               ((freq > 779.0) and (freq < 928.0))):
            return CC1101.ERR_INVALID_FREQUENCY

        # set mode to standby
        self.write_command(CC1101.SIDLE)

        # set carrier frequency
        base = 1
        FRF = int((freq * (base << 16)) / 26.0)
        state  = self.SPIsetRegValue(CC1101.FREQ2, (FRF & 0xFF0000) >> 16)
        state |= self.SPIsetRegValue(CC1101.FREQ1, (FRF & 0x00FF00) >>  8)
        state |= self.SPIsetRegValue(CC1101.FREQ0,  FRF & 0x0000FF)

        if (state == CC1101.ERR_NONE):
            self._freq = freq

        # FIXME
        # (We are skipping this for the moment, because we only want to receive)
        # Update the TX power accordingly to new freq. (PA values depend on chosen freq)
        #return setOutputPower(_power)
        return state

    def setOutputPower(self, power):
        # round to the known frequency settings
        if self._freq < 374.0:
            # 315 MHz
            f = 0
        elif self._freq < 650.5:
            # 434 MHz
            f = 1
        elif self._freq < 891.5:
            # 868 MHz
            f = 2
        else:
            # 915 MHz
            f = 3

        # get raw power setting
        paTable = [[0x12, 0x12, 0x03, 0x03],
                   [0x0D, 0x0E, 0x0F, 0x0E],
                   [0x1C, 0x1D, 0x1E, 0x1E],
                   [0x34, 0x34, 0x27, 0x27],
                   [0x51, 0x60, 0x50, 0x8E],
                   [0x85, 0x84, 0x81, 0xCD],
                   [0xCB, 0xC8, 0xCB, 0xC7],
                   [0xC2, 0xC0, 0xC2, 0xC0]]

        # requires Python >=3.10
        if power == -30:
            powerRaw = paTable[0][f]
            
        elif power == -20:
            powerRaw = paTable[1][f]
        
        elif power == -15:
            powerRaw = paTable[2][f]
            
        elif power == -10:
            powerRaw = paTable[3][f]
            
        elif power == 0:
            powerRaw = paTable[4][f]
            
        elif power == 5:
            powerRaw = paTable[5][f]
            
        elif power == 7:
            powerRaw = paTable[6][f]
            
        elif power == 10:
            powerRaw = paTable[7][f]
            
        else:
            return CC1101.ERR_INVALID_OUTPUT_POWER

        # store the value
        self._power = power

        # FIXME
        if self._modulation == CC1101.CC1101_MOD_FORMAT_ASK_OOK:
            # Amplitude modulation:
            # PA_TABLE[0] is the power to be used when transmitting a 0  (no power)
            # PA_TABLE[1] is the power to be used when transmitting a 1  (full power)

            # FIXME
            # paValues = [0x00, powerRaw]
            # SPIwriteRegisterBurst(RADIOLIB_CC1101_REG_PATABLE, paValues, 2);
            return CC1101.ERR_NONE

        else:
            # Freq modulation:
            # PA_TABLE[0] is the power to be used when transmitting.
            # FIXME
            #return(SPIsetRegValue(RADIOLIB_CC1101_REG_PATABLE, powerRaw));
            pass

    def setBitRate(self, br):
        # RADIOLIB_CHECK_RANGE(br, 0.025, 600.0, RADIOLIB_ERR_INVALID_BIT_RATE);

        # set mode to standby
        self.write_command(CC1101.SIDLE)

        # calculate exponent and mantissa values
        (e, m) = self.getExpMant(br * 1000.0, 256, 28, 14)
        #print("setBitrate(): e=", e, "m=", m)
        
        # set bit rate value
        state  = self.SPIsetRegValue(CC1101.MDMCFG4, int(e), 3, 0)
        state |= self.SPIsetRegValue(CC1101.MDMCFG3, int(m))
        
        if state == CC1101.ERR_NONE:
            self._br = br
        
        return state

    def getExpMant(self, target, mantOffset, divExp, expMax):
        # get table origin point (exp = 0, mant = 0)
        origin = (mantOffset * CC1101.CC1101_CRYSTAL_FREQ * 1000000.0)/(1 << divExp)

        # iterate over possible exponent values
        for e in range(expMax, -1, -1):
            # get table column start value (exp = e, mant = 0);
            intervalStart = (1 << e) * origin

            # check if target value is in this column
            if target >= intervalStart:
                # save exponent value
                exp = e

                # calculate size of step between table rows
                stepSize = intervalStart/mantOffset

                # get target point position (exp = e, mant = m)
                mant = (target - intervalStart) / stepSize

                # we only need the first match, terminate
                return exp, mant

    def setRxBandwidth(self, rxBw):
        # FIXME
        #RADIOLIB_CHECK_RANGE(rxBw, 58.0, 812.0, RADIOLIB_ERR_INVALID_RX_BANDWIDTH);

        # set mode to standby
        self.write_command(CC1101.SIDLE)

        # calculate exponent and mantissa values
        for e in range(3, -1, -1):
            for m in range(3, -1, -1):
                point = (CC1101.CC1101_CRYSTAL_FREQ * 1000000.0)/(8 * (m + 4) * (1 << e))
                if (abs((rxBw * 1000.0) - point) <= 1000):
                    # set Rx channel filter bandwidth
                    #print("setRxBandwidth(): point=", point, "e=", e, "m=", m)
                    return self.SPIsetRegValue(CC1101.MDMCFG4, (e << 6) | (m << 4), 7, 4)

        return CC1101.ERR_INVALID_RX_BANDWIDTH

    def setFrequencyDeviation(self, freqDev):
        # set frequency deviation to lowest available setting (required for digimodes)
        newFreqDev = freqDev
        if freqDev < 0.0:
            newFreqDev = 1.587

        # check range unless 0 (special value)
        if freqDev != 0:
            # FIXME
            #RADIOLIB_CHECK_RANGE(newFreqDev, 1.587, 380.8, RADIOLIB_ERR_INVALID_FREQUENCY_DEVIATION);
            pass
        
        # set mode to standby
        self.write_command(CC1101.SIDLE)

        # calculate exponent and mantissa values
        (e, m) = self.getExpMant(newFreqDev * 1000.0, 8, 17, 7)

        # set frequency deviation value
        state  = self.SPIsetRegValue(CC1101.DEVIATN, (int(e) << 4), 6, 4)
        state |= self.SPIsetRegValue(CC1101.DEVIATN, int(m), 2, 0)
        
        return state

    def setPreambleLength(self, preambleLength):
        # check allowed values
        if preambleLength == 16:
            value = CC1101.CC1101_NUM_PREAMBLE_2
            
        elif preambleLength == 24:
            value = CC1101.CC1101_NUM_PREAMBLE_3
            
        elif preambleLength == 32:
            value = CC1101.CC1101_NUM_PREAMBLE_4
            
        elif preambleLength == 48:
            value = CC1101.CC1101_NUM_PREAMBLE_6
            
        elif preambleLength == 64:
            value = CC1101.CC1101_NUM_PREAMBLE_8
            
        elif preambleLength == 96:
            value = CC1101.CC1101_NUM_PREAMBLE_12
            
        elif preambleLength == 128:
            value = CC1101.CC1101_NUM_PREAMBLE_16
            
        elif preambleLength == 192:
            value = CC1101.CC1101_NUM_PREAMBLE_24
            
        else:
            return CC1101.ERR_INVALID_PREAMBLE_LENGTH
        
        return self.SPIsetRegValue(CC1101.MDMCFG1, value, 6, 4)

    def variablePacketLengthMode(self, maxLen):
        return self.setPacketMode(CC1101.CC1101_LENGTH_CONFIG_VARIABLE, maxLen)

    def fixedPacketLengthMode(self, length):
        return self.setPacketMode(CC1101.CC1101_LENGTH_CONFIG_FIXED, length)

    def setPacketMode(self, mode, length):
        # check length
        if length > CC1101.CC1101_MAX_PACKET_LENGTH:
            return CC1101.ERR_PACKET_TOO_LONG
         
        # set PKTCTRL0.LENGTH_CONFIG
        state = self.SPIsetRegValue(CC1101.PKTCTRL0, mode, 1, 0)
        # RADIOLIB_ASSERT(state);

        # set length to register
        state = self.SPIsetRegValue(CC1101.PKTLEN, length)
        # RADIOLIB_ASSERT(state);

        # update the cached value
        self._packetLength = length
        self._packetLengthConfig = mode
        return state

    def packetMode(self):
        state  = self.SPIsetRegValue(CC1101.PKTCTRL1, CC1101.CC1101_CRC_AUTOFLUSH_OFF | CC1101.CC1101_APPEND_STATUS_ON | CC1101.CC1101_ADR_CHK_NONE, 3, 0)
        state |= self.SPIsetRegValue(CC1101.PKTCTRL0, CC1101.CC1101_WHITE_DATA_OFF | CC1101.CC1101_PKT_FORMAT_NORMAL, 6, 4)
        # Use current _crcOn state to match RadioLib configuration
        crcSetting = CC1101.CC1101_CRC_ON if self._crcOn else CC1101.CC1101_CRC_OFF
        state |= self.SPIsetRegValue(CC1101.PKTCTRL0, crcSetting | self._packetLengthConfig, 2, 0)
        return state

    def setCrcFiltering(self, crcOn):
        self._crcOn = crcOn

        if crcOn:
            return self.SPIsetRegValue(CC1101.PKTCTRL0, CC1101.CC1101_CRC_ON, 2, 2)
        else:
            return self.SPIsetRegValue(CC1101.PKTCTRL0, CC1101.CC1101_CRC_OFF, 2, 2)
    
    def setSyncWord(self, syncH, syncL, maxErrBits, requireCarrierSense):
        syncWord = [ syncH, syncL ]
        return self.setSyncWord2(syncWord, maxErrBits, requireCarrierSense)
    
    def setSyncWord2(self, syncWord, maxErrBits, requireCarrierSense):
        if (maxErrBits > 1) or (len(syncWord) != 2):
            return CC1101.ERR_INVALID_SYNC_WORD

        # sync word must not contain value 0x00
        for w in syncWord:
            if w == 0x00:
                return CC1101.ERR_INVALID_SYNC_WORD

        # enable sync word filtering
        state = self.enableSyncWordFiltering(maxErrBits, requireCarrierSense)
        # RADIOLIB_ASSERT(state);

        # set sync word register
        state  = self.SPIsetRegValue(CC1101.SYNC1, syncWord[0])
        state |= self.SPIsetRegValue(CC1101.SYNC0, syncWord[1])

        return state

    def enableSyncWordFiltering(self, maxErrBits, requireCarrierSense):
        if maxErrBits == 0:
            # in 16 bit sync word, expect all 16 bits
            return self.SPIsetRegValue(CC1101.MDMCFG2, CC1101.CC1101_SYNC_MODE_16_16_THR if requireCarrierSense else CC1101.CC1101_SYNC_MODE_16_16, 2, 0)
        
        elif maxErrBits == 1:
            # in 16 bit sync word, expect at least 15 bits
            return self.SPIsetRegValue(CC1101.MDMCFG2, CC1101.CC1101_SYNC_MODE_15_16_THR if requireCarrierSense else CC1101.CC1101_SYNC_MODE_15_16, 2, 0)
        
        else:
            return CC1101.ERR_INVALID_SYNC_WORD

    def disableSyncWordFiltering(self, requireCarrierSense):
        return self.SPIsetRegValue(CC1101.MDMCFG2, CC1101.CC1101_SYNC_MODE_NONE_THR if requireCarrierSense else CC1101.CC1101_SYNC_MODE_NONE, 2, 0)

    def getRSSI(self):
        # In packet mode with appended status bytes, use the RSSI from packet status
        # Otherwise, read from RSSI register
        if self._rawRSSI is not None:
            # Use RSSI from packet status bytes
            if self._rawRSSI >= 128:
                rssi = ((self._rawRSSI - 256.0)/2.0) - 74.0
            else:
                rssi = ((self._rawRSSI)/2.0) - 74.0
        else:
            # Fall back to reading RSSI register (works in both direct and packet mode)
            rawRssi = self.read_register(CC1101.RSSI)
            if rawRssi >= 128:
                rssi = ((rawRssi - 256) / 2) - 74
            else:
                rssi = (rawRssi / 2) - 74
        
        return rssi


if __name__ == "__main__":
    # Demo the connection to a CC1101 by reading values from the chip

    cc1101 = CC1101(config.SPI_ID, config.SS_PIN, config.GDO0_PIN, config.GDO2_PIN)

    # Read status byte
    status = cc1101.write_command(CC1101.SNOP)
    print("Status byte", hex(status), bin(status))

    # Read version
    version = cc1101.read_register(CC1101.VERSION, CC1101.STATUS_REGISTER)
    print("VERSION", hex(version))

    # Prove burst and single register access deliver same results
    burst = cc1101.read_burst(CC1101.IOCFG2, 3)
    for i in range(len(burst)):
        print(hex(burst[i]), end=' ')
    print()

    for register in (CC1101.IOCFG2, CC1101.IOCFG1, CC1101.IOCFG0):
        print(hex(cc1101.read_register(register)), end=' ')
    print()
