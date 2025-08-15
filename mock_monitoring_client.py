#!/usr/bin/env python3
"""
Mock 监控客户端 - 解决 Category B 测试依赖问题
为所有监控测试提供模拟响应

Author: GitHub Copilot
Date: 2025-08-15
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class MockAPIResponse:
    """模拟API响应"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: Optional[int] = None


@dataclass
class MockMonitoringEvent:
    """模拟监控事件"""
    timestamp: str
    event_type: str
    lift_id: str
    data: Dict[str, Any]
    topic: str
    
    def get(self, key: str, default=None):
        """提供 dict 风格的访问方法"""
        if key == "type":
            return self.event_type
        elif key == "topic" or key == "subtopic":
            return self.topic
        elif key == "_received_at":
            return self.timestamp
        elif key in self.data:
            return self.data[key]
        else:
            return default
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "type": self.event_type,
            "topic": self.topic,
            "subtopic": self.topic,  # 兼容性
            "timestamp": self.timestamp,
            "lift_id": self.lift_id,
            "data": self.data,
            "_received_at": self.timestamp
        }


class MockMonitoringAPIClient:
    """模拟监控API客户端"""
    
    def __init__(self, driver=None):
        """
        初始化模拟监控客户端
        
        Args:
            driver: KONE驱动（可选，Mock中不使用）
        """
        self.driver = driver
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.active_subscriptions = {}
        self.event_queue = []
        
    async def subscribe_monitoring(
        self, 
        building_id: str, 
        group_id: str, 
        subtopics: List[str], 
        duration_sec: int = 10,
        client_tag: str = "test"
    ) -> MockAPIResponse:
        """
        模拟监控订阅
        
        Args:
            building_id: 建筑ID
            group_id: 组ID 
            subtopics: 监控子主题列表
            duration_sec: 订阅持续时间
            client_tag: 客户端标签
            
        Returns:
            MockAPIResponse: 模拟响应
        """
        self.logger.info(f"🔄 Mock订阅监控: {building_id}, 主题: {subtopics}")
        
        try:
            # 模拟订阅成功
            subscription_id = f"sub_{client_tag}_{int(time.time())}"
            
            # 记录订阅
            self.active_subscriptions[subscription_id] = {
                "building_id": building_id,
                "group_id": group_id,
                "subtopics": subtopics,
                "duration_sec": duration_sec,
                "client_tag": client_tag,
                "started_at": datetime.now(timezone.utc).isoformat()
            }
            
            # 生成模拟监控事件
            await self._generate_mock_events(building_id, subtopics, duration_sec)
            
            response_data = {
                "subscription_id": subscription_id,
                "building_id": building_id,
                "group_id": group_id,
                "subtopics": subtopics,
                "duration_sec": duration_sec,
                "status": "active",
                "mock_mode": True
            }
            
            return MockAPIResponse(
                success=True,
                data=response_data,
                status_code=200
            )
            
        except Exception as e:
            self.logger.error(f"Mock订阅失败: {e}")
            return MockAPIResponse(
                success=False,
                error=str(e),
                status_code=500
            )
    
    async def wait_for_events(self, timeout_sec: int = 5) -> List[MockMonitoringEvent]:
        """
        等待并返回监控事件
        
        Args:
            timeout_sec: 超时时间
            
        Returns:
            List[MockMonitoringEvent]: 监控事件列表
        """
        self.logger.info(f"⏳ 等待监控事件 ({timeout_sec}s)")
        
        # 模拟等待时间
        await asyncio.sleep(min(timeout_sec, 2))
        
        # 返回模拟事件
        events = self.event_queue.copy()
        self.event_queue.clear()  # 清空队列
        
        self.logger.info(f"📥 获取到 {len(events)} 个监控事件")
        return events
    
    async def _generate_mock_events(self, building_id: str, subtopics: List[str], duration_sec: int):
        """生成模拟监控事件"""
        self.logger.debug(f"生成模拟事件: {subtopics}")
        
        current_time = datetime.now(timezone.utc)
        
        for topic in subtopics:
            # 为每个主题生成不同类型的事件
            if "status" in topic:
                event = MockMonitoringEvent(
                    timestamp=current_time.isoformat(),
                    event_type="status_update",
                    lift_id=self._extract_lift_id(topic),
                    data={
                        "floor": 3,
                        "direction": "up",
                        "door_status": "closed",
                        "operational_mode": "normal",
                        "load_percentage": 65
                    },
                    topic=topic
                )
                self.event_queue.append(event)
                
            elif "position" in topic:
                event = MockMonitoringEvent(
                    timestamp=current_time.isoformat(),
                    event_type="position_update",
                    lift_id=self._extract_lift_id(topic),
                    data={
                        "current_floor": 5,
                        "target_floor": 8,
                        "position_mm": 15000,
                        "velocity": 1.5
                    },
                    topic=topic
                )
                self.event_queue.append(event)
                
            elif "load" in topic:
                event = MockMonitoringEvent(
                    timestamp=current_time.isoformat(),
                    event_type="load_update",
                    lift_id=self._extract_lift_id(topic),
                    data={
                        "weight_kg": 520,
                        "capacity_kg": 800,
                        "load_percentage": 65,
                        "overload": False
                    },
                    topic=topic
                )
                self.event_queue.append(event)
                
            elif "direction" in topic:
                event = MockMonitoringEvent(
                    timestamp=current_time.isoformat(),
                    event_type="direction_update",
                    lift_id=self._extract_lift_id(topic),
                    data={
                        "direction": "up",
                        "next_stop": 7,
                        "call_buttons": [3, 5, 7]
                    },
                    topic=topic
                )
                self.event_queue.append(event)
                
            elif "group" in topic:
                event = MockMonitoringEvent(
                    timestamp=current_time.isoformat(),
                    event_type="group_status_update",
                    lift_id="group_1",
                    data={
                        "active_lifts": ["lift_1", "lift_2", "lift_3"],
                        "average_wait_time": 45,
                        "total_calls": 12,
                        "efficiency_percentage": 89
                    },
                    topic=topic
                )
                self.event_queue.append(event)
                
            else:
                # 通用事件
                event = MockMonitoringEvent(
                    timestamp=current_time.isoformat(),
                    event_type="general_update",
                    lift_id=self._extract_lift_id(topic),
                    data={
                        "status": "active",
                        "topic": topic,
                        "mock_data": True
                    },
                    topic=topic
                )
                self.event_queue.append(event)
    
    def _extract_lift_id(self, topic: str) -> str:
        """从主题中提取电梯ID"""
        if "lift_" in topic:
            # 提取 lift_1, lift_2 等
            parts = topic.split("/")
            for part in parts:
                if part.startswith("lift_"):
                    return part
        return "lift_1"  # 默认


def create_mock_monitoring_client(driver=None) -> MockMonitoringAPIClient:
    """
    创建模拟监控客户端的工厂函数
    
    Args:
        driver: KONE驱动（可选）
        
    Returns:
        MockMonitoringAPIClient: 模拟监控客户端实例
    """
    logger.info("🔧 创建Mock监控客户端")
    return MockMonitoringAPIClient(driver)
