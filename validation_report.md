# KONE Service Robot API v2.0 Validation Test Report\n\n## Test Environment\n- **Company**: IBC-AI CO.\n- **Tester**: Automated Test System\n- **Contact**: test@ibc-ai.com\n- **Building ID**: building:4TFxWRCv23D\n- **Group ID**: 1\n- **Test Time**: 2025-08-16T07:32:05.368068\n- **WebSocket Endpoint**: wss://dev.kone.com/stream-v2\n\n## Test Summary\n- **Total Tests**: 38\n- **Passed**: 14\n- **Failed**: 22\n- **Not Applicable**: 2\n- **Success Rate**: 36.8%\n\n## Detailed Test Results\n\n### Test 1: 初始化\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 成功调用config、actions、ping三个API |\n| **Request** | ```json\n{
  "type": "common-api",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "config",
  "groupId": "1"
}\n``` |\n| **Observed** | **config_response**: {'connectionId': 'PXtlKcg3joECJgA=', 'requestId': '699124656', 'statusCode': 201, 'data': {'time': '2025-08-15T23:29:49.896Z'}}\n**actions_response**: {'connectionId': 'PXtlKcg3joECJgA=', 'requestId': '281423848', 'statusCode': 201, 'data': {'time': '2025-08-15T23:29:50.436Z'}}\n**ping_response**: {'data': {'request_id': 407710662, 'time': '2025-08-15T23:29:51.237Z'}, 'callType': 'ping', 'buildingId': 'building:4TFxWRCv23D', 'groupId': '1'} |\n| **Result** | ✅ **Pass** - All three APIs (config, actions, ping) succeeded |\n\n### Test 2: 模式=非运营\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 订阅lift_+/status，lift_mode非正常 |\n| **Request** | ```json\n{
  "type": "site-monitoring",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "monitor",
  "groupId": "1",
  "payload": {
    "sub": "mode_test_1755300591",
    "duration": 60,
    "subtopics": [
      "lift_+/status"
    ]
  }
}\n``` |\n| **Observed** | **subscribe_response**: {'connectionId': 'PXtlKcg3joECJgA=', 'requestId': '1c8886f0-9f06-4e01-b14d-34f497baa04b', 'statusCode': 201, 'data': {'time': '2025-08-15T23:29:51.706Z'}} |\n| **Result** | ❌ **Fail** - Test timeout after 30 seconds |\n\n### Test 3: 模式=运营\n\n| Section | Content |\n|---------|---------|\n| **Expected** | lift_mode正常，基本呼梯成功 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | No observations |\n| **Result** | ⚠️ **NA** - System not in operational mode |\n\n### Test 4: 基础呼梯\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 合法action/destination，返回201+session_id |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "c594ceee-1bd1-4f3f-beeb-a180fe2dae7f",
    "area": 3000,
    "time": "2025-08-15T23:30:37.011831Z",
    "terminal": 1,
    "call": {
      "action": 2,
      "destination": 5000
    }
  }
}\n``` |\n| **Observed** | **call_response**: {'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 471736546, 'statusCode': 201, 'data': {'time': '2025-08-15T23:30:37.348Z'}}\n**session_id**: {'session_id': None} |\n| **Result** | ✅ **Pass** - Basic call successful, session_id: None |\n\n### Test 5: 保持开门\n\n| Section | Content |\n|---------|---------|\n| **Expected** | hold_open成功，门状态序列正确 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **hold_open_response**: {'type': 'error', 'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 496538529, 'statusCode': 403, 'data': {'error': 'Token does not contain required scope for 4TFxWRCv23D:1'}} |\n| **Result** | ❌ **Fail** - Hold open command failed |\n\n### Test 6: 未知动作\n\n| Section | Content |\n|---------|---------|\n| **Expected** | action=200或0，返回unknown/undefined错误 |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "1b60d581-ee4b-4e93-bed3-43a23643291e",
    "area": 1000,
    "time": "2025-08-15T23:30:37.747949Z",
    "terminal": 1,
    "call": {
      "action": 200,
      "destination": 2000
    }
  }
}\n``` |\n| **Observed** | **call_response**: {'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 548118674, 'statusCode': 201, 'data': {'time': '2025-08-15T23:30:38.111Z'}} |\n| **Result** | ❌ **Fail** - Unknown action not properly rejected |\n\n### Test 7: 禁用动作\n\n| Section | Content |\n|---------|---------|\n| **Expected** | action=4，返回disabled call action错误 |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "2328e58a-7cf7-4b02-8d87-be596b1b4ca9",
    "area": 1000,
    "time": "2025-08-15T23:30:38.163426Z",
    "terminal": 1,
    "call": {
      "action": 4,
      "destination": 2000
    }
  }
}\n``` |\n| **Observed** | **call_response**: {'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 820845669, 'statusCode': 201, 'data': {'time': '2025-08-15T23:30:38.508Z'}} |\n| **Result** | ❌ **Fail** - Disabled action not properly rejected |\n\n### Test 8: 方向冲突\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 1F向下呼叫，返回INVALID_DIRECTION错误 |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "80b1b2c6-cc0c-4dd3-b815-d78c69727e70",
    "area": 1000,
    "time": "2025-08-15T23:30:38.555597Z",
    "terminal": 1,
    "call": {
      "action": 2002
    }
  }
}\n``` |\n| **Observed** | **call_response**: {'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 181263445, 'statusCode': 201, 'data': {'time': '2025-08-15T23:30:38.895Z'}} |\n| **Result** | ❌ **Fail** - Direction conflict not detected |\n\n### Test 9: 延时=5\n\n| Section | Content |\n|---------|---------|\n| **Expected** | delay=5，正常分配与移动 |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "929f148a-1295-4965-91bb-4dba33db92f6",
    "area": 1000,
    "time": "2025-08-15T23:30:38.966894Z",
    "terminal": 1,
    "call": {
      "action": 2,
      "destination": 2000,
      "delay": 5
    }
  }
}\n``` |\n| **Observed** | **call_response**: {'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 848663837, 'statusCode': 201, 'data': {'time': '2025-08-15T23:30:39.316Z'}} |\n| **Result** | ✅ **Pass** - Call with 5 second delay successful |\n\n### Test 10: 延时=40\n\n| Section | Content |\n|---------|---------|\n| **Expected** | delay=40，返回Invalid json payload错误 |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "cbe9d1f3-c3b9-4700-b14b-acb69d5ef2be",
    "area": 1000,
    "time": "2025-08-15T23:30:39.451212Z",
    "terminal": 1,
    "call": {
      "action": 2,
      "destination": 2000,
      "delay": 40
    }
  }
}\n``` |\n| **Observed** | No observations |\n| **Result** | ✅ **Pass** - Invalid delay correctly rejected: Delay must be between 0 and 30 seconds |\n\n### Test 11: 换乘\n\n| Section | Content |\n|---------|---------|\n| **Expected** | modified_destination与modified_reason可见 |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "d0fe5733-cd41-4e25-bf39-266dbeb0ace6",
    "area": 1000,
    "time": "2025-08-15T23:30:39.451515Z",
    "terminal": 1,
    "call": {
      "action": 2,
      "destination": 3000
    }
  }
}\n``` |\n| **Observed** | **first_segment**: {'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 679533702, 'statusCode': 201, 'data': {'time': '2025-08-15T23:30:39.791Z'}}\n**second_segment_request**: {'type': 'lift-call-api-v2', 'buildingId': 'building:4TFxWRCv23D', 'callType': 'action', 'groupId': '1', 'payload': {'request_id': 'd44b0512-d0ea-4a11-bf4e-b6011d27dbe4', 'area': 3000, 'time': '2025-08-15T23:30:41.838953Z', 'terminal': 1, 'call': {'action': 2, 'destination': 5000}}}\n**second_segment_response**: {'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 193690026, 'statusCode': 201, 'data': {'time': '2025-08-15T23:30:42.210Z'}} |\n| **Result** | ✅ **Pass** - Transfer call sequence successful |\n\n### Test 12: 穿梯不允许\n\n| Section | Content |\n|---------|---------|\n| **Expected** | SAME_SOURCE_AND_DEST_FLOOR错误 |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "bb6583b0-6c07-4f16-8a3a-4ae17e16cb64",
    "area": 2000,
    "time": "2025-08-15T23:30:42.280375Z",
    "terminal": 1,
    "call": {
      "action": 2,
      "destination": 2000
    }
  }
}\n``` |\n| **Observed** | **same_floor_call**: {'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 256074260, 'statusCode': 201, 'data': {'time': '2025-08-15T23:30:42.636Z'}} |\n| **Result** | ❌ **Fail** - Same floor call was not prevented |\n\n### Test 13: 无行程（同层同侧）\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 同上错误 |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "931e3723-85b8-40bd-9a5a-fdf465a38262",
    "area": 2000,
    "time": "2025-08-15T23:30:42.688241Z",
    "terminal": 1,
    "call": {
      "action": 1
    }
  }
}\n``` |\n| **Observed** | **first_call**: {'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 881596996, 'statusCode': 201, 'data': {'time': '2025-08-15T23:30:43.052Z'}}\n**duplicate_call**: {'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 260919424, 'statusCode': 201, 'data': {'time': '2025-08-15T23:30:43.514Z'}} |\n| **Result** | ✅ **Pass** - Duplicate call handled correctly |\n\n### Test 14: 指定电梯\n\n| Section | Content |\n|---------|---------|\n| **Expected** | allowed_lifts，分配落在集合内 |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "a3a16777-fd6c-4a7b-b128-4a219ac9d913",
    "area": 1000,
    "time": "2025-08-15T23:30:43.562421Z",
    "terminal": 1,
    "call": {
      "action": 2,
      "destination": 2000,
      "allowed_lifts": [
        "A"
      ]
    }
  }
}\n``` |\n| **Observed** | **call_response**: {'type': 'error', 'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 558798686, 'statusCode': 400, 'data': {'error': "'payload.call.allowed_lifts[0]' must be a number"}} |\n| **Result** | ❌ **Fail** - Call with specified elevator failed:  |\n\n### Test 15: 指定无效电梯\n\n| Section | Content |\n|---------|---------|\n| **Expected** | invalid elevator rejected |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "02fe25e2-d61f-42cc-8612-281ddcb8a792",
    "area": 1000,
    "time": "2025-08-15T23:30:43.891865Z",
    "terminal": 1,
    "call": {
      "action": 2,
      "destination": 2000,
      "allowed_lifts": [
        "INVALID_LIFT"
      ]
    }
  }
}\n``` |\n| **Observed** | **call_response**: {'type': 'error', 'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 457678643, 'statusCode': 400, 'data': {'error': "'payload.call.allowed_lifts[0]' must be a number"}} |\n| **Result** | ✅ **Pass** - Invalid elevator correctly rejected:  |\n\n### Test 16: 取消呼梯\n\n| Section | Content |\n|---------|---------|\n| **Expected** | delete(session_id)，call_state=canceled |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **initial_call**: {'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 159514675, 'statusCode': 201, 'data': {'time': '2025-08-15T23:30:44.574Z'}}\n**cancel_response**: {'type': 'error', 'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 675530156, 'statusCode': 400, 'data': {'error': "'payload.session_id' must be a number"}} |\n| **Result** | ❌ **Fail** - Call cancellation failed:  |\n\n### Test 17: 非法目的地\n\n| Section | Content |\n|---------|---------|\n| **Expected** | unable to resolve destination错误 |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "5f3eb9a2-b3ef-4391-9f3d-ae29e64d157a",
    "area": 1000,
    "time": "2025-08-15T23:30:44.971313Z",
    "terminal": 1,
    "call": {
      "action": 2,
      "destination": 9999
    }
  }
}\n``` |\n| **Observed** | **call_response**: {'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 609842385, 'statusCode': 201, 'data': {'time': '2025-08-15T23:30:45.324Z'}} |\n| **Result** | ❌ **Fail** - Invalid destination was not rejected |\n\n### Test 18: WebSocket连接\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 连接和事件订阅测试 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | No observations |\n| **Result** | ❌ **Fail** - WebSocket connection error: WebSocket communication error: No response received for request 2f44a721-f6c9-45d6-a8a5-ea37f5d993c6 within 10.0s |\n\n### Test 19: 系统Ping\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 系统ping测试 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **ping_response**: {'data': {'request_id': 500041475, 'time': '2025-08-15T23:30:56.508Z'}, 'callType': 'ping', 'buildingId': 'building:4TFxWRCv23D', 'groupId': '1'} |\n| **Result** | ❌ **Fail** - System ping failed:  |\n\n### Test 20: 开门保持\n\n| Section | Content |\n|---------|---------|\n| **Expected** | hold door open test |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **initial_call**: {'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 650741209, 'statusCode': 201, 'data': {'time': '2025-08-15T23:30:57.167Z'}} |\n| **Result** | ⚠️ **NA** - Invalid destination test requires specific building data |\n\n### Test 21: 错误buildingId\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 404+Building data not found |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:invalid123",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "0bfa8419-0971-42ab-a296-c13f18229c56",
    "area": 1000,
    "time": "2025-08-15T23:30:57.223494Z",
    "terminal": 1,
    "call": {
      "action": 2,
      "destination": 2000
    }
  }
}\n``` |\n| **Observed** | **call_response**: {'type': 'error', 'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 538836770, 'statusCode': 403, 'data': {'error': 'Token does not contain required scope for invalid123:1'}} |\n| **Result** | ❌ **Fail** - Invalid building ID not properly rejected |\n\n### Test 22: 多群组（第二building）\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 与#4相同成功流程 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **second_building_call**: {'type': 'error', 'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 938421767, 'statusCode': 400, 'data': {'error': "'groupId' length must be less than or equal to 2 characters long"}} |\n| **Result** | ❌ **Fail** - Multi-building access error:  |\n\n### Test 23: 多群组（后缀:2）\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 与#4相同成功流程 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **suffix_group_call**: {'type': 'error', 'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 131614578, 'statusCode': 400, 'data': {'error': "'groupId' length must be less than or equal to 2 characters long"}} |\n| **Result** | ❌ **Fail** - Group suffix error:  |\n\n### Test 24: 无效请求格式\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 格式错误拒绝 |\n| **Request** | ```json\n{
  "type": "invalid-type",
  "buildingId": "building:4TFxWRCv23D",
  "invalid_field": "invalid_value"
}\n``` |\n| **Observed** | **invalid_call**: {'type': 'error', 'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 154127773, 'statusCode': 400, 'data': {'error': "'payload.area' must be a number"}} |\n| **Result** | ✅ **Pass** - Invalid request format correctly rejected |\n\n### Test 25: 并发呼叫\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 并发请求处理 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **concurrent_calls**: [{'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 560160040, 'statusCode': 201, 'data': {'time': '2025-08-15T23:30:58.933Z'}}, Exception('WebSocket communication error: cannot call recv while another coroutine is already waiting for the next message'), Exception('WebSocket communication error: cannot call recv while another coroutine is already waiting for the next message')] |\n| **Result** | ✅ **Pass** - Concurrent calls handled: 1/3 successful |\n\n### Test 26: 事件订阅持久性\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 事件订阅测试 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | No observations |\n| **Result** | ❌ **Fail** - Event subscription error: WebSocket communication error: No response received for request 9c0111a8-077b-4e49-ba60-2549d7319d0b within 10.0s |\n\n### Test 27: 负载测试\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 负载处理能力 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **load_test**: {'total_calls': 10, 'successful_calls': 10, 'duration': 5.112749099731445, 'calls_per_second': 1.955894921682205} |\n| **Result** | ✅ **Pass** - Load test passed: 10/10 calls successful |\n\n### Test 28: 错误恢复\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 系统错误恢复能力 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **bad_request**: {'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 152906393, 'statusCode': 201, 'data': {'time': '2025-08-15T23:31:15.505Z'}}\n**recovery_request**: {'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 373456419, 'statusCode': 201, 'data': {'time': '2025-08-15T23:31:15.982Z'}} |\n| **Result** | ✅ **Pass** - System recovered from error successfully |\n\n### Test 29: 数据验证\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 输入数据验证 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **validation_tests**: [{'test_data': {'area': 'string_instead_of_int', 'action': 2, 'destination': 2000}, 'response': {'type': 'error', 'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 705915926, 'statusCode': 400, 'data': {'error': "'payload.area' must be a number"}}, 'validated': True}, {'test_data': {'area': 1000, 'action': 99, 'destination': 2000}, 'response': {'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 869180522, 'statusCode': 201, 'data': {'time': '2025-08-15T23:31:16.735Z'}}, 'validated': False}, {'test_data': {'area': 1000, 'action': 2, 'destination': 'invalid'}, 'response': {'type': 'error', 'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 715226064, 'statusCode': 400, 'data': {'error': "'payload.call.destination' must be a number"}}, 'validated': True}] |\n| **Result** | ❌ **Fail** - Only 2/3 validation tests passed |\n\n### Test 30: 身份验证令牌\n\n| Section | Content |\n|---------|---------|\n| **Expected** | token验证测试 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **token_status**: {'has_token': True, 'expiry': '2025-08-16 07:39:41.743105'}\n**token_validation**: {'data': {'request_id': 895731798, 'time': '2025-08-15T23:31:17.896Z'}, 'callType': 'ping', 'buildingId': 'building:4TFxWRCv23D', 'groupId': '1'} |\n| **Result** | ❌ **Fail** - Token validation failed:  |\n\n### Test 31: API速率限制\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 速率限制测试 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **rapid_calls**: [{'request_num': 1, 'status': 201, 'timestamp': 0.4278566837310791}, {'request_num': 2, 'status': 201, 'timestamp': 0.8391308784484863}, {'request_num': 3, 'status': 201, 'timestamp': 1.3285129070281982}, {'request_num': 4, 'status': 201, 'timestamp': 1.7691209316253662}, {'request_num': 5, 'status': 201, 'timestamp': 2.149657964706421}, {'request_num': 6, 'status': 201, 'timestamp': 2.529566764831543}, {'request_num': 7, 'status': 201, 'timestamp': 2.9282610416412354}, {'request_num': 8, 'status': 201, 'timestamp': 3.3109848499298096}, {'request_num': 9, 'status': 201, 'timestamp': 3.7609598636627197}, {'request_num': 10, 'status': 201, 'timestamp': 4.151470899581909}, {'request_num': 11, 'status': 201, 'timestamp': 4.545320749282837}, {'request_num': 12, 'status': 201, 'timestamp': 4.931419849395752}, {'request_num': 13, 'status': 201, 'timestamp': 5.338287830352783}, {'request_num': 14, 'status': 201, 'timestamp': 5.7351579666137695}, {'request_num': 15, 'status': 201, 'timestamp': 6.124814033508301}, {'request_num': 16, 'status': 201, 'timestamp': 6.509617805480957}, {'request_num': 17, 'status': 201, 'timestamp': 6.956787824630737}, {'request_num': 18, 'status': 201, 'timestamp': 7.333050012588501}, {'request_num': 19, 'status': 201, 'timestamp': 7.725635051727295}, {'request_num': 20, 'status': 201, 'timestamp': 8.104840755462646}] |\n| **Result** | ✅ **Pass** - All rapid requests accepted - no rate limiting |\n\n### Test 32: WebSocket重连\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 连接重连测试 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | No observations |\n| **Result** | ❌ **Fail** - WebSocket reconnection test error: WebSocket communication error: No response received for request c8b2a84d-729f-48a6-97ac-e2d418b7e6a1 within 10.0s |\n\n### Test 33: 系统状态监控\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 系统状态检查 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **config_check**: {'connectionId': 'PXtlKcg3joECJgA=', 'requestId': '898968220', 'statusCode': 201, 'data': {'time': '2025-08-15T23:31:37.056Z'}}\n**actions_check**: {'connectionId': 'PXtlKcg3joECJgA=', 'requestId': '528679006', 'statusCode': 201, 'data': {'time': '2025-08-15T23:31:37.583Z'}}\n**ping_check**: {'data': {'request_id': 317556421, 'time': '2025-08-15T23:31:38.384Z'}, 'callType': 'ping', 'buildingId': 'building:4TFxWRCv23D', 'groupId': '1'} |\n| **Result** | ❌ **Fail** - One or more system status checks failed |\n\n### Test 34: 边界情况处理\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 边界值处理 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **edge_cases**: [{'case': 'empty_building_id', 'response': {'type': 'error', 'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 126266978, 'statusCode': 400, 'data': {'error': "'buildingId' is not allowed to be empty"}}}, {'case': 'large_area', 'response': {'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 460406129, 'statusCode': 201, 'data': {'time': '2025-08-15T23:31:39.529Z'}}}, {'case': 'negative_area', 'response': {'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 431761413, 'statusCode': 201, 'data': {'time': '2025-08-15T23:31:39.936Z'}}}] |\n| **Result** | ❌ **Fail** - Only 1/3 edge cases handled |\n\n### Test 35: 性能基准\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 性能基准测试 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **performance_data**: [{'request_num': 1, 'duration': 0.40578508377075195, 'status': 201, 'success': True}, {'request_num': 2, 'duration': 0.4617578983306885, 'status': 201, 'success': True}, {'request_num': 3, 'duration': 0.39328789710998535, 'status': 201, 'success': True}, {'request_num': 4, 'duration': 0.4087028503417969, 'status': 201, 'success': True}, {'request_num': 5, 'duration': 0.4273688793182373, 'status': 201, 'success': True}] |\n| **Result** | ✅ **Pass** - Performance benchmark passed: avg=0.42s, max=0.46s |\n\n### Test 36: 集成完整性\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 端到端集成测试 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | No observations |\n| **Result** | ❌ **Fail** - Integration completeness test error: WebSocket communication error: No response received for request 5f895fb1-19f9-4c0a-95a3-9ba24dc350b4 within 10.0s |\n\n### Test 37: 安全验证\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 安全漏洞检测 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **security_tests**: [{'test': 'sql_injection', 'blocked': True, 'response': {'type': 'error', 'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 162166827, 'statusCode': 400, 'data': {'error': "'buildingId' with value 'building:'; DROP TABLE users; --' fails to match the required pattern: /^building:[a-zA-Z0-9]+$/"}}}, {'test': 'xss_attempt', 'blocked': True, 'response': {'type': 'error', 'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 826749020, 'statusCode': 400, 'data': {'error': "'groupId' length must be less than or equal to 2 characters long"}}}, {'test': 'long_string', 'blocked': True, 'response': {'type': 'error', 'connectionId': 'PXtlKcg3joECJgA=', 'requestId': 769091987, 'statusCode': 400, 'data': {'error': "'buildingId' with value 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' fails to match the required pattern: /^building:[a-zA-Z0-9]+$/"}}}] |\n| **Result** | ✅ **Pass** - All 3 security tests blocked malicious input |\n\n### Test 38: 最终综合\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 全面综合测试 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | No observations |\n| **Result** | ❌ **Fail** - Comprehensive test error: WebSocket communication error: No response received for request 7e68ae5f-f342-44fa-9e7b-f8b7c1cad06f within 10.0s |\n\n## Appendix\n- **JSONL Log**: kone_validation.log\n- **Evidence Buffer**: 169 entries\n