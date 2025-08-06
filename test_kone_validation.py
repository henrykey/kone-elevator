#!/usr/bin/env python
"""
KONE Service Robot API Solution Validation Test Suite v2.0
基于KONE验证测试指南的自动化测试脚本

Author: IBC-AI Co.
Date: 2025-08-06
Version: 2.0.1
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kone_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class KoneValidationTester:
    """KONE API验证测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.building_id = "building:9990000951"
        self.group_id = "1"
        self.terminal_id = 1
        self.test_results = []
        self.session_id = None
        
    async def setup(self):
        """测试环境初始化"""
        logger.info("🚀 开始KONE API验证测试")
        logger.info("=" * 60)
        
        # 检查API可用性
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/")
                if response.status_code == 200:
                    logger.info("✅ API服务可用")
                else:
                    logger.error(f"❌ API服务不可用: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ 无法连接到API服务: {e}")
            return False
        
        # 初始化连接
        result = await self._api_request("GET", "/api/elevator/initialize")
        if result.get('success'):
            self.session_id = result.get('session_id')
            logger.info(f"✅ 测试环境初始化成功，Session ID: {self.session_id}")
            return True
        else:
            logger.error(f"❌ 测试环境初始化失败: {result}")
            return False
    
    async def _api_request(self, method: str, endpoint: str, data: dict = None, params: dict = None) -> dict:
        """执行API请求"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                url = f"{self.base_url}{endpoint}"
                if method == "GET":
                    response = await client.get(url, params=params)
                elif method == "POST":
                    response = await client.post(url, json=data, params=params)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                return response.json()
            except Exception as e:
                return {"success": False, "error": str(e)}
    
    def _log_test_result(self, test_name: str, test_id: str, expected: str, result: dict, passed: bool, notes: str = ""):
        """记录测试结果"""
        test_record = {
            "test_id": test_id,
            "test_name": test_name,
            "expected": expected,
            "result": result,
            "status": "PASS" if passed else "FAIL",
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(test_record)
        
        status_icon = "✅" if passed else "❌"
        logger.info(f"{status_icon} {test_id}: {test_name} - {'PASS' if passed else 'FAIL'}")
        if not passed:
            logger.error(f"   Expected: {expected}")
            logger.error(f"   Got: {result}")
        if notes:
            logger.info(f"   Notes: {notes}")
    
    async def test_flow_0_authentication(self):
        """Flow 0: 认证和初始化测试"""
        logger.info("\n🔐 Flow 0: 认证和初始化测试")
        
        # Test 1: OAuth Token获取 (通过初始化间接测试)
        result = await self._api_request("GET", "/api/elevator/initialize")
        expected = "HTTP 201, 成功创建会话并获取token"
        passed = result.get('success') and result.get('status_code') == 201
        self._log_test_result(
            "OAuth Token获取和会话创建",
            "Test-001",
            expected,
            result,
            passed,
            "通过initialize端点间接验证OAuth认证流程"
        )
        
        if passed:
            self.session_id = result.get('session_id')
    
    async def test_flow_1_basic_calls(self):
        """Flow 1-3: 基本电梯呼叫测试"""
        logger.info("\n🏢 Flow 1-3: 基本电梯呼叫测试")
        
        # Test 2: 基本目的地呼叫
        call_data = {
            "building_id": self.building_id,
            "source": 3000,
            "destination": 5000,
            "action_id": 2,
            "group_id": self.group_id,
            "terminal": self.terminal_id
        }
        
        result = await self._api_request("POST", "/api/elevator/call", call_data)
        expected = "HTTP 201, 呼叫成功注册"
        passed = result.get('success') and result.get('status_code') == 201
        self._log_test_result(
            "基本目的地呼叫 (3楼→5楼)",
            "Test-002",
            expected,
            result,
            passed,
            "测试最基本的电梯呼叫功能"
        )
        
        # Test 3: 带延迟参数的呼叫
        call_data_with_delay = call_data.copy()
        call_data_with_delay["delay"] = 15
        
        result = await self._api_request("POST", "/api/elevator/call", call_data_with_delay)
        expected = "HTTP 201, 带延迟的呼叫成功"
        passed = result.get('success') and result.get('status_code') == 201
        self._log_test_result(
            "带延迟参数的呼叫 (15秒延迟)",
            "Test-003",
            expected,
            result,
            passed,
            "验证delay参数在有效范围内的处理"
        )
        
        # Test 4: 群组呼叫
        call_data_group = call_data.copy()
        call_data_group["group_size"] = 3
        
        result = await self._api_request("POST", "/api/elevator/call", call_data_group)
        expected = "HTTP 201, 群组呼叫成功"
        passed = result.get('success') and result.get('status_code') == 201
        self._log_test_result(
            "群组呼叫 (3人)",
            "Test-004",
            expected,
            result,
            passed,
            "验证群组大小参数处理"
        )
    
    async def test_flow_4_parameter_validation(self):
        """Flow 4-6: 参数验证测试"""
        logger.info("\n✅ Flow 4-6: 参数验证测试")
        
        # Test 5: 相同楼层错误
        call_data = {
            "building_id": self.building_id,
            "source": 3000,
            "destination": 3000,  # 相同楼层
            "action_id": 2,
            "group_id": self.group_id
        }
        
        result = await self._api_request("POST", "/api/elevator/call", call_data)
        expected = "HTTP 400, SAME_SOURCE_AND_DEST_FLOOR错误"
        passed = not result.get('success') and 'SAME_SOURCE_AND_DEST_FLOOR' in str(result.get('error', ''))
        self._log_test_result(
            "相同楼层错误验证",
            "Test-005",
            expected,
            result,
            passed,
            "验证起始楼层和目标楼层相同的错误处理"
        )
        
        # Test 6: 无效延迟参数
        call_data = {
            "building_id": self.building_id,
            "source": 3000,
            "destination": 5000,
            "delay": 45,  # 超过30秒限制
            "action_id": 2,
            "group_id": self.group_id
        }
        
        result = await self._api_request("POST", "/api/elevator/call", call_data)
        expected = "HTTP 400, delay参数验证错误"
        passed = not result.get('success') and result.get('status_code') == 400
        self._log_test_result(
            "无效延迟参数验证",
            "Test-006",
            expected,
            result,
            passed,
            "验证延迟参数超出范围(0-30秒)的错误处理"
        )
        
        # Test 7: 无效群组大小
        call_data = {
            "building_id": self.building_id,
            "source": 3000,
            "destination": 5000,
            "group_size": 150,  # 超过100人限制
            "action_id": 2,
            "group_id": self.group_id
        }
        
        result = await self._api_request("POST", "/api/elevator/call", call_data)
        expected = "HTTP 400, 群组大小验证错误"
        passed = not result.get('success')
        self._log_test_result(
            "无效群组大小验证",
            "Test-007",
            expected,
            result,
            passed,
            "验证群组大小超出范围(1-100)的错误处理"
        )
    
    async def test_flow_7_call_cancellation(self):
        """Flow 7-9: 呼叫取消测试"""
        logger.info("\n❌ Flow 7-9: 呼叫取消测试")
        
        # 先发起一个呼叫用于取消
        call_data = {
            "building_id": self.building_id,
            "source": 3000,
            "destination": 5000,
            "action_id": 2,
            "group_id": self.group_id
        }
        call_result = await self._api_request("POST", "/api/elevator/call", call_data)
        
        if call_result.get('success'):
            request_id = call_result.get('request_id', 'test_request_id')
            
            # Test 8: 基本呼叫取消
            params = {
                "building_id": self.building_id,
                "request_id": request_id
            }
            
            result = await self._api_request("POST", "/api/elevator/cancel", params=params)
            expected = "HTTP 202, 取消请求已接受"
            passed = result.get('success') and result.get('status_code') == 202
            self._log_test_result(
                "基本呼叫取消",
                "Test-008",
                expected,
                result,
                passed,
                "验证有效请求的取消功能"
            )
        
        # Test 9: 取消不存在的呼叫
        params = {
            "building_id": self.building_id,
            "request_id": "non_existent_request"
        }
        
        result = await self._api_request("POST", "/api/elevator/cancel", params=params)
        expected = "HTTP 404或适当的错误响应"
        passed = not result.get('success')
        self._log_test_result(
            "取消不存在的呼叫",
            "Test-009",
            expected,
            result,
            passed,
            "验证无效请求ID的错误处理"
        )
    
    async def test_flow_10_status_monitoring(self):
        """Flow 10-11: 状态监控测试"""
        logger.info("\n📊 Flow 10-11: 状态监控测试")
        
        # Test 10: 电梯模式检查
        params = {
            "building_id": self.building_id,
            "group_id": self.group_id
        }
        
        result = await self._api_request("GET", "/api/elevator/mode", params=params)
        expected = "HTTP 200, 返回电梯模式信息"
        passed = result.get('success') and result.get('status_code') == 200
        self._log_test_result(
            "电梯模式检查",
            "Test-010",
            expected,
            result,
            passed,
            "验证电梯运行模式获取功能"
        )
        
        # Test 11: 建筑配置获取
        params = {
            "building_id": self.building_id
        }
        
        result = await self._api_request("GET", "/api/elevator/config", params=params)
        expected = "HTTP 200, 返回建筑配置信息"
        passed = result.get('success') and result.get('status_code') == 200
        self._log_test_result(
            "建筑配置获取",
            "Test-011",
            expected,
            result,
            passed,
            "验证建筑拓扑配置获取功能"
        )
        
        # Test 12: 连接性测试 (Ping)
        params = {
            "building_id": self.building_id
        }
        
        result = await self._api_request("GET", "/api/elevator/ping", params=params)
        expected = "HTTP 200, 返回Ping响应和延迟信息"
        passed = result.get('success') and result.get('status_code') == 200
        self._log_test_result(
            "连接性测试 (Ping)",
            "Test-012",
            expected,
            result,
            passed,
            f"验证网络连接，延迟: {result.get('latency_ms', 'N/A')}ms"
        )
    
    async def test_extended_scenarios(self):
        """扩展场景测试 (Test 13-25)"""
        logger.info("\n🔧 扩展场景测试")
        
        extended_tests = [
            {
                "id": "Test-013",
                "name": "多楼层跨越呼叫",
                "data": {"building_id": self.building_id, "source": 3000, "destination": 7000, "action_id": 2, "group_id": self.group_id},
                "description": "测试跨越多个楼层的长距离呼叫"
            },
            {
                "id": "Test-014", 
                "name": "带语言偏好的呼叫",
                "data": {"building_id": self.building_id, "source": 3000, "destination": 5000, "action_id": 2, "group_id": self.group_id, "language": "zh-CN"},
                "description": "测试多语言支持功能"
            },
            {
                "id": "Test-015",
                "name": "高优先级呼叫",
                "data": {"building_id": self.building_id, "source": 3000, "destination": 5000, "action_id": 2, "group_id": self.group_id, "priority": "HIGH"},
                "description": "测试高优先级呼叫处理"
            },
            {
                "id": "Test-016",
                "name": "指定电梯呼叫",
                "data": {"building_id": self.building_id, "source": 3000, "destination": 5000, "action_id": 2, "group_id": self.group_id, "allowed_lifts": [1001010]},
                "description": "测试指定特定电梯的呼叫"
            },
            {
                "id": "Test-017",
                "name": "大群组呼叫",
                "data": {"building_id": self.building_id, "source": 3000, "destination": 5000, "action_id": 2, "group_id": self.group_id, "group_size": 8},
                "description": "测试大群组（8人）呼叫"
            }
        ]
        
        for test in extended_tests:
            result = await self._api_request("POST", "/api/elevator/call", test["data"])
            expected = "HTTP 201, 呼叫成功注册"
            passed = result.get('success', False)
            
            self._log_test_result(
                test["name"],
                test["id"],
                expected,
                result,
                passed,
                test["description"]
            )
            
            # 小延迟避免请求过快
            await asyncio.sleep(0.5)
    
    async def test_error_scenarios(self):
        """错误场景测试 (Test 26-30)"""
        logger.info("\n⚠️  错误场景测试")
        
        error_tests = [
            {
                "id": "Test-026",
                "name": "不支持的电梯类型",
                "endpoint": "/api/elevator/initialize",
                "params": {"elevator_type": "invalid_brand"},
                "method": "GET",
                "description": "测试不支持电梯品牌的错误处理"
            },
            {
                "id": "Test-027",
                "name": "无效建筑ID格式",
                "endpoint": "/api/elevator/call",
                "data": {"building_id": "invalid_format", "source": 3000, "destination": 5000, "action_id": 2},
                "method": "POST",
                "description": "测试无效建筑ID格式的错误处理"
            },
            {
                "id": "Test-028",
                "name": "缺少必需参数",
                "endpoint": "/api/elevator/call",
                "data": {"building_id": self.building_id, "source": 3000},  # 缺少destination
                "method": "POST",
                "description": "测试缺少必需参数的错误处理"
            }
        ]
        
        for test in error_tests:
            if test["method"] == "GET":
                result = await self._api_request("GET", test["endpoint"], params=test.get("params"))
            else:
                result = await self._api_request("POST", test["endpoint"], test.get("data"))
            
            expected = "适当的错误响应"
            passed = not result.get('success', True)  # 期望失败
            
            self._log_test_result(
                test["name"],
                test["id"],
                expected,
                result,
                passed,
                test["description"]
            )
    
    async def run_all_tests(self):
        """运行所有测试"""
        start_time = time.time()
        
        # 环境初始化
        if not await self.setup():
            logger.error("❌ 测试环境初始化失败，终止测试")
            return
        
        # 执行测试套件
        await self.test_flow_0_authentication()
        await self.test_flow_1_basic_calls()
        await self.test_flow_4_parameter_validation()
        await self.test_flow_7_call_cancellation()
        await self.test_flow_10_status_monitoring()
        await self.test_extended_scenarios()
        await self.test_error_scenarios()
        
        # 生成测试报告
        end_time = time.time()
        self.generate_report(end_time - start_time)
    
    def generate_report(self, duration: float):
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t['status'] == 'PASS'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 KONE API验证测试结果汇总")
        logger.info("=" * 60)
        logger.info(f"测试时间: {duration:.2f}秒")
        logger.info(f"总测试数: {total_tests}")
        logger.info(f"通过: {passed_tests}")
        logger.info(f"失败: {failed_tests}")
        logger.info(f"成功率: {success_rate:.1f}%")
        
        # 失败测试详情
        if failed_tests > 0:
            logger.info("\n❌ 失败的测试:")
            for test in self.test_results:
                if test['status'] == 'FAIL':
                    logger.info(f"  - {test['test_id']}: {test['test_name']}")
        
        # 保存详细报告
        report_data = {
            "summary": {
                "test_date": datetime.now().isoformat(),
                "duration_seconds": duration,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": f"{success_rate:.1f}%",
                "building_id": self.building_id,
                "api_version": "v2.0",
                "tester": "IBC-AI Co."
            },
            "test_results": self.test_results
        }
        
        with open("kone_validation_results.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n✅ 详细测试报告已保存到 kone_validation_results.json")
        logger.info("🎯 测试完成!")

async def main():
    """主函数"""
    tester = KoneValidationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
