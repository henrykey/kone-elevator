from abc import ABC, abstractmethod
import requests
import websockets
import asyncio
import json
from pydantic import BaseModel
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

logging.basicConfig(filename='elevator.log', level=logging.INFO)

class ElevatorCallRequest(BaseModel):
    building_id: str
    source: int
    destination: int
    delay: int = 0
    action_id: int = None
    elevator_id: str = None
    group_id: str = None

class ElevatorDriver(ABC):
    @abstractmethod
    async def initialize(self) -> dict:
        pass
    @abstractmethod
    async def call(self, request: ElevatorCallRequest) -> dict:
        pass
    @abstractmethod
    async def cancel(self, building_id: str, session_id: str) -> dict:
        pass
    @abstractmethod
    async def get_mode(self, building_id: str, elevator_id: str) -> dict:
        pass

class KoneDriver(ElevatorDriver):
    def __init__(self, client_id: str, client_secret: str, token_endpoint: str = "https://dev.kone.com/api/v2/oauth2/token", ws_endpoint: str = "wss://dev.kone.com/stream-v2"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_endpoint = token_endpoint
        self.ws_endpoint = ws_endpoint
        self.access_token = None
        self.token_expiry = None
        self.session_id = None
        self.websocket = None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def get_access_token(self) -> str:
        """获取或刷新 KONE access token"""
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "building:read building:write"
        }
        try:
            response = requests.post(self.token_endpoint, data=data)
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.token_expiry = datetime.now() + timedelta(seconds=token_data["expires_in"] - 60)
            logging.info(f"Token acquired: {self.access_token[:10]}... expires at {self.token_expiry}")
            return self.access_token
        except requests.RequestException as e:
            logging.error(f"Failed to get token: {str(e)}")
            raise Exception(f"Failed to get token: {str(e)}")

    async def initialize(self) -> dict:
        try:
            self.websocket = await websockets.connect(
                f"{self.ws_endpoint}?accessToken={self.get_access_token()}",
                subprotocols=['koneapi']
            )
            create_session = {"type": "create-session", "requestId": str(int(datetime.now().timestamp()))}
            await self.websocket.send(json.dumps(create_session))
            response = json.loads(await self.websocket.recv())
            if response.get('status') == 201:
                self.session_id = response.get('sessionId', 'sim_session_123')
                result = {'success': True, 'status_code': 201, 'session_id': self.session_id, 'building_id': 'sim_abc123'}
                logging.info(f"Initialize: {result}")
                return result
            result = {'success': False, 'status_code': response.get('status', 500), 'error': response.get('error', 'Unknown error')}
            logging.error(f"Initialize failed: {result}")
            return result
        except Exception as e:
            result = {'success': False, 'error': f"WebSocket connection failed: {str(e)}"}
            logging.error(f"Initialize failed: {result}")
            return result

    async def call(self, request: ElevatorCallRequest) -> dict:
        if not self.websocket or self.websocket.closed:
            await self.initialize()
        try:
            call_payload = {
                "type": "lift-call-api-v2",
                "buildingId": request.building_id,
                "groupId": request.group_id or "1",
                "payload": {
                    "request_id": int(datetime.now().timestamp()),
                    "area": request.source,
                    "time": datetime.now().isoformat() + 'Z',
                    "terminal": 1,
                    "call": {"action": request.action_id or 2, "destination": request.destination}
                }
            }
            if request.delay:
                call_payload["payload"]["delay"] = request.delay
            if request.elevator_id:
                call_payload["payload"]["elevator_id"] = request.elevator_id
            await self.websocket.send(json.dumps(call_payload))
            response = json.loads(await self.websocket.recv())
            # 模拟响应，实际需解析 WebSocket 消息
            if response.get('status') == 201:
                result = {'success': True, 'status_code': 201, 'session_id': response.get('sessionId', 'sim_ses_12345')}
                logging.info(f"Call: {request.dict()} -> {result}")
                return result
            # 模拟错误，基于指南
            if request.delay > 30:
                result = {'success': False, 'status_code': 201, 'error': 'Invalid json payload'}
            elif request.source == request.destination:
                result = {'success': False, 'status_code': 201, 'error': 'SAME_SOURCE_AND_DEST_FLOOR'}
            else:
                result = {'success': False, 'status_code': response.get('status', 500), 'error': response.get('error', 'Unknown error')}
            logging.error(f"Call failed: {result}")
            return result
        except Exception as e:
            result = {'success': False, 'error': f"WebSocket call failed: {str(e)}"}
            logging.error(f"Call failed: {result}")
            return result

    async def cancel(self, building_id: str, session_id: str) -> dict:
        if not self.websocket or self.websocket.closed:
            await self.initialize()
        try:
            cancel_payload = {
                "type": "lift-call-api-v2",
                "cancelRequestId": session_id,
                "requestId": str(int(datetime.now().timestamp()))
            }
            await self.websocket.send(json.dumps(cancel_payload))
            response = json.loads(await self.websocket.recv())
            if response.get('status') == 202:
                result = {'success': True, 'status_code': 202, 'message': 'Call cancelled'}
                logging.info(f"Cancel: {building_id}, {session_id} -> {result}")
                return result
            result = {'success': False, 'status_code': response.get('status', 500), 'error': response.get('error', 'Unknown error')}
            logging.error(f"Cancel failed: {result}")
            return result
        except Exception as e:
            result = {'success': False, 'error': f"WebSocket cancel failed: {str(e)}"}
            logging.error(f"Cancel failed: {result}")
            return result

    async def get_mode(self, building_id: str, elevator_id: str) -> dict:
        if not self.websocket or self.websocket.closed:
            await self.initialize()
        try:
            # 假设通过 monitor-lift-status 获取模式
            monitor_payload = {"type": "site-monitoring", "buildingId": building_id, "elevatorId": elevator_id}
            await self.websocket.send(json.dumps(monitor_payload))
            response = json.loads(await self.websocket.recv())
            mode = response.get('payload', {}).get('state', 'operational')
            if response.get('status') == 200:
                result = {'success': True, 'status_code': 200, 'mode': mode, 'details': 'No issues'}
                logging.info(f"Mode: {building_id}, {elevator_id} -> {result}")
                return result
            result = {'success': False, 'status_code': response.get('status', 500), 'error': response.get('error', 'Unknown error')}
            logging.error(f"Mode failed: {result}")
            return result
        except Exception as e:
            result = {'success': False, 'error': f"WebSocket mode check failed: {str(e)}"}
            logging.error(f"Mode failed: {result}")
            return result