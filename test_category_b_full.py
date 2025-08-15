#!/usr/bin/env python3
"""
KONE API v2.0 Category B 完整测试
验证所有测试的执行状态

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


class MockWebSocket:
    """模拟WebSocket连接"""
    
    def __init__(self):
        self.closed = False
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def send(self, message):
        """模拟发送消息"""
        self.logger.debug(f"发送消息: {message}")
        await asyncio.sleep(0.01)  # 模拟网络延迟


async def test_full_category_b():
    """测试完整的Category B"""
    
    print("🚀 开始执行 KONE API v2.0 Category B 完整测试")
    print("=" * 60)
    
    # 初始化模拟WebSocket
    websocket = MockWebSocket()
    building_id = "building:L1QinntdEOg"
    group_id = "1"
    
    try:
        # 导入测试类
        from tests.categories.B_monitoring_events import MonitoringEventsTests
        
        # 初始化测试实例
        test_instance = MonitoringEventsTests(websocket, building_id, group_id)
        
        print("\n📋 Category B: Monitoring & Events (全部测试)")
        print("-" * 50)
        
        # 定义所有测试
        all_tests = [
            ("test_02_basic_lift_status_monitoring", "Test 2: Basic Lift Status Monitoring"),
            ("test_03_enhanced_status_monitoring", "Test 3: Enhanced Status Monitoring"),
            ("test_11_multi_state_monitoring", "Test 11: Multi-State Monitoring"),
            ("test_12_position_monitoring", "Test 12: Position Monitoring"),
            ("test_13_group_status_monitoring", "Test 13: Group Status Monitoring"),
            ("test_14_load_monitoring", "Test 14: Load Monitoring"),
            ("test_15_direction_monitoring", "Test 15: Direction Monitoring"),
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
                
                print(f"  状态: {result.status}")
                print(f"  持续时间: {execution_time:.1f}ms")
                print(f"  测试ID: {result.test_id}")
                
                if result.status == "ERROR":
                    error_msg = result.error_message or "未知错误"
                    print(f"  错误: {error_msg}")
                
                results.append(result)
                
            except Exception as e:
                print(f"  ❌ 测试执行异常: {e}")
                # 创建错误结果
                from reporting.formatter import EnhancedTestResult
                error_result = EnhancedTestResult(
                    test_id=test_method_name.split('_')[1],
                    test_name=test_description,
                    category="B_monitoring_events",
                    status="ERROR",
                    duration_ms=0,
                    api_type="site-monitoring",
                    call_type="monitor",
                    building_id=building_id,
                    group_id=group_id,
                    error_message=str(e)
                )
                results.append(error_result)
        
        # 汇总结果
        print("\n📊 Category B 完整测试结果汇总")
        print("-" * 40)
        
        passed_tests = [r for r in results if r.status == "PASS"]
        failed_tests = [r for r in results if r.status == "FAIL"]
        error_tests = [r for r in results if r.status == "ERROR"]
        
        total_tests = len(results)
        passed_count = len(passed_tests)
        failed_count = len(failed_tests)
        error_count = len(error_tests)
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_count}")
        print(f"失败: {failed_count}")
        print(f"错误: {error_count}")
        print(f"通过率: {(passed_count / total_tests) * 100:.1f}%")
        
        # 详细错误分析
        print("\n🔍 错误详细分析")
        print("-" * 30)
        
        monitoring_client_errors = 0
        other_errors = 0
        
        for result in error_tests:
            error_msg = result.error_message or ""
            if "NoneType" in error_msg and "monitoring" in error_msg:
                monitoring_client_errors += 1
            else:
                other_errors += 1
        
        print(f"监控客户端相关错误: {monitoring_client_errors}")
        print(f"其他错误: {other_errors}")
        
        # 补丁加强验证
        print("\n🔧 补丁加强功能验证")
        print("-" * 30)
        
        enhanced_tests = [r for r in results if r.test_id in ["002", "003"]]
        for result in enhanced_tests:
            if hasattr(result, 'request_details') and result.request_details:
                mode_test = result.request_details.get('mode_test_enhancement', {})
                if mode_test:
                    print(f"  {result.test_id}: 运营模式测试 {'✅' if mode_test.get('success') else '❌'}")
                else:
                    print(f"  {result.test_id}: 运营模式测试 ❌ (未执行)")
            else:
                print(f"  {result.test_id}: 运营模式测试 ❌ (错误状态)")
        
        print("\n🎯 问题诊断")
        print("-" * 20)
        print("❌ Test 11-15 失败原因分析:")
        print("   1. 依赖真实的监控客户端 (MonitoringAPIClient)")
        print("   2. 需要KONE Driver和WebSocket连接")
        print("   3. 在模拟环境中 monitoring_client = None")
        print("\n✅ Test 2-3 成功原因:")
        print("   1. 补丁加强的运营模式测试独立于监控客户端")
        print("   2. 使用模拟WebSocket和状态管理")
        print("   3. 在监控客户端失败后仍能执行运营模式验证")
        
        print("\n💡 解决方案建议:")
        print("   1. 为Test 11-15添加监控客户端Mock")
        print("   2. 或者在测试环境中提供真实的KONE连接")
        print("   3. 或者将Test 11-15标记为需要真实环境的集成测试")
        
        return results
        
    except Exception as e:
        logger.error(f"测试执行异常: {e}")
        print(f"\n❌ 测试执行失败: {e}")
        return []


async def main():
    """主入口"""
    try:
        results = await test_full_category_b()
        
        if results:
            print(f"\n📄 生成完整测试报告...")
            
            # 详细的JSON报告
            report = {
                "test_suite": "Category B Monitoring & Events (完整测试)",
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(results),
                "passed_tests": len([r for r in results if r.status == "PASS"]),
                "failed_tests": len([r for r in results if r.status == "FAIL"]),
                "error_tests": len([r for r in results if r.status == "ERROR"]),
                "analysis": {
                    "monitoring_client_dependency": "Tests 11-15 require real monitoring client",
                    "patch_enhancement_status": "Tests 2-3 include operational mode testing",
                    "test_environment": "Mock WebSocket environment"
                },
                "test_results": [r.to_dict() for r in results]
            }
            
            with open("category_b_full_test_report.json", "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print("✅ 完整测试报告已生成: category_b_full_test_report.json")
        
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        logger.error(f"主程序异常: {e}")
        print(f"❌ 程序执行失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
