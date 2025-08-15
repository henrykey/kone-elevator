#!/usr/bin/env python3
"""
KONE API v2.0 统一客户端
Author: IBC-AI CO.

实现统一的 WebSocket API 客户端，严格遵循 elevator-websocket-api-v2.yaml 规范
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

import websockets
from websockets.exceptions import ConnectionClosed


logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """API 响应封装"""
    success: bool
    status_code: Optional[int]
    data: Dict[str, Any]
    error: Optional[str]
    duration_ms: float
    request_id: Optional[str]


class CommonAPIClient:
    """通用 API 客户端 (common-api 类型)"""
    
    def __init__(self, websocket: websockets.WebSocketServerProtocol):
        self.websocket = websocket
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def get_building_config(self, building_id: str, group_id: str = "1") -> APIResponse:
        """
        获取建筑配置
        
        Args:
            building_id: 建筑ID，格式: building:{id}
            group_id: 组ID，默认为"1"
            
        Returns:
            APIResponse: 包含配置数据的响应
        """
        start_time = datetime.now()
        request_id = str(uuid.uuid4())
        
        payload = {
            "type": "common-api",
            "buildingId": building_id,
            "callType": "config",
            "groupId": group_id,
            "requestId": request_id,
            "payload": {}
        }
        
        try:
            self.logger.debug(f"Sending building config request: {json.dumps(payload, indent=2)}")
            await self.websocket.send(json.dumps(payload))
            
            # 等待响应
            response_raw = await asyncio.wait_for(self.websocket.recv(), timeout=30.0)
            response_data = json.loads(response_raw)
            
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            self.logger.debug(f"Received building config response: {json.dumps(response_data, indent=2)[:500]}...")
            
            # 解析响应
            if "statusCode" in response_data and response_data["statusCode"] in [200, 201]:
                return APIResponse(
                    success=True,
                    status_code=response_data.get("statusCode"),
                    data=response_data,
                    error=None,
                    duration_ms=duration_ms,
                    request_id=request_id
                )
            else:
                return APIResponse(
                    success=False,
                    status_code=response_data.get("statusCode"),
                    data=response_data,
                    error=response_data.get("message", "Unknown error"),
                    duration_ms=duration_ms,
                    request_id=request_id
                )
                
        except asyncio.TimeoutError:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            return APIResponse(
                success=False,
                status_code=None,
                data={},
                error="Request timeout (30s)",
                duration_ms=duration_ms,
                request_id=request_id
            )
        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.error(f"Building config request failed: {e}")
            return APIResponse(
                success=False,
                status_code=None,
                data={},
                error=str(e),
                duration_ms=duration_ms,
                request_id=request_id
            )
    
    async def get_actions_config(self, building_id: str, group_id: str = "1") -> APIResponse:
        """
        获取动作配置
        
        Args:
            building_id: 建筑ID，格式: building:{id}
            group_id: 组ID，默认为"1"
            
        Returns:
            APIResponse: 包含动作配置的响应
        """
        start_time = datetime.now()
        request_id = str(uuid.uuid4())
        
        payload = {
            "type": "common-api",
            "buildingId": building_id,
            "callType": "actions",
            "groupId": group_id,
            "requestId": request_id,
            "payload": {}
        }
        
        try:
            self.logger.debug(f"Sending actions config request: {json.dumps(payload, indent=2)}")
            await self.websocket.send(json.dumps(payload))
            
            # 等待响应
            response_raw = await asyncio.wait_for(self.websocket.recv(), timeout=30.0)
            response_data = json.loads(response_raw)
            
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            self.logger.debug(f"Received actions config response: {json.dumps(response_data, indent=2)[:500]}...")
            
            # 解析响应
            # 对于 actions 响应，可能没有 statusCode 字段
            if "statusCode" in response_data:
                if response_data["statusCode"] in [200, 201]:
                    return APIResponse(
                        success=True,
                        status_code=response_data.get("statusCode"),
                        data=response_data,
                        error=None,
                        duration_ms=duration_ms,
                        request_id=request_id
                    )
                else:
                    return APIResponse(
                        success=False,
                        status_code=response_data.get("statusCode"),
                        data=response_data,
                        error=response_data.get("message", "Unknown error"),
                        duration_ms=duration_ms,
                        request_id=request_id
                    )
            else:
                # 没有 statusCode 字段，检查是否有有效的数据结构
                if "data" in response_data and isinstance(response_data["data"], dict):
                    return APIResponse(
                        success=True,
                        status_code=200,  # 假设的成功状态码
                        data=response_data,
                        error=None,
                        duration_ms=duration_ms,
                        request_id=request_id
                    )
                else:
                    return APIResponse(
                        success=False,
                        status_code=None,
                        data=response_data,
                        error="Invalid response format",
                        duration_ms=duration_ms,
                        request_id=request_id
                    )
                
        except asyncio.TimeoutError:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            return APIResponse(
                success=False,
                status_code=None,
                data={},
                error="Request timeout (30s)",
                duration_ms=duration_ms,
                request_id=request_id
            )
        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.error(f"Actions config request failed: {e}")
            return APIResponse(
                success=False,
                status_code=None,
                data={},
                error=str(e),
                duration_ms=duration_ms,
                request_id=request_id
            )
    
    async def call_common_api(
        self, 
        call_type: str, 
        building_id: str, 
        group_id: str = "1", 
        payload: Optional[Dict[str, Any]] = None
    ) -> APIResponse:
        """
        通用 common-api 调用
        
        Args:
            call_type: 调用类型 (config, actions, ping)
            building_id: 建筑ID
            group_id: 组ID
            payload: 载荷数据
            
        Returns:
            APIResponse: API响应
        """
        if call_type == "config":
            return await self.get_building_config(building_id, group_id)
        elif call_type == "actions":
            return await self.get_actions_config(building_id, group_id)
        elif call_type == "ping":
            return await self._ping(building_id, group_id, payload or {})
        else:
            raise ValueError(f"Unsupported call_type: {call_type}")
    
    async def send_request_and_wait_response(
        self, 
        payload: Dict[str, Any], 
        timeout: float = 30.0
    ) -> Optional[Dict[str, Any]]:
        """
        发送任意请求并等待响应
        
        Args:
            payload: 请求载荷
            timeout: 超时时间(秒)
            
        Returns:
            Optional[Dict[str, Any]]: 响应数据，如果超时或出错返回 None
        """
        try:
            self.logger.debug(f"Sending request: {json.dumps(payload, indent=2)}")
            await self.websocket.send(json.dumps(payload))
            
            # 等待响应
            response_raw = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
            response_data = json.loads(response_raw)
            
            self.logger.debug(f"Received response: {json.dumps(response_data, indent=2)}")
            return response_data
            
        except asyncio.TimeoutError:
            self.logger.error(f"Request timeout after {timeout}s")
            return None
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            return None
    
    async def _ping(self, building_id: str, group_id: str, payload: Dict[str, Any]) -> APIResponse:
        """
        Ping API 调用
        """
        start_time = datetime.now()
        request_id = str(uuid.uuid4())
        
        ping_payload = {
            "type": "common-api",
            "buildingId": building_id,
            "callType": "ping",
            "groupId": group_id,
            "requestId": request_id,
            "payload": {
                "request_id": payload.get("request_id", int(datetime.now().timestamp() * 1000))
            }
        }
        
        try:
            await self.websocket.send(json.dumps(ping_payload))
            response_raw = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
            response_data = json.loads(response_raw)
            
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            return APIResponse(
                success="statusCode" in response_data and response_data["statusCode"] in [200, 201],
                status_code=response_data.get("statusCode"),
                data=response_data,
                error=response_data.get("message") if response_data.get("statusCode")  not in [200, 201] else None,
                duration_ms=duration_ms,
                request_id=request_id
            )
        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            return APIResponse(
                success=False,
                status_code=None,
                data={},
                error=str(e),
                duration_ms=duration_ms,
                request_id=request_id
            )


class LiftCallAPIClient:
    """电梯呼叫 API 客户端 (lift-call-api-v2 类型)"""
    
    def __init__(self, websocket: websockets.WebSocketServerProtocol, building_config: Dict[str, Any]):
        self.websocket = websocket
        self.building_config = building_config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._area_mapping = self._build_area_mapping()
    
    def _build_area_mapping(self) -> Dict[int, int]:
        """
        构建楼层号到区域ID的映射
        
        Returns:
            Dict[int, int]: floor_number -> area_id 映射
        """
        mapping = {}
        try:
            # TODO: 根据实际的 building config 结构解析
            # 这里需要根据实际的配置格式调整
            if "payload" in self.building_config and "areas" in self.building_config["payload"]:
                for area in self.building_config["payload"]["areas"]:
                    if "floor" in area and "id" in area:
                        mapping[area["floor"]] = area["id"]
            
            self.logger.debug(f"Built area mapping: {mapping}")
            return mapping
        except Exception as e:
            self.logger.warning(f"Failed to build area mapping: {e}")
            return {}
    
    def get_area_id(self, floor_number: int) -> int:
        """
        获取楼层对应的区域ID
        
        Args:
            floor_number: 楼层号
            
        Returns:
            int: 区域ID
            
        Raises:
            ValueError: 当楼层号无对应区域时
        """
        if floor_number in self._area_mapping:
            return self._area_mapping[floor_number]
        else:
            # TODO: 根据规范确定默认映射策略
            # 这里暂时使用简单的偏移映射
            area_id = 1000 + floor_number * 1000  # 假设的映射逻辑
            self.logger.warning(f"No mapping for floor {floor_number}, using calculated area_id: {area_id}")
            return area_id
    
    async def make_destination_call(
        self,
        from_floor: int,
        to_floor: int,
        *,
        action_id: int = 2,
        delay: int = 0,
        terminal: int = 1,
        building_id: str,
        group_id: str = "1"
    ) -> APIResponse:
        """
        发起目的地呼叫
        
        Args:
            from_floor: 起始楼层
            to_floor: 目标楼层
            action_id: 动作ID (默认 2)
            delay: 延迟秒数
            terminal: 终端ID
            building_id: 建筑ID
            group_id: 组ID
            
        Returns:
            APIResponse: 呼叫响应
        """
        start_time = datetime.now()
        request_id = str(uuid.uuid4())
        
        source_area_id = self.get_area_id(from_floor)
        destination_area_id = self.get_area_id(to_floor)
        
        payload = {
            "type": "lift-call-api-v2",
            "buildingId": building_id,
            "callType": "action",
            "groupId": group_id,
            "payload": {
                "request_id": request_id,
                "area": source_area_id,
                "time": datetime.now(timezone.utc).isoformat(),
                "terminal": terminal,
                "call": {
                    "action": action_id,
                    "destination": destination_area_id,
                    "delay": delay
                }
            }
        }
        
        try:
            self.logger.debug(f"Sending destination call: {json.dumps(payload, indent=2)}")
            await self.websocket.send(json.dumps(payload))
            
            response_raw = await asyncio.wait_for(self.websocket.recv(), timeout=30.0)
            response_data = json.loads(response_raw)
            
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            return APIResponse(
                success="statusCode" in response_data and response_data["statusCode"] in [200, 201],
                status_code=response_data.get("statusCode"),
                data=response_data,
                error=response_data.get("message") if response_data.get("statusCode") not in [200, 201] else None,
                duration_ms=duration_ms,
                request_id=request_id
            )
        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            return APIResponse(
                success=False,
                status_code=None,
                data={},
                error=str(e),
                duration_ms=duration_ms,
                request_id=request_id
            )


class MonitoringAPIClient:
    """监控 API 客户端 (site-monitoring 类型)"""
    
    def __init__(self, driver):
        """
        初始化监控客户端
        
        Args:
            driver: KoneDriver 实例，用于共享 WebSocket 连接和消息处理
        """
        self.driver = driver
        self.websocket = driver.websocket
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.events: List[Dict[str, Any]] = []
    
    async def subscribe_monitoring(
        self,
        building_id: str,
        group_id: str,
        subtopics: List[str],
        *,
        duration_sec: int = 300,
        client_tag: Optional[str] = None
    ) -> APIResponse:
        """
        订阅监控事件，使用 KoneDriver 的消息系统
        
        Args:
            building_id: 建筑ID
            group_id: 组ID
            subtopics: 监控主题列表
            duration_sec: 订阅持续时间(秒)
            client_tag: 客户端标识
            
        Returns:
            APIResponse: 订阅响应
        """
        start_time = datetime.now()
        request_id = str(uuid.uuid4())
        
        payload = {
            "type": "site-monitoring",
            "buildingId": building_id,
            "callType": "monitor",
            "groupId": group_id,
            "requestId": request_id,  # 添加 requestId 字段
            "payload": {
                "sub": client_tag or request_id,
                "duration": duration_sec,
                "subtopics": subtopics
            }
        }
        
        try:
            self.logger.debug(f"Sending monitoring subscription: {json.dumps(payload, indent=2)}")
            
            # 使用 KoneDriver 的消息发送系统
            response = await self.driver._send_message(payload, wait_response=True, timeout=30)
            
            self.logger.info(f"Monitoring subscription response: {json.dumps(response, indent=2)}")
            
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            return APIResponse(
                success="statusCode" in response and response["statusCode"] in [200, 201],
                status_code=response.get("statusCode"),
                data=response,
                error=response.get("message") if response.get("statusCode")  not in [200, 201] else None,
                duration_ms=duration_ms,
                request_id=request_id
            )
        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            return APIResponse(
                success=False,
                status_code=None,
                data={},
                error=str(e),
                duration_ms=duration_ms,
                request_id=request_id
            )
    
    async def wait_for_events(self, timeout_sec: int = 30) -> List[Dict[str, Any]]:
        """
        等待并收集监控事件
        
        Args:
            timeout_sec: 超时时间(秒)
            
        Returns:
            List[Dict]: 收集到的事件列表
        """
        events = []
        end_time = datetime.now().timestamp() + timeout_sec
        
        while datetime.now().timestamp() < end_time:
            try:
                remaining_time = end_time - datetime.now().timestamp()
                if remaining_time <= 0:
                    break
                
                response_raw = await asyncio.wait_for(self.websocket.recv(), timeout=remaining_time)
                event_data = json.loads(response_raw)
                
                # 记录事件
                event_data["_received_at"] = datetime.now(timezone.utc).isoformat()
                events.append(event_data)
                self.events.append(event_data)
                
                self.logger.debug(f"Received monitoring event: {json.dumps(event_data, indent=2)[:200]}...")
                
            except asyncio.TimeoutError:
                break
            except ConnectionClosed:
                self.logger.warning("WebSocket connection closed while waiting for events")
                break
            except Exception as e:
                self.logger.error(f"Error receiving monitoring event: {e}")
                break
        
        return events
    
    def summarize_events(self) -> Dict[str, Any]:
        """
        汇总收集到的事件
        
        Returns:
            Dict: 事件汇总信息
        """
        total_events = len(self.events)
        event_types = {}
        
        for event in self.events:
            event_type = event.get("type", "unknown")
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        return {
            "total_events": total_events,
            "event_types": event_types,
            "first_event_at": self.events[0].get("_received_at") if self.events else None,
            "last_event_at": self.events[-1].get("_received_at") if self.events else None
        }


class ResponseParser:
    """响应解析器"""
    
    @staticmethod
    def parse_session_id(resp: Dict[str, Any]) -> Optional[str]:
        """解析会话ID"""
        return resp.get("payload", {}).get("sessionId")
    
    @staticmethod
    def parse_allocation_mode(resp: Dict[str, Any]) -> Optional[str]:
        """解析分配模式"""
        return resp.get("payload", {}).get("allocationMode")
    
    @staticmethod
    def parse_error(resp: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析错误信息"""
        if resp.get("statusCode") not in [200, 201]:
            return {
                "code": resp.get("statusCode"),
                "message": resp.get("message", "Unknown error"),
                "details": resp.get("payload", {})
            }
        return None
