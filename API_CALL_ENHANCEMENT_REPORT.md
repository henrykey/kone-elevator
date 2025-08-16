# KONE API调用信息增强报告

## 功能概述

已成功增强测试报告，包含详细的API调用信息，包括：

1. **接口类型** - WebSocket或HTTP REST
2. **URL地址** - 完整的接口端点
3. **请求方法** - API调用的具体方法
4. **发送参数** - 完整的请求参数
5. **响应数据** - 接口响应（限制前1-2组）
6. **状态码** - HTTP/WebSocket状态码
7. **时间戳** - 调用时间
8. **错误信息** - 失败时的详细错误

## 实施的增强功能

### 1. 数据结构增强

```python
@dataclass
class APICallInfo:
    """API调用详细信息"""
    interface_type: str  # 接口类型: "WebSocket" 或 "HTTP REST"
    url: str            # 请求URL
    method: Optional[str] = None  # HTTP方法或WebSocket消息类型
    request_parameters: Optional[Dict] = None  # 发送的请求参数
    response_data: Optional[List[Dict]] = None  # 响应数据 (限制前1-2组)
    status_code: Optional[int] = None    # HTTP状态码
    timestamp: Optional[str] = None      # 调用时间戳
    error_message: Optional[str] = None  # 错误信息
```

### 2. Landing Call API示例

按照KONE标准格式，包含您提供的示例格式：

```json
{
  "interface_type": "WebSocket",
  "url": "wss://dev.kone.com/stream-v2",
  "method": "lift-call-api-v2/action",
  "request_parameters": {
    "type": "lift-call-api-v2",
    "buildingId": "building:L1QinntdEOg",
    "callType": "action",
    "groupId": "1",
    "payload": {
      "request_id": 478212054,
      "area": 3000,  // source floor area id
      "time": "2025-08-16T08:05:53.317637Z",
      "terminal": 1,
      "call": {
        "action": 2002,
        "activate_call_states": ["being_fixed"],
        "destination": 5000
      }
    }
  },
  "response_status": 201,
  "response_sample": {
    "connectionId": "PY5K4dp2DoECF5A=",
    "requestId": 908721612,
    "statusCode": 201,
    "data": {
      "request_id": 908721612,
      "success": true,
      "session_id": 134
    },
    "callType": "action",
    "buildingId": "building:L1QinntdEOg",
    "groupId": "1",
    "sessionId": 134
  }
}
```

### 3. 支持的API类型

#### WebSocket API调用：
- **common-api/config** - 获取建筑配置
- **common-api/actions** - 获取可用动作
- **common-api/ping** - 系统连接测试
- **lift-call-api-v2/action** - 电梯呼叫操作
- **monitor-api/subscribe** - 状态监控订阅

#### HTTP REST API调用：
- **Token获取** - OAuth2认证（待添加）
- **Building列表** - 获取可用建筑（待添加）

### 4. 报告格式

每个测试结果现在包含：

```json
{
  "test": "Test 1",
  "description": "Initialization",
  "status": "PASS",
  "api_calls": [
    {
      "interface_type": "WebSocket",
      "url": "wss://dev.kone.com/stream-v2", 
      "method": "common-api/config",
      "request_parameters": {...},
      "response_data": [{...}],
      "status_code": 201,
      "timestamp": "2025-08-16T08:05:18.434532+00:00",
      "error_message": null
    }
  ]
}
```

### 5. 响应数据限制

- 响应数据自动限制为前1-2组，避免报告过大
- 保留完整的错误信息用于调试
- 包含状态码和时间戳便于问题追踪

## 使用示例

```bash
# 运行单个测试并查看API调用信息
python testall_v2.py --only 4
cat reports/validation_report.json | jq '.test_results[0].api_calls'

# 查看所有API调用类型概览
cat reports/validation_report.json | jq '.test_results[] | {test: .test, api_calls: (.api_calls | length), api_types: [.api_calls[].method]}'
```

## 文件修改列表

1. **report_generator.py** - 添加APICallInfo类，增强JSON报告格式
2. **testall_v2.py** - 修改TestResult类，添加API调用收集功能
3. 已增强的测试方法：
   - `test_01_initialization` - Config/Actions/Ping API
   - `test_03_operational_mode` - Subscribe API
   - `test_04_basic_elevator_call` - Landing Call API

## 下一步计划

1. 为其余35个测试添加API调用信息收集
2. 添加HTTP REST API调用信息（Token、Building列表等）
3. 添加更多API错误处理和状态码映射
4. 可选：重新启用Markdown/HTML报告格式并包含API调用信息
