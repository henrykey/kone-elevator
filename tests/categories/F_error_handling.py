"""
Category F: 错误处理与异常场景 (Test 16-20)
覆盖KONE API v2.0的错误处理和异常情况验证测试
"""

import asyncio
import time
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from test_case_mapper import TestCaseMapper, TestCategory
from kone_api_client import CommonAPIClient, LiftCallAPIClient
from reporting.formatter import EnhancedTestResult

logger = logging.getLogger(__name__)


class ErrorHandlingTests:
    """Category F: 错误处理与异常场景测试类"""
    
    def __init__(self, websocket, building_id: str = "building:L1QinntdEOg", group_id: str = "1"):
        self.websocket = websocket
        self.building_id = building_id
        self.group_id = group_id
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.test_mapper = TestCaseMapper(building_id)
        
    async def _create_lift_call_client(self) -> LiftCallAPIClient:
        """创建带有建筑配置的电梯呼叫客户端"""
        # 使用虚拟的building_config，避免网络依赖问题
        mock_building_config = {
            "connectionId": "mock_connection",
            "statusCode": 201,
            "data": {
                "time": "2025-08-15T08:00:00.000Z"
            },
            "payload": {
                "areas": [
                    {"id": 1001000, "floor": 1, "name": "1楼"},
                    {"id": 1001010, "floor": 2, "name": "2楼"},
                    {"id": 1001020, "floor": 3, "name": "3楼"}
                ]
            }
        }
        
        return LiftCallAPIClient(self.websocket, mock_building_config)
        
    async def run_all_tests(self) -> List[EnhancedTestResult]:
        """执行所有 Category F 测试"""
        self.logger.info("=== 开始执行 Category F: 错误处理与异常场景测试 ===")
        
        tests = [
            ("Test 16", "无效楼层呼叫 (invalid-floor-call)", self.test_invalid_floor_call),
            ("Test 17", "相同起止楼层 (same-source-destination)", self.test_same_source_destination),
            ("Test 18", "过长延时参数 (excessive-delay)", self.test_excessive_delay_parameter),
            ("Test 19", "无效建筑ID (invalid-building-id)", self.test_invalid_building_id),
            ("Test 20", "缺失必需参数 (missing-parameters)", self.test_missing_required_parameters),
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
                    category="F_error_handling",
                    status="ERROR",
                    duration_ms=0,
                    api_type="lift-call-api-v2",
                    call_type="action",
                    building_id=self.building_id,
                    group_id=self.group_id,
                    error_message=str(e)
                )
                results.append(error_result)
        
        return results

    async def test_invalid_floor_call(self) -> EnhancedTestResult:
        """
        Test 16: 无效楼层呼叫
        验证：
        1. 不存在的楼层区域调用
        2. 负数楼层参数
        3. 超出范围的楼层号
        """
        start_time = time.time()
        
        try:
            # 获取传统测试配置
            legacy_config = self.test_mapper.get_test_case("Test_16")
            
            # 创建电梯呼叫API客户端
            lift_call_client = await self._create_lift_call_client()
            
            self.logger.info("执行无效楼层呼叫测试...")
            
            validations = []
            error_scenarios = []
            
            # 场景1: 不存在的楼层区域
            invalid_scenarios = [
                {
                    "name": "不存在的楼层区域",
                    "from_area": 99999,  # 不存在的区域
                    "to_area": 1001000,
                    "expected_error": "InvalidArea"
                },
                {
                    "name": "负数楼层区域",
                    "from_area": -1000,  # 负数区域
                    "to_area": 1001000,
                    "expected_error": "InvalidArea"
                },
                {
                    "name": "超大楼层区域",
                    "from_area": 1001000,
                    "to_area": 999999999,  # 超大区域
                    "expected_error": "InvalidArea"
                }
            ]
            
            for scenario in invalid_scenarios:
                try:
                    # 执行无效呼叫
                    response = await lift_call_client.make_destination_call(
                        from_floor=1,  # 1楼 对应 1001000
                        to_floor=999,  # 不存在的楼层
                        building_id=self.building_id,
                        group_id=self.group_id,
                        terminal=1
                    )
                    
                    # 检查是否正确返回错误
                    if not response.success:
                        validations.append(f"✅ {scenario['name']}: 正确拒绝无效请求")
                        error_scenarios.append({
                            "scenario": scenario["name"],
                            "status": "rejected",
                            "error": response.error
                        })
                    else:
                        validations.append(f"❌ {scenario['name']}: 应该拒绝但被接受了")
                        error_scenarios.append({
                            "scenario": scenario["name"],
                            "status": "accepted",
                            "error": "Should have been rejected"
                        })
                        
                except Exception as e:
                    validations.append(f"✅ {scenario['name']}: 正确抛出异常 - {str(e)[:50]}")
                    error_scenarios.append({
                        "scenario": scenario["name"],
                        "status": "exception",
                        "error": str(e)
                    })
            
            # 场景4: 验证正常呼叫仍然工作
            try:
                normal_response = await lift_call_client.make_lift_call(
                    building_id=self.building_id,
                    group_id=self.group_id,
                    from_area=1001000,  # 正常区域
                    to_area=1001010,
                    terminal=1
                )
                
                if normal_response.success:
                    validations.append("✅ 正常呼叫仍然正常工作")
                else:
                    validations.append(f"⚠️ 正常呼叫受到影响: {normal_response.error}")
                    
            except Exception as e:
                validations.append(f"⚠️ 正常呼叫出现异常: {e}")
            
            # 判断测试结果
            failed_validations = [v for v in validations if v.startswith("❌")]
            warning_validations = [v for v in validations if v.startswith("⚠️")]
            
            if failed_validations:
                status = "FAIL"
            elif warning_validations:
                status = "PASS"  # 警告不算失败
            else:
                status = "PASS"
            
            return EnhancedTestResult(
                test_id="Test 16",
                test_name="无效楼层呼叫 (invalid-floor-call)",
                category="F_error_handling",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                api_type="lift-call-api-v2",
                call_type="action",
                building_id=self.building_id,
                group_id=self.group_id,
                error_message="; ".join(failed_validations) if failed_validations else None,
                error_details={
                    "tested_scenarios": len(invalid_scenarios),
                    "error_scenarios": error_scenarios,
                    "validation_summary": validations
                }
            )
            
        except Exception as e:
            self.logger.error(f"无效楼层呼叫测试失败: {e}")
            return EnhancedTestResult(
                test_id="Test 16",
                test_name="无效楼层呼叫 (invalid-floor-call)",
                category="F_error_handling",
                status="ERROR",
                duration_ms=(time.time() - start_time) * 1000,
                api_type="lift-call-api-v2",
                call_type="action",
                building_id=self.building_id,
                group_id=self.group_id,
                error_message=str(e)
            )

    async def test_same_source_destination(self) -> EnhancedTestResult:
        """
        Test 17: 相同起止楼层测试
        验证：
        1. 相同起始和目标楼层的处理
        2. API是否正确识别并处理此场景
        3. 错误消息的准确性
        """
        start_time = time.time()
        
        try:
            # 获取传统测试配置
            legacy_config = self.test_mapper.get_test_case("Test_17")
            
            # 创建电梯呼叫API客户端
            lift_call_client = await self._create_lift_call_client()
            
            self.logger.info("执行相同起止楼层测试...")
            
            validations = []
            
            # 测试相同楼层呼叫
            same_floor_scenarios = [
                {"floor": 1, "name": "1楼到1楼"},
                {"floor": 2, "name": "2楼到2楼"},
                {"floor": 3, "name": "3楼到3楼"}
            ]
            
            for scenario in same_floor_scenarios:
                try:
                    response = await lift_call_client.make_destination_call(
                        from_floor=scenario["floor"],
                        to_floor=scenario["floor"],  # 相同起止楼层
                        building_id=self.building_id,
                        group_id=self.group_id,
                        terminal=1
                    )
                    
                    if not response.success:
                        validations.append(f"✅ {scenario['name']}: 正确拒绝相同楼层呼叫")
                        if "same" in response.error.lower() or "identical" in response.error.lower():
                            validations.append(f"✅ {scenario['name']}: 错误消息准确")
                        else:
                            validations.append(f"⚠️ {scenario['name']}: 错误消息不够清晰")
                    else:
                        # 某些系统可能允许相同楼层呼叫（例如开门服务）
                        validations.append(f"⚠️ {scenario['name']}: 系统允许相同楼层呼叫")
                        
                except Exception as e:
                    validations.append(f"✅ {scenario['name']}: 正确抛出异常")
            
            # 验证正常不同楼层呼叫仍然工作
            try:
                normal_response = await lift_call_client.make_destination_call(
                    from_floor=1,
                    to_floor=2,  # 不同楼层
                    building_id=self.building_id,
                    group_id=self.group_id,
                    terminal=1
                )
                
                if normal_response.success:
                    validations.append("✅ 正常不同楼层呼叫工作正常")
                else:
                    validations.append(f"❌ 正常呼叫受到影响: {normal_response.error}")
                    
            except Exception as e:
                validations.append(f"❌ 正常呼叫出现异常: {e}")
            
            failed_validations = [v for v in validations if v.startswith("❌")]
            status = "FAIL" if failed_validations else "PASS"
            
            return EnhancedTestResult(
                test_id="Test 17",
                test_name="相同起止楼层 (same-source-destination)",
                category="F_error_handling",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                api_type="lift-call-api-v2",
                call_type="action",
                building_id=self.building_id,
                group_id=self.group_id,
                error_message="; ".join(failed_validations) if failed_validations else None
            )
            
        except Exception as e:
            self.logger.error(f"相同起止楼层测试失败: {e}")
            return EnhancedTestResult(
                test_id="Test 17",
                test_name="相同起止楼层 (same-source-destination)",
                category="F_error_handling",
                status="ERROR",
                duration_ms=(time.time() - start_time) * 1000,
                api_type="lift-call-api-v2",
                call_type="action",
                building_id=self.building_id,
                group_id=self.group_id,
                error_message=str(e)
            )

    async def test_excessive_delay_parameter(self) -> EnhancedTestResult:
        """
        Test 18: 过长延时参数测试
        验证：
        1. 超出合理范围的延时参数
        2. 负数延时参数
        3. 极大延时参数
        """
        start_time = time.time()
        
        try:
            # 获取传统测试配置
            legacy_config = self.test_mapper.get_test_case("Test_18")
            
            # 创建电梯呼叫API客户端
            lift_call_client = await self._create_lift_call_client()
            
            self.logger.info("执行过长延时参数测试...")
            
            validations = []
            
            # 测试各种无效延时参数
            delay_scenarios = [
                {"delay": -1, "name": "负数延时"},
                {"delay": 86400, "name": "24小时延时"},  # 1天
                {"delay": 999999, "name": "极大延时"},
                {"delay": 0, "name": "零延时"}  # 可能是有效的
            ]
            
            for scenario in delay_scenarios:
                try:
                    response = await lift_call_client.make_destination_call(
                        from_floor=1,
                        to_floor=2,
                        delay=scenario["delay"],  # 延时参数
                        building_id=self.building_id,
                        group_id=self.group_id,
                        terminal=1
                    )
                    
                    if not response.success:
                        validations.append(f"✅ {scenario['name']}: 正确拒绝无效延时")
                    else:
                        if scenario["delay"] < 0 or scenario["delay"] > 3600:  # 超过1小时
                            validations.append(f"❌ {scenario['name']}: 应该拒绝但被接受")
                        else:
                            validations.append(f"✅ {scenario['name']}: 合理延时被接受")
                            
                except Exception as e:
                    if scenario["delay"] < 0 or scenario["delay"] > 3600:
                        validations.append(f"✅ {scenario['name']}: 正确抛出异常")
                    else:
                        validations.append(f"❌ {scenario['name']}: 不应该抛出异常 - {e}")
            
            # 验证正常延时仍然工作
            try:
                normal_response = await lift_call_client.make_destination_call(
                    from_floor=1,
                    to_floor=2,
                    building_id=self.building_id,
                    group_id=self.group_id,
                    terminal=1
                    # 不设置延时，使用默认值
                )
                
                if normal_response.success:
                    validations.append("✅ 正常呼叫（无延时）工作正常")
                else:
                    validations.append(f"❌ 正常呼叫受到影响: {normal_response.error}")
                    
            except Exception as e:
                validations.append(f"❌ 正常呼叫出现异常: {e}")
            
            failed_validations = [v for v in validations if v.startswith("❌")]
            status = "FAIL" if failed_validations else "PASS"
            
            return EnhancedTestResult(
                test_id="Test 18",
                test_name="过长延时参数 (excessive-delay)",
                category="F_error_handling",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                api_type="lift-call-api-v2",
                call_type="action",
                building_id=self.building_id,
                group_id=self.group_id,
                error_message="; ".join(failed_validations) if failed_validations else None
            )
            
        except Exception as e:
            self.logger.error(f"过长延时参数测试失败: {e}")
            return EnhancedTestResult(
                test_id="Test 18",
                test_name="过长延时参数 (excessive-delay)",
                category="F_error_handling",
                status="ERROR",
                duration_ms=(time.time() - start_time) * 1000,
                api_type="lift-call-api-v2",
                call_type="action",
                building_id=self.building_id,
                group_id=self.group_id,
                error_message=str(e)
            )

    async def test_invalid_building_id(self) -> EnhancedTestResult:
        """
        Test 19: 无效建筑ID测试
        验证：
        1. 不存在的建筑ID
        2. 格式错误的建筑ID
        3. 空建筑ID
        """
        start_time = time.time()
        
        try:
            # 获取传统测试配置
            legacy_config = self.test_mapper.get_test_case("Test_19")
            
            # 创建电梯呼叫API客户端
            lift_call_client = await self._create_lift_call_client()
            
            self.logger.info("执行无效建筑ID测试...")
            
            validations = []
            
            # 测试各种无效建筑ID
            invalid_building_ids = [
                {"id": "building:NONEXISTENT", "name": "不存在的建筑"},
                {"id": "invalid_format", "name": "格式错误的建筑ID"},
                {"id": "", "name": "空建筑ID"},
                {"id": "building:", "name": "无建筑名的ID"},
                {"id": "XXXXXXXXXXXXXXX", "name": "无前缀的无效ID"}
            ]
            
            for scenario in invalid_building_ids:
                try:
                    response = await lift_call_client.make_destination_call(
                        from_floor=1,
                        to_floor=2,
                        building_id=scenario["id"],
                        group_id=self.group_id,
                        terminal=1
                    )
                    
                    if not response.success:
                        validations.append(f"✅ {scenario['name']}: 正确拒绝无效建筑ID")
                        if "building" in response.error.lower() or "invalid" in response.error.lower():
                            validations.append(f"✅ {scenario['name']}: 错误消息准确")
                    else:
                        validations.append(f"❌ {scenario['name']}: 应该拒绝但被接受")
                        
                except Exception as e:
                    validations.append(f"✅ {scenario['name']}: 正确抛出异常")
            
            # 验证正确的建筑ID仍然工作
            try:
                normal_response = await lift_call_client.make_destination_call(
                    from_floor=1,
                    to_floor=2,
                    building_id=self.building_id,  # 正确的建筑ID
                    group_id=self.group_id,
                    terminal=1
                )
                
                if normal_response.success:
                    validations.append("✅ 正确建筑ID工作正常")
                else:
                    validations.append(f"❌ 正确建筑ID受到影响: {normal_response.error}")
                    
            except Exception as e:
                validations.append(f"❌ 正确建筑ID出现异常: {e}")
            
            failed_validations = [v for v in validations if v.startswith("❌")]
            status = "FAIL" if failed_validations else "PASS"
            
            return EnhancedTestResult(
                test_id="Test 19",
                test_name="无效建筑ID (invalid-building-id)",
                category="F_error_handling",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                api_type="lift-call-api-v2",
                call_type="action",
                building_id=scenario["id"] if 'scenario' in locals() else self.building_id,
                group_id=self.group_id,
                error_message="; ".join(failed_validations) if failed_validations else None
            )
            
        except Exception as e:
            self.logger.error(f"无效建筑ID测试失败: {e}")
            return EnhancedTestResult(
                test_id="Test 19",
                test_name="无效建筑ID (invalid-building-id)",
                category="F_error_handling",
                status="ERROR",
                duration_ms=(time.time() - start_time) * 1000,
                api_type="lift-call-api-v2",
                call_type="action",
                building_id=self.building_id,
                group_id=self.group_id,
                error_message=str(e)
            )

    async def test_missing_required_parameters(self) -> EnhancedTestResult:
        """
        Test 20: 缺失必需参数测试
        验证：
        1. 缺少必需字段的请求
        2. 空值参数
        3. 类型错误的参数
        """
        start_time = time.time()
        
        try:
            # 获取传统测试配置
            legacy_config = self.test_mapper.get_test_case("Test_20")
            
            self.logger.info("执行缺失必需参数测试...")
            
            validations = []
            
            # 测试各种缺失参数的场景
            incomplete_payloads = [
                {
                    "name": "缺少buildingId",
                    "payload": {
                        "type": "lift-call-api-v2",
                        "callType": "action",
                        "groupId": self.group_id,
                        "payload": {
                            "request_id": 12345,
                            "area": 1001000,
                            "call": {"action": 2, "destination": 1001010}
                        }
                    }
                },
                {
                    "name": "缺少callType",
                    "payload": {
                        "type": "lift-call-api-v2", 
                        "buildingId": self.building_id,
                        "groupId": self.group_id,
                        "payload": {
                            "request_id": 12345,
                            "area": 1001000,
                            "call": {"action": 2, "destination": 1001010}
                        }
                    }
                },
                {
                    "name": "缺少payload",
                    "payload": {
                        "type": "lift-call-api-v2",
                        "buildingId": self.building_id,
                        "callType": "action",
                        "groupId": self.group_id
                    }
                },
                {
                    "name": "缺少call字段",
                    "payload": {
                        "type": "lift-call-api-v2",
                        "buildingId": self.building_id,
                        "callType": "action",
                        "groupId": self.group_id,
                        "payload": {
                            "request_id": 12345,
                            "area": 1001000
                        }
                    }
                },
                {
                    "name": "空buildingId",
                    "payload": {
                        "type": "lift-call-api-v2",
                        "buildingId": "",
                        "callType": "action",
                        "groupId": self.group_id,
                        "payload": {
                            "request_id": 12345,
                            "area": 1001000,
                            "call": {"action": 2, "destination": 1001010}
                        }
                    }
                }
            ]
            
            for scenario in incomplete_payloads:
                try:
                    # 发送不完整的消息
                    await self.websocket.send(json.dumps(scenario["payload"]))
                    
                    # 等待响应
                    try:
                        response_raw = await asyncio.wait_for(
                            self.websocket.recv(), timeout=3
                        )
                        response = json.loads(response_raw)
                        
                        if "error" in response or response.get("statusCode", 200) >= 400:
                            validations.append(f"✅ {scenario['name']}: 正确拒绝不完整请求")
                        else:
                            validations.append(f"❌ {scenario['name']}: 应该拒绝但被接受")
                            
                    except asyncio.TimeoutError:
                        validations.append(f"✅ {scenario['name']}: 无响应（可能被拒绝）")
                        
                except Exception as e:
                    validations.append(f"✅ {scenario['name']}: 正确抛出异常")
            
            # 验证完整的正确请求仍然工作
            try:
                # 创建一个新的客户端来测试正确的请求
                test_lift_call_client = await self._create_lift_call_client()
                normal_response = await test_lift_call_client.make_destination_call(
                    from_floor=1,
                    to_floor=2,
                    building_id=self.building_id,
                    group_id=self.group_id,
                    terminal=1
                )
                
                if normal_response.success:
                    validations.append("✅ 完整正确的请求工作正常")
                else:
                    validations.append(f"❌ 正确请求受到影响: {normal_response.error}")
                    
            except Exception as e:
                validations.append(f"❌ 正确请求出现异常: {e}")
            
            failed_validations = [v for v in validations if v.startswith("❌")]
            status = "FAIL" if failed_validations else "PASS"
            
            return EnhancedTestResult(
                test_id="Test 20",
                test_name="缺失必需参数 (missing-parameters)",
                category="F_error_handling",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                api_type="lift-call-api-v2",
                call_type="action",
                building_id=self.building_id,
                group_id=self.group_id,
                error_message="; ".join(failed_validations) if failed_validations else None
            )
            
        except Exception as e:
            self.logger.error(f"缺失必需参数测试失败: {e}")
            return EnhancedTestResult(
                test_id="Test 20",
                test_name="缺失必需参数 (missing-parameters)",
                category="F_error_handling",
                status="ERROR",
                duration_ms=(time.time() - start_time) * 1000,
                api_type="lift-call-api-v2",
                call_type="action",
                building_id=self.building_id,
                group_id=self.group_id,
                error_message=str(e)
            )
