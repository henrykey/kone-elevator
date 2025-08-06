# Elevator Control API v2.0

基于KONE SR-API v2.0的WebSocket电梯控制REST API服务，支持实时电梯呼叫、状态监控和多品牌扩展。

## 🚀 功能特性

- **WebSocket实时通信**: 基于KONE SR-API v2.0的WebSocket协议
- **OAuth 2.0认证**: 完整的客户端凭证流程和令牌管理
- **多品牌支持**: 抽象驱动架构，支持KONE等多种电梯品牌
- **REST API包装**: 将WebSocket功能包装为易于集成的REST接口
- **实时监控**: 电梯状态、位置、门状态等实时事件推送
- **完整日志记录**: 结构化日志，支持调试和审计
- **参数验证**: 严格的输入验证和错误处理

## 📋 系统要求

- Python 3.8+
- FastAPI 0.104+
- WebSockets支持
- KONE API访问凭证

## 🛠 安装和配置

### 1. 克隆项目
```bash
git clone <repository-url>
cd elevator-control-api
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置文件
编辑 `config.yaml` 文件，填入KONE API凭证：

```yaml
kone:
  client_id: "your_client_id_here"
  client_secret: "your_client_secret_here"
  token_endpoint: "https://dev.kone.com/api/v2/oauth2/token"
  websocket_endpoint: "wss://dev.kone.com/stream-v2"
  scope: "callgiving/building:9990000951 robotcall/building:9990000951"

logging:
  level: "INFO"
  file: "elevator.log"

api:
  host: "0.0.0.0"
  port: 8000
```

### 4. 启动服务
```bash
python app.py
```

或使用uvicorn：
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## 📖 API文档

### 基础端点

#### 获取API信息
```http
GET /
```

#### 获取系统状态
```http
GET /api/elevator/status
```

### 电梯操作

#### 初始化连接
```http
GET /api/elevator/initialize?elevator_type=kone
```

#### 发起电梯呼叫
```http
POST /api/elevator/call?elevator_type=kone
Content-Type: application/json

{
  "building_id": "building:9990000951",
  "source": 3000,
  "destination": 5000,
  "action_id": 2,
  "group_id": "1",
  "delay": 0,
  "language": "en-GB",
  "priority": "LOW",
  "group_size": 1
}
```

#### 取消呼叫
```http
POST /api/elevator/cancel?building_id=building:9990000951&request_id=call_123&elevator_type=kone
```

#### 获取电梯模式
```http
GET /api/elevator/mode?building_id=building:9990000951&group_id=1&elevator_type=kone
```

#### 获取建筑配置
```http
GET /api/elevator/config?building_id=building:9990000951&elevator_type=kone
```

#### Ping连接测试
```http
GET /api/elevator/ping?building_id=building:9990000951&elevator_type=kone
```

### 响应格式

#### 成功响应
```json
{
  "success": true,
  "status_code": 201,
  "request_id": "uuid-string",
  "session_id": "session-uuid",
  "message": "Call registered successfully"
}
```

#### 错误响应
```json
{
  "success": false,
  "status_code": 400,
  "error": "SAME_SOURCE_AND_DEST_FLOOR",
  "message": "Source and destination cannot be the same"
}
```

## 🔧 架构设计

### 核心组件

1. **ElevatorDriver (抽象基类)**
   - 定义统一的电梯操作接口
   - 支持多品牌电梯扩展

2. **KoneDriver (KONE实现)**
   - WebSocket连接管理
   - OAuth 2.0认证
   - 消息队列处理
   - 实时事件监听

3. **FastAPI应用**
   - REST API端点暴露
   - 请求验证和路由
   - 错误处理和响应

4. **ElevatorDriverFactory (工厂模式)**
   - 驱动实例创建
   - 配置文件管理

### WebSocket消息流程

```
客户端 -> REST API -> WebSocket驱动 -> KONE API
                                   <- 实时事件推送
```

## 🧪 测试

### 运行单元测试
```bash
pytest test_kone_api_v2.py -v
```

### 运行完整测试套件
```bash
pytest test_elevator.py -v --tb=short
```

### KONE验证测试
基于KONE Service Robot API solution validation test guide v2.0：
```bash
python test_kone_validation.py
```

## 📊 日志和监控

### 日志文件
- **位置**: `elevator.log`
- **格式**: 结构化JSON日志
- **内容**: API调用、WebSocket消息、错误信息

### 监控指标
- WebSocket连接状态
- API响应时间
- 成功/失败率
- 令牌刷新频率

## 🔒 安全特性

- **OAuth 2.0认证**: 安全的API访问控制
- **HTTPS/WSS加密**: 端到端加密传输
- **参数验证**: 严格的输入验证
- **会话管理**: 安全的会话生命周期管理
- **令牌自动刷新**: 防止令牌过期

## 🚨 错误处理

### 常见错误码

| 状态码 | 错误类型 | 描述 |
|--------|----------|------|
| 400 | SAME_SOURCE_AND_DEST_FLOOR | 起始楼层与目标楼层相同 |
| 400 | Invalid delay | 延迟参数超出范围(0-30秒) |
| 401 | Authentication failed | OAuth认证失败 |
| 404 | Invalid building id | 无效的建筑ID |
| 409 | Request not cancellable | 请求不在可取消状态 |
| 500 | Internal error | 服务内部错误 |

### 重试机制
- WebSocket连接自动重连
- OAuth令牌自动刷新
- 消息发送失败重试

## 🔄 扩展其他电梯品牌

### 1. 实现驱动类
```python
class OtisDriver(ElevatorDriver):
    async def initialize(self) -> dict:
        # Otis特定的初始化逻辑
        pass
    
    async def call(self, request: ElevatorCallRequest) -> dict:
        # Otis特定的呼叫逻辑
        pass
    # ... 其他方法
```

### 2. 注册到工厂
```python
# 在ElevatorDriverFactory中添加
if elevator_type.lower() == 'otis':
    return OtisDriver(**kwargs)
```

### 3. 更新配置
```yaml
otis:
  api_endpoint: "https://otis-api.com"
  api_key: "your_otis_api_key"
```

## 📝 开发指南

### 代码风格
- 使用Black进行代码格式化
- 遵循PEP 8编码规范
- 类型提示支持

### 提交规范
- 功能: `feat: 添加新功能`
- 修复: `fix: 修复bug`
- 文档: `docs: 更新文档`
- 测试: `test: 添加测试`

## 📞 支持和联系

- **公司**: IBC-AI Co.
- **邮箱**: contact@ibc-ai.com
- **技术支持**: support@ibc-ai.com
- **文档**: [API文档链接]

## 📄 许可证

[许可证信息]

## 🔄 更新日志

### v2.0.1 (2025-08-06)
- 实现完整的KONE SR-API v2.0支持
- 添加WebSocket实时通信
- 完善OAuth 2.0认证流程
- 支持多种电梯操作类型
- 添加实时状态监控

### v2.0.0 (2025-08-06)
- 初始版本发布
- 基础REST API实现
- KONE驱动支持

---

**Author**: IBC-AI Co. - Elevator Systems Division
