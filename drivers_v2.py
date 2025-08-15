from abc import ABC, abstractmethod
import requests
import aiohttp
import websockets
import asyncio
import json
import uuid
import yaml
import time
from typing import Dict, Optional, List, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from collections import deque

# 配置日志
logging.basicConfig(
    filename='elevator.log', 
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 证据缓冲区用于记录请求/响应/事件
EVIDENCE_BUFFER = deque(maxlen=10000)

def log_evidence(phase: str, data: Dict[str, Any]):
    """记录证据到缓冲区和文件"""
    evidence = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'phase': phase,
        **data
    }
    EVIDENCE_BUFFER.append(evidence)
    
    # 写入JSONL文件
    try:
        with open('kone_validation.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps(evidence, ensure_ascii=False) + '\n')
    except Exception as e:
        logger.error(f"Failed to write evidence: {e}")

# WebSocket API v2 消息模型 - 严格遵循 elevator-websocket-api-v2.yaml

class CommonApiPayload(BaseModel):
    """common-api 通用负载"""
    request_id: Optional[str] = None

class LiftCallApiV2Payload(BaseModel):
    """lift-call-api-v2 负载"""
    request_id: str = Field(..., description="唯一请求ID")
    area: int = Field(..., description="源区域ID")
    time: str = Field(..., description="ISO 8601时间戳")
    terminal: int = Field(1, description="终端ID")
    call: Optional[Dict[str, Any]] = None  # action呼叫时使用
    served_area: Optional[int] = None     # hold_open时使用
    lift_deck: Optional[str] = None       # hold_open时使用  
    hard_time: Optional[int] = None       # hold_open时使用
    soft_time: Optional[int] = None       # hold_open时使用
    session_id: Optional[str] = None      # delete时使用

class SiteMonitoringPayload(BaseModel):
    """site-monitoring 负载"""
    sub: str = Field(..., description="订阅ID")
    duration: int = Field(300, le=300, description="订阅持续时间(秒)")
    subtopics: List[str] = Field(..., description="订阅主题列表")

class WebSocketMessage(BaseModel):
    """WebSocket消息基础结构"""
    type: str = Field(..., description="消息类型")
    buildingId: str = Field(..., description="建筑ID")
    callType: str = Field(..., description="呼叫类型")
    groupId: str = Field("1", description="组ID")
    requestId: Optional[str] = None
    payload: Union[CommonApiPayload, LiftCallApiV2Payload, SiteMonitoringPayload] = None

# Legacy classes for backward compatibility (simplified)
class ElevatorCallRequest(BaseModel):
    """Legacy support for existing code"""
    building_id: str = Field(..., description="Building ID")
    group_id: str = Field("1", description="Group ID")
    from_floor: int = Field(..., description="Source floor number")
    to_floor: int = Field(..., description="Destination floor number")
    user_id: str = Field(..., description="User ID")
    source: Optional[int] = Field(None, description="Source area ID")
    destination: Optional[int] = Field(None, description="Destination area ID")
    action_id: int = Field(2, description="Action ID")
    call_type: str = Field("action", description="Call type")
    terminal: int = Field(1, description="Terminal ID")
    delay: int = Field(0, ge=0, le=30, description="Delay in seconds")
    language: Optional[str] = Field("en-GB", description="Language preference")
    priority: Optional[str] = Field("LOW", description="Call priority")
    group_size: Optional[int] = Field(1, description="Group size")
    allowed_lifts: Optional[List[int]] = Field(None, description="Allowed lifts")

class ElevatorDriver(ABC):
    """电梯驱动抽象接口 - 严格遵循 WebSocket API v2"""
    
    @abstractmethod
    async def get_building_config(self, building_id: str, group_id: Optional[str] = None) -> dict:
        """获取建筑配置 - common-api config"""
        pass
    
    @abstractmethod
    async def get_actions(self, building_id: str, group_id: Optional[str] = None) -> dict:
        """获取可用动作 - common-api actions"""
        pass
    
    @abstractmethod
    async def ping(self, building_id: str, group_id: Optional[str] = None) -> dict:
        """Ping测试 - common-api ping"""
        pass
    
    @abstractmethod
    async def subscribe(self, building_id: str, subtopics: List[str], duration: int = 300, 
                       group_id: Optional[str] = None, sub: Optional[str] = None) -> dict:
        """订阅监控 - site-monitoring"""
        pass
    
    @abstractmethod
    async def call_action(self, building_id: str, area: int, action: int, 
                         destination: Optional[int] = None, delay: Optional[int] = None, 
                         allowed_lifts: Optional[List[int]] = None, group_size: int = 1, 
                         terminal: int = 1, group_id: Optional[str] = None) -> dict:
        """动作呼叫 - lift-call-api-v2 action"""
        pass
    
    @abstractmethod
    async def hold_open(self, building_id: str, lift_deck: str, served_area: int, 
                       hard_time: int, soft_time: Optional[int] = None, 
                       group_id: Optional[str] = None) -> dict:
        """保持开门 - lift-call-api-v2 hold_open"""
        pass
    
    @abstractmethod
    async def delete_call(self, building_id: str, session_id: str, 
                         group_id: Optional[str] = None) -> dict:
        """删除呼叫 - lift-call-api-v2 delete"""
        pass
    
    @abstractmethod
    async def next_event(self, timeout: float = 30.0) -> Optional[dict]:
        """获取下一个事件"""
        pass

class KoneDriverV2(ElevatorDriver):
    """KONE WebSocket API v2 驱动实现"""
    
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
        self.event_queue = asyncio.Queue()
        self.pending_requests = {}
        self.is_listening = False
        self.connection_lock = asyncio.Lock()
        
    async def _get_access_token(self) -> str:
        """获取访问令牌"""
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry - timedelta(minutes=5):
            return self.access_token
            
        # 尝试从配置文件加载缓存的token
        cached_token, cached_expiry = self._load_cached_token()
        if cached_token and cached_expiry and datetime.now() < cached_expiry - timedelta(minutes=5):
            self.access_token = cached_token
            self.token_expiry = cached_expiry
            return cached_token
            
        # 请求新token
        import base64
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'client_credentials',
            'scope': 'application/inventory callgiving/*'
        }
        
        log_evidence('request', {
            'method': 'POST',
            'url': self.token_endpoint,
            'headers': {k: v for k, v in headers.items() if 'Authorization' not in k},
            'data': data
        })
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.token_endpoint, data=data, headers=headers) as response:
                response_data = await response.json()
                
                log_evidence('response', {
                    'status': response.status,
                    'data': {k: v for k, v in response_data.items() if 'access_token' not in k}
                })
                
                if response.status == 200:
                    self.access_token = response_data['access_token']
                    expires_in = response_data.get('expires_in', 3600)
                    self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                    
                    # 保存token到配置
                    self._save_token_to_config(self.access_token, self.token_expiry)
                    return self.access_token
                else:
                    raise Exception(f"Token request failed: {response.status}")
    
    def _load_cached_token(self) -> tuple[Optional[str], Optional[datetime]]:
        """从配置文件加载缓存的token"""
        try:
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            
            cached = config.get('kone', {}).get('cached_token', {})
            token = cached.get('access_token')
            expires_str = cached.get('expires_at')
            
            if token and expires_str:
                expires_at = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                return token, expires_at.replace(tzinfo=None)
                
        except Exception as e:
            logger.error(f"Failed to load cached token: {e}")
        
        return None, None
    
    def _save_token_to_config(self, access_token: str, expires_at: datetime):
        """保存token到配置文件"""
        try:
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            
            if 'kone' not in config:
                config['kone'] = {}
            
            # 脱敏处理 - 仅保存必要信息
            config['kone']['cached_token'] = {
                'access_token': access_token,
                'expires_at': expires_at.isoformat(),
                'token_type': 'Bearer'
            }
            
            with open('config.yaml', 'w') as f:
                yaml.safe_dump(config, f, default_flow_style=False, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save token: {e}")
    
    async def _ensure_connection(self):
        """确保WebSocket连接"""
        async with self.connection_lock:
            if self.websocket and not self.websocket.closed:
                return
                
            token = await self._get_access_token()
            uri = f"{self.ws_endpoint}?accessToken={token}"
            
            log_evidence('request', {
                'method': 'WebSocket',
                'url': self.ws_endpoint,
                'note': 'Establishing connection'
            })
            
            try:
                self.websocket = await websockets.connect(uri, subprotocols=['koneapi'])
                
                log_evidence('response', {
                    'status': 'connected',
                    'note': 'WebSocket connection established'
                })
                
                # 启动事件监听
                if not self.is_listening:
                    asyncio.create_task(self._listen_events())
                    self.is_listening = True
                    
            except Exception as e:
                log_evidence('response', {
                    'status': 'error',
                    'error': str(e)
                })
                raise
    
    async def _listen_events(self):
        """监听WebSocket事件"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    
                    log_evidence('event', {
                        'type': data.get('type', 'unknown'),
                        'data': data
                    })
                    
                    await self.event_queue.put(data)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.is_listening = False
        except Exception as e:
            logger.error(f"Error in event listener: {e}")
            self.is_listening = False
    
    async def _send_message(self, message: dict) -> dict:
        """发送WebSocket消息并等待响应"""
        await self._ensure_connection()
        
        request_id = message.get('requestId') or message.get('payload', {}).get('request_id') or str(uuid.uuid4())
        
        log_evidence('request', {
            'request_id': request_id,
            'message': message
        })
        
        await self.websocket.send(json.dumps(message))
        
        # 等待响应
        timeout = 30.0
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                
                # 检查是否是对应的响应
                if (response.get('requestId') == request_id or 
                    response.get('payload', {}).get('request_id') == request_id):
                    
                    log_evidence('response', {
                        'request_id': request_id,
                        'response': response
                    })
                    return response
                else:
                    # 不是对应响应，放回队列
                    await self.event_queue.put(response)
                    
            except asyncio.TimeoutError:
                continue
                
        raise TimeoutError(f"No response received for request {request_id}")
    
    async def get_building_config(self, building_id: str, group_id: Optional[str] = None) -> dict:
        """获取建筑配置"""
        message = {
            'type': 'common-api',
            'buildingId': building_id,
            'callType': 'config',
            'groupId': group_id or '1',
            'payload': {
                'request_id': str(uuid.uuid4())
            }
        }
        return await self._send_message(message)
    
    async def get_actions(self, building_id: str, group_id: Optional[str] = None) -> dict:
        """获取可用动作"""
        message = {
            'type': 'common-api', 
            'buildingId': building_id,
            'callType': 'actions',
            'groupId': group_id or '1',
            'payload': {
                'request_id': str(uuid.uuid4())
            }
        }
        return await self._send_message(message)
    
    async def ping(self, building_id: str, group_id: Optional[str] = None) -> dict:
        """Ping测试"""
        message = {
            'type': 'common-api',
            'buildingId': building_id, 
            'callType': 'ping',
            'groupId': group_id or '1',
            'payload': {
                'request_id': str(uuid.uuid4())
            }
        }
        return await self._send_message(message)
    
    async def subscribe(self, building_id: str, subtopics: List[str], duration: int = 300,
                       group_id: Optional[str] = None, sub: Optional[str] = None) -> dict:
        """订阅监控"""
        message = {
            'type': 'site-monitoring',
            'buildingId': building_id,
            'callType': 'monitor', 
            'groupId': group_id or '1',
            'payload': {
                'sub': sub or f'monitor_{int(time.time())}',
                'duration': min(duration, 300),
                'subtopics': subtopics
            }
        }
        return await self._send_message(message)
    
    async def call_action(self, building_id: str, area: int, action: int,
                         destination: Optional[int] = None, delay: Optional[int] = None,
                         allowed_lifts: Optional[List[int]] = None, group_size: int = 1,
                         terminal: int = 1, group_id: Optional[str] = None) -> dict:
        """动作呼叫"""
        call_data = {
            'action': action
        }
        
        if destination is not None:
            call_data['destination'] = destination
            
        if delay is not None:
            if not (0 <= delay <= 30):
                raise ValueError("Delay must be between 0 and 30 seconds")
            call_data['delay'] = delay
            
        if allowed_lifts:
            call_data['allowed_lifts'] = allowed_lifts
            
        call_data['group_size'] = group_size
        
        message = {
            'type': 'lift-call-api-v2',
            'buildingId': building_id,
            'callType': 'action',
            'groupId': group_id or '1',
            'payload': {
                'request_id': str(uuid.uuid4()),
                'area': area,
                'time': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                'terminal': terminal,
                'call': call_data
            }
        }
        return await self._send_message(message)
    
    async def hold_open(self, building_id: str, lift_deck: str, served_area: int,
                       hard_time: int, soft_time: Optional[int] = None,
                       group_id: Optional[str] = None) -> dict:
        """保持开门"""
        if not (0 <= hard_time <= 10):
            raise ValueError("hard_time must be between 0 and 10 seconds")
            
        if soft_time is not None and not (0 <= soft_time <= 30):
            raise ValueError("soft_time must be between 0 and 30 seconds")
        
        payload = {
            'request_id': str(uuid.uuid4()),
            'served_area': served_area,
            'lift_deck': lift_deck,
            'hard_time': hard_time,
            'time': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'terminal': 1
        }
        
        if soft_time is not None:
            payload['soft_time'] = soft_time
        
        message = {
            'type': 'lift-call-api-v2',
            'buildingId': building_id,
            'callType': 'hold_open',
            'groupId': group_id or '1',
            'payload': payload
        }
        return await self._send_message(message)
    
    async def delete_call(self, building_id: str, session_id: str,
                         group_id: Optional[str] = None) -> dict:
        """删除呼叫"""
        message = {
            'type': 'lift-call-api-v2', 
            'buildingId': building_id,
            'callType': 'delete',
            'groupId': group_id or '1',
            'payload': {
                'request_id': str(uuid.uuid4()),
                'session_id': session_id,
                'time': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                'terminal': 1
            }
        }
        return await self._send_message(message)
    
    async def next_event(self, timeout: float = 30.0) -> Optional[dict]:
        """获取下一个事件"""
        try:
            event = await asyncio.wait_for(self.event_queue.get(), timeout=timeout)
            return event
        except asyncio.TimeoutError:
            return None
    
    async def close(self):
        """关闭连接"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        self.is_listening = False

    # Legacy method support for backward compatibility
    async def initialize(self) -> dict:
        """Legacy initialize method"""
        try:
            # Just ensure connection is established
            await self._ensure_connection()
            return {
                'success': True,
                'status_code': 200,
                'message': 'Connection established'
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': 500,
                'error': str(e)
            }
    
    async def call(self, request: ElevatorCallRequest) -> dict:
        """Legacy call method"""
        try:
            response = await self.call_action(
                building_id=request.building_id,
                area=request.source or (request.from_floor * 1000),
                action=request.action_id,
                destination=request.destination or (request.to_floor * 1000),
                delay=request.delay,
                allowed_lifts=request.allowed_lifts,
                group_size=request.group_size or 1,
                terminal=request.terminal,
                group_id=request.group_id
            )
            
            return {
                'success': True,
                'status_code': 201,
                'data': response
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': 500,
                'error': str(e)
            }
    
    async def cancel(self, building_id: str, session_id: str) -> dict:
        """Legacy cancel method"""
        try:
            response = await self.delete_call(building_id, session_id)
            return {
                'success': True,
                'status_code': 202,
                'data': response
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': 500,
                'error': str(e)
            }
    
    async def get_mode(self, building_id: str, group_id: str) -> dict:
        """Legacy get_mode method - use monitoring subscription"""
        try:
            # Subscribe to lift status to get mode
            response = await self.subscribe(
                building_id=building_id,
                subtopics=['lift_+/status'],
                duration=30,
                group_id=group_id
            )
            
            # Wait for status event
            event = await self.next_event(timeout=10.0)
            if event and event.get('type') == 'monitor-lift-status':
                lift_mode = event.get('payload', {}).get('lift_mode', 'unknown')
                return {
                    'success': True,
                    'status_code': 200,
                    'data': {'mode': lift_mode}
                }
            
            return {
                'success': False,
                'status_code': 404,
                'error': 'No status event received'
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': 500,
                'error': str(e)
            }
    
    async def get_config(self, building_id: str) -> dict:
        """Legacy get_config method"""
        try:
            response = await self.get_building_config(building_id)
            return {
                'success': True,
                'status_code': 200,
                'data': response
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': 500,
                'error': str(e)
            }


class ElevatorDriverFactory:
    """电梯驱动工厂类"""
    
    @staticmethod
    def create_driver(elevator_type: str, **kwargs) -> ElevatorDriver:
        """根据类型创建电梯驱动"""
        if elevator_type.lower() == 'kone':
            return KoneDriverV2(**kwargs)
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
                drivers['kone'] = KoneDriverV2(
                    client_id=kone_config['client_id'],
                    client_secret=kone_config['client_secret'],
                    token_endpoint=kone_config.get('token_endpoint', 'https://dev.kone.com/api/v2/oauth2/token'),
                    ws_endpoint=kone_config.get('ws_endpoint', 'wss://dev.kone.com/stream-v2')
                )
            
            return drivers
            
        except Exception as e:
            logger.error(f"Failed to create drivers from config: {e}")
            return {}

# Legacy support - 保持向后兼容
KoneDriver = KoneDriverV2
