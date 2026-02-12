"""
Unit tests for Bresser Lightning decoder
"""
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from bresser_decoder import (
    decodeBresserLightningPayload,
    DECODE_OK
)


class TestBresserLightningDecoder:
    """Test cases for Bresser Lightning decoder"""

    def test_valid_message(self):
        """Test decoding valid lightning message from bresser_decoder.py"""
        # Test data from C++ code (with 0xaa whitening applied)
        msg = bytes([0x73, 0x69, 0xB5, 0x08, 0xAA, 0xA2, 0x90, 0xAA, 
                     0xAA, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                     0x00, 0x00, 0x00, 0x7F, 0xFF, 0xFF, 0xFF, 0xFF,
                     0xFF, 0xFF])
        status, data = decodeBresserLightningPayload(msg, 26)
        
        assert status == DECODE_OK
        assert data is not None
        assert 'sensor_id' in data
        assert 'battery_ok' in data
        assert 'strike_count' in data
        assert 'distance_km' in data

    def test_raw_payload_from_sensortransmitter(self):
        """Test decoding raw payload from SensorTransmitter.ino rawPayload()"""
        # This is the payload_lightning from SensorTransmitter.ino (whitened data)
        msg = bytes([0x73, 0x69, 0xB5, 0x08, 0xAA, 0xA2, 0x90, 0xAA, 0xAA, 0xAA, 0x00, 0x00, 0x00,
                     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x7F, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
        
        status, data = decodeBresserLightningPayload(msg, 26)
        
        # This is real test data from SensorTransmitter with proper whitening and digest
        assert status == DECODE_OK
        assert data is not None
        assert 'sensor_id' in data
        assert 'battery_ok' in data
        assert 'strike_count' in data
        assert 'distance_km' in data

    def test_empty_message(self):
        """Test decoding empty message"""
        msg = bytes([0x00] * 26)
        status, data = decodeBresserLightningPayload(msg, 26)
        
        # Should fail validation
        assert status != DECODE_OK or data is None

    def test_all_ff_message(self):
        """Test decoding all 0xFF message"""
        msg = bytes([0xFF] * 26)
        status, data = decodeBresserLightningPayload(msg, 26)
        
        # Should fail validation
        assert status != DECODE_OK or data is None

    def test_lightning_data_values(self):
        """Test that lightning data values are reasonable"""
        msg = bytes([0x73, 0x69, 0xB5, 0x08, 0xAA, 0xA2, 0x90, 0xAA, 
                     0xAA, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                     0x00, 0x00, 0x00, 0x7F, 0xFF, 0xFF, 0xFF, 0xFF,
                     0xFF, 0xFF])
        status, data = decodeBresserLightningPayload(msg, 26)
        
        if status == DECODE_OK and data is not None:
            # Check that lightning values are within reasonable ranges
            assert 'strike_count' in data
            assert data['strike_count'] >= 0
            assert 'distance_km' in data
            assert data['distance_km'] >= 0
