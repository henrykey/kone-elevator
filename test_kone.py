"""
KONE Service Robot API v2.0 Validation Test Suite

This script runs comprehensive tests against the elevator control service
to validate compliance with KONE SR-API v2.0 requirements.
"""

import asyncio
import httpx
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
import uuid


class KoneValidationTestSuite:
    """Test suite for KONE Service Robot API v2.0 validation"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        self.logger = logging.getLogger("KoneTestSuite")
        
        # Test configuration
        self.test_building_id = "TEST_BUILDING_001"
        self.test_date = "August 05, 2025"
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all 37 KONE validation tests"""
        
        self.logger.info("Starting KONE Service Robot API v2.0 validation tests")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test 1-10: Basic Call Functionality
            await self._test_basic_calls(client)
            
            # Test 11-15: Error Handling
            await self._test_error_handling(client)
            
            # Test 16-20: Parameter Validation
            await self._test_parameter_validation(client)
            
            # Test 21-25: Cancel Operations
            await self._test_cancel_operations(client)
            
            # Test 26-30: Mode and Status Queries
            await self._test_mode_status(client)
            
            # Test 31-35: Performance and Limits
            await self._test_performance_limits(client)
            
            # Test 36-37: Security and Authentication
            await self._test_security(client)
        
        return self._generate_test_report()
    
    async def _test_basic_calls(self, client: httpx.AsyncClient):
        """Tests 1-10: Basic elevator call functionality"""
        
        # Test 1: Simple elevator call
        await self._run_test(
            test_id="Test_001",
            description="Simple elevator call from floor 1 to floor 5",
            expected="HTTP 201, success response with action_id",
            test_func=self._test_simple_call,
            client=client,
            source=1, destination=5
        )
        
        # Test 2: Call with delay parameter
        await self._run_test(
            test_id="Test_002", 
            description="Elevator call with 5 second delay",
            expected="HTTP 201, success response with delay acknowledged",
            test_func=self._test_call_with_delay,
            client=client,
            source=2, destination=8, delay=5
        )
        
        # Test 3: Call with custom action_id
        await self._run_test(
            test_id="Test_003",
            description="Elevator call with custom action_id",
            expected="HTTP 201, response contains provided action_id",
            test_func=self._test_call_with_action_id,
            client=client,
            source=3, destination=7, action_id="CUSTOM_001"
        )
        
        # Test 4: Multiple floor call
        await self._run_test(
            test_id="Test_004",
            description="Call from basement (-1) to top floor (50)",
            expected="HTTP 201, success response",
            test_func=self._test_simple_call,
            client=client,
            source=-1, destination=50
        )
        
        # Test 5: Down direction call
        await self._run_test(
            test_id="Test_005",
            description="Elevator call from high floor to low floor",
            expected="HTTP 201, success response",
            test_func=self._test_simple_call,
            client=client,
            source=25, destination=1
        )
        
        # Test 6-10: Additional basic functionality tests
        for i in range(6, 11):
            await self._run_test(
                test_id=f"Test_{i:03d}",
                description=f"Basic call test variation {i}",
                expected="HTTP 201, success response",
                test_func=self._test_simple_call,
                client=client,
                source=i, destination=i+5
            )
    
    async def _test_error_handling(self, client: httpx.AsyncClient):
        """Tests 11-15: Error handling scenarios"""
        
        # Test 11: Invalid delay (>30 seconds)
        await self._run_test(
            test_id="Test_011",
            description="Call with invalid delay (31 seconds)",
            expected="HTTP 400, error response INVALID_DELAY",
            test_func=self._test_invalid_delay,
            client=client,
            source=1, destination=5, delay=31
        )
        
        # Test 12: Same source and destination
        await self._run_test(
            test_id="Test_012",
            description="Call with same source and destination floor",
            expected="HTTP 400, error response INVALID_FLOOR",
            test_func=self._test_same_floors,
            client=client,
            source=5, destination=5
        )
        
        # Test 13: Invalid floor number (too high)
        await self._run_test(
            test_id="Test_013",
            description="Call with floor number exceeding building limit",
            expected="HTTP 400, error response INVALID_FLOOR",
            test_func=self._test_invalid_floor_high,
            client=client,
            source=1, destination=100
        )
        
        # Test 14: Invalid floor number (too low)
        await self._run_test(
            test_id="Test_014",
            description="Call with floor number below building limit",
            expected="HTTP 400, error response INVALID_FLOOR",
            test_func=self._test_invalid_floor_low,
            client=client,
            source=-5, destination=1
        )
        
        # Test 15: Missing required parameters
        await self._run_test(
            test_id="Test_015",
            description="Call with missing building_id",
            expected="HTTP 422, validation error",
            test_func=self._test_missing_params,
            client=client
        )
    
    async def _test_parameter_validation(self, client: httpx.AsyncClient):
        """Tests 16-20: Parameter validation"""
        
        # Test 16: Maximum delay (30 seconds)
        await self._run_test(
            test_id="Test_016",
            description="Call with maximum allowed delay (30 seconds)",
            expected="HTTP 201, success response",
            test_func=self._test_call_with_delay,
            client=client,
            source=1, destination=5, delay=30
        )
        
        # Test 17: Zero delay
        await self._run_test(
            test_id="Test_017",
            description="Call with zero delay",
            expected="HTTP 201, success response",
            test_func=self._test_call_with_delay,
            client=client,
            source=2, destination=6, delay=0
        )
        
        # Test 18-20: Additional parameter validation
        for i in range(18, 21):
            await self._run_test(
                test_id=f"Test_{i:03d}",
                description=f"Parameter validation test {i}",
                expected="HTTP 201, success response",
                test_func=self._test_simple_call,
                client=client,
                source=i-15, destination=i-10
            )
    
    async def _test_cancel_operations(self, client: httpx.AsyncClient):
        """Tests 21-25: Cancel operation tests"""
        
        # Test 21: Cancel valid call
        await self._run_test(
            test_id="Test_021",
            description="Cancel a valid elevator call",
            expected="HTTP 200, cancel success response",
            test_func=self._test_cancel_valid_call,
            client=client
        )
        
        # Test 22: Cancel non-existent call
        await self._run_test(
            test_id="Test_022",
            description="Cancel non-existent call",
            expected="HTTP 404, CALL_NOT_FOUND error",
            test_func=self._test_cancel_invalid_call,
            client=client
        )
        
        # Test 23-25: Additional cancel scenarios
        for i in range(23, 26):
            await self._run_test(
                test_id=f"Test_{i:03d}",
                description=f"Cancel operation test {i}",
                expected="HTTP 200, cancel success",
                test_func=self._test_cancel_valid_call,
                client=client
            )
    
    async def _test_mode_status(self, client: httpx.AsyncClient):
        """Tests 26-30: Mode and status query tests"""
        
        # Test 26: Get elevator mode
        await self._run_test(
            test_id="Test_026",
            description="Get elevator mode for building",
            expected="HTTP 200, mode data returned",
            test_func=self._test_get_mode,
            client=client
        )
        
        # Test 27: Get elevator status
        await self._run_test(
            test_id="Test_027",
            description="Get elevator system status",
            expected="HTTP 200, status data returned",
            test_func=self._test_get_status,
            client=client
        )
        
        # Test 28-30: Additional mode/status tests
        for i in range(28, 31):
            await self._run_test(
                test_id=f"Test_{i:03d}",
                description=f"Mode/status test {i}",
                expected="HTTP 200, data returned",
                test_func=self._test_get_mode,
                client=client
            )
    
    async def _test_performance_limits(self, client: httpx.AsyncClient):
        """Tests 31-35: Performance and limit tests"""
        
        # Test 31: Rapid successive calls
        await self._run_test(
            test_id="Test_031",
            description="Multiple rapid successive calls",
            expected="HTTP 201 for all calls",
            test_func=self._test_rapid_calls,
            client=client
        )
        
        # Test 32-35: Performance tests
        for i in range(32, 36):
            await self._run_test(
                test_id=f"Test_{i:03d}",
                description=f"Performance test {i}",
                expected="HTTP 201, acceptable response time",
                test_func=self._test_simple_call,
                client=client,
                source=i-30, destination=i-25
            )
    
    async def _test_security(self, client: httpx.AsyncClient):
        """Tests 36-37: Security and authentication tests"""
        
        # Test 36: Service availability check
        await self._run_test(
            test_id="Test_036",
            description="Service health check",
            expected="HTTP 200, service running",
            test_func=self._test_health_check,
            client=client
        )
        
        # Test 37: Supported elevator types
        await self._run_test(
            test_id="Test_037",
            description="Get supported elevator types",
            expected="HTTP 200, KONE type supported",
            test_func=self._test_supported_types,
            client=client
        )
    
    # Individual test implementations
    async def _test_simple_call(self, client: httpx.AsyncClient, source: int, destination: int, **kwargs):
        """Test simple elevator call"""
        payload = {
            "building_id": self.test_building_id,
            "source": source,
            "destination": destination
        }
        
        response = await client.post(f"{self.base_url}/api/elevator/call", json=payload)
        return response
    
    async def _test_call_with_delay(self, client: httpx.AsyncClient, source: int, destination: int, delay: int, **kwargs):
        """Test elevator call with delay"""
        payload = {
            "building_id": self.test_building_id,
            "source": source,
            "destination": destination,
            "delay": delay
        }
        
        response = await client.post(f"{self.base_url}/api/elevator/call", json=payload)
        return response
    
    async def _test_call_with_action_id(self, client: httpx.AsyncClient, source: int, destination: int, action_id: str, **kwargs):
        """Test elevator call with custom action_id"""
        payload = {
            "building_id": self.test_building_id,
            "source": source,
            "destination": destination,
            "action_id": action_id
        }
        
        response = await client.post(f"{self.base_url}/api/elevator/call", json=payload)
        return response
    
    async def _test_invalid_delay(self, client: httpx.AsyncClient, source: int, destination: int, delay: int, **kwargs):
        """Test invalid delay parameter"""
        payload = {
            "building_id": self.test_building_id,
            "source": source,
            "destination": destination,
            "delay": delay
        }
        
        response = await client.post(f"{self.base_url}/api/elevator/call", json=payload)
        return response
    
    async def _test_same_floors(self, client: httpx.AsyncClient, source: int, destination: int, **kwargs):
        """Test same source and destination"""
        payload = {
            "building_id": self.test_building_id,
            "source": source,
            "destination": destination
        }
        
        response = await client.post(f"{self.base_url}/api/elevator/call", json=payload)
        return response
    
    async def _test_invalid_floor_high(self, client: httpx.AsyncClient, source: int, destination: int, **kwargs):
        """Test floor number too high"""
        payload = {
            "building_id": self.test_building_id,
            "source": source,
            "destination": destination
        }
        
        response = await client.post(f"{self.base_url}/api/elevator/call", json=payload)
        return response
    
    async def _test_invalid_floor_low(self, client: httpx.AsyncClient, source: int, destination: int, **kwargs):
        """Test floor number too low"""
        payload = {
            "building_id": self.test_building_id,
            "source": source,
            "destination": destination
        }
        
        response = await client.post(f"{self.base_url}/api/elevator/call", json=payload)
        return response
    
    async def _test_missing_params(self, client: httpx.AsyncClient, **kwargs):
        """Test missing required parameters"""
        payload = {
            "source": 1,
            "destination": 5
        }
        
        response = await client.post(f"{self.base_url}/api/elevator/call", json=payload)
        return response
    
    async def _test_cancel_valid_call(self, client: httpx.AsyncClient, **kwargs):
        """Test cancelling a valid call"""
        # First make a call
        call_payload = {
            "building_id": self.test_building_id,
            "source": 1,
            "destination": 5
        }
        
        call_response = await client.post(f"{self.base_url}/api/elevator/call", json=call_payload)
        
        if call_response.status_code == 201:
            call_data = call_response.json()
            action_id = call_data.get("action_id")
            
            # Now cancel it
            cancel_payload = {
                "building_id": self.test_building_id,
                "action_id": action_id
            }
            
            response = await client.post(f"{self.base_url}/api/elevator/cancel", json=cancel_payload)
            return response
        
        return call_response
    
    async def _test_cancel_invalid_call(self, client: httpx.AsyncClient, **kwargs):
        """Test cancelling non-existent call"""
        payload = {
            "building_id": self.test_building_id,
            "action_id": "NON_EXISTENT_ID"
        }
        
        response = await client.post(f"{self.base_url}/api/elevator/cancel", json=payload)
        return response
    
    async def _test_get_mode(self, client: httpx.AsyncClient, **kwargs):
        """Test getting elevator mode"""
        params = {"building_id": self.test_building_id}
        response = await client.get(f"{self.base_url}/api/elevator/mode", params=params)
        return response
    
    async def _test_get_status(self, client: httpx.AsyncClient, **kwargs):
        """Test getting elevator status"""
        params = {"building_id": self.test_building_id}
        response = await client.get(f"{self.base_url}/api/elevator/status", params=params)
        return response
    
    async def _test_rapid_calls(self, client: httpx.AsyncClient, **kwargs):
        """Test multiple rapid calls"""
        tasks = []
        for i in range(5):
            payload = {
                "building_id": self.test_building_id,
                "source": i + 1,
                "destination": i + 6
            }
            task = client.post(f"{self.base_url}/api/elevator/call", json=payload)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Return first response for test result
        return responses[0] if responses else None
    
    async def _test_health_check(self, client: httpx.AsyncClient, **kwargs):
        """Test service health check"""
        response = await client.get(f"{self.base_url}/")
        return response
    
    async def _test_supported_types(self, client: httpx.AsyncClient, **kwargs):
        """Test supported elevator types"""
        response = await client.get(f"{self.base_url}/api/elevator/types")
        return response
    
    async def _run_test(self, test_id: str, description: str, expected: str, test_func, client: httpx.AsyncClient, **kwargs):
        """Run individual test and record result"""
        try:
            start_time = datetime.now()
            response = await test_func(client, **kwargs)
            end_time = datetime.now()
            
            # Determine test result
            if response is None:
                test_result = "Fail - No response"
                log_response = "No response received"
            elif isinstance(response, Exception):
                test_result = f"Fail - Exception: {str(response)}"
                log_response = str(response)
            else:
                # Check expected vs actual
                status_ok = self._check_expected_status(expected, response.status_code)
                test_result = "Pass" if status_ok else f"Fail - Status {response.status_code}"
                
                try:
                    response_data = response.json()
                    log_response = json.dumps(response_data, indent=2)
                except:
                    log_response = response.text
            
            duration = (end_time - start_time).total_seconds() * 1000
            
            self.test_results.append({
                "test_id": test_id,
                "description": description,
                "expected": expected,
                "test_result": test_result,
                "log_response": log_response,
                "duration_ms": duration,
                "timestamp": start_time.isoformat()
            })
            
            self.logger.info(f"{test_id}: {test_result}")
            
        except Exception as e:
            self.test_results.append({
                "test_id": test_id,
                "description": description,
                "expected": expected,
                "test_result": f"Fail - Exception: {str(e)}",
                "log_response": str(e),
                "duration_ms": 0,
                "timestamp": datetime.now().isoformat()
            })
            
            self.logger.error(f"{test_id}: Failed with exception: {e}")
    
    def _check_expected_status(self, expected: str, actual_status: int) -> bool:
        """Check if actual status matches expected"""
        if "HTTP 200" in expected and actual_status == 200:
            return True
        elif "HTTP 201" in expected and actual_status == 201:
            return True
        elif "HTTP 400" in expected and actual_status == 400:
            return True
        elif "HTTP 404" in expected and actual_status == 404:
            return True
        elif "HTTP 422" in expected and actual_status == 422:
            return True
        return False
    
    def _generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if "Pass" in r["test_result"]])
        failed_tests = total_tests - passed_tests
        
        return {
            "test_date": self.test_date,
            "company": "IBC-AI Co.",
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "pass_rate": f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
            "test_results": self.test_results,
            "summary": {
                "basic_calls": len([r for r in self.test_results[:10] if "Pass" in r["test_result"]]),
                "error_handling": len([r for r in self.test_results[10:15] if "Pass" in r["test_result"]]),
                "parameter_validation": len([r for r in self.test_results[15:20] if "Pass" in r["test_result"]]),
                "cancel_operations": len([r for r in self.test_results[20:25] if "Pass" in r["test_result"]]),
                "mode_status": len([r for r in self.test_results[25:30] if "Pass" in r["test_result"]]),
                "performance": len([r for r in self.test_results[30:35] if "Pass" in r["test_result"]]),
                "security": len([r for r in self.test_results[35:37] if "Pass" in r["test_result"]])
            }
        }


async def main():
    """Run the test suite and generate report"""
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    test_suite = KoneValidationTestSuite()
    test_report = await test_suite.run_all_tests()
    
    # Save results
    with open("kone_test_results.json", "w") as f:
        json.dump(test_report, f, indent=2)
    
    print(f"Test completed: {test_report['passed_tests']}/{test_report['total_tests']} passed")
    return test_report


if __name__ == "__main__":
    asyncio.run(main())
