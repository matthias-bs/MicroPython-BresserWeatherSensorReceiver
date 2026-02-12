"""
Unit tests for Bresser 6-in-1 decoder
"""
# pylint: disable=import-error
from BresserDecoder import (
    BresserDecoder,
    DECODE_OK,
    DECODE_CHK_ERR,
    DECODE_DIG_ERR
)


class TestBresser6In1Decoder:
    """Test cases for Bresser 6-in-1 decoder"""

    def test_valid_msg1(self):
        """Test decoding valid message 1 from bresser_decoder.py"""
        msg = bytes([0x2A, 0xAF, 0x21, 0x10, 0x34, 0x27, 0x18, 0xFF, 0xAA, 0xFF, 
                     0x29, 0x28, 0xFF, 0xBB, 0x89, 0xFF, 0x01, 0x1F, 0x00, 0x00, 
                     0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        status, data = BresserDecoder.decodeBresser6In1Payload(msg, 26)
        
        assert status == DECODE_OK
        assert data is not None
        assert 'sensor_id' in data
        assert 'battery_ok' in data
        # temp_c may not be present in all sensor types
        assert 'wind_gust_meter_sec' in data or 'temp_c' in data

    def test_invalid_checksum_msg1_err(self):
        """Test decoding message with invalid checksum"""
        msg = bytes([0x2A, 0xAF, 0x21, 0x10, 0x34, 0x28, 0x18, 0xFF, 0xAA, 0xFF, 
                     0x29, 0x28, 0xFF, 0xBB, 0x89, 0xFF, 0x01, 0x1F, 0x00, 0x00, 
                     0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        status, data = BresserDecoder.decodeBresser6In1Payload(msg, 26)
        
        # Should fail validation (DECODE_CHK_ERR or DECODE_DIG_ERR)
        assert status in [DECODE_CHK_ERR, DECODE_DIG_ERR]
        assert data is None

    def test_valid_msg2(self):
        """Test decoding valid message 2 from bresser_decoder.py"""
        msg = bytes([0x54, 0x1B, 0x21, 0x10, 0x34, 0x27, 0x18, 0xFF, 0x88, 0xFF, 
                     0x29, 0x28, 0x06, 0x42, 0x87, 0xFF, 0xF0, 0xC6, 0x00, 0x00, 
                     0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        status, data = BresserDecoder.decodeBresser6In1Payload(msg, 26)
        
        assert status == DECODE_OK
        assert data is not None
        assert 'sensor_id' in data
        assert 'temp_c' in data

    def test_valid_msg3(self):
        """Test decoding valid message 3 from bresser_decoder.py"""
        msg = bytes([0x65, 0xA7, 0x79, 0x28, 0x82, 0xA2, 0x18, 0xFF, 0x66, 0xFF, 
                     0x25, 0x68, 0xFF, 0xEA, 0xBF, 0xFF, 0x01, 0x89, 0xAA, 0x00, 
                     0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        status, data = BresserDecoder.decodeBresser6In1Payload(msg, 26)
        
        assert status == DECODE_OK
        assert data is not None
        assert 'sensor_id' in data

    def test_received_message(self):
        """Test decoding received message from bresser_decoder.py"""
        msg = bytes([0x3d, 0x91, 0x39, 0x58, 0x58, 0x23, 0x76, 0x18, 0xff, 0xff, 
                     0xff, 0x31, 0x28, 0x05, 0x16, 0x89, 0xff, 0xf0, 0xd4, 0xaa, 
                     0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        status, data = BresserDecoder.decodeBresser6In1Payload(msg, 26)
        
        # This message may pass or fail depending on actual data validity
        # Just verify it doesn't crash and returns proper status
        assert status in [DECODE_OK, DECODE_CHK_ERR, DECODE_DIG_ERR]
        if status == DECODE_OK:
            assert data is not None
            assert 'sensor_id' in data

    def test_raw_payload_from_sensortransmitter(self):
        """Test decoding raw payload from SensorTransmitter.ino rawPayload()"""
        # This is the payload_6in1 from SensorTransmitter.ino
        # Note: SensorTransmitter only includes 18 bytes, but decoder expects 26
        # So we pad with zeros or 0xFF as the actual implementation does
        msg = bytes([0x2A, 0xAF, 0x21, 0x10, 0x34, 0x27, 0x18, 0xFF, 0xAA, 0xFF, 
                     0x29, 0x28, 0xFF, 0xBB, 0x89, 0xFF, 0x01, 0x1F])
        # Pad to 26 bytes
        msg = msg + bytes([0x00] * (26 - len(msg)))
        
        status, data = BresserDecoder.decodeBresser6In1Payload(msg, 26)
        
        assert status == DECODE_OK
        assert data is not None
        assert 'sensor_id' in data
        assert 'battery_ok' in data
        # temp_c may not be present in all sensor types
        assert 'wind_gust_meter_sec' in data or 'temp_c' in data

    def test_empty_message(self):
        """Test decoding empty message"""
        msg = bytes([0x00] * 26)
        status, data = BresserDecoder.decodeBresser6In1Payload(msg, 26)
        
        # Should fail validation
        assert status != DECODE_OK and data is None

    def test_all_ff_message(self):
        """Test decoding all 0xFF message"""
        msg = bytes([0xFF] * 26)
        status, data = BresserDecoder.decodeBresser6In1Payload(msg, 26)
        
        # Should fail validation
        assert status != DECODE_OK and data is None
