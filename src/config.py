"""Configuration for cc1101.py"""
###################################################################################################
# config.py
#
# Bresser Weather Sensor Receiver
#
# CC1101 radio module hardware interface configuration
#
# These are the values which are dependent on the microcontroller and development board
# hardware design. This module connects cc1101.py to your setup.
# Aside from these constants no further configuration is required. 
# Most of the values are used as default function arguments, so changing them after the program
# has started has no effect.
#
# created: 02/2026
#
# MIT License
#
# Copyright (c) 2026 Matthias Prinke
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
###################################################################################################

BOARD = "Generic ESP32" # Reminder which board you have configured. Has no effect.

# ESP32:
# HSPI (id=1)
# VSPI (id=2)
# see https://docs.micropython.org/en/latest/esp32/quickref.html#hardware-spi-bus
SPI_ID_LIST         = [2]       # List with all possible SPI hardware channel ID's for your board
MISO_PIN_PER_SPI_ID = {"2": 19} # Pin number of MISO for every SPI channel ID of your board

SPI_ID   = 2   # Hardware SPI channel ID to use for communication with your CC1101
SS_PIN   = 27  # Slave select pin connected to CC1101's CSn. Dependent on your hardware design
GDO0_PIN = 21  # Pin connected to CC101's GDO2 pin. Dependent on your hardware design
GDO2_PIN = 33  # Pin connected to CC101's GDO2 pin. Dependent on your hardware design
