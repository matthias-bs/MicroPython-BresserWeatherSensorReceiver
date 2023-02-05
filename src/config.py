# Configuration for cc1101.py
#
# These are the values which are dependent on the microcontroller
# and development board hardware design. This module connects 
# cc1101.py to your setup. 
# Aside from these constants no further configuration is required. 
# Most of the values are used as default function arguments, so
# changing them after the program has started has no effect.
#
# Released under MIT license

BOARD               = "Generic ESP32"            # Reminder which board you have configured. Has no effect.

# ESP32:
# HSPI (id=1)
# VSPI (id=2)
# see https://docs.micropython.org/en/latest/esp32/quickref.html#hardware-spi-bus
SPI_ID_LIST         = [2]                        # List with all possible SPI hardware channel ID's for your board
MISO_PIN_PER_SPI_ID = {"2": 19}                  # Pin number of MISO for every SPI channel ID of your board

SPI_ID   = 2   # Hardware SPI channel ID to use for communication with your CC1101
SS_PIN   = 27  # Slave select pin connected to CC1101's CSn. Dependent on your hardware design
GDO0_PIN = 21  # Pin connected to CC101's GDO2 pin. Dependent on your hardware design
GDO2_PIN = 33  # Pin connected to CC101's GDO2 pin. Dependent on your hardware design
