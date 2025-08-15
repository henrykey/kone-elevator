#!/usr/bin/env python3
"""
KONE API v2.0 Category C 完整补丁测试
验证所有测试（Test 5-8, 14）和补丁功能都能正常工作

Author: GitHub Copilot
Date: 2025-08-15
"""

import asyncio
import json
import logging
import time
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class MockCommonAPIClient:
    """模拟 CommonAPIClient"""
    
    def __init__(self, building_id: str):
        self.building_id = building_id
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def send_request_and_wait_response(self, payload: dict, timeout: float = 10.0):
        """模拟发送请求并等待响应"""
        self.logger.info(f"模拟发送请求: {payload['callType']}")
        
        # 模拟处理时间
        await asyncio.sleep(0.1)
        
        # 根据请求类型生成模拟响应
        request_id = payload.get("payload", {}).get("request_id", "mock_id")
        
        if payload.get("callType") == "action":
            # 模拟电梯呼叫响应
            return {
                "statusCode": 201,
                "requestId": request_id,
                "data": {
                    "sessionId": f"session_{int(time.time())}",
                    "liftDeck": 1001010,
                    "time": datetime.now().isoformat()
                }
            }
        elif payload.get("callType") == "delete":
            # 模拟取消呼叫响应
            return {
                "statusCode": 200,
                "requestId": request_id,
                "data": {
                    "cancelled": True,
                    "time": datetime.now().isoformat()
                }
            }
        elif payload.get("callType") == "hold_open":
            # 模拟门控制响应
            return {
                "statusCode": 200,
                "requestId": request_id,
                "data": {
                    "door_held": True,
                    "lift_deck": payload.get("payload", {}).get("lift_deck"),
                    "time": datetime.now().isoformat()
                }
            }
        else:
            # 未知请求类型
            return {
                "statusCode": 400,
                "requestId": request_id,
                "error": "Unknown call type"
            }


