"""
Unit tests for Bresser 7-in-1 decoder
"""
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from bresser_decoder import (
    decodeBresser7In1Payload,
    DECODE_OK
)


class TestBresser7In1Decoder:
    """Test cases for Bresser 7-in-1 decoder"""

    def test_placeholder_message(self):
        """Test decoding placeholder message from bresser_decoder.py"""
        # NOTE: This is placeholder data for demonstration purposes.
        msg = bytes([0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 
                     0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA,
                     0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA,
                     0xAA, 0xAA])
        status, data = decodeBresser7In1Payload(msg, 26)
        
        # Expected to fail with placeholder data
        assert status != DECODE_OK or data is None

    def test_raw_payload_from_sensortransmitter(self):
        """Test decoding raw payload from SensorTransmitter.ino rawPayload()"""
        # This is the payload_7in1 from SensorTransmitter.ino (whitened data)
        msg = bytes([0xC4, 0xD6, 0x3A, 0xC5, 0xBD, 0xFA, 0x18, 0xAA, 0xAA, 0xAA, 0xAA, 0xAB, 0xFC,
                     0xAA, 0x98, 0xDA, 0x89, 0xA3, 0x2F, 0xEC, 0xAF, 0x9A, 0xAA, 0xAA, 0xAA, 0x00])
        
        status, data = decodeBresser7In1Payload(msg, 26)
        
        # This is real test data from SensorTransmitter with proper whitening and digest
        assert status == DECODE_OK
        assert data is not None
        assert 'sensor_id' in data
        assert 'battery_ok' in data

    def test_empty_message(self):
        """Test decoding empty message"""
        msg = bytes([0x00] * 26)
        status, data = decodeBresser7In1Payload(msg, 26)
        
        # Should fail validation
        assert status != DECODE_OK or data is None

    def test_all_ff_message(self):
        """Test decoding all 0xFF message"""
        msg = bytes([0xFF] * 26)
        status, data = decodeBresser7In1Payload(msg, 26)
        
        # Should fail validation
        assert status != DECODE_OK or data is None

    def test_message_structure(self):
        """Test that decoded data has expected structure for valid message"""
        msg = bytes([0xC4, 0xD6, 0x3A, 0xC5, 0xBD, 0xFA, 0x18, 0xAA, 0xAA, 0xAA, 0xAA, 0xAB, 0xFC,
                     0xAA, 0x98, 0xDA, 0x89, 0xA3, 0x2F, 0xEC, 0xAF, 0x9A, 0xAA, 0xAA, 0xAA, 0x00])
        
        status, data = decodeBresser7In1Payload(msg, 26)
        
        if status == DECODE_OK and data is not None:
            # Check for common fields in 7-in-1 sensors
            assert 'sensor_id' in data
            assert 'battery_ok' in data
            assert 'channel' in data
