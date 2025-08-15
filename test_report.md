# KONE Service Robot API v2.0 Validation Test Report\n\n## Test Environment\n- **Company**: IBC-AI CO.\n- **Tester**: Automated Test System\n- **Contact**: test@ibc-ai.com\n- **Building ID**: building:L1QinntdEOg\n- **Group ID**: 1\n- **Test Time**: 2025-08-16T00:55:55.895515\n- **WebSocket Endpoint**: wss://dev.kone.com/stream-v2\n\n## Test Summary\n- **Total Tests**: 1\n- **Passed**: 0\n- **Failed**: 1\n- **Not Applicable**: 0\n- **Success Rate**: 0.0%\n\n## Detailed Test Results\n\n### Test 1: 初始化\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 成功调用config、actions、ping三个API |\n| **Request** | ```json\n{
  "type": "common-api",
  "buildingId": "building:L1QinntdEOg",
  "callType": "config",
  "groupId": "1"
}\n``` |\n| **Observed** | No observations |\n| **Result** | ❌ **Fail** - Exception: No response received for request 300e8a92-a9e8-4422-9888-474e061421dd |\n\n## Appendix\n- **JSONL Log**: kone_validation.log\n- **Evidence Buffer**: 6 entries\n