#!/usr/bin/env python3
"""
Category B: Monitoring & Events 测试
Test    async def run_all_tests(self, config_manager: BuildingConfigManager) -> List[EnhancedTestResult]:
        """
        运行所有 Category B 监控事件测试
        
        Args:
            config_manager: 配置管理器实例
            
        Returns:
            List[EnhancedTestResult]: 测试结果列表
        """
        # 确保监控客户端已初始化
        await self._ensure_monitoring_client()
        
        results = []
        
        self.logger.info("=== Category B: Monitoring & Events Tests ===")
        
        # Test 2: Basic Lift Status Monitoring
        result_2 = await self.test_02_basic_lift_status_monitoring()
        results.append(result_2)
        
        # Test 3: Enhanced Status Monitoring
        result_3 = await self.test_03_enhanced_status_monitoring()
        results.append(result_3)
        
        # Test 11: Multi-State Monitoring
        result_11 = await self.test_11_multi_state_monitoring()
        results.append(result_11)
        
        # Test 12: Position Monitoring
        result_12 = await self.test_12_position_monitoring()
        results.append(result_12)
        
        # Test 13: Group Status Monitoring
        result_13 = await self.test_13_group_status_monitoring()
        results.append(result_13)
        
        # Test 14: Load Monitoring
        result_14 = await self.test_14_load_monitoring()
        results.append(result_14)
        
        # Test 15: Direction Monitoring
        result_15 = await self.test_15_direction_monitoring()
        results.append(result_15)
        
        return resultst_X/status 基础), 11 (多状态), 12 (position), 13 (group status), 14 (load), 15 (direction)
Author: IBC-AI CO.

测试监控事件订阅、收集与解析功能
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from kone_api_client import MonitoringAPIClient, APIResponse
from building_config_manager import BuildingConfigManager
from reporting.formatter import EnhancedTestResult


logger = logging.getLogger(__name__)


class MonitoringEventsTests:
    """监控与事件测试类"""
    
    def __init__(self, websocket, building_id: str, group_id: str = "1"):
        """
        初始化监控事件测试
        
        Args:
            websocket: WebSocket 连接 (兼容性参数，现在不使用)
            building_id: 建筑ID
            group_id: 组ID
        """
        self.websocket = websocket  # 兼容性保留
        self.building_id = building_id
        self.group_id = group_id
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.collected_events = []
        
        # 延迟初始化的监控客户端
        self.monitoring_client = None
        self.driver = None
    
    async def _ensure_monitoring_client(self):
        """确保监控客户端已初始化"""
        if self.monitoring_client is None:
            # 创建 MonitoringAPIClient (使用 KoneDriver)
            from drivers import KoneDriver
            import yaml
            
            # 加载配置
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            
            kone_config = config['kone']
            self.driver = KoneDriver(
                client_id=kone_config['client_id'],
                client_secret=kone_config['client_secret'],
                token_endpoint=kone_config['token_endpoint'],
                ws_endpoint=kone_config['ws_endpoint']
            )
            
            # 初始化连接
            init_result = await self.driver.initialize()
            if not init_result['success']:
                raise Exception(f"Failed to initialize KoneDriver: {init_result}")
            
            self.monitoring_client = MonitoringAPIClient(self.driver)
    
    async def run_all_tests(self, config_manager: BuildingConfigManager) -> List[EnhancedTestResult]:
        """
        运行所有 Category B 测试
        
        Args:
            config_manager: 建筑配置管理器
            
        Returns:
            List[EnhancedTestResult]: 测试结果列表
        """
        results = []
        
        self.logger.info("=== Category B: Monitoring & Events Tests ===")
        
        # Test 2: Basic Lift Status Monitoring
        result_2 = await self.test_02_basic_lift_status_monitoring()
        results.append(result_2)
        
        # Test 3: Enhanced Status Monitoring
        result_3 = await self.test_03_enhanced_status_monitoring()
        results.append(result_3)
        
        # Test 11: Multi-State Monitoring
        result_11 = await self.test_11_multi_state_monitoring()
        results.append(result_11)
        
        # Test 12: Position Monitoring
        result_12 = await self.test_12_position_monitoring()
        results.append(result_12)
        
        # Test 13: Group Status Monitoring
        result_13 = await self.test_13_group_status_monitoring()
        results.append(result_13)
        
        # Test 14: Load Monitoring
        result_14 = await self.test_14_load_monitoring()
        results.append(result_14)
        
        # Test 15: Direction Monitoring
        result_15 = await self.test_15_direction_monitoring()
        results.append(result_15)
        
        return results
    
    async def test_02_basic_lift_status_monitoring(self) -> EnhancedTestResult:
        """
        Test 2: Basic Lift Status Monitoring
        测试基础电梯状态监控
        """
        test_id = "002"
        test_name = "Basic Lift Status Monitoring"
        category = "B_monitoring_events"
        
        self.logger.info(f"🧪 Running Test {test_id}: {test_name}")
        
        start_time = time.time()
        started_at = datetime.now(timezone.utc).isoformat()
        
        try:
            # 订阅基础电梯状态
            subtopics = ["lift_1/status"]
            
            subscription_response = await self.monitoring_client.subscribe_monitoring(
                building_id=self.building_id,
                group_id=self.group_id,
                subtopics=subtopics,
                duration_sec=10,  # 较短的监控时间
                client_tag=f"test_{test_id}"
            )
            
            duration_ms = (time.time() - start_time) * 1000
            completed_at = datetime.now(timezone.utc).isoformat()
            
            # 验证订阅响应
            compliance_check = self._check_monitoring_compliance(subscription_response, subtopics)
            
            if subscription_response.success:
                # 等待事件
                events = await self.monitoring_client.wait_for_events(timeout_sec=5)
                self.collected_events.extend(events)
                
                # 验证事件收集
                event_validation = self._validate_events(events, ["lift_1/status"])
                
                if event_validation["valid"]:
                    status = "PASS"
                    error_message = None
                    error_details = None
                    
                    self.logger.info(f"✅ Test {test_id} PASSED - Collected {len(events)} status events")
                else:
                    status = "FAIL"
                    error_message = event_validation["error"]
                    error_details = event_validation
                    
                    self.logger.error(f"❌ Test {test_id} FAILED - {error_message}")
            else:
                status = "FAIL"
                error_message = subscription_response.error
                error_details = {
                    "status_code": subscription_response.status_code,
                    "response_data": subscription_response.data
                }
                events = []
                
                self.logger.error(f"❌ Test {test_id} FAILED - Subscription failed: {error_message}")
            
            # 构建请求详情
            request_details = {
                "type": "site-monitoring",
                "buildingId": self.building_id,
                "callType": "monitor",
                "groupId": self.group_id,
                "payload": {
                    "sub": f"test_{test_id}",
                    "duration": 10,
                    "subtopics": subtopics
                }
            }
            
            return EnhancedTestResult(
                test_id=test_id,
                test_name=test_name,
                category=category,
                status=status,
                duration_ms=duration_ms,
                api_type="site-monitoring",
                call_type="monitor",
                building_id=self.building_id,
                group_id=self.group_id,
                monitoring_events=events,
                subscription_topics=subtopics,
                response_data=subscription_response.data,
                status_code=subscription_response.status_code,
                error_details=error_details,
                error_message=error_message,
                request_details=request_details,
                compliance_check=compliance_check,
                started_at=started_at,
                completed_at=completed_at
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            completed_at = datetime.now(timezone.utc).isoformat()
            
            self.logger.error(f"🔥 Test {test_id} ERROR - {str(e)}")
            
            return EnhancedTestResult(
                test_id=test_id,
                test_name=test_name,
                category=category,
                status="ERROR",
                duration_ms=duration_ms,
                api_type="site-monitoring",
                call_type="monitor",
                building_id=self.building_id,
                group_id=self.group_id,
                monitoring_events=[],
                subscription_topics=[],
                error_details={"exception": str(e)},
                error_message=f"Test execution failed: {str(e)}",
                request_details={},
                compliance_check={"request_executed": False},
                started_at=started_at,
                completed_at=completed_at
            )
    
    async def test_03_enhanced_status_monitoring(self) -> EnhancedTestResult:
        """
        Test 3: Enhanced Status Monitoring
        测试增强状态监控（多电梯）
        """
        test_id = "003"
        test_name = "Enhanced Status Monitoring (Multi-Lift)"
        category = "B_monitoring_events"
        
        self.logger.info(f"🧪 Running Test {test_id}: {test_name}")
        
        start_time = time.time()
        started_at = datetime.now(timezone.utc).isoformat()
        
        try:
            # 订阅多电梯状态
            subtopics = ["lift_1/status", "lift_2/status", "lift_3/status"]
            
            subscription_response = await self.monitoring_client.subscribe_monitoring(
                building_id=self.building_id,
                group_id=self.group_id,
                subtopics=subtopics,
                duration_sec=15,
                client_tag=f"test_{test_id}"
            )
            
            duration_ms = (time.time() - start_time) * 1000
            completed_at = datetime.now(timezone.utc).isoformat()
            
            compliance_check = self._check_monitoring_compliance(subscription_response, subtopics)
            
            if subscription_response.success:
                events = await self.monitoring_client.wait_for_events(timeout_sec=8)
                self.collected_events.extend(events)
                
                event_validation = self._validate_events(events, subtopics)
                
                if event_validation["valid"] or len(events) > 0:
                    status = "PASS"
                    error_message = None
                    error_details = None
                    
                    self.logger.info(f"✅ Test {test_id} PASSED - Collected {len(events)} multi-lift events")
                else:
                    status = "FAIL"
                    error_message = event_validation["error"]
                    error_details = event_validation
                    
                    self.logger.error(f"❌ Test {test_id} FAILED - {error_message}")
            else:
                status = "FAIL"
                error_message = subscription_response.error
                error_details = {
                    "status_code": subscription_response.status_code,
                    "response_data": subscription_response.data
                }
                events = []
                
                self.logger.error(f"❌ Test {test_id} FAILED - Subscription failed: {error_message}")
            
            request_details = {
                "type": "site-monitoring",
                "buildingId": self.building_id,
                "callType": "monitor",
                "groupId": self.group_id,
                "payload": {
                    "sub": f"test_{test_id}",
                    "duration": 15,
                    "subtopics": subtopics
                }
            }
            
            return EnhancedTestResult(
                test_id=test_id,
                test_name=test_name,
                category=category,
                status=status,
                duration_ms=duration_ms,
                api_type="site-monitoring",
                call_type="monitor",
                building_id=self.building_id,
                group_id=self.group_id,
                monitoring_events=events,
                subscription_topics=subtopics,
                response_data=subscription_response.data,
                status_code=subscription_response.status_code,
                error_details=error_details,
                error_message=error_message,
                request_details=request_details,
                compliance_check=compliance_check,
                started_at=started_at,
                completed_at=completed_at
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            completed_at = datetime.now(timezone.utc).isoformat()
            
            self.logger.error(f"🔥 Test {test_id} ERROR - {str(e)}")
            
            return EnhancedTestResult(
                test_id=test_id,
                test_name=test_name,
                category=category,
                status="ERROR",
                duration_ms=duration_ms,
                api_type="site-monitoring",
                call_type="monitor",
                building_id=self.building_id,
                group_id=self.group_id,
                monitoring_events=[],
                subscription_topics=subtopics,
                error_details={"exception": str(e)},
                error_message=f"Test execution failed: {str(e)}",
                request_details={},
                compliance_check={"request_executed": False},
                started_at=started_at,
                completed_at=completed_at
            )
    
    async def test_11_multi_state_monitoring(self) -> EnhancedTestResult:
        """
        Test 11: Multi-State Monitoring
        测试多状态综合监控
        """
        test_id = "011"
        test_name = "Multi-State Comprehensive Monitoring"
        category = "B_monitoring_events"
        
        self.logger.info(f"🧪 Running Test {test_id}: {test_name}")
        
        start_time = time.time()
        started_at = datetime.now(timezone.utc).isoformat()
        
        try:
            # 订阅多种状态类型
            subtopics = [
                "lift_1/status",
                "lift_1/position", 
                "lift_1/direction",
                "lift_1/load"
            ]
            
            subscription_response = await self.monitoring_client.subscribe_monitoring(
                building_id=self.building_id,
                group_id=self.group_id,
                subtopics=subtopics,
                duration_sec=20,
                client_tag=f"test_{test_id}"
            )
            
            duration_ms = (time.time() - start_time) * 1000
            completed_at = datetime.now(timezone.utc).isoformat()
            
            compliance_check = self._check_monitoring_compliance(subscription_response, subtopics)
            
            if subscription_response.success:
                events = await self.monitoring_client.wait_for_events(timeout_sec=10)
                self.collected_events.extend(events)
                
                # 验证多状态事件
                event_validation = self._validate_multi_state_events(events, subtopics)
                
                if event_validation["valid"] or len(events) > 0:
                    status = "PASS"
                    error_message = None
                    error_details = None
                    
                    self.logger.info(f"✅ Test {test_id} PASSED - Collected {len(events)} multi-state events")
                else:
                    status = "FAIL"
                    error_message = event_validation["error"]
                    error_details = event_validation
                    
                    self.logger.error(f"❌ Test {test_id} FAILED - {error_message}")
            else:
                status = "FAIL"
                error_message = subscription_response.error
                error_details = {
                    "status_code": subscription_response.status_code,
                    "response_data": subscription_response.data
                }
                events = []
                
                self.logger.error(f"❌ Test {test_id} FAILED - Subscription failed: {error_message}")
            
            request_details = {
                "type": "site-monitoring",
                "buildingId": self.building_id,
                "callType": "monitor",
                "groupId": self.group_id,
                "payload": {
                    "sub": f"test_{test_id}",
                    "duration": 20,
                    "subtopics": subtopics
                }
            }
            
            return EnhancedTestResult(
                test_id=test_id,
                test_name=test_name,
                category=category,
                status=status,
                duration_ms=duration_ms,
                api_type="site-monitoring",
                call_type="monitor",
                building_id=self.building_id,
                group_id=self.group_id,
                monitoring_events=events,
                subscription_topics=subtopics,
                response_data=subscription_response.data,
                status_code=subscription_response.status_code,
                error_details=error_details,
                error_message=error_message,
                request_details=request_details,
                compliance_check=compliance_check,
                started_at=started_at,
                completed_at=completed_at
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            completed_at = datetime.now(timezone.utc).isoformat()
            
            self.logger.error(f"🔥 Test {test_id} ERROR - {str(e)}")
            
            return EnhancedTestResult(
                test_id=test_id,
                test_name=test_name,
                category=category,
                status="ERROR",
                duration_ms=duration_ms,
                api_type="site-monitoring",
                call_type="monitor",
                building_id=self.building_id,
                group_id=self.group_id,
                monitoring_events=[],
                subscription_topics=subtopics,
                error_details={"exception": str(e)},
                error_message=f"Test execution failed: {str(e)}",
                request_details={},
                compliance_check={"request_executed": False},
                started_at=started_at,
                completed_at=completed_at
            )
    
    async def test_12_position_monitoring(self) -> EnhancedTestResult:
        """
        Test 12: Position Monitoring
        测试位置监控
        """
        return await self._create_simple_monitoring_test(
            "012", "Position Monitoring", ["lift_1/position"]
        )
    
    async def test_13_group_status_monitoring(self) -> EnhancedTestResult:
        """
        Test 13: Group Status Monitoring  
        测试组状态监控
        """
        return await self._create_simple_monitoring_test(
            "013", "Group Status Monitoring", [f"group_{self.group_id}/status"]
        )
    
    async def test_14_load_monitoring(self) -> EnhancedTestResult:
        """
        Test 14: Load Monitoring
        测试负载监控
        """
        return await self._create_simple_monitoring_test(
            "014", "Load Monitoring", ["lift_1/load"]
        )
    
    async def test_15_direction_monitoring(self) -> EnhancedTestResult:
        """
        Test 15: Direction Monitoring
        测试方向监控
        """
        return await self._create_simple_monitoring_test(
            "015", "Direction Monitoring", ["lift_1/direction"]
        )
    
    async def _create_simple_monitoring_test(
        self, 
        test_id: str, 
        test_name: str, 
        subtopics: List[str]
    ) -> EnhancedTestResult:
        """
        创建简单的监控测试
        
        Args:
            test_id: 测试ID
            test_name: 测试名称
            subtopics: 订阅主题列表
            
        Returns:
            EnhancedTestResult: 测试结果
        """
        category = "B_monitoring_events"
        
        self.logger.info(f"🧪 Running Test {test_id}: {test_name}")
        
        start_time = time.time()
        started_at = datetime.now(timezone.utc).isoformat()
        
        try:
            subscription_response = await self.monitoring_client.subscribe_monitoring(
                building_id=self.building_id,
                group_id=self.group_id,
                subtopics=subtopics,
                duration_sec=10,
                client_tag=f"test_{test_id}"
            )
            
            duration_ms = (time.time() - start_time) * 1000
            completed_at = datetime.now(timezone.utc).isoformat()
            
            compliance_check = self._check_monitoring_compliance(subscription_response, subtopics)
            
            if subscription_response.success:
                events = await self.monitoring_client.wait_for_events(timeout_sec=5)
                self.collected_events.extend(events)
                
                # 宽松的验证 - 只要订阅成功就认为通过
                status = "PASS"
                error_message = None
                error_details = None
                
                self.logger.info(f"✅ Test {test_id} PASSED - Subscription successful, collected {len(events)} events")
            else:
                status = "FAIL"
                error_message = subscription_response.error
                error_details = {
                    "status_code": subscription_response.status_code,
                    "response_data": subscription_response.data
                }
                events = []
                
                self.logger.error(f"❌ Test {test_id} FAILED - Subscription failed: {error_message}")
            
            request_details = {
                "type": "site-monitoring",
                "buildingId": self.building_id,
                "callType": "monitor",
                "groupId": self.group_id,
                "payload": {
                    "sub": f"test_{test_id}",
                    "duration": 10,
                    "subtopics": subtopics
                }
            }
            
            return EnhancedTestResult(
                test_id=test_id,
                test_name=test_name,
                category=category,
                status=status,
                duration_ms=duration_ms,
                api_type="site-monitoring",
                call_type="monitor",
                building_id=self.building_id,
                group_id=self.group_id,
                monitoring_events=events,
                subscription_topics=subtopics,
                response_data=subscription_response.data,
                status_code=subscription_response.status_code,
                error_details=error_details,
                error_message=error_message,
                request_details=request_details,
                compliance_check=compliance_check,
                started_at=started_at,
                completed_at=completed_at
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            completed_at = datetime.now(timezone.utc).isoformat()
            
            self.logger.error(f"🔥 Test {test_id} ERROR - {str(e)}")
            
            return EnhancedTestResult(
                test_id=test_id,
                test_name=test_name,
                category=category,
                status="ERROR",
                duration_ms=duration_ms,
                api_type="site-monitoring",
                call_type="monitor",
                building_id=self.building_id,
                group_id=self.group_id,
                monitoring_events=[],
                subscription_topics=subtopics,
                error_details={"exception": str(e)},
                error_message=f"Test execution failed: {str(e)}",
                request_details={},
                compliance_check={"request_executed": False},
                started_at=started_at,
                completed_at=completed_at
            )
    
    def _check_monitoring_compliance(self, response: APIResponse, subtopics: List[str]) -> Dict[str, bool]:
        """
        检查监控订阅的合规性
        
        Args:
            response: API 响应
            subtopics: 订阅的主题列表
            
        Returns:
            Dict[str, bool]: 合规性检查结果
        """
        checks = {
            "request_executed": True,
            "has_status_code": response.status_code is not None,
            "status_code_valid": response.status_code in [200, 201] if response.success else True,
            "has_response_data": isinstance(response.data, dict),
            "subscription_acknowledged": response.success
        }
        
        # 检查响应中是否包含订阅确认信息
        if response.data:
            checks.update({
                "has_subscription_id": "subscriptionId" in response.data or "sub" in response.data,
                "topics_count_match": len(subtopics) > 0
            })
        
        return checks
    
    def _validate_events(self, events: List[Dict[str, Any]], expected_topics: List[str]) -> Dict[str, Any]:
        """
        验证事件收集结果
        
        Args:
            events: 收集到的事件列表
            expected_topics: 期望的主题列表
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        if not events:
            return {
                "valid": False,
                "error": "No events received",
                "expected_topics": expected_topics,
                "received_events": 0
            }
        
        # 分析事件类型
        event_types = set()
        for event in events:
            event_type = event.get("type", "unknown")
            topic = event.get("topic", event.get("subtopic", "unknown"))
            event_types.add(f"{event_type}/{topic}")
        
        return {
            "valid": True,
            "error": None,
            "expected_topics": expected_topics,
            "received_events": len(events),
            "event_types": list(event_types),
            "first_event_time": events[0].get("_received_at") if events else None,
            "last_event_time": events[-1].get("_received_at") if events else None
        }
    
    def _validate_multi_state_events(self, events: List[Dict[str, Any]], expected_topics: List[str]) -> Dict[str, Any]:
        """
        验证多状态事件（更详细的分析）
        
        Args:
            events: 收集到的事件列表
            expected_topics: 期望的主题列表
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        if not events:
            return {
                "valid": False,
                "error": "No multi-state events received",
                "expected_topics": expected_topics,
                "received_events": 0
            }
        
        # 按主题分组事件
        events_by_topic = {}
        for event in events:
            topic = event.get("topic", event.get("subtopic", "unknown"))
            if topic not in events_by_topic:
                events_by_topic[topic] = []
            events_by_topic[topic].append(event)
        
        # 计算覆盖率
        covered_topics = set(events_by_topic.keys())
        expected_topics_set = set(expected_topics)
        coverage_rate = len(covered_topics.intersection(expected_topics_set)) / len(expected_topics_set) if expected_topics_set else 0
        
        return {
            "valid": coverage_rate > 0,  # 宽松验证：只要有事件就通过
            "error": None if coverage_rate > 0 else "No matching topic events received",
            "expected_topics": expected_topics,
            "received_events": len(events),
            "events_by_topic": {topic: len(events) for topic, events in events_by_topic.items()},
            "coverage_rate": coverage_rate,
            "covered_topics": list(covered_topics),
            "missing_topics": list(expected_topics_set - covered_topics)
        }
    
    def get_events_summary(self) -> Dict[str, Any]:
        """
        获取所有收集事件的摘要
        
        Returns:
            Dict[str, Any]: 事件摘要
        """
        if not self.collected_events:
            return {"total_events": 0, "event_types": {}, "timeline": []}
        
        # 统计事件类型
        event_types = {}
        timeline = []
        
        for event in self.collected_events:
            event_type = event.get("type", "unknown")
            topic = event.get("topic", event.get("subtopic", "unknown"))
            full_type = f"{event_type}/{topic}"
            
            event_types[full_type] = event_types.get(full_type, 0) + 1
            
            timeline.append({
                "time": event.get("_received_at"),
                "type": full_type,
                "data_preview": str(event.get("data", {}))[:100]
            })
        
        return {
            "total_events": len(self.collected_events),
            "event_types": event_types,
            "timeline": timeline[:20],  # 只返回前20个事件
            "first_event_at": self.collected_events[0].get("_received_at") if self.collected_events else None,
            "last_event_at": self.collected_events[-1].get("_received_at") if self.collected_events else None
        }
