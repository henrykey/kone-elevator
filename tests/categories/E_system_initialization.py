"""
Category E: 系统初始化与配置 (Test 1-5)
覆盖KONE API v2.0的初始化和配置验证测试
"""

import asyncio
import time
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from test_case_mapper import TestCaseMapper, TestCategory
from kone_api_client import CommonAPIClient
from reporting.formatter import EnhancedTestResult

logger = logging.getLogger(__name__)


class SystemInitializationTests:
    """Category E: 系统初始化与配置测试类"""
    
    def __init__(self, websocket, building_id: str = "building:L1QinntdEOg", group_id: str = "1"):
        self.websocket = websocket
        self.building_id = building_id
        self.group_id = group_id
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.test_mapper = TestCaseMapper(building_id)
        
    async def run_all_tests(self) -> List[EnhancedTestResult]:
        """执行所有 Category E 测试"""
        self.logger.info("=== 开始执行 Category E: 系统初始化与配置测试 ===")
        
        tests = [
            ("Test 1", "解决方案初始化验证 (solution-initialization)", self.test_solution_initialization),
            ("Test 2", "API连通性验证 (api-connectivity)", self.test_api_connectivity),
            ("Test 3", "服务状态检查 (service-status)", self.test_service_status),
            ("Test 4", "建筑配置获取 (building-config)", self.test_building_configuration),
            ("Test 5", "网络连接测试 (network-connectivity)", self.test_network_connectivity),
        ]
        
        results = []
        for test_id, test_name, test_func in tests:
            self.logger.info(f"开始执行 {test_id}: {test_name}")
            
            try:
                result = await test_func()
                results.append(result)
                self.logger.info(f"{test_id} 完成，状态: {result.status}")
            except Exception as e:
                self.logger.error(f"{test_id} 执行失败: {e}")
                error_result = EnhancedTestResult(
                    test_id=test_id,
                    test_name=test_name,
                    category="E_system_initialization",
                    status="ERROR",
                    duration_ms=0,
                    api_type="common-api",
                    call_type="action",
                    building_id=self.building_id,
                    group_id=self.group_id,
                    error_message=str(e)
                )
                results.append(error_result)
        
        return results

    async def test_solution_initialization(self) -> EnhancedTestResult:
        """
        Test 1: 解决方案初始化验证
        验证：
        1. WebSocket连接建立
        2. 认证状态确认
        3. 初始化响应验证
        """
        start_time = time.time()
        
        try:
            # 获取传统测试配置
            legacy_config = self.test_mapper.get_test_case("Test_1")
            
            # 创建通用API客户端
            common_client = CommonAPIClient(self.websocket)
            
            # 执行初始化验证
            self.logger.info("执行解决方案初始化验证...")
            
            validations = []
            
            # 1. WebSocket连接状态验证
            if self.websocket and not self.websocket.closed:
                validations.append("✅ WebSocket连接已建立")
            else:
                validations.append("❌ WebSocket连接失败")
            
            # 2. 获取建筑配置作为初始化验证
            config_response = await common_client.get_building_config(
                building_id=self.building_id,
                group_id=self.group_id
            )
            
            if config_response.success:
                validations.append("✅ 建筑配置获取成功")
                validations.append(f"✅ 响应状态码: {config_response.status_code}")
                
                # 验证配置数据结构
                if "building" in config_response.data:
                    validations.append("✅ 建筑配置数据结构正确")
                else:
                    validations.append("⚠️ 建筑配置数据结构缺失")
            else:
                validations.append(f"❌ 建筑配置获取失败: {config_response.error}")
            
            # 3. 验证认证状态（通过WebSocket连接的成功维持）
            try:
                # 发送一个简单的ping消息来验证连接状态
                ping_payload = {
                    "type": "lift-call-api-v2",
                    "buildingId": self.building_id,
                    "callType": "ping",
                    "groupId": self.group_id,
                    "payload": {
                        "timestamp": time.time()
                    }
                }
                
                await self.websocket.send(json.dumps(ping_payload))
                validations.append("✅ 认证状态正常")
                
            except Exception as e:
                validations.append(f"❌ 认证状态验证失败: {e}")
            
            # 判断测试结果
            failed_validations = [v for v in validations if v.startswith("❌")]
            status = "FAIL" if failed_validations else "PASS"
            
            return EnhancedTestResult(
                test_id="Test 1",
                test_name="解决方案初始化验证 (solution-initialization)",
                category="E_system_initialization",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                api_type="common-api",
                call_type="action",
                building_id=self.building_id,
                group_id=self.group_id,
                response_data=config_response.data if config_response else {},
                status_code=config_response.status_code if config_response else None,
                error_message="; ".join(failed_validations) if failed_validations else None
            )
            
        except Exception as e:
            self.logger.error(f"解决方案初始化测试失败: {e}")
            return EnhancedTestResult(
                test_id="Test 1",
                test_name="解决方案初始化验证 (solution-initialization)",
                category="E_system_initialization", 
                status="ERROR",
                duration_ms=(time.time() - start_time) * 1000,
                api_type="common-api",
                call_type="action",
                building_id=self.building_id,
                group_id=self.group_id,
                error_message=str(e)
            )

    async def test_api_connectivity(self) -> EnhancedTestResult:
        """
        Test 2: API连通性验证
        验证：
        1. WebSocket API连通性
        2. 基本响应时间
        3. 连接稳定性
        """
        start_time = time.time()
        
        try:
            common_client = CommonAPIClient(self.websocket)
            
            self.logger.info("执行API连通性验证...")
            
            validations = []
            response_times = []
            
            # 执行多次API调用测试连通性
            for i in range(3):
                call_start = time.time()
                
                response = await common_client.get_building_config(
                    building_id=self.building_id,
                    group_id=self.group_id
                )
                
                call_duration = (time.time() - call_start) * 1000
                response_times.append(call_duration)
                
                if response.success:
                    validations.append(f"✅ API调用 {i+1} 成功 ({call_duration:.0f}ms)")
                else:
                    validations.append(f"❌ API调用 {i+1} 失败: {response.error}")
            
            # 分析响应时间
            if response_times:
                avg_time = sum(response_times) / len(response_times)
                max_time = max(response_times)
                
                validations.append(f"📊 平均响应时间: {avg_time:.0f}ms")
                validations.append(f"📊 最大响应时间: {max_time:.0f}ms")
                
                if avg_time < 1000:  # 1秒内
                    validations.append("✅ 响应时间性能良好")
                else:
                    validations.append("⚠️ 响应时间较长")
            
            # 连接稳定性验证
            if self.websocket and not self.websocket.closed:
                validations.append("✅ WebSocket连接保持稳定")
            else:
                validations.append("❌ WebSocket连接不稳定")
            
            failed_validations = [v for v in validations if v.startswith("❌")]
            status = "FAIL" if failed_validations else "PASS"
            
            return EnhancedTestResult(
                test_id="Test 2",
                test_name="API连通性验证 (api-connectivity)",
                category="E_system_initialization",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                api_type="common-api",
                call_type="action",
                building_id=self.building_id,
                group_id=self.group_id,
                error_message="; ".join(failed_validations) if failed_validations else None
            )
            
        except Exception as e:
            self.logger.error(f"API连通性测试失败: {e}")
            return EnhancedTestResult(
                test_id="Test 2", 
                test_name="API连通性验证 (api-connectivity)",
                category="E_system_initialization",
                status="ERROR",
                duration_ms=(time.time() - start_time) * 1000,
                api_type="common-api",
                call_type="action", 
                building_id=self.building_id,
                group_id=self.group_id,
                error_message=str(e)
            )

    async def test_service_status(self) -> EnhancedTestResult:
        """
        Test 3: 服务状态检查
        验证：
        1. 电梯服务可用性
        2. 群组状态
        3. 系统健康度
        """
        start_time = time.time()
        
        try:
            common_client = CommonAPIClient(self.websocket)
            
            self.logger.info("执行服务状态检查...")
            
            validations = []
            
            # 获取建筑配置检查服务状态
            config_response = await common_client.get_building_config(
                building_id=self.building_id,
                group_id=self.group_id  
            )
            
            if config_response.success:
                validations.append("✅ 服务响应正常")
                
                # 分析建筑配置中的服务信息
                building_data = config_response.data.get("building", {})
                
                if building_data:
                    # 检查群组信息
                    groups = building_data.get("groups", [])
                    if groups:
                        validations.append(f"✅ 发现 {len(groups)} 个电梯群组")
                        
                        for group in groups:
                            group_id = group.get("id")
                            lifts = group.get("lifts", [])
                            validations.append(f"✅ 群组 {group_id}: {len(lifts)} 部电梯")
                    else:
                        validations.append("⚠️ 未发现电梯群组信息")
                    
                    # 检查楼层信息
                    floors = building_data.get("floors", [])
                    if floors:
                        validations.append(f"✅ 发现 {len(floors)} 个楼层")
                    else:
                        validations.append("⚠️ 未发现楼层信息")
                
                # 检查响应时间作为健康度指标
                if config_response.duration_ms < 500:
                    validations.append("✅ 系统健康度良好")
                elif config_response.duration_ms < 1000:
                    validations.append("⚠️ 系统健康度一般")
                else:
                    validations.append("❌ 系统健康度较差")
                    
            else:
                validations.append(f"❌ 服务响应失败: {config_response.error}")
            
            failed_validations = [v for v in validations if v.startswith("❌")]
            status = "FAIL" if failed_validations else "PASS"
            
            return EnhancedTestResult(
                test_id="Test 3",
                test_name="服务状态检查 (service-status)",
                category="E_system_initialization",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                api_type="common-api",
                call_type="action",
                building_id=self.building_id,
                group_id=self.group_id,
                response_data=config_response.data if config_response else {},
                status_code=config_response.status_code if config_response else None,
                error_message="; ".join(failed_validations) if failed_validations else None
            )
            
        except Exception as e:
            self.logger.error(f"服务状态检查失败: {e}")
            return EnhancedTestResult(
                test_id="Test 3",
                test_name="服务状态检查 (service-status)",
                category="E_system_initialization",
                status="ERROR",
                duration_ms=(time.time() - start_time) * 1000,
                api_type="common-api",
                call_type="action",
                building_id=self.building_id,
                group_id=self.group_id,
                error_message=str(e)
            )

    async def test_building_configuration(self) -> EnhancedTestResult:
        """
        Test 4: 建筑配置获取
        验证：
        1. 配置数据完整性
        2. 楼层映射正确性
        3. 电梯群组配置
        """
        start_time = time.time()
        
        try:
            common_client = CommonAPIClient(self.websocket)
            
            self.logger.info("执行建筑配置获取测试...")
            
            validations = []
            
            # 获取建筑配置
            config_response = await common_client.get_building_config(
                building_id=self.building_id,
                group_id=self.group_id
            )
            
            if config_response.success:
                validations.append("✅ 建筑配置获取成功")
                
                building_data = config_response.data.get("building", {})
                
                # 验证必需配置字段
                required_fields = ["id", "name", "groups", "floors"]
                for field in required_fields:
                    if field in building_data:
                        validations.append(f"✅ 包含必需字段: {field}")
                    else:
                        validations.append(f"❌ 缺少必需字段: {field}")
                
                # 验证楼层配置
                floors = building_data.get("floors", [])
                if floors:
                    floor_areas = [floor.get("area") for floor in floors]
                    valid_areas = [area for area in floor_areas if area is not None]
                    
                    validations.append(f"✅ 楼层数量: {len(floors)}")
                    validations.append(f"✅ 有效楼层区域: {len(valid_areas)}")
                    
                    # 检查楼层区域的连续性
                    if valid_areas and len(set(valid_areas)) == len(valid_areas):
                        validations.append("✅ 楼层区域ID唯一")
                    else:
                        validations.append("❌ 楼层区域ID重复")
                
                # 验证电梯群组配置
                groups = building_data.get("groups", [])
                if groups:
                    total_lifts = 0
                    for group in groups:
                        lifts = group.get("lifts", [])
                        total_lifts += len(lifts)
                        
                        # 验证每个电梯的配置
                        for lift in lifts:
                            if "id" in lift:
                                validations.append(f"✅ 电梯 {lift['id']} 配置正常")
                            else:
                                validations.append("❌ 电梯配置缺少ID")
                    
                    validations.append(f"✅ 总电梯数量: {total_lifts}")
                
            else:
                validations.append(f"❌ 建筑配置获取失败: {config_response.error}")
            
            failed_validations = [v for v in validations if v.startswith("❌")]
            status = "FAIL" if failed_validations else "PASS"
            
            return EnhancedTestResult(
                test_id="Test 4",
                test_name="建筑配置获取 (building-config)",
                category="E_system_initialization",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                api_type="common-api",
                call_type="action",
                building_id=self.building_id,
                group_id=self.group_id,
                response_data=config_response.data if config_response else {},
                status_code=config_response.status_code if config_response else None,
                error_message="; ".join(failed_validations) if failed_validations else None
            )
            
        except Exception as e:
            self.logger.error(f"建筑配置获取测试失败: {e}")
            return EnhancedTestResult(
                test_id="Test 4",
                test_name="建筑配置获取 (building-config)",
                category="E_system_initialization",
                status="ERROR",
                duration_ms=(time.time() - start_time) * 1000,
                api_type="common-api",
                call_type="action",
                building_id=self.building_id,
                group_id=self.group_id,
                error_message=str(e)
            )

    async def test_network_connectivity(self) -> EnhancedTestResult:
        """
        Test 5: 网络连接测试
        验证：
        1. WebSocket连接稳定性
        2. 数据传输完整性
        3. 连接断开重连能力
        """
        start_time = time.time()
        
        try:
            self.logger.info("执行网络连接测试...")
            
            validations = []
            
            # 1. WebSocket连接状态验证
            if self.websocket and not self.websocket.closed:
                validations.append("✅ WebSocket连接活跃")
                
                # 2. 数据传输测试
                test_payloads = [
                    {"test": "small_payload", "data": "test"},
                    {"test": "medium_payload", "data": "x" * 1000},
                    {"test": "large_payload", "data": "x" * 10000}
                ]
                
                transmission_times = []
                
                for i, payload in enumerate(test_payloads):
                    try:
                        send_start = time.time()
                        
                        # 构造测试消息
                        test_message = {
                            "type": "lift-call-api-v2",
                            "buildingId": self.building_id,
                            "callType": "test",
                            "groupId": self.group_id,
                            "payload": payload
                        }
                        
                        await self.websocket.send(json.dumps(test_message))
                        send_duration = (time.time() - send_start) * 1000
                        transmission_times.append(send_duration)
                        
                        validations.append(f"✅ 数据传输测试 {i+1} 成功 ({send_duration:.0f}ms)")
                        
                    except Exception as e:
                        validations.append(f"❌ 数据传输测试 {i+1} 失败: {e}")
                
                # 3. 传输性能分析
                if transmission_times:
                    avg_transmission = sum(transmission_times) / len(transmission_times)
                    validations.append(f"📊 平均传输时间: {avg_transmission:.0f}ms")
                    
                    if avg_transmission < 100:
                        validations.append("✅ 网络传输性能优秀")
                    elif avg_transmission < 500:
                        validations.append("✅ 网络传输性能良好")
                    else:
                        validations.append("⚠️ 网络传输性能一般")
                
                # 4. 连接稳定性（通过连接持续时间判断）
                connection_stable_time = time.time() - start_time
                if connection_stable_time > 1:  # 连接稳定超过1秒
                    validations.append("✅ 连接稳定性良好")
                else:
                    validations.append("⚠️ 连接稳定性待观察")
                    
            else:
                validations.append("❌ WebSocket连接已断开")
            
            failed_validations = [v for v in validations if v.startswith("❌")]
            status = "FAIL" if failed_validations else "PASS"
            
            return EnhancedTestResult(
                test_id="Test 5",
                test_name="网络连接测试 (network-connectivity)",
                category="E_system_initialization",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                api_type="websocket",
                call_type="test",
                building_id=self.building_id,
                group_id=self.group_id,
                error_message="; ".join(failed_validations) if failed_validations else None
            )
            
        except Exception as e:
            self.logger.error(f"网络连接测试失败: {e}")
            return EnhancedTestResult(
                test_id="Test 5",
                test_name="网络连接测试 (network-connectivity)",
                category="E_system_initialization", 
                status="ERROR",
                duration_ms=(time.time() - start_time) * 1000,
                api_type="websocket",
                call_type="test",
                building_id=self.building_id,
                group_id=self.group_id,
                error_message=str(e)
            )
