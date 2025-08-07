from abc import ABC, abstractmethod
import requests
import aiohttp
import websockets
import asyncio
import json
import uuid
import yaml
from typing import Dict, Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

# 配置日志
logging.basicConfig(
    filename='elevator.log', 
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API v2 消息模型
class CallRequest(BaseModel):
    action: int = Field(..., description="Action ID for landing calls, destination calls and car calls")
    destination: Optional[int] = Field(None, description="Destination area for destination calls")
    language: Optional[str] = Field("en-GB", description="Preferred signaling language")
    delay: Optional[int] = Field(0, ge=0, le=30, description="Delay in seconds")
    call_replacement_priority: Optional[str] = Field("LOW", description="Call replacement priority")
    group_size: Optional[int] = Field(1, ge=1, le=100, description="Group size for group calls")
    allowed_lifts: Optional[List[int]] = Field(None, description="List of allowed lift deck IDs")

class LiftCallPayload(BaseModel):
    request_id: str = Field(..., description="Unique request ID")
    area: int = Field(..., description="Source area/floor")
    time: str = Field(..., description="ISO 8601 timestamp")
    terminal: int = Field(..., description="Terminal ID")
    call: CallRequest
    media_id: Optional[str] = Field(None, description="Access control media ID")
    media_cc: Optional[str] = Field(None, description="Company code portion of media ID")
    media_type: Optional[str] = Field(None, description="Media type (e.g., RFID)")

class LiftCallMessage(BaseModel):
    type: str = Field("lift-call-api-v2", description="Message type")
    buildingId: str = Field(..., description="Building ID in format building:${id}")
    callType: str = Field(..., description="Call type: action, hold_open, delete")
    groupId: str = Field(..., description="Group ID")
    payload: LiftCallPayload

class CancelCallMessage(BaseModel):
    type: str = Field("lift-call-api-v2", description="Message type")
    cancelRequestId: str = Field(..., description="Request ID to cancel")
    requestId: str = Field(..., description="New request ID for cancellation")

class CreateSessionMessage(BaseModel):
    type: str = Field("create-session", description="Message type")
    requestId: str = Field(..., description="Request ID")

class ResumeSessionMessage(BaseModel):
    type: str = Field("resume-session", description="Message type") 
    requestId: str = Field(..., description="Request ID")
    sessionId: str = Field(..., description="Session ID to resume")
    resendLatestStateUpToSeconds: Optional[int] = Field(30, description="Resend latest state")

class ElevatorCallRequest(BaseModel):
    building_id: str = Field(..., description="Building ID")
    group_id: str = Field("1", description="Group ID")
    from_floor: int = Field(..., description="Source floor number")
    to_floor: int = Field(..., description="Destination floor number")
    user_id: str = Field(..., description="User ID")
    source: Optional[int] = Field(None, description="Source area ID (auto-calculated if not provided)")
    destination: Optional[int] = Field(None, description="Destination area ID (auto-calculated if not provided)")
    action_id: int = Field(2, description="Action ID for destination calls")
    call_type: str = Field("action", description="Call type")
    terminal: int = Field(1, description="Terminal ID")
    delay: int = Field(0, ge=0, le=30, description="Delay in seconds")
    language: Optional[str] = Field("en-GB", description="Language preference")
    priority: Optional[str] = Field("LOW", description="Call priority")
    group_size: Optional[int] = Field(1, description="Group size")
    allowed_lifts: Optional[List[int]] = Field(None, description="Allowed lifts")

class ElevatorDriver(ABC):
    @abstractmethod
    async def initialize(self) -> dict:
        """Initialize connection and create session"""
        pass
    
    @abstractmethod
    async def call(self, request: ElevatorCallRequest) -> dict:
        """Make elevator call"""
        pass
    
    @abstractmethod
    async def cancel(self, building_id: str, request_id: str) -> dict:
        """Cancel elevator call"""
        pass
    
    @abstractmethod
    async def get_mode(self, building_id: str, group_id: str) -> dict:
        """Get elevator mode/status"""
        pass
    
    @abstractmethod
    async def get_config(self, building_id: str) -> dict:
        """Get building configuration"""
        pass
    
    @abstractmethod
    async def ping(self, building_id: str) -> dict:
        """Ping building to check connectivity"""
        pass

class KoneDriver(ElevatorDriver):
    def __init__(self, client_id: str, client_secret: str, 
                 token_endpoint: str = "https://dev.kone.com/api/v2/oauth2/token",
                 ws_endpoint: str = "wss://dev.kone.com/stream-v2"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_endpoint = token_endpoint
        self.ws_endpoint = ws_endpoint
        # 从 token_endpoint 推导 base_url
        self.base_url = token_endpoint.replace('/oauth2/token', '') if '/oauth2/token' in token_endpoint else "https://dev.kone.com/api/v2"
        self.access_token = None
        self.token_expiry = None
        self.session_id = None
        self.websocket = None
        self.session = requests.Session()  # HTTP session for REST API calls
        self.connection_lock = asyncio.Lock()
        self.message_queue = asyncio.Queue()
        self.pending_requests = {}
        self.is_listening = False

    def _load_config(self):
        """加载配置文件"""
        try:
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            return config.get('kone', {})
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def _save_token_to_config(self, access_token: str, expires_at: datetime):
        """保存token到配置文件"""
        try:
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            
            if 'kone' not in config:
                config['kone'] = {}
            if 'cached_token' not in config['kone']:
                config['kone']['cached_token'] = {}
            
            config['kone']['cached_token']['access_token'] = access_token
            config['kone']['cached_token']['expires_at'] = expires_at.isoformat()
            config['kone']['cached_token']['token_type'] = "Bearer"
            
            with open('config.yaml', 'w') as f:
                yaml.safe_dump(config, f, default_flow_style=False, indent=2)
            
            logger.info(f"Token cached to config, expires at {expires_at}")
            
        except Exception as e:
            logger.error(f"Failed to save token to config: {e}")
    
    def _load_cached_token(self) -> tuple[Optional[str], Optional[datetime]]:
        """从配置文件加载缓存的token"""
        try:
            config = self._load_config()
            cached_token = config.get('cached_token', {})
            
            access_token = cached_token.get('access_token')
            expires_at_str = cached_token.get('expires_at')
            
            if access_token and expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str)
                # 检查是否还有至少5分钟有效期
                if expires_at > datetime.now() + timedelta(minutes=5):
                    logger.info(f"Loaded cached token, expires at {expires_at}")
                    return access_token, expires_at
                else:
                    logger.info("Cached token expired or expiring soon")
            
            return None, None
            
        except Exception as e:
            logger.error(f"Failed to load cached token: {e}")
            return None, None

    async def get_access_token(self) -> str:
        """获取访问令牌 - 支持缓存和自动刷新"""
        try:
            # 检查缓存的token是否还有效
            if await self._is_token_valid():
                logger.info("Using cached access token")
                return self.access_token
            
            # 获取新的token
            logger.info("Requesting new access token")
            
            # 使用Basic Authentication（RFC 6749标准）
            import base64
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            response = requests.post(
                self.token_endpoint,
                data={'grant_type': 'client_credentials', 'scope': 'application/inventory callgiving/*'},
                headers={
                    'Authorization': f'Basic {encoded_credentials}',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # 保存到配置文件
                await self._save_token_to_config(self.access_token, self.token_expires_at)
                
                logger.info(f"New access token obtained, expires in {expires_in}s")
                return self.access_token
            else:
                raise Exception(f"Token request failed: {response.status_code}, {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            raise

    async def _is_token_valid(self) -> bool:
        """检查token是否有效（未过期且存在）"""
        if not self.access_token or not self.token_expires_at:
            # 尝试从配置文件加载
            await self._load_token_from_config()
            
        if not self.access_token or not self.token_expires_at:
            return False
            
        # 提前5分钟刷新token
        return datetime.now() < (self.token_expires_at - timedelta(minutes=5))

    async def _load_token_from_config(self):
        """从配置文件加载缓存的token"""
        try:
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            
            cached_token = config.get('kone', {}).get('cached_token', {})
            
            if cached_token.get('access_token') and cached_token.get('expires_at'):
                self.access_token = cached_token['access_token']
                self.token_expires_at = datetime.fromisoformat(cached_token['expires_at'])
                logger.info("Token loaded from config cache")
        except Exception as e:
            logger.debug(f"Could not load token from config: {e}")

    async def _save_token_to_config(self, token: str, expires_at: datetime):
        """将token保存到配置文件"""
        try:
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            
            # 更新token缓存
            config['kone']['cached_token'] = {
                'access_token': token,
                'expires_at': expires_at.isoformat(),
                'token_type': 'Bearer'
            }
            
            with open('config.yaml', 'w') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                
            logger.info("Token saved to config cache")
        except Exception as e:
            logger.warning(f"Could not save token to config: {e}")

    async def _connect_websocket(self) -> bool:
        """建立WebSocket连接"""
        try:
            if self.websocket and not self.websocket.closed:
                return True
                
            token = await self.get_access_token()
            uri = f"{self.ws_endpoint}?accessToken={token}"
            
            logger.info(f"Connecting to WebSocket: {uri}")
            self.websocket = await websockets.connect(
                uri,
                subprotocols=['koneapi'],
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            )
            
            logger.info("WebSocket connected successfully")
            
            # 启动消息监听
            if not self.is_listening:
                asyncio.create_task(self._listen_messages())
                self.is_listening = True
                
            return True
            
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            self.websocket = None
            return False

    async def _listen_messages(self):
        """监听WebSocket消息"""
        try:
            while self.websocket and not self.websocket.closed:
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=70)
                    data = json.loads(message)
                    # Log all incoming WebSocket messages (IBC-AI CO.)
                    logger.info(f"WebSocket received message: {json.dumps(data, indent=2)}")
                    await self._handle_message(data)
                except asyncio.TimeoutError:
                    logger.warning("WebSocket receive timeout, sending ping")
                    await self.websocket.ping()
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("WebSocket connection closed")
                    break
                except Exception as e:
                    logger.error(f"Error receiving message: {e}")
                    
        except Exception as e:
            logger.error(f"Message listener error: {e}")
        finally:
            self.is_listening = False

    async def _handle_message(self, data: dict):
        """处理接收到的消息"""
        try:
            request_id = data.get('requestId')
            
            # 处理标准响应消息（有顶级requestId的消息）
            if request_id and request_id in self.pending_requests:
                future = self.pending_requests.pop(request_id)
                if not future.done():
                    future.set_result(data)
                return
            
            # 处理ping响应消息（requestId在data.request_id中）
            elif data.get('callType') == 'ping' and data.get('data', {}).get('request_id'):
                ping_request_id = data['data']['request_id']
                print(f"[DEBUG] 后台收到ping响应，request_id: {ping_request_id}")
                logger.info(f"Received ping response with request_id: {ping_request_id}")
                
                if ping_request_id in self.pending_requests:
                    future = self.pending_requests.pop(ping_request_id)
                    if not future.done():
                        future.set_result(data)
                        print(f"[DEBUG] 成功将ping响应传递给等待中的future")
                        logger.info(f"Resolved ping response for request_id: {ping_request_id}")
                    return
                else:
                    print(f"[DEBUG] 收到ping响应但找不到对应的pending request: {ping_request_id}")
                    logger.warning(f"Received ping response but no pending request for: {ping_request_id}")
            
            # 记录所有消息用于调试
            logger.info(f"Received message: {json.dumps(data, indent=2)}")
            
            # 处理会话创建响应
            if data.get('type') == 'session-created':
                self.session_id = data.get('sessionId')
                logger.info(f"Session created: {self.session_id}")
                
            # 处理状态更新
            elif 'monitor' in data.get('type', ''):
                await self.message_queue.put(data)
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def _send_message(self, message: dict, wait_response: bool = True, timeout: int = 30) -> dict:
        """发送消息并等待响应"""
        async with self.connection_lock:
            if not await self._connect_websocket():
                raise Exception("Failed to establish WebSocket connection")
            
            request_id = message.get('requestId', str(uuid.uuid4()))
            message['requestId'] = request_id
            
            try:
                if wait_response:
                    future = asyncio.Future()
                    self.pending_requests[request_id] = future
                
                await self.websocket.send(json.dumps(message))
                logger.info(f"Sent message: {json.dumps(message, indent=2)}")
                
                if wait_response:
                    try:
                        response = await asyncio.wait_for(future, timeout=timeout)
                        return response
                    except asyncio.TimeoutError:
                        self.pending_requests.pop(request_id, None)
                        raise Exception(f"Request timeout after {timeout}s")
                else:
                    return {"success": True, "message": "Message sent"}
                    
            except Exception as e:
                self.pending_requests.pop(request_id, None)
                raise e

    async def initialize(self) -> dict:
        """初始化连接并创建会话"""
        try:
            # 建立WebSocket连接
            if not await self._connect_websocket():
                return {
                    'success': False, 
                    'status_code': 500, 
                    'error': 'Failed to establish WebSocket connection'
                }
            
            # 创建会话
            create_session_msg = CreateSessionMessage(
                type="create-session",
                requestId=str(uuid.uuid4())
            )
            
            response = await self._send_message(create_session_msg.dict())
            
            if response.get('statusCode') == 201:
                self.session_id = response.get('data', {}).get('sessionId')
                result = {
                    'success': True,
                    'status_code': 201,
                    'session_id': self.session_id,
                    'message': 'Session created successfully'
                }
                logger.info(f"Session initialized: {result}")
                return result
            else:
                result = {
                    'success': False,
                    'status_code': response.get('statusCode', 500),
                    'error': response.get('error', 'Session creation failed')
                }
                logger.error(f"Session initialization failed: {result}")
                return result
                
        except Exception as e:
            result = {
                'success': False,
                'status_code': 500,
                'error': f'Initialization failed: {str(e)}'
            }
            logger.error(f"Initialization error: {result}")
            return result

    async def call(self, request: ElevatorCallRequest) -> dict:
        """发起电梯呼叫"""
        try:
            # 确保连接已建立
            if not self.websocket or self.websocket.closed:
                init_result = await self.initialize()
                if not init_result['success']:
                    return init_result
            
            # 计算源区域和目标区域（如果未提供）
            source_area = request.source or (request.from_floor * 1000)
            destination_area = request.destination or (request.to_floor * 1000)
            
            # 构建呼叫消息
            # 确保buildingId符合v2规范格式: building:${buildingId}
            formatted_building_id = request.building_id if request.building_id.startswith("building:") else f"building:{request.building_id}"
            
            call_payload = LiftCallPayload(
                request_id=str(uuid.uuid4()),
                area=source_area,
                time=datetime.now().isoformat() + 'Z',
                terminal=request.terminal,
                call=CallRequest(
                    action=request.action_id,
                    destination=destination_area,
                    delay=request.delay,
                    call_replacement_priority=request.priority,
                    group_size=request.group_size,
                    allowed_lifts=request.allowed_lifts
                )
            )
            
            lift_call_msg = LiftCallMessage(
                type="lift-call-api-v2",
                buildingId=formatted_building_id,
                callType=request.call_type,
                groupId=request.group_id,
                payload=call_payload
            )
            
            response = await self._send_message(lift_call_msg.dict())
            
            if response.get('statusCode') == 201:
                result = {
                    'success': True,
                    'status_code': 201,
                    'request_id': call_payload.request_id,
                    'session_id': response.get('sessionId'),
                    'message': 'Call registered successfully'
                }
                logger.info(f"Call successful: {request.dict()} -> {result}")
                return result
            else:
                result = {
                    'success': False,
                    'status_code': response.get('status', 500),
                    'error': response.get('error', 'Call failed')
                }
                logger.error(f"Call failed: {result}")
                return result
                
        except Exception as e:
            result = {
                'success': False,
                'status_code': 500,
                'error': f'Call failed: {str(e)}'
            }
            logger.error(f"Call error: {result}")
            return result

    async def cancel(self, building_id: str, request_id: str) -> dict:
        """取消电梯呼叫"""
        try:
            if not self.websocket or self.websocket.closed:
                init_result = await self.initialize()
                if not init_result['success']:
                    return init_result
            
            cancel_msg = CancelCallMessage(
                type="lift-call-api-v2",
                cancelRequestId=request_id,
                requestId=str(uuid.uuid4())
            )
            
            response = await self._send_message(cancel_msg.dict())
            
            if response.get('statusCode') == 202:
                result = {
                    'success': True,
                    'status_code': 202,
                    'message': 'Cancellation accepted'
                }
                logger.info(f"Cancel successful: {building_id}, {request_id} -> {result}")
                return result
            else:
                result = {
                    'success': False,
                    'status_code': response.get('status', 500),
                    'error': response.get('error', 'Cancellation failed')
                }
                logger.error(f"Cancel failed: {result}")
                return result
                
        except Exception as e:
            result = {
                'success': False,
                'status_code': 500,
                'error': f'Cancel failed: {str(e)}'
            }
            logger.error(f"Cancel error: {result}")
            return result

    async def get_mode(self, building_id: str, group_id: str) -> dict:
        """获取电梯模式/状态 - 使用site-monitoring订阅"""
        try:
            if not self.websocket or self.websocket.closed:
                init_result = await self.initialize()
                if not init_result['success']:
                    return init_result
            
            # 使用site-monitoring订阅电梯状态
            # 确保buildingId符合v2规范格式: building:${buildingId}
            formatted_building_id = building_id if building_id.startswith("building:") else f"building:{building_id}"
            
            monitor_msg = {
                "type": "site-monitoring",
                "buildingId": formatted_building_id,
                "callType": "monitor",
                "groupId": group_id,
                "payload": {
                    "sub": f"elevator-status-{uuid.uuid4()}",
                    "duration": 60,
                    "subtopics": ["lift_status/+", "deck_position/+"]
                }
            }
            
            response = await self._send_message(monitor_msg, timeout=10)
            
            if response.get('statusCode') == 200:
                # 等待状态更新消息
                try:
                    status_msg = await asyncio.wait_for(self.message_queue.get(), timeout=5)
                    mode = status_msg.get('lift_mode', 0)
                    fault_active = status_msg.get('fault_active', False)
                    
                    result = {
                        'success': True,
                        'status_code': 200,
                        'mode': 'operational' if mode >= 0 and not fault_active else 'fault',
                        'lift_mode': mode,
                        'fault_active': fault_active,
                        'details': status_msg
                    }
                    logger.info(f"Mode check: {building_id}, {group_id} -> {result}")
                    return result
                except asyncio.TimeoutError:
                    # 返回默认状态
                    result = {
                        'success': True,
                        'status_code': 200,
                        'mode': 'operational',
                        'lift_mode': 0,
                        'fault_active': False,
                        'details': 'No recent status updates'
                    }
                    return result
            else:
                result = {
                    'success': False,
                    'status_code': response.get('status', 500),
                    'error': response.get('error', 'Mode check failed')
                }
                logger.error(f"Mode check failed: {result}")
                return result
                
        except Exception as e:
            result = {
                'success': False,
                'status_code': 500,
                'error': f'Mode check failed: {str(e)}'
            }
            logger.error(f"Mode check error: {result}")
            return result

    async def get_config(self, building_id: str) -> dict:
        """获取建筑配置"""
        try:
            if not self.websocket or self.websocket.closed:
                init_result = await self.initialize()
                if not init_result['success']:
                    return init_result
            
            # 确保buildingId符合v2规范格式: building:${buildingId}
            formatted_building_id = building_id if building_id.startswith("building:") else f"building:{building_id}"
            
            config_msg = {
                "type": "common-api",
                "buildingId": formatted_building_id,
                "callType": "config",
                "groupId": "1"
            }
            
            response = await self._send_message(config_msg)
            
            if response.get('statusCode') == 200:
                result = {
                    'success': True,
                    'status_code': 200,
                    'config': response.get('payload', {}),
                    'message': 'Configuration retrieved'
                }
                logger.info(f"Config retrieved: {building_id}")
                return result
            else:
                result = {
                    'success': False,
                    'status_code': response.get('status', 500),
                    'error': response.get('error', 'Config retrieval failed')
                }
                logger.error(f"Config retrieval failed: {result}")
                return result
                
        except Exception as e:
            result = {
                'success': False,
                'status_code': 500,
                'error': f'Config retrieval failed: {str(e)}'
            }
            logger.error(f"Config error: {result}")
            return result

    async def ping(self, building_id: str) -> dict:
        """Ping建筑以检查连接性 - 使用消息队列避免与后台监听器冲突 (IBC-AI CO.)"""
        try:
            # 确保已初始化并有WebSocket连接
            if not self.websocket or self.websocket.closed:
                print(f"[DEBUG] WebSocket未连接，先初始化...")
                init_result = await self.initialize()
                if not init_result['success']:
                    return init_result
            
            # 确保buildingId符合v2规范格式: building:${buildingId}
            formatted_building_id = building_id if building_id.startswith("building:") else f"building:{building_id}"
            
            # 生成唯一request_id用于追踪响应
            request_id = int(datetime.now().timestamp() * 1000)
            
            # 构造ping消息，完全模仿ping.py的成功逻辑
            ping_msg = {
                "type": "common-api",
                "buildingId": formatted_building_id,
                "callType": "ping",
                "groupId": "1",
                "payload": {
                    "request_id": request_id
                }
            }
            
            start_time = datetime.now()
            print(f"[DEBUG] 开始ping测试: {building_id}")
            print(f"[DEBUG] 使用消息队列机制，request_id: {request_id}")
            
            # 注册pending request到消息队列
            response_future = asyncio.Future()
            self.pending_requests[request_id] = response_future
            
            try:
                # 发送ping消息
                async with self.connection_lock:
                    await self.websocket.send(json.dumps(ping_msg))
                    print(f"[DEBUG] 已发送ping消息: {json.dumps(ping_msg, indent=2)}")
                    logger.info(f"Sent ping message: {json.dumps(ping_msg, indent=2)}")
                
                # 等待通过消息队列接收响应
                timeout_duration = 30
                print(f"[DEBUG] 等待ping响应，超时: {timeout_duration}秒...")
                
                try:
                    response_data = await asyncio.wait_for(response_future, timeout=timeout_duration)
                    end_time = datetime.now()
                    latency = (end_time - start_time).total_seconds() * 1000
                    
                    print(f"[DEBUG] 通过消息队列收到ping响应: {json.dumps(response_data, indent=2)}")
                    
                    result = {
                        'success': True,
                        'status_code': response_data.get('statusCode', 200),
                        'latency_ms': round(latency, 2),
                        'server_time': response_data.get('data', {}).get('time'),
                        'message': 'Ping successful',
                        'response_data': response_data
                    }
                    print(f"[DEBUG] Ping成功: {result}")
                    logger.info(f"Ping successful: {building_id}, latency: {latency}ms")
                    return result
                    
                except asyncio.TimeoutError:
                    result = {
                        'success': False,
                        'status_code': 408,
                        'error': f'Ping timeout after {timeout_duration}s'
                    }
                    print(f"[DEBUG] Ping超时: {result}")
                    logger.error(f"Ping timeout: {result}")
                    return result
                    
            finally:
                # 清理pending request
                self.pending_requests.pop(request_id, None)
                
        except Exception as e:
            result = {
                'success': False,
                'status_code': 500,
                'error': f'Ping failed: {str(e)}'
            }
            print(f"[DEBUG] Ping错误: {result}")
            logger.error(f"Ping error: {result}")
            return result
            return result

    async def get_actions(self, building_id: str, group_id: str = "1") -> dict:
        """获取建筑支持的操作列表"""
        try:
            if not self.websocket or self.websocket.closed:
                init_result = await self.initialize()
                if not init_result['success']:
                    return init_result
            
            # 确保buildingId符合v2规范格式: building:${buildingId}
            formatted_building_id = building_id if building_id.startswith("building:") else f"building:{building_id}"
            
            actions_msg = {
                "type": "common-api",
                "buildingId": formatted_building_id,
                "callType": "actions",
                "groupId": group_id
            }
            
            response = await self._send_message(actions_msg)
            
            if response.get('statusCode') == 200:
                result = {
                    'success': True,
                    'status_code': 200,
                    'actions': response.get('payload', {}),
                    'message': 'Actions retrieved'
                }
                logger.info(f"Actions retrieved: {building_id}")
                return result
            else:
                result = {
                    'success': False,
                    'status_code': response.get('status', 500),
                    'error': response.get('error', 'Actions retrieval failed')
                }
                logger.error(f"Actions retrieval failed: {result}")
                return result
                
        except Exception as e:
            result = {
                'success': False,
                'status_code': 500,
                'error': f'Actions retrieval failed: {str(e)}'
            }
            logger.error(f"Actions error: {result}")
            return result

    async def get_resources(self) -> dict:
        """获取当前token可访问的所有building id信息"""
        try:
            # Ensure we have a valid access token (IBC-AI CO.)
            token = await self.get_access_token()
            
            # Build the correct API endpoint URL (IBC-AI CO.)
            url = f"{self.base_url}/application/self/resources"
            
            # Set up request headers with Bearer token (IBC-AI CO.)
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Create aiohttp session and send GET request (IBC-AI CO.)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    # Check if request was successful (IBC-AI CO.)
                    if response.status == 200:
                        # Parse and return the JSON response (IBC-AI CO.)
                        json_data = await response.json()
                        logger.info(f"Successfully retrieved resources from {url}")
                        return json_data
                    else:
                        # Get error message for logging (IBC-AI CO.)
                        error_text = await response.text()
                        error_msg = f"Resource request failed: {response.status}, {error_text}"
                        logger.error(f"get_resources error: {error_msg}")
                        # Raise exception with detailed error information (IBC-AI CO.)
                        raise Exception(error_msg)
                        
        except Exception as e:
            # Log any unexpected errors (IBC-AI CO.)
            logger.error(f"get_resources unexpected error: {e}")
            # Re-raise the exception for caller handling (IBC-AI CO.)
            raise e

    async def close(self):
        """关闭WebSocket连接和HTTP session"""
        try:
            if self.websocket and not self.websocket.closed:
                await self.websocket.close()
                logger.info("WebSocket connection closed")
            
            # 关闭HTTP session
            if hasattr(self, 'session') and self.session:
                self.session.close()
                logger.info("HTTP session closed")
        except Exception as e:
            logger.error(f"Error closing connections: {e}")


class ElevatorDriverFactory:
    """电梯驱动工厂类"""
    
    @staticmethod
    def create_driver(elevator_type: str, **kwargs) -> ElevatorDriver:
        """根据类型创建电梯驱动"""
        if elevator_type.lower() == 'kone':
            return KoneDriver(**kwargs)
        else:
            raise ValueError(f"Unsupported elevator type: {elevator_type}")
    
    @staticmethod
    def create_from_config(config_path: str = 'config.yaml') -> Dict[str, ElevatorDriver]:
        """从配置文件创建驱动实例"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            drivers = {}
            kone_config = config.get('kone', {})
            if kone_config:
                drivers['kone'] = KoneDriver(
                    client_id=kone_config['client_id'],
                    client_secret=kone_config['client_secret'],
                    token_endpoint=kone_config.get('token_endpoint', 'https://dev.kone.com/api/v2/oauth2/token'),
                    ws_endpoint=kone_config.get('ws_endpoint', 'wss://dev.kone.com/stream-v2')
                )
            
            return drivers
            
        except Exception as e:
            logger.error(f"Failed to create drivers from config: {e}")
            return {}