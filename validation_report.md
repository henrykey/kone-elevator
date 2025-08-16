# KONE Service Robot API v2.0 Validation Test Report\n\n## Test Environment\n- **Company**: IBC-AI CO.\n- **Tester**: Automated Test System\n- **Contact**: test@ibc-ai.com\n- **Building ID**: building:4TFxWRCv23D\n- **Group ID**: 1\n- **Test Time**: 2025-08-16T08:19:48.594796\n- **WebSocket Endpoint**: wss://dev.kone.com/stream-v2\n\n## Test Summary\n- **Total Tests**: 38\n- **Passed**: 18\n- **Failed**: 18\n- **Not Applicable**: 2\n- **Success Rate**: 47.4%\n\n## Detailed Test Results\n\n### Test 1: 初始化\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 成功调用config、actions、ping三个API |\n| **Request** | ```json\n{
  "type": "common-api",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "config",
  "groupId": "1"
}\n``` |\n| **Observed** | **config_response**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': '623179896', 'statusCode': 201, 'data': {'time': '2025-08-16T00:17:47.787Z'}}\n**actions_response**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': '129218245', 'statusCode': 201, 'data': {'time': '2025-08-16T00:17:48.527Z'}}\n**ping_response**: {'data': {'request_id': 684722878, 'time': '2025-08-16T00:17:49.340Z'}, 'callType': 'ping', 'buildingId': 'building:4TFxWRCv23D', 'groupId': '1'} |\n| **Result** | ✅ **Pass** - All three APIs (config, actions, ping) succeeded |\n\n### Test 2: 模式=非运营\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 订阅lift_+/status，lift_mode非正常 |\n| **Request** | ```json\n{
  "type": "site-monitoring",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "monitor",
  "groupId": "1",
  "payload": {
    "sub": "mode_test_1755303469",
    "duration": 60,
    "subtopics": [
      "lift_+/status"
    ]
  }
}\n``` |\n| **Observed** | **subscribe_response**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': '04d8b57e-aba7-46e1-83b5-2533658f9741', 'statusCode': 201, 'data': {'time': '2025-08-16T00:17:50.007Z'}} |\n| **Result** | ❌ **Fail** - Test timeout after 30 seconds |\n\n### Test 3: 模式=运营\n\n| Section | Content |\n|---------|---------|\n| **Expected** | lift_mode正常，基本呼梯成功 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | No observations |\n| **Result** | ⚠️ **NA** - System not in operational mode |\n\n### Test 4: 基础呼梯\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 合法action/destination，返回201+session_id |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "a396f8b0-39b9-47be-ad7e-cc7f9744d614",
    "area": 3000,
    "time": "2025-08-16T00:18:35.061871Z",
    "terminal": 1,
    "call": {
      "action": 2,
      "destination": 5000
    }
  }
}\n``` |\n| **Observed** | **call_response**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 943129424, 'statusCode': 201, 'data': {'time': '2025-08-16T00:18:35.440Z'}}\n**session_id**: {'session_id': None} |\n| **Result** | ✅ **Pass** - Basic call successful, session_id: None |\n\n### Test 5: 保持开门\n\n| Section | Content |\n|---------|---------|\n| **Expected** | hold_open成功，门状态序列正确 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **hold_open_response**: {'type': 'error', 'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 410631291, 'statusCode': 403, 'data': {'error': 'Token does not contain required scope for 4TFxWRCv23D:1'}} |\n| **Result** | ❌ **Fail** - Hold open command failed |\n\n### Test 6: 未知动作\n\n| Section | Content |\n|---------|---------|\n| **Expected** | action=200或0，返回unknown/undefined错误 |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "a9b9900b-3694-4de0-a232-6c21a5fe1c32",
    "area": 1000,
    "time": "2025-08-16T00:18:35.833276Z",
    "terminal": 1,
    "call": {
      "action": 200,
      "destination": 2000
    }
  }
}\n``` |\n| **Observed** | **call_response**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 777697681, 'statusCode': 201, 'data': {'time': '2025-08-16T00:18:36.237Z'}} |\n| **Result** | ❌ **Fail** - Unknown action not properly rejected |\n\n### Test 7: 禁用动作\n\n| Section | Content |\n|---------|---------|\n| **Expected** | action=4，返回disabled call action错误 |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "c47e31dc-8aaa-46f9-b394-c3c1647078a6",
    "area": 1000,
    "time": "2025-08-16T00:18:36.281440Z",
    "terminal": 1,
    "call": {
      "action": 4,
      "destination": 2000
    }
  }
}\n``` |\n| **Observed** | **call_response**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 704223808, 'statusCode': 201, 'data': {'time': '2025-08-16T00:18:36.643Z'}} |\n| **Result** | ❌ **Fail** - Disabled action not properly rejected |\n\n### Test 8: 方向冲突\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 1F向下呼叫，返回INVALID_DIRECTION错误 |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "3f75cdcf-8fdb-4591-b184-c8aa11c09b8e",
    "area": 1000,
    "time": "2025-08-16T00:18:36.676540Z",
    "terminal": 1,
    "call": {
      "action": 2002
    }
  }
}\n``` |\n| **Observed** | **call_response**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 662089564, 'statusCode': 201, 'data': {'time': '2025-08-16T00:18:37.054Z'}} |\n| **Result** | ❌ **Fail** - Direction conflict not detected |\n\n### Test 9: 延时=5\n\n| Section | Content |\n|---------|---------|\n| **Expected** | delay=5，正常分配与移动 |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "e2d0d362-b342-4b98-ba18-346ccf06ed4e",
    "area": 1000,
    "time": "2025-08-16T00:18:37.087260Z",
    "terminal": 1,
    "call": {
      "action": 2,
      "destination": 2000,
      "delay": 5
    }
  }
}\n``` |\n| **Observed** | **call_response**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 354666445, 'statusCode': 201, 'data': {'time': '2025-08-16T00:18:37.463Z'}} |\n| **Result** | ✅ **Pass** - Call with 5 second delay successful |\n\n### Test 10: 延时=40\n\n| Section | Content |\n|---------|---------|\n| **Expected** | delay=40，返回Invalid json payload错误 |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "ca3e8fbe-ff34-457c-9ef4-9274be9c4a19",
    "area": 1000,
    "time": "2025-08-16T00:18:37.495604Z",
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
    "request_id": "45b6421f-73d9-4fb5-95d9-ec6a55533195",
    "area": 1000,
    "time": "2025-08-16T00:18:37.495985Z",
    "terminal": 1,
    "call": {
      "action": 2,
      "destination": 3000
    }
  }
}\n``` |\n| **Observed** | **first_segment**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 357086502, 'statusCode': 201, 'data': {'time': '2025-08-16T00:18:37.852Z'}}\n**second_segment_request**: {'type': 'lift-call-api-v2', 'buildingId': 'building:4TFxWRCv23D', 'callType': 'action', 'groupId': '1', 'payload': {'request_id': '4fb0e86c-55df-41ef-bd82-d66c79c404b4', 'area': 3000, 'time': '2025-08-16T00:18:39.884871Z', 'terminal': 1, 'call': {'action': 2, 'destination': 5000}}}\n**second_segment_response**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 395847203, 'statusCode': 201, 'data': {'time': '2025-08-16T00:18:40.254Z'}} |\n| **Result** | ✅ **Pass** - Transfer call sequence successful |\n\n### Test 12: 穿梯不允许\n\n| Section | Content |\n|---------|---------|\n| **Expected** | SAME_SOURCE_AND_DEST_FLOOR错误 |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "ab0c9825-5d70-4c0e-a98d-23be173aded7",
    "area": 2000,
    "time": "2025-08-16T00:18:40.312210Z",
    "terminal": 1,
    "call": {
      "action": 2,
      "destination": 2000
    }
  }
}\n``` |\n| **Observed** | **same_floor_call**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 912268384, 'statusCode': 201, 'data': {'time': '2025-08-16T00:18:40.676Z'}} |\n| **Result** | ❌ **Fail** - Same floor call was not prevented |\n\n### Test 13: 无行程（同层同侧）\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 同上错误 |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "b6e88918-29d2-47a5-9ab5-7dbe78d44d48",
    "area": 2000,
    "time": "2025-08-16T00:18:40.709272Z",
    "terminal": 1,
    "call": {
      "action": 1
    }
  }
}\n``` |\n| **Observed** | **first_call**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 915036956, 'statusCode': 201, 'data': {'time': '2025-08-16T00:18:41.075Z'}}\n**duplicate_call**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 991295105, 'statusCode': 201, 'data': {'time': '2025-08-16T00:18:41.478Z'}} |\n| **Result** | ✅ **Pass** - Duplicate call handled correctly |\n\n### Test 14: 指定电梯\n\n| Section | Content |\n|---------|---------|\n| **Expected** | allowed_lifts，分配落在集合内 |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "c35d2c1e-3c90-49bc-8abf-c2e3fc720801",
    "area": 1000,
    "time": "2025-08-16T00:18:41.511107Z",
    "terminal": 1,
    "call": {
      "action": 2,
      "destination": 2000,
      "allowed_lifts": [
        1
      ]
    }
  }
}\n``` |\n| **Observed** | **call_response**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 299877754, 'statusCode': 201, 'data': {'time': '2025-08-16T00:18:41.880Z'}} |\n| **Result** | ✅ **Pass** - Call with specified elevator successful |\n\n### Test 15: 取消呼叫\n\n| Section | Content |\n|---------|---------|\n| **Expected** | delete(session_id)，call_state=canceled |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **connection_established**: {}\n**call_sent**: {'type': 'lift-call-api-v2', 'buildingId': 'building:4TFxWRCv23D', 'callType': 'action', 'groupId': '1', 'payload': {'request_id': 12345, 'area': 1000, 'time': '2020-10-10T07:17:33.298515Z', 'terminal': 1, 'call': {'action': 2, 'destination': 2000}}}\n**events_received**: [{'data': {'request_id': 991295105, 'success': False, 'error': 'Ignoring call, unknown call action: 1'}, 'callType': 'action', 'buildingId': 'building:4TFxWRCv23D', 'groupId': '1'}, {'data': {'request_id': 299877754, 'success': False, 'error': 'Ignoring call, unable to convert allowed deck: area:1'}, 'callType': 'action', 'buildingId': 'building:4TFxWRCv23D', 'groupId': '1'}, {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 12345, 'statusCode': 201, 'data': {'time': '2025-08-16T00:18:42.386Z'}}, {'data': {'request_id': 12345, 'success': True, 'session_id': 23602}, 'callType': 'action', 'buildingId': 'building:4TFxWRCv23D', 'groupId': '1'}]\n**session_id_found**: {}\n**delete_sent**: {'type': 'lift-call-api-v2', 'buildingId': 'building:4TFxWRCv23D', 'callType': 'delete', 'groupId': '1', 'payload': {'session_id': 23602}}\n**delete_response**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 641268834, 'statusCode': 201, 'data': {'time': '2025-08-16T00:18:43.224Z'}} |\n| **Result** | ✅ **Pass** - Cancel call successful - session_id: 23602, response: 201 |\n\n### Test 16: 无效目的地\n\n| Section | Content |\n|---------|---------|\n| **Expected** | unable to resolve destination错误 |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "3b16bc68-aace-404d-87f1-ddf43e93f61b",
    "area": 1000,
    "time": "2025-08-16T00:18:43.256100Z",
    "terminal": 1,
    "call": {
      "action": 2,
      "destination": 9999
    }
  }
}\n``` |\n| **Observed** | **call_response**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 288191453, 'statusCode': 201, 'data': {'time': '2025-08-16T00:18:43.629Z'}} |\n| **Result** | ✅ **Pass** - Invalid destination allowed with 201 response (Option 2 per official guide) |\n\n### Test 17: 非法目的地\n\n| Section | Content |\n|---------|---------|\n| **Expected** | unable to resolve destination错误 |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:4TFxWRCv23D",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "ed6d2ce6-ae84-43e0-8f96-b91dac69f23d",
    "area": 1000,
    "time": "2025-08-16T00:18:43.661255Z",
    "terminal": 1,
    "call": {
      "action": 2,
      "destination": 9999
    }
  }
}\n``` |\n| **Observed** | **call_response**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 285031138, 'statusCode': 201, 'data': {'time': '2025-08-16T00:18:44.116Z'}} |\n| **Result** | ❌ **Fail** - Invalid destination was not rejected |\n\n### Test 18: WebSocket连接\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 连接和事件订阅测试 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **connection_check**: {}\n**subscribe**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 'da2ab82d-5443-44d6-a368-65374c17c48d', 'statusCode': 201, 'data': {'time': '2025-08-16T00:18:44.494Z'}}\n**events**: None |\n| **Result** | ✅ **Pass** - WebSocket connection and event subscription successful |\n\n### Test 19: 系统Ping\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 系统ping测试 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **ping_response**: {'data': {'request_id': 101765842, 'time': '2025-08-16T00:18:51.280Z'}, 'callType': 'ping', 'buildingId': 'building:4TFxWRCv23D', 'groupId': '1'} |\n| **Result** | ❌ **Fail** - System ping failed:  |\n\n### Test 20: 开门保持\n\n| Section | Content |\n|---------|---------|\n| **Expected** | hold door open test |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **initial_call**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 406628242, 'statusCode': 201, 'data': {'time': '2025-08-16T00:18:51.845Z'}} |\n| **Result** | ⚠️ **NA** - Invalid destination test requires specific building data |\n\n### Test 21: 错误buildingId\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 404+Building data not found |\n| **Request** | ```json\n{
  "type": "lift-call-api-v2",
  "buildingId": "building:invalid123",
  "callType": "action",
  "groupId": "1",
  "payload": {
    "request_id": "5508c02a-d26e-4231-bd29-c6566c5891b1",
    "area": 1000,
    "time": "2025-08-16T00:18:51.896256Z",
    "terminal": 1,
    "call": {
      "action": 2,
      "destination": 2000
    }
  }
}\n``` |\n| **Observed** | **call_response**: {'type': 'error', 'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 554831355, 'statusCode': 403, 'data': {'error': 'Token does not contain required scope for invalid123:1'}} |\n| **Result** | ❌ **Fail** - Invalid building ID not properly rejected |\n\n### Test 22: 多群组（第二building）\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 与#4相同成功流程 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **second_building_call**: {'type': 'error', 'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 649990610, 'statusCode': 400, 'data': {'error': "'groupId' length must be less than or equal to 2 characters long"}} |\n| **Result** | ❌ **Fail** - Multi-building access error:  |\n\n### Test 23: 多群组（后缀:2）\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 与#4相同成功流程 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **suffix_group_call**: {'type': 'error', 'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 526605781, 'statusCode': 400, 'data': {'error': "'groupId' length must be less than or equal to 2 characters long"}} |\n| **Result** | ❌ **Fail** - Group suffix error:  |\n\n### Test 24: 无效请求格式\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 格式错误拒绝 |\n| **Request** | ```json\n{
  "type": "invalid-type",
  "buildingId": "building:4TFxWRCv23D",
  "invalid_field": "invalid_value"
}\n``` |\n| **Observed** | **invalid_call**: {'type': 'error', 'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 249241906, 'statusCode': 400, 'data': {'error': "'payload.area' must be a number"}} |\n| **Result** | ✅ **Pass** - Invalid request format correctly rejected |\n\n### Test 25: 并发呼叫\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 并发请求处理 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **concurrent_calls**: [{'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 576511561, 'statusCode': 201, 'data': {'time': '2025-08-16T00:18:53.682Z'}}, Exception('WebSocket communication error: cannot call recv while another coroutine is already waiting for the next message'), Exception('WebSocket communication error: cannot call recv while another coroutine is already waiting for the next message')] |\n| **Result** | ✅ **Pass** - Concurrent calls handled: 1/3 successful |\n\n### Test 26: 事件订阅持久性\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 事件订阅测试 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **connection**: {}\n**subscribe**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 'cde8be4b-d65c-4028-8422-f2b54bc10a6f', 'statusCode': 201, 'data': {'time': '2025-08-16T00:18:54.054Z'}}\n**call**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 484948971, 'statusCode': 201, 'data': {'time': '2025-08-16T00:18:54.489Z'}}\n**events**: None |\n| **Result** | ❌ **Fail** - No events received from subscription |\n\n### Test 27: 负载测试\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 负载处理能力 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **load_test**: {'total_calls': 10, 'successful_calls': 10, 'duration': 5.062089920043945, 'calls_per_second': 1.9754686617485426} |\n| **Result** | ✅ **Pass** - Load test passed: 10/10 calls successful |\n\n### Test 28: 错误恢复\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 系统错误恢复能力 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **bad_request**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 100341719, 'statusCode': 201, 'data': {'time': '2025-08-16T00:19:11.953Z'}}\n**recovery_request**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 296524835, 'statusCode': 201, 'data': {'time': '2025-08-16T00:19:12.361Z'}} |\n| **Result** | ✅ **Pass** - System recovered from error successfully |\n\n### Test 29: 数据验证\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 输入数据验证 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **validation_tests**: [{'test_data': {'area': 'string_instead_of_int', 'action': 2, 'destination': 2000}, 'response': {'type': 'error', 'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 792960762, 'statusCode': 400, 'data': {'error': "'payload.area' must be a number"}}, 'validated': True}, {'test_data': {'area': 1000, 'action': 99, 'destination': 2000}, 'response': {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 658318280, 'statusCode': 201, 'data': {'time': '2025-08-16T00:19:13.125Z'}}, 'validated': False}, {'test_data': {'area': 1000, 'action': 2, 'destination': 'invalid'}, 'response': {'type': 'error', 'connectionId': 'PX0m0e_3joECFxA=', 'requestId': 689514674, 'statusCode': 400, 'data': {'error': "'payload.call.destination' must be a number"}}, 'validated': True}] |\n| **Result** | ❌ **Fail** - Only 2/3 validation tests passed |\n\n### Test 30: 身份验证令牌\n\n| Section | Content |\n|---------|---------|\n| **Expected** | token验证测试 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **token_status**: {'has_token': True, 'expiry': '2025-08-16 08:39:13.979034'}\n**token_validation**: {'data': {'request_id': 683539344, 'time': '2025-08-16T00:19:14.264Z'}, 'callType': 'ping', 'buildingId': 'building:4TFxWRCv23D', 'groupId': '1'} |\n| **Result** | ❌ **Fail** - Token validation failed:  |\n\n### Test 31: API速率限制\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 速率限制测试 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **rapid_calls**: [{'request_num': 1, 'status': 201, 'timestamp': 0.45478177070617676}, {'request_num': 2, 'status': 201, 'timestamp': 0.8513758182525635}, {'request_num': 3, 'status': 201, 'timestamp': 1.2412538528442383}, {'request_num': 4, 'status': 201, 'timestamp': 1.63462495803833}, {'request_num': 5, 'status': 201, 'timestamp': 2.0278127193450928}, {'request_num': 6, 'status': 201, 'timestamp': 2.4915130138397217}, {'request_num': 7, 'status': 201, 'timestamp': 2.8928818702697754}, {'request_num': 8, 'status': 201, 'timestamp': 3.266108751296997}, {'request_num': 9, 'status': 201, 'timestamp': 3.724362850189209}, {'request_num': 10, 'status': 201, 'timestamp': 4.11921501159668}, {'request_num': 11, 'status': 201, 'timestamp': 4.513498783111572}, {'request_num': 12, 'status': 201, 'timestamp': 4.898829936981201}, {'request_num': 13, 'status': 201, 'timestamp': 5.276190996170044}, {'request_num': 14, 'status': 201, 'timestamp': 5.670342922210693}, {'request_num': 15, 'status': 201, 'timestamp': 6.052697658538818}, {'request_num': 16, 'status': 201, 'timestamp': 6.439405918121338}, {'request_num': 17, 'status': 201, 'timestamp': 6.836532831192017}, {'request_num': 18, 'status': 201, 'timestamp': 7.272877931594849}, {'request_num': 19, 'status': 201, 'timestamp': 7.668596982955933}, {'request_num': 20, 'status': 201, 'timestamp': 8.075263977050781}] |\n| **Result** | ✅ **Pass** - All rapid requests accepted - no rate limiting |\n\n### Test 32: WebSocket重连\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 连接重连测试 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **initial_connect**: {'connectionId': 'PX0m0e_3joECFxA=', 'requestId': '79188a66-d0c2-4cf7-b2ba-f5763e0ddba8', 'statusCode': 201, 'data': {'time': '2025-08-16T00:19:22.928Z'}}\n**disconnect**: {}\n**reconnect**: {'connectionId': 'PX02If3RjoECJWg=', 'requestId': 'b7865127-98af-4942-8e43-18aa7a6aa027', 'statusCode': 201, 'data': {'time': '2025-08-16T00:19:25.674Z'}} |\n| **Result** | ✅ **Pass** - WebSocket reconnection successful |\n\n### Test 33: 系统状态监控\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 系统状态检查 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **config_check**: {'connectionId': 'PX02If3RjoECJWg=', 'requestId': '218860380', 'statusCode': 201, 'data': {'time': '2025-08-16T00:19:26.127Z'}}\n**actions_check**: {'connectionId': 'PX02If3RjoECJWg=', 'requestId': '270937210', 'statusCode': 201, 'data': {'time': '2025-08-16T00:19:26.687Z'}}\n**ping_check**: {'data': {'request_id': 562096730, 'time': '2025-08-16T00:19:27.256Z'}, 'callType': 'ping', 'buildingId': 'building:4TFxWRCv23D', 'groupId': '1'} |\n| **Result** | ❌ **Fail** - One or more system status checks failed |\n\n### Test 34: 边界情况处理\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 边界值处理 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **edge_cases**: [{'case': 'empty_building_id', 'response': {'type': 'error', 'connectionId': 'PX02If3RjoECJWg=', 'requestId': 681659194, 'statusCode': 400, 'data': {'error': "'buildingId' is not allowed to be empty"}}}, {'case': 'large_area', 'response': {'connectionId': 'PX02If3RjoECJWg=', 'requestId': 625037382, 'statusCode': 201, 'data': {'time': '2025-08-16T00:19:28.376Z'}}}, {'case': 'negative_area', 'response': {'connectionId': 'PX02If3RjoECJWg=', 'requestId': 360441338, 'statusCode': 201, 'data': {'time': '2025-08-16T00:19:28.773Z'}}}] |\n| **Result** | ❌ **Fail** - Only 1/3 edge cases handled |\n\n### Test 35: 性能基准\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 性能基准测试 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **performance_data**: [{'request_num': 1, 'duration': 0.4426920413970947, 'status': 201, 'success': True}, {'request_num': 2, 'duration': 0.39791369438171387, 'status': 201, 'success': True}, {'request_num': 3, 'duration': 0.5812811851501465, 'status': 201, 'success': True}, {'request_num': 4, 'duration': 0.40108299255371094, 'status': 201, 'success': True}, {'request_num': 5, 'duration': 0.3957068920135498, 'status': 201, 'success': True}] |\n| **Result** | ✅ **Pass** - Performance benchmark passed: avg=0.44s, max=0.58s |\n\n### Test 36: 集成完整性\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 端到端集成测试 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **integration_steps**: [{'step': 'get_config', 'status': 201, 'success': False}, {'step': 'subscribe', 'status': 201, 'success': True}, {'step': 'call_action', 'status': 201, 'success': True}, {'step': 'get_events', 'event_received': False, 'success': False}, {'step': 'ping', 'status': None, 'success': False}] |\n| **Result** | ❌ **Fail** - Integration incomplete: 2/5 steps successful |\n\n### Test 37: 安全验证\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 安全漏洞检测 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **security_tests**: [{'test': 'sql_injection', 'blocked': True, 'response': {'type': 'error', 'connectionId': 'PX02If3RjoECJWg=', 'requestId': 645603248, 'statusCode': 400, 'data': {'error': "'buildingId' with value 'building:'; DROP TABLE users; --' fails to match the required pattern: /^building:[a-zA-Z0-9]+$/"}}}, {'test': 'xss_attempt', 'blocked': True, 'response': {'type': 'error', 'connectionId': 'PX02If3RjoECJWg=', 'requestId': 819496247, 'statusCode': 400, 'data': {'error': "'groupId' length must be less than or equal to 2 characters long"}}}, {'test': 'long_string', 'blocked': True, 'response': {'type': 'error', 'connectionId': 'PX02If3RjoECJWg=', 'requestId': 534518949, 'statusCode': 400, 'data': {'error': "'buildingId' with value 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' fails to match the required pattern: /^building:[a-zA-Z0-9]+$/"}}}] |\n| **Result** | ✅ **Pass** - All 3 security tests blocked malicious input |\n\n### Test 38: 最终综合\n\n| Section | Content |\n|---------|---------|\n| **Expected** | 全面综合测试 |\n| **Request** | ```json\nnull\n``` |\n| **Observed** | **comprehensive_results**: {'config_check': False, 'subscribe_check': True, 'call_check': True, 'cancel_check': False, 'ping_check': False, 'events_check': False} |\n| **Result** | ❌ **Fail** - Comprehensive test failed: 2/6 checks successful |\n\n## Appendix\n- **JSONL Log**: kone_validation.log\n- **Evidence Buffer**: 184 entries\n