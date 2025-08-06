from abc import ABC, abstractmethod
import requests
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
    source: int = Field(..., description="Source floor/area")
    destination: int = Field(..., description="Destination floor/area")
    delay: int = Field(0, ge=0, le=30, description="Delay in seconds")
    action_id: int = Field(2, description="Action ID")
    group_id: str = Field("1", description="Group ID")
    call_type: str = Field("action", description="Call type")
    terminal: int = Field(1, description="Terminal ID")
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
        self.access_token = None
        self.token_expiry = None
        self.session_id = None
        self.websocket = None
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

    async def get_access_token(self) -> str:
        """获取OAuth 2.0 access token"""
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token
        
        config = self._load_config()
        scope = config.get('scope', f'callgiving/{self.client_id} robotcall/{self.client_id}')
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": scope
        }
        
        try:
            response = requests.post(self.token_endpoint, data=data, timeout=30)
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
            
            logger.info(f"Token acquired successfully, expires at {self.token_expiry}")
            return self.access_token
            
        except requests.RequestException as e:
            logger.error(f"Failed to get access token: {e}")
            raise Exception(f"OAuth token acquisition failed: {str(e)}")

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
            if request_id and request_id in self.pending_requests:
                future = self.pending_requests.pop(request_id)
                if not future.done():
                    future.set_result(data)
            
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
            
            if response.get('status') == 201:
                self.session_id = response.get('sessionId')
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
                    'status_code': response.get('status', 500),
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
            
            # 构建呼叫消息
            call_payload = LiftCallPayload(
                request_id=str(uuid.uuid4()),
                area=request.source,
                time=datetime.now().isoformat() + 'Z',
                terminal=request.terminal,
                call=CallRequest(
                    action=request.action_id,
                    destination=request.destination,
                    language=request.language,
                    delay=request.delay,
                    call_replacement_priority=request.priority,
                    group_size=request.group_size,
                    allowed_lifts=request.allowed_lifts
                )
            )
            
            lift_call_msg = LiftCallMessage(
                type="lift-call-api-v2",
                buildingId=request.building_id,
                callType=request.call_type,
                groupId=request.group_id,
                payload=call_payload
            )
            
            response = await self._send_message(lift_call_msg.dict())
            
            if response.get('status') == 201:
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
            
            if response.get('status') == 202:
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
        """获取电梯模式/状态"""
        try:
            if not self.websocket or self.websocket.closed:
                init_result = await self.initialize()
                if not init_result['success']:
                    return init_result
            
            # 订阅电梯状态监控
            monitor_msg = {
                "type": "site-monitoring",
                "buildingId": building_id,
                "callType": "monitor",
                "groupId": group_id,
                "payload": {
                    "sub": f"elevator-status-{uuid.uuid4()}",
                    "duration": 60,
                    "subtopics": ["lift_status/+", "deck_position/+"]
                }
            }
            
            response = await self._send_message(monitor_msg, timeout=10)
            
            if response.get('status') == 200:
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
            
            config_msg = {
                "type": "common-api",
                "buildingId": building_id,
                "callType": "config",
                "groupId": "1"
            }
            
            response = await self._send_message(config_msg)
            
            if response.get('status') == 200:
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
        """Ping建筑以检查连接性"""
        try:
            if not self.websocket or self.websocket.closed:
                init_result = await self.initialize()
                if not init_result['success']:
                    return init_result
            
            ping_msg = {
                "type": "common-api",
                "buildingId": building_id,
                "callType": "ping",
                "groupId": "1",
                "payload": {
                    "request_id": int(datetime.now().timestamp() * 1000)
                }
            }
            
            start_time = datetime.now()
            response = await self._send_message(ping_msg, timeout=10)
            end_time = datetime.now()
            
            if response.get('status') == 200:
                latency = (end_time - start_time).total_seconds() * 1000
                result = {
                    'success': True,
                    'status_code': 200,
                    'latency_ms': round(latency, 2),
                    'server_time': response.get('server_time'),
                    'message': 'Ping successful'
                }
                logger.info(f"Ping successful: {building_id}, latency: {latency}ms")
                return result
            else:
                result = {
                    'success': False,
                    'status_code': response.get('status', 500),
                    'error': response.get('error', 'Ping failed')
                }
                logger.error(f"Ping failed: {result}")
                return result
                
        except Exception as e:
            result = {
                'success': False,
                'status_code': 500,
                'error': f'Ping failed: {str(e)}'
            }
            logger.error(f"Ping error: {result}")
            return result

    async def close(self):
        """关闭WebSocket连接"""
        try:
            if self.websocket and not self.websocket.closed:
                await self.websocket.close()
                logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"Error closing WebSocket: {e}")


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