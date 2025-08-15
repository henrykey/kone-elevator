# KONE Service Robot API v2.0 Validation Test Report\n\n## Test Environment\n- **Company**: IBC-AI CO.\n- **Tester**: Automated Test System\n- **Contact**: test@ibc-ai.com\n- **Building ID**: building:L1QinntdEOg\n- **Group ID**: 1\n- **Test Time**: 2025-08-16T01:19:29.114491\n- **WebSocket Endpoint**: wss://dev.kone.com/stream-v2\n\n## Test Summary\n- **Total Tests**: 5\n- **Passed**: 0\n- **Failed**: 5\n- **Not Applicable**: 0\n- **Success Rate**: 0.0%\n\n## Detailed Test Results\n\n### Test 1: 初始化\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 成功调用config、actions、ping三个API |\n| **Request** | ```json\n{
  "type": "common-api",
  "buildingId": "building:L1QinntdEOg",
  "callType": "config",
  "groupId": "1"
}\n``` |\n| **Observed** | No observations |\n| **Result** | ❌ **Fail** - Exception: No response received for request 737f2821-3bef-452a-99fc-563f387de88b |\n\n### Test 4: 基础呼梯\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 合法action/destination，返回201+session_id |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:L1QinntdEOg",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "b3c22b56-143c-4118-a98a-b6cec94b0d98",
    "area": 3000,
    "time": "2025-08-15T17:18:28.407007Z",
    "terminal": 1,
    "call": {
      "action": 2,
      "destination": 5000
    }
  }
}\n``` |\n| **Observed** | **call_response**: {'type': 'error', 'connectionId': 'PW3HCdqQjoECJNw=', 'requestId': '7bbc5273-e19e-4d11-a3b2-51d4c0db5f55', 'statusCode': 400, 'data': {'error': "'payload.request_id' must be a number"}} |\n| **Result** | ❌ **Fail** - Basic call failed |\n\n### Test 16: 取消呼梯\n\n| Section | Content |\n|---------|---------|\n| **Expected** | delete(session_id)，call_state=canceled |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **initial_call**: {'type': 'error', 'connectionId': 'PW3HCdqQjoECJNw=', 'requestId': '5b850298-85b0-4854-83de-0983df94c5c5', 'statusCode': 400, 'data': {'error': "'payload.request_id' must be a number"}} |\n| **Result** | ❌ **Fail** - Could not create call to cancel |\n\n### Test 30: 身份验证令牌\n\n| Section | Content |\n|---------|---------|\n| **Expected** | token验证测试 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **token_status**: {'has_token': True, 'expiry': '2025-08-16 01:55:23.898184'} |\n| **Result** | ❌ **Fail** - Authentication test error: No response received for request 322da1ed-86b2-4943-9826-f0e06a1ab484 |\n\n### Test 38: 最终综合\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 全面综合测试 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | No observations |\n| **Result** | ❌ **Fail** - Comprehensive test error: No response received for request 6a281eef-7dcb-45d4-a8fb-f286fd660c9c |\n\n## Appendix\n- **JSONL Log**: kone_validation.log\n- **Evidence Buffer**: 14 entries\n