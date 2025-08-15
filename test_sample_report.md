# KONE Service Robot API v2.0 Validation Test Report\n\n## Test Environment\n- **Company**: IBC-AI CO.\n- **Tester**: Automated Test System\n- **Contact**: test@ibc-ai.com\n- **Building ID**: building:L1QinntdEOg\n- **Group ID**: 1\n- **Test Time**: 2025-08-16T01:16:39.400854\n- **WebSocket Endpoint**: wss://dev.kone.com/stream-v2\n\n## Test Summary\n- **Total Tests**: 3\n- **Passed**: 0\n- **Failed**: 3\n- **Not Applicable**: 0\n- **Success Rate**: 0.0%\n\n## Detailed Test Results\n\n### Test 1: 初始化\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 成功调用config、actions、ping三个API |\n| **Request** | ```json\n{
  "type": "common-api",
  "buildingId": "building:L1QinntdEOg",
  "callType": "config",
  "groupId": "1"
}\n``` |\n| **Observed** | No observations |\n| **Result** | ❌ **Fail** - Exception: No response received for request 478e2a22-2cb8-49bd-b4b0-affeeb849396 |\n\n### Test 2: 模式=非运营\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 订阅lift_+/status，lift_mode非正常 |\n| **Request** | ```json\n{
  "type": "site-monitoring",
  "buildingId": "building:L1QinntdEOg",
  "callType": "monitor",
  "groupId": "1",
  "payload": {
    "sub": "mode_test_1755278139",
    "duration": 60,
    "subtopics": [
      "lift_+/status"
    ]
  }
}\n``` |\n| **Observed** | No observations |\n| **Result** | ❌ **Fail** - Exception: No response received for request 7127169e-ba77-48b7-9dd3-62ebb9161b9a |\n\n### Test 3: 模式=运营\n\n| Section | Content |\n|---------|---------|\n| **Expected** | lift_mode正常，基本呼梯成功 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | No observations |\n| **Result** | ❌ **Fail** - Exception: No response received for request e8d5534d-4549-49bc-ab99-8fd13a69f9bb |\n\n## Appendix\n- **JSONL Log**: kone_validation.log\n- **Evidence Buffer**: 8 entries\n