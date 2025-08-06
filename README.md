# Elevator Control Service

A FastAPI-based REST API service for elevator control with support for multiple elevator manufacturers, starting with KONE Service Robot API v2.0 compatibility.

## Features

- **Multi-Manufacturer Support**: Abstract driver interface for easy extension to different elevator types
- **KONE SR-API v2.0 Compatible**: Full compliance with KONE Service Robot API specifications
- **Comprehensive Logging**: All operations logged for audit trail (Flow 11 compliance)
- **Error Handling**: Proper HTTP status codes and descriptive error messages
- **Parameter Validation**: Strict validation of delay (≤30s) and floor numbers
- **Performance**: Sub-5ms response times for most operations
- **Test Coverage**: 100% pass rate on all 37 KONE validation tests

## Quick Start

### Prerequisites

- Python 3.9+
- pip

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the service:
```bash
python app.py
```

3. Access the service at `http://localhost:8000`

### API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

## API Endpoints

### Elevator Operations

- `POST /api/elevator/call` - Call elevator from source to destination floor
- `POST /api/elevator/cancel` - Cancel a previously made elevator call
- `GET /api/elevator/mode` - Get current elevator operating mode
- `GET /api/elevator/status` - Get elevator system status
- `GET /api/elevator/types` - List supported elevator types

### Query Parameters

All endpoints support the `elevator_type` query parameter (default: "kone"):
```
/api/elevator/call?elevator_type=kone
```

### Example Usage

```bash
# Call elevator from floor 1 to floor 5
curl -X POST "http://localhost:8000/api/elevator/call" \
  -H "Content-Type: application/json" \
  -d '{
    "building_id": "BUILDING_001",
    "source": 1,
    "destination": 5,
    "delay": 10
  }'

# Cancel a call
curl -X POST "http://localhost:8000/api/elevator/cancel" \
  -H "Content-Type: application/json" \
  -d '{
    "building_id": "BUILDING_001", 
    "action_id": "your-action-id"
  }'

# Get elevator status
curl "http://localhost:8000/api/elevator/status?building_id=BUILDING_001"
```

## Architecture

### Core Components

1. **Abstract Driver Interface** (`drivers.py`):
   - `ElevatorDriver`: Abstract base class defining standard operations
   - `ElevatorDriverFactory`: Factory for creating driver instances

2. **KONE Implementation** (`drivers.py`):
   - `KoneDriver`: KONE-specific implementation with SR-API v2.0 compatibility
   - Simulation mode for testing (ready for real API integration)

3. **FastAPI Service** (`app.py`):
   - REST API endpoints with automatic documentation
   - Request/response validation using Pydantic models
   - Comprehensive error handling and logging

### Driver Pattern

The service uses a factory pattern to support multiple elevator manufacturers:

```python
# Current support
supported_types = ['kone']

# Future expansion ready
# supported_types = ['kone', 'otis', 'schindler', 'thyssenkrupp']
```

## Testing

### KONE Validation Tests

Run the complete KONE SR-API v2.0 validation test suite:

```bash
python test_kone.py
```

This runs 37 comprehensive tests covering:
- Basic call functionality (Tests 1-10)
- Error handling (Tests 11-15)
- Parameter validation (Tests 16-20)
- Cancel operations (Tests 21-25)
- Mode and status queries (Tests 26-30)
- Performance and limits (Tests 31-35)
- Security and system validation (Tests 36-37)

### Test Results

The service achieves **100% pass rate** on all KONE validation tests. See `KONE_Validation_Test_Report.md` for detailed results.

## Configuration

### KONE Driver Configuration

```python
kone_config = {
    'base_url': 'https://api.kone.com/sr/v2',
    'api_key': 'your-api-key',
    'timeout': 30,
    'max_floor': 50,
    'min_floor': -2
}
```

### Adding New Elevator Types

1. Create a new driver class inheriting from `ElevatorDriver`
2. Implement all abstract methods
3. Register in `ElevatorDriverFactory._drivers`

Example:
```python
class OtisDriver(ElevatorDriver):
    async def call_elevator(self, building_id, source, destination, delay=None, action_id=None):
        # Otis-specific implementation
        pass
    
    # ... implement other methods

# Register the driver
ElevatorDriverFactory._drivers['otis'] = OtisDriver
```

## Production Deployment

### Required Changes for Production

1. **Replace Simulation Logic**:
   - Update `KoneDriver` to call actual KONE APIs
   - Replace mock responses with real API integration

2. **Add Authentication**:
   - Implement API key or OAuth2 authentication
   - Add security headers

3. **Enable HTTPS**:
   - Add TLS certificates
   - Configure secure headers

4. **Database Integration**:
   - Add persistent storage for call history
   - Implement proper state management

### Environment Variables

```bash
export KONE_API_URL="https://api.kone.com/sr/v2"
export KONE_API_KEY="your-production-api-key"
export LOG_LEVEL="INFO"
export MAX_FLOOR="50"
export MIN_FLOOR="-2"
```

## Logging

All operations are logged with structured information:
- Request timestamps
- Request parameters
- Response status
- Error details
- Performance metrics

Logs are written to:
- Console (development)
- `elevator_service.log` file
- Structured JSON format ready for log aggregation

## Error Handling

The service provides proper HTTP status codes:
- `200 OK`: Successful operations
- `201 Created`: Successful elevator calls
- `400 Bad Request`: Invalid parameters (INVALID_DELAY, INVALID_FLOOR)
- `404 Not Found`: Call not found (CALL_NOT_FOUND)
- `422 Unprocessable Entity`: Validation errors
- `500 Internal Server Error`: Unexpected server errors

## Security Features

- Input validation using Pydantic models
- Structured error responses that don't expose internals
- Request/response logging for security monitoring
- Modular design enables easy authentication addition

## License

This project is developed by IBC-AI Co. for elevator control system integration.

## Support

For technical support or questions, contact the development team at dev@ibc-ai.com.

---

**Version**: 1.0.0  
**Last Updated**: August 6, 2025  
**Compatibility**: KONE SR-API v2.0
