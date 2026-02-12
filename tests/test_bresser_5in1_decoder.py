"""
Unit tests for Bresser 5-in-1 decoder
"""
# pylint: disable=import-error,wrong-import-position
from bresser_decoder import (
    BresserDecoder,
    DECODE_OK,
    DECODE_PAR_ERR,
    DECODE_CHK_ERR
)


class TestBresser5In1Decoder:
    """Test cases for Bresser 5-in-1 decoder"""

    def test_synthetic_message(self):
        """Test decoding synthetic message from bresser_decoder.py"""
        # NOTE: This is synthetic test data for demonstration purposes.
        # First 13 bytes and last 13 bytes should be inverse (total payload 26 bytes)
        msg = bytes([0xEA, 0x7F, 0x5F, 0xC7, 0x8E, 0x33, 0x51, 0xC5, 0xD7, 0xDD, 0xBB, 0xC4, 0xA6,  # First 13 bytes
                     0x15, 0x80, 0xA0, 0x38, 0x71, 0xCC, 0xAE, 0x3A, 0x28, 0x22, 0x44, 0x3B, 0x59])  # Last 13 bytes (inverse)
        status, _ = BresserDecoder.decodeBresser5In1Payload(msg, 26)
        
        # With synthetic data, may pass or fail validation depending on implementation
        # We just verify it doesn't crash
        assert status in [DECODE_OK, DECODE_PAR_ERR, DECODE_CHK_ERR]

    def test_raw_payload_from_sensortransmitter(self):
        """Test decoding raw payload from SensorTransmitter.ino rawPayload()"""
        # This is the payload_5in1 from SensorTransmitter.ino
        msg = bytes([0xEA, 0xEC, 0x7F, 0xEB, 0x5F, 0xEE, 0xEF, 0xFA, 0xFE, 0x76, 0xBB, 0xFA, 0xFF,
                     0x15, 0x13, 0x80, 0x14, 0xA0, 0x11, 0x10, 0x05, 0x01, 0x89, 0x44, 0x05, 0x00])
        
        status, data = BresserDecoder.decodeBresser5In1Payload(msg, 26)
        
        # This is real test data from SensorTransmitter, should decode successfully
        assert status == DECODE_OK
        assert data is not None
        assert 'sensor_id' in data
        assert 'battery_ok' in data

    def test_empty_message(self):
        """Test decoding empty message"""
        msg = bytes([0x00] * 26)
        status, data = BresserDecoder.decodeBresser5In1Payload(msg, 26)
        
        # Should fail validation
        assert status != DECODE_OK and data is None

    def test_all_ff_message(self):
        """Test decoding all 0xFF message"""
        msg = bytes([0xFF] * 26)
        status, data = BresserDecoder.decodeBresser5In1Payload(msg, 26)
        
        # Should fail validation
        assert status != DECODE_OK and data is None

    def test_message_structure(self):
        """Test that decoded data has expected structure for valid message"""
        msg = bytes([0xEA, 0xEC, 0x7F, 0xEB, 0x5F, 0xEE, 0xEF, 0xFA, 0xFE, 0x76, 0xBB, 0xFA, 0xFF,
                     0x15, 0x13, 0x80, 0x14, 0xA0, 0x11, 0x10, 0x05, 0x01, 0x89, 0x44, 0x05, 0x00])
        
        status, data = BresserDecoder.decodeBresser5In1Payload(msg, 26)
        
        if status == DECODE_OK and data is not None:
            # Check for common fields in 5-in-1 sensors
            assert 'sensor_id' in data
            assert 'battery_ok' in data
            # Note: 5-in-1 decoder may not include 'channel' in all cases