async def test_complete_category_c():
    """测试完整的Category C和所有补丁功能"""
    
    print("🚀 开始执行 KONE API v2.0 Category C 完整补丁测试")
    print("目标: 所有测试通过，补丁功能严格对齐官方指南")
    print("=" * 80)
    
    # 初始化模拟客户端
    building_id = "building:L1QinntdEOg"
    mock_client = MockCommonAPIClient(building_id)
    
    try:
        # 导入测试类
        from tests.categories.C_elevator_calls import ElevatorCallsTests
        
        # 初始化测试实例
        test_instance = ElevatorCallsTests(mock_client)
        
        print("\n📋 Category C: Elevator Calls (所有测试 + 补丁)")
        print("-" * 60)
        
        # 定义所有测试
        all_tests = [
            ("test_basic_lift_call", "Test 5: 基础电梯呼叫 (destination call)"),
            ("test_lift_call_parameters", "Test 6: 电梯呼叫参数验证 (Option 1/2 enhanced)"),
            ("test_lift_call_cancellation", "Test 7: 电梯呼叫取消"),
            ("test_door_control", "Test 8: 电梯门控制 (soft_time patch)"),
            ("test_specific_lift_call", "Test 14: 特定电梯呼叫 (allowed-lifts patch)"),
        ]
        
        results = []
        
        for test_method_name, test_description in all_tests:
            print(f"\n🔧 执行 {test_description}")
            
            try:
                # 获取测试方法
                test_method = getattr(test_instance, test_method_name)
                
                # 执行测试
                start_time = time.time()
                result = await test_method()
                execution_time = (time.time() - start_time) * 1000
                
                status_emoji = "✅" if result.status == "PASS" else "❌" if result.status == "FAIL" else "⚠️"
                print(f"  {status_emoji} 状态: {result.status}")
                print(f"  ⏱️  持续时间: {execution_time:.1f}ms")
                print(f"  🆔 测试ID: {result.test_id}")
                
                if result.status != "PASS":
                    error_msg = result.error_message or "未知错误"
                    print(f"  📝 详情: {error_msg}")
                
                # 检查补丁功能
                if hasattr(result, 'test_name') and 'enhanced' in result.test_name.lower():
                    print(f"  🌟 补丁功能: 已集成到测试中")
                elif hasattr(result, 'test_name') and 'patch' in result.test_name.lower():
                    print(f"  🌟 补丁功能: 专用补丁测试")
                
                results.append(result)
                
            except Exception as e:
                print(f"  ❌ 测试执行异常: {e}")
                # 创建错误结果
                from reporting.formatter import EnhancedTestResult
                error_result = EnhancedTestResult(
                    test_id=test_method_name.replace('test_', 'Test '),
                    test_name=test_description,
                    category="C_elevator_calls",
                    status="ERROR",
                    duration_ms=0,
                    api_type="lift-call-api-v2",
                    call_type="unknown",
                    building_id=building_id,
                    group_id="1",
                    error_message=str(e)
                )
                results.append(error_result)
        
        # 汇总结果
        print("\n📊 Category C 完整补丁测试结果汇总")
        print("-" * 50)
        
        passed_tests = [r for r in results if r.status == "PASS"]
        failed_tests = [r for r in results if r.status == "FAIL"]
        error_tests = [r for r in results if r.status == "ERROR"]
        
        total_tests = len(results)
        passed_count = len(passed_tests)
        failed_count = len(failed_tests)
        error_count = len(error_tests)
        
        print(f"总测试数: {total_tests}")
        print(f"✅ 通过: {passed_count}")
        print(f"❌ 失败: {failed_count}")
        print(f"⚠️  错误: {error_count}")
        print(f"🎯 通过率: {(passed_count / total_tests) * 100:.1f}%")
        
        # 补丁功能分析
        print("\n🔍 补丁功能分析")
        print("-" * 25)
        
        patch_features = [
            {"name": "Test 8: soft_time field", "target": "door_control"},
            {"name": "Test 14: allowed-lifts parameter", "target": "specific_lift_call"},
            {"name": "Test 6: Option 1/2 branches", "target": "parameter_validation"}
        ]
        
        implemented_patches = 0
        for feature in patch_features:
            test_found = any(feature["target"] in r.test_id.lower().replace(" ", "_") 
                           for r in passed_tests)
            if test_found:
                implemented_patches += 1
                print(f"✅ {feature['name']}: 已实现")
            else:
                print(f"❌ {feature['name']}: 未找到")
        
        print(f"\n补丁实现率: {(implemented_patches / len(patch_features)) * 100:.1f}%")
        
        # 综合评估
        if passed_count == total_tests and implemented_patches == len(patch_features):
            print("\n🌟 完美！所有 Category C 测试和补丁都成功！")
            print("✅ 原有功能: 完全正常")
            print("✅ 补丁功能: 严格对齐官方指南")
            print("✅ 系统兼容: Mock环境完全支持")
        elif passed_count >= total_tests * 0.9:
            print(f"\n🎉 优秀！Category C 通过率达到 {(passed_count/total_tests)*100:.1f}%")
            print("✅ 主要功能正常")
            if failed_count > 0:
                print(f"⚠️  需要关注 {failed_count} 个失败测试")
        else:
            print(f"\n⚠️ Category C 需要进一步修复")
            print(f"❌ 通过率仅 {(passed_count/total_tests)*100:.1f}%")
        
        # 失败测试详情
        if failed_tests or error_tests:
            print("\n❌ 失败/错误测试详情:")
            for result in failed_tests + error_tests:
                print(f"  - {result.test_id}: {result.test_name}")
                if result.error_message:
                    print(f"    错误: {result.error_message}")
        
        return results
        
    except Exception as e:
        logger.error(f"测试执行异常: {e}")
        print(f"\n❌ 测试执行失败: {e}")
        return []


async def main():
    """主入口"""
    try:
        results = await test_complete_category_c()
        
        if results:
            print(f"\n📄 生成完整测试报告...")
            
            # 详细的JSON报告
            report = {
                "test_suite": "Category C Complete Patch Test",
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(results),
                "passed_tests": len([r for r in results if r.status == "PASS"]),
                "failed_tests": len([r for r in results if r.status == "FAIL"]),
                "error_tests": len([r for r in results if r.status == "ERROR"]),
                "patch_features": {
                    "test_8_soft_time": "Door control with soft_time field",
                    "test_14_allowed_lifts": "Specific lift call with allowed-lifts parameter",
                    "test_6_option_branches": "Parameter validation with Option 1/2 branches"
                },
                "test_results": [r.to_dict() for r in results]
            }
            
            with open("category_c_complete_patch_test_report.json", "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print("✅ 完整测试报告已生成: category_c_complete_patch_test_report.json")
        
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        logger.error(f"主程序异常: {e}")
        print(f"❌ 程序执行失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
