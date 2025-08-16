# KONE Service Robot API Solution Validation Test Report

**SR-API (Service Robot API)**  
**Version**: 2.0  
**Author**: IBC-AI CO.

---

## Document Purpose

Ensuring the quality and security of a solution is every developer's responsibility. This document gives guidance on evaluating the readiness of those solutions that use Service Robot API.

---

## Test Information

### Setup
Get access to the equipment for testing:
- Virtual equipment, available in KONE API portal
- Preproduction equipment, by contacting KONE API Support

### Pre-Test Setup  
Test environments available for the correct KONE API organization.
Building id can be retrieved (/resource endpoint).

### Date
| Test Date (dd.mm.yyyy) | Value |
|-------------------------|-------|
| Test execution date     | 16.08.2025 |

### Solution Provider
| Item                 | Value |
|----------------------|-------|
| Company name         | IBC-AI CO. |
| Company address      | 123 Test Street, Test City |
| Contact person name  | Test Engineer |
| Email                | test@ibc-ai.com |
| Telephone number     | +1-555-0123 |
| Tester               | Automated Test System |

### Tested System
| Item                     | Value |
|--------------------------|-------|
| System name              | KONE Elevator Control Service |
| System version           | 待填写 |
| Software name            | 待填写 |
| Software version         | 待填写 |
| KONE SR-API              | v2.0 |
| KONE test assistant email | 待填写 |

---

## Test Summary

| Metric | Value |
|--------|-------|
| Total Tests | 2 |
| Passed | 1 ✅ |
| Failed | 1 ❌ |
| Errors | 0 ⚠️ |
| Skipped | 0 ⏭️ |
| Success Rate | 50.0% |
| Total Duration | 2.30 seconds |

---

## Authentication & Token Scope Validation

This section provides detailed information about OAuth2 token validation and scope verification. 
Token validation helps identify whether test failures are due to authentication/authorization issues rather than test script problems.

### Token Scope Validation Results

| Requested Scope | Token Scopes | Match | Status | Error Message |
|----------------|--------------|-------|--------|---------------|
| `callv2/group:L1QinntdEOg:1` | `callv2/group:L1QinntdEOg:1 application/inventory` | True | ✅ | - |
| `callgiving/group:L1QinntdEOg:1` | `callgiving/group:L1QinntdEOg:1` | True | ✅ | - |
| `topology/group:L1QinntdEOg:1` | `application/inventory` | False | ❌ | Token does not contain required scope topology/group:L1QinntdEOg:1 |

### Authentication Summary

- **Total Scope Validations**: 3
- **Successful Validations**: 2 ✅
- **Failed Validations**: 1 ❌
- **Success Rate**: 66.7% if total_auths > 0 else 0%

### Common Authentication Issues

**⚠️ Authentication failures detected!**

Common causes of authentication failures:
- **Invalid Scope**: Token does not contain the required scope for the operation
- **Expired Token**: Token has expired and needs to be refreshed  
- **Wrong Building/Group**: Scope format incorrect for target building/group
- **API Credentials**: Invalid client_id or client_secret in configuration

**Troubleshooting Steps:**
1. Verify the scope format matches: `callv2/group:{buildingId}:{groupId}`
2. Check token expiration and refresh logic
3. Validate client credentials in config.yaml
4. Ensure building and group IDs are correct


---

## Service Robot API Solution Validation Test Results

| Test | Description | Expected result | Test result |
|------|-------------|-----------------|-------------|
| Test_1 | Initialize solution and establish connections | Authentication successful, connections established | PASS - All authentication steps completed successfully |
| Test_2 | Validate token scopes for API access | Token contains required scopes | FAIL - Missing topology scope |

---

## Detailed Test Information

### Test_1: Solution initialization
**Status:** ✅ PASS  
**Duration:** 1500.00 ms
**Category:** Authentication

### Test_2: Token scope validation
**Status:** ❌ FAIL  
**Duration:** 800.00 ms
**Category:** Authentication

#### Error Information
```
Token validation failed for topology scope
```


---

## Test Analysis and Recommendations

❌ **Needs Improvement**: The system requires significant attention with 50.0% success rate.

### Key Areas for Improvement:
- **Authentication**: 1 failed tests need attention

---

*Report generated on 2025-08-16T10:48:19.620886 by IBC-AI CO.*
