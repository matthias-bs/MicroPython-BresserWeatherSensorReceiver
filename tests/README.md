# Unit Tests

This directory contains unit tests for the Bresser Weather Sensor decoders.

## Running Tests

### Install Dependencies

```bash
pip install -r requirements-test.txt
```

### Run All Tests

```bash
pytest tests/
```

### Run Tests with Coverage

```bash
pytest tests/ --cov=src --cov-report=term-missing
```

### Run Tests for a Specific Decoder

```bash
# 6-in-1 decoder tests
pytest tests/test_bresser_6in1_decoder.py -v

# 5-in-1 decoder tests
pytest tests/test_bresser_5in1_decoder.py -v

# 7-in-1 decoder tests
pytest tests/test_bresser_7in1_decoder.py -v

# Lightning decoder tests
pytest tests/test_bresser_lightning_decoder.py -v

# Leakage decoder tests
pytest tests/test_bresser_leakage_decoder.py -v
```

## Test Data Sources

The test data comes from two main sources:

1. **Original test data from bresser_decoder.py**: Test messages that were originally in the `main()` function
2. **SensorTransmitter test data**: Raw payload data from [SensorTransmitter.ino](https://github.com/matthias-bs/SensorTransmitter/blob/main/SensorTransmitter.ino)

## Test Structure

Each decoder has its own test file with the following test categories:

- **Valid messages**: Tests with known good payloads that should decode successfully
- **Invalid messages**: Tests with corrupted or invalid checksums/digests
- **Edge cases**: Tests with empty messages, all 0xFF messages, etc.
- **Data structure validation**: Tests that verify the decoded data has the expected structure

## Continuous Integration

Tests are automatically run on GitHub Actions for Python versions 3.9, 3.10, and 3.11 on every push and pull request. See `.github/workflows/pytest.yml` for the workflow configuration.

## Coverage

Current test coverage is approximately 74% for bresser_decoder.py, covering all major decoder functions:
- `decodeBresser6In1Payload()`
- `decodeBresser5In1Payload()`
- `decodeBresser7In1Payload()`
- `decodeBresserLightningPayload()`
- `decodeBresserLeakagePayload()`
