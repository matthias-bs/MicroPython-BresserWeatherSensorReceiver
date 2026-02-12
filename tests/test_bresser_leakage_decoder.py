"""
Unit tests for Bresser Leakage decoder
"""
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# pylint: disable=import-error,wrong-import-position
from bresser_decoder import (
    decodeBresserLeakagePayload,
    DECODE_OK
)


class TestBresserLeakageDecoder:
    """Test cases for Bresser Leakage decoder"""

    def test_valid_message(self):
        """Test decoding valid leakage message from bresser_decoder.py"""
        # Test data from issue #77 examples
        msg = bytes([0xC7, 0x70, 0x35, 0x97, 0x04, 0x08, 0x57, 0x70,
                     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                     0x03, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
                     0xFF, 0xFF])
        status, data = decodeBresserLeakagePayload(msg, 26)
        
        assert status == DECODE_OK
        assert data is not None
        assert 'sensor_id' in data
        assert 'battery_ok' in data
        assert 'alarm' in data

    def test_raw_payload_from_sensortransmitter(self):
        """Test decoding raw payload from SensorTransmitter.ino rawPayload()"""
        # This is the payload_leakage from SensorTransmitter.ino
        msg = bytes([0xB3, 0xDA, 0x55, 0x57, 0x17, 0x40, 0x53, 0x70, 0x00, 0x00, 0x00, 0x00, 0x00,
                     0x00, 0x00, 0x00, 0x03, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFB])
        
        status, data = decodeBresserLeakagePayload(msg, 26)
        
        # This is real test data from SensorTransmitter
        assert status == DECODE_OK
        assert data is not None
        assert 'sensor_id' in data
        assert 'battery_ok' in data
        assert 'alarm' in data

    def test_empty_message(self):
        """Test decoding empty message"""
        msg = bytes([0x00] * 26)
        status, data = decodeBresserLeakagePayload(msg, 26)
        
        # Should fail validation
        assert status != DECODE_OK or data is None

    def test_all_ff_message(self):
        """Test decoding all 0xFF message"""
        msg = bytes([0xFF] * 26)
        status, data = decodeBresserLeakagePayload(msg, 26)
        
        # Should fail validation
        assert status != DECODE_OK or data is None

    def test_leakage_alarm_field(self):
        """Test that leakage alarm field is boolean"""
        msg = bytes([0xC7, 0x70, 0x35, 0x97, 0x04, 0x08, 0x57, 0x70,
                     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                     0x03, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
                     0xFF, 0xFF])
        status, data = decodeBresserLeakagePayload(msg, 26)
        
        if status == DECODE_OK and data is not None:
            # Check that alarm is a boolean value
            assert 'alarm' in data
            assert isinstance(data['alarm'], (bool, int))
            # If int, should be 0 or 1
            if isinstance(data['alarm'], int):
                assert data['alarm'] in [0, 1]
