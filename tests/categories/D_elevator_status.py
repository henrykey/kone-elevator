#!/usr/bin/env python3
"""
Category D: 电梯状态查询与实时更新测试
Test 9, 10, 11, 12: 电梯状态监控 API 核心功能

根据 elevator-websocket-api-v2.yaml 规范实现：
- Test 9: 电梯状态监控 (monitor-lift-status)
- Test 10: 电梯位置监控 (monitor-lift-position)
- Test 11: 电梯舱体位置监控 (monitor-deck-position)
- Test 12: 电梯到达时间预测 (monitor-next-stop-eta)
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from kone_api_client import MonitoringAPIClient
from reporting.formatter import EnhancedTestResult


class ElevatorStatusTests:
    """Category D: 电梯状态查询与实时更新测试类"""
    
    def __init__(self, websocket, building_id: str, group_id: str = "1"):
        self.websocket = websocket
        self.building_id = building_id
        self.group_id = group_id
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.test_results: List[EnhancedTestResult] = []
    
    def _create_monitoring_client(self) -> MonitoringAPIClient:
        """创建兼容的监控API客户端"""
        class SimpleDriver:
            def __init__(self, websocket):
                self.websocket = websocket
            
            async def _send_message(self, payload: Dict[str, Any], wait_response: bool = True, timeout: int = 30) -> Dict[str, Any]:
                """发送消息到WebSocket并等待响应"""
                import json
                import asyncio
                
                # 发送消息
                await self.websocket.send(json.dumps(payload))
                
                if wait_response:
                    try:
                        # 等待响应 - 订阅响应应该包含statusCode
                        response_raw = await asyncio.wait_for(
                            self.websocket.recv(), 
                            timeout=timeout
                        )
                        response = json.loads(response_raw)
                        
                        # 如果响应包含statusCode，说明是订阅响应
                        if "statusCode" in response:
                            return response
                        
                        # 否则可能是事件数据，继续等待真正的订阅响应
                        while True:
                            response_raw = await asyncio.wait_for(
                                self.websocket.recv(), 
                                timeout=timeout
                            )
                            response = json.loads(response_raw)
                            if "statusCode" in response:
                                return response
                        
                    except asyncio.TimeoutError:
                        return {"statusCode": 408, "error": "Timeout"}
                
                return {"statusCode": 200}
        
        driver = SimpleDriver(self.websocket)
        return MonitoringAPIClient(driver)
    
    async def run_all_tests(self) -> List[EnhancedTestResult]:
        """执行所有 Category D 测试"""
        self.logger.info("=== 开始执行 Category D: 电梯状态查询与实时更新测试 ===")
        
        tests = [
            ("Test 9", "电梯状态监控 (monitor-lift-status)", self.test_lift_status_monitoring),
            ("Test 10", "电梯位置监控 (monitor-lift-position)", self.test_lift_position_monitoring),
            ("Test 11", "电梯舱体位置监控 (monitor-deck-position)", self.test_deck_position_monitoring),
            ("Test 12", "电梯到达时间预测 (monitor-next-stop-eta)", self.test_next_stop_eta_monitoring),
        ]
        
        for test_id, description, test_func in tests:
            try:
                self.logger.info(f"开始执行 {test_id}: {description}")
                result = await test_func()
                result.test_id = test_id
                result.test_name = description
                self.test_results.append(result)
                self.logger.info(f"{test_id} 完成，状态: {result.status}")
            except Exception as e:
                self.logger.error(f"{test_id} 执行失败: {e}")
                error_result = EnhancedTestResult(
                    test_id=test_id,
                    test_name=description,
                    category="D_elevator_status",
                    status="ERROR",
                    duration_ms=0.0,
                    api_type="site-monitoring",
                    call_type="monitor",
                    building_id=self.building_id,
                    group_id=self.group_id,
                    error_message=str(e)
                )
                self.test_results.append(error_result)
        
        return self.test_results
    
    async def test_lift_status_monitoring(self) -> EnhancedTestResult:
        """Test 9: 电梯状态监控 (monitor-lift-status)
        
        验证：
        1. 订阅电梯状态更新
        2. 验证状态事件格式
        3. 验证状态字段完整性
        """
        start_time = time.time()
        
        try:
            # 创建监控客户端
            monitoring_client = self._create_monitoring_client()
            
            # 订阅电梯状态监控
            self.logger.info("订阅电梯状态监控...")
            subtopics = [
                "lift_1/status",
                "lift_2/status",
                "lift_3/status"
            ]
            
            response = await monitoring_client.subscribe_monitoring(
                building_id=self.building_id,
                group_id=self.group_id,
                subtopics=subtopics,
                duration_sec=8,  # 监控 8 秒
                client_tag="test_lift_status"
            )
            
            validations = []
            
            if not response.success:
                validations.append(f"❌ 监控订阅失败: {response.error}")
                status = "FAIL"
            else:
                validations.append("✅ 监控订阅成功")
                
                # 等待并收集状态事件
                self.logger.info("收集电梯状态事件...")
                await asyncio.sleep(5)  # 等待事件
                
                # 验证收集到的事件
                events = monitoring_client.events
                self.logger.info(f"收集到 {len(events)} 个状态事件")
                
                if len(events) == 0:
                    validations.append("⚠️ 未收集到状态事件（可能系统无活动）")
                else:
                    validations.append(f"✅ 收集到 {len(events)} 个状态事件")
                    
                    # 验证状态事件格式
                    status_events = [e for e in events if "status" in e.get("type", "")]
                    if status_events:
                        status_event = status_events[0]
                        self._validate_status_event(status_event, validations)
                    else:
                        validations.append("⚠️ 未收到 lift-status 类型事件")
                
                # 验证订阅响应格式
                if response.status_code == 201:
                    validations.append("✅ 监控响应状态码正确")
                else:
                    validations.append(f"❌ 监控响应状态码: {response.status_code}")
            
            failed_validations = [v for v in validations if v.startswith("❌")]
            status = "FAIL" if failed_validations else "PASS"
            
            return EnhancedTestResult(
                test_id="Test 9",
                test_name="电梯状态监控 (monitor-lift-status)",
                category="D_elevator_status",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                api_type="site-monitoring",
                call_type="monitor",
                building_id=self.building_id,
                group_id=self.group_id,
                monitoring_events=monitoring_client.events if hasattr(monitoring_client, 'events') else [],
                subscription_topics=subtopics,
                response_data=response.data,
                status_code=response.status_code,
                error_message="; ".join(failed_validations) if failed_validations else None
            )
            
        except Exception as e:
            self.logger.error(f"电梯状态监控测试失败: {e}")
            return EnhancedTestResult(
                test_id="Test 9",
                test_name="电梯状态监控 (monitor-lift-status)",
                category="D_elevator_status",
                status="ERROR",
                duration_ms=(time.time() - start_time) * 1000,
                api_type="site-monitoring",
                call_type="monitor",
                building_id=self.building_id,
                group_id=self.group_id,
                error_message=str(e)
            )
    
    def _validate_status_event(self, event: Dict[str, Any], validations: List[str]):
        """验证状态事件格式"""
        # 验证时间字段
        if "time" in event:
            validations.append("✅ 状态事件包含时间字段")
        else:
            validations.append("❌ 状态事件缺少时间字段")
        
        # 验证 decks 字段
        if "decks" in event:
            validations.append("✅ 状态事件包含 decks 信息")
            decks = event["decks"]
            if isinstance(decks, list) and len(decks) > 0:
                deck = decks[0]
                if "area" in deck:
                    validations.append("✅ deck 包含 area 字段")
                else:
                    validations.append("❌ deck 缺少 area 字段")
        else:
            validations.append("❌ 状态事件缺少 decks 字段")
        
        # 验证其他状态字段
        status_fields = ["lift_mode", "fault_active", "nominal_speed"]
        for field in status_fields:
            if field in event:
                validations.append(f"✅ 包含 {field} 字段")
            else:
                validations.append(f"⚠️ 缺少 {field} 字段（可选）")
    
    async def test_lift_position_monitoring(self) -> EnhancedTestResult:
        """Test 10: 电梯位置监控 (monitor-lift-position)
        
        验证：
        1. 订阅电梯位置更新
        2. 验证位置事件格式
        3. 验证位置字段完整性
        """
        start_time = time.time()
        
        try:
            # 创建监控客户端
            monitoring_client = self._create_monitoring_client()
            
            # 订阅电梯位置监控
            self.logger.info("订阅电梯位置监控...")
            subtopics = [
                "lift_1/position",
                "lift_2/position"
            ]
            
            response = await monitoring_client.subscribe_monitoring(
                building_id=self.building_id,
                group_id=self.group_id,
                subtopics=subtopics,
                duration_sec=8,
                client_tag="test_lift_position"
            )
            
            validations = []
            
            if not response.success:
                validations.append(f"❌ 位置监控订阅失败: {response.error}")
                status = "FAIL"
            else:
                validations.append("✅ 位置监控订阅成功")
                
                # 等待并收集位置事件
                await asyncio.sleep(5)
                events = monitoring_client.events
                
                if len(events) == 0:
                    validations.append("⚠️ 未收集到位置事件")
                else:
                    validations.append(f"✅ 收集到 {len(events)} 个位置事件")
                    
                    # 验证位置事件格式
                    position_events = [e for e in events if "position" in e.get("type", "")]
                    if position_events:
                        position_event = position_events[0]
                        self._validate_position_event(position_event, validations)
                    else:
                        validations.append("⚠️ 未收到 position 类型事件")
            
            failed_validations = [v for v in validations if v.startswith("❌")]
            status = "FAIL" if failed_validations else "PASS"
            
            return EnhancedTestResult(
                test_id="Test 10",
                test_name="电梯位置监控 (monitor-lift-position)",
                category="D_elevator_status",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                api_type="site-monitoring",
                call_type="monitor",
                building_id=self.building_id,
                group_id=self.group_id,
                monitoring_events=monitoring_client.events if hasattr(monitoring_client, 'events') else [],
                subscription_topics=subtopics,
                response_data=response.data,
                status_code=response.status_code,
                error_message="; ".join(failed_validations) if failed_validations else None
            )
            
        except Exception as e:
            self.logger.error(f"电梯位置监控测试失败: {e}")
            return EnhancedTestResult(
                test_id="Test 10",
                test_name="电梯位置监控 (monitor-lift-position)",
                category="D_elevator_status",
                status="ERROR",
                duration_ms=(time.time() - start_time) * 1000,
                api_type="site-monitoring",
                call_type="monitor",
                building_id=self.building_id,
                group_id=self.group_id,
                error_message=str(e)
            )
    
    def _validate_position_event(self, event: Dict[str, Any], validations: List[str]):
        """验证位置事件格式"""
        required_fields = ["time", "dir", "coll", "moving_state", "area", "cur", "adv", "door"]
        
        for field in required_fields:
            if field in event:
                validations.append(f"✅ 包含必需字段 {field}")
            else:
                validations.append(f"❌ 缺少必需字段 {field}")
        
        # 验证方向枚举值
        if "dir" in event and event["dir"] in ["UP", "DOWN"]:
            validations.append("✅ 方向字段值有效")
        elif "dir" in event:
            validations.append(f"⚠️ 方向字段值: {event['dir']} (非标准)")
    
    async def test_deck_position_monitoring(self) -> EnhancedTestResult:
        """Test 11: 电梯舱体位置监控 (monitor-deck-position)
        
        验证：
        1. 订阅舱体位置更新
        2. 验证舱体事件格式
        3. 验证舱体字段完整性
        """
        start_time = time.time()
        
        try:
            # 创建兼容的监控客户端
            monitoring_client = self._create_monitoring_client()
            
            # 订阅舱体位置监控
            self.logger.info("订阅电梯舱体位置监控...")
            subtopics = [
                "lift_1/deck_position",
                "lift_2/deck_position"
            ]
            
            response = await monitoring_client.subscribe_monitoring(
                building_id=self.building_id,
                group_id=self.group_id,
                subtopics=subtopics,
                duration_sec=8,
                client_tag="test_deck_position"
            )
            
            validations = []
            
            if not response.success:
                validations.append(f"❌ 舱体位置监控订阅失败: {response.error}")
                status = "FAIL"
            else:
                validations.append("✅ 舱体位置监控订阅成功")
                
                await asyncio.sleep(5)
                events = monitoring_client.events
                
                if len(events) == 0:
                    validations.append("⚠️ 未收集到舱体位置事件")
                else:
                    validations.append(f"✅ 收集到 {len(events)} 个舱体位置事件")
                    
                    # 验证舱体位置事件格式
                    deck_events = [e for e in events if "deck" in e.get("type", "")]
                    if deck_events:
                        deck_event = deck_events[0]
                        self._validate_deck_position_event(deck_event, validations)
                    else:
                        validations.append("⚠️ 未收到 deck_position 类型事件")
            
            failed_validations = [v for v in validations if v.startswith("❌")]
            status = "FAIL" if failed_validations else "PASS"
            
            return EnhancedTestResult(
                test_id="Test 11",
                test_name="电梯舱体位置监控 (monitor-deck-position)",
                category="D_elevator_status",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                api_type="site-monitoring",
                call_type="monitor",
                building_id=self.building_id,
                group_id=self.group_id,
                monitoring_events=monitoring_client.events if hasattr(monitoring_client, 'events') else [],
                subscription_topics=subtopics,
                response_data=response.data,
                status_code=response.status_code,
                error_message="; ".join(failed_validations) if failed_validations else None
            )
            
        except Exception as e:
            self.logger.error(f"舱体位置监控测试失败: {e}")
            return EnhancedTestResult(
                test_id="Test 11",
                test_name="电梯舱体位置监控 (monitor-deck-position)",
                category="D_elevator_status",
                status="ERROR",
                duration_ms=(time.time() - start_time) * 1000,
                api_type="site-monitoring",
                call_type="monitor",
                building_id=self.building_id,
                group_id=self.group_id,
                error_message=str(e)
            )
    
    def _validate_deck_position_event(self, event: Dict[str, Any], validations: List[str]):
        """验证舱体位置事件格式"""
        required_fields = ["time", "dir", "coll", "moving_state"]
        
        for field in required_fields:
            if field in event:
                validations.append(f"✅ 包含必需字段 {field}")
            else:
                validations.append(f"❌ 缺少必需字段 {field}")
        
        # 验证移动状态
        if "moving_state" in event:
            valid_states = ["STANDING", "MOVING", "LOADING"]
            if event["moving_state"] in valid_states:
                validations.append("✅ 移动状态值有效")
            else:
                validations.append(f"⚠️ 移动状态: {event['moving_state']} (非标准)")
    
    async def test_next_stop_eta_monitoring(self) -> EnhancedTestResult:
        """Test 12: 电梯到达时间预测 (monitor-next-stop-eta)
        
        验证：
        1. 订阅到达时间预测
        2. 验证 ETA 事件格式
        3. 验证时间预测字段
        """
        start_time = time.time()
        
        try:
            # 创建兼容的监控客户端
            monitoring_client = self._create_monitoring_client()
            
            # 订阅到达时间预测
            self.logger.info("订阅电梯到达时间预测...")
            subtopics = [
                "lift_1/next_stop_eta",
                "lift_2/next_stop_eta"
            ]
            
            response = await monitoring_client.subscribe_monitoring(
                building_id=self.building_id,
                group_id=self.group_id,
                subtopics=subtopics,
                duration_sec=8,
                client_tag="test_next_stop_eta"
            )
            
            validations = []
            
            if not response.success:
                validations.append(f"❌ ETA 监控订阅失败: {response.error}")
                status = "FAIL"
            else:
                validations.append("✅ ETA 监控订阅成功")
                
                await asyncio.sleep(5)
                events = monitoring_client.events
                
                if len(events) == 0:
                    validations.append("⚠️ 未收集到 ETA 事件")
                else:
                    validations.append(f"✅ 收集到 {len(events)} 个 ETA 事件")
                    
                    # 验证 ETA 事件格式
                    eta_events = [e for e in events if "eta" in e.get("type", "")]
                    if eta_events:
                        eta_event = eta_events[0]
                        self._validate_eta_event(eta_event, validations)
                    else:
                        validations.append("⚠️ 未收到 next_stop_eta 类型事件")
            
            failed_validations = [v for v in validations if v.startswith("❌")]
            status = "FAIL" if failed_validations else "PASS"
            
            return EnhancedTestResult(
                test_id="Test 12",
                test_name="电梯到达时间预测 (monitor-next-stop-eta)",
                category="D_elevator_status",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                api_type="site-monitoring",
                call_type="monitor",
                building_id=self.building_id,
                group_id=self.group_id,
                monitoring_events=monitoring_client.events if hasattr(monitoring_client, 'events') else [],
                subscription_topics=subtopics,
                response_data=response.data,
                status_code=response.status_code,
                error_message="; ".join(failed_validations) if failed_validations else None
            )
            
        except Exception as e:
            self.logger.error(f"ETA 监控测试失败: {e}")
            return EnhancedTestResult(
                test_id="Test 12",
                test_name="电梯到达时间预测 (monitor-next-stop-eta)",
                category="D_elevator_status",
                status="ERROR",
                duration_ms=(time.time() - start_time) * 1000,
                api_type="site-monitoring",
                call_type="monitor",
                building_id=self.building_id,
                group_id=self.group_id,
                error_message=str(e)
            )
    
    def _validate_eta_event(self, event: Dict[str, Any], validations: List[str]):
        """验证 ETA 事件格式"""
        required_fields = ["time", "eta", "last_start_time"]
        
        for field in required_fields:
            if field in event:
                validations.append(f"✅ 包含必需字段 {field}")
            else:
                validations.append(f"❌ 缺少必需字段 {field}")
        
        # 验证 decks 信息
        if "decks" in event:
            validations.append("✅ 包含 decks 信息")
            decks = event["decks"]
            if isinstance(decks, dict):
                deck_fields = ["area", "next_stop", "current_position"]
                for field in deck_fields:
                    if field in decks:
                        validations.append(f"✅ deck 包含 {field}")
                    else:
                        validations.append(f"❌ deck 缺少 {field}")
        else:
            validations.append("❌ ETA 事件缺少 decks 信息")
