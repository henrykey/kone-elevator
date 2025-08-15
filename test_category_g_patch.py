#!/usr/bin/env python3
"""
KONE API v2.0 Category G 修正版测试示例
严格对齐指南 Test 36/37

执行指令中的核心技术挑战：
1. 模拟 DTU（数据传输单元）断开导致的通信中断
2. 在中断状态下发起 ping 请求并正确识别 ping 失败
3. 监控通信恢复事件，重新执行 ping 直至成功  
4. 恢复后重新发起电梯呼叫并验证完整响应数据

Author: GitHub Copilot
Date: 2025-08-15
"""

import asyncio
import json
import logging
import time
import websockets
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
    
    async def recv(self):
        """模拟接收消息"""
        await asyncio.sleep(0.01)
        return '{"status": "ok"}'


async def test_category_g_patch():
    """测试Category G修正版实现"""
    
    print("🚀 开始执行 KONE API v2.0 Category G 修正版测试")
    print("=" * 60)
    
    # 初始化模拟WebSocket
    websocket = MockWebSocket()
    building_id = "building:L1QinntdEOg"
    group_id = "1"
    
    try:
        # 导入测试类
        from tests.categories.G_integration_e2e import IntegrationE2ETestsG
        
        # 初始化测试实例
        test_instance = IntegrationE2ETestsG(websocket, building_id, group_id)
        
        print("\n📋 Category G: Integration & E2E Tests (Test 36-37)")
        print("-" * 50)
        
        # 执行 Test 36: Call failure, communication interrupted
        print("\n🔧 执行 Test 36: Call failure, communication interrupted – Ping building or group")
        start_time = time.time()
        
        result_36 = await test_instance.test_36_call_failure_communication_interrupted()
        
        print(f"  状态: {result_36.status}")
        print(f"  持续时间: {result_36.duration_ms:.1f}ms")
        print(f"  API类型: {result_36.api_type}")
        print(f"  调用类型: {result_36.call_type}")
        
        if hasattr(result_36, 'ping_attempts') and result_36.ping_attempts:
            print(f"  Ping尝试次数: {result_36.ping_attempts}")
        if hasattr(result_36, 'downtime_sec') and result_36.downtime_sec:
            print(f"  中断持续时间: {result_36.downtime_sec:.1f}秒")
        if hasattr(result_36, 'recovery_timestamp') and result_36.recovery_timestamp:
            print(f"  恢复时间戳: {result_36.recovery_timestamp}")
        
        # 执行 Test 37: End-to-end communication enabled
        print("\n🔧 执行 Test 37: End-to-end communication enabled (DTU connected)")
        
        result_37 = await test_instance.test_37_end_to_end_communication_enabled()
        
        print(f"  状态: {result_37.status}")
        print(f"  持续时间: {result_37.duration_ms:.1f}ms")
        print(f"  API类型: {result_37.api_type}")
        print(f"  调用类型: {result_37.call_type}")
        
        if hasattr(result_37, 'recovery_timestamp') and result_37.recovery_timestamp:
            print(f"  恢复时间戳: {result_37.recovery_timestamp}")
        if hasattr(result_37, 'post_recovery_call') and result_37.post_recovery_call:
            print(f"  恢复后呼叫: {result_37.post_recovery_call}")
        
        # 汇总结果
        print("\n📊 测试结果汇总")
        print("-" * 30)
        
        all_results = [result_36, result_37]
        passed_tests = [r for r in all_results if r.status == "PASS"]
        failed_tests = [r for r in all_results if r.status == "FAIL"]
        error_tests = [r for r in all_results if r.status == "ERROR"]
        
        total_tests = len(all_results)
        passed_count = len(passed_tests)
        success_rate = (passed_count / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_count}")
        print(f"失败: {len(failed_tests)}")
        print(f"错误: {len(error_tests)}")
        print(f"通过率: {success_rate:.1f}%")
        
        # 验证新字段
        print("\n🔍 EnhancedTestResult 新字段验证")
        print("-" * 40)
        
        for result in all_results:
            print(f"\n{result.test_id}:")
            new_fields = ['ping_attempts', 'downtime_sec', 'recovery_timestamp', 'post_recovery_call']
            for field in new_fields:
                if hasattr(result, field):
                    value = getattr(result, field)
                    if value is not None:
                        print(f"  ✅ {field}: {value}")
                    else:
                        print(f"  ⚪ {field}: None (正常)")
                else:
                    print(f"  ❌ {field}: 缺失")
        
        print("\n🎉 Category G 修正版测试完成！")
        
        if success_rate == 100:
            print("✅ 所有测试通过，严格对齐KONE官方指南！")
        else:
            print(f"⚠️ {100-success_rate:.1f}% 测试需要进一步调试")
        
        return all_results
        
    except Exception as e:
        logger.error(f"测试执行异常: {e}")
        print(f"\n❌ 测试执行失败: {e}")
        return []


async def main():
    """主入口"""
    try:
        results = await test_category_g_patch()
        
        if results:
            print(f"\n📄 生成测试报告...")
            
            # 简单的JSON报告
            report = {
                "test_suite": "Category G Integration & E2E (修正版)",
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(results),
                "passed_tests": len([r for r in results if r.status == "PASS"]),
                "failed_tests": len([r for r in results if r.status == "FAIL"]),
                "error_tests": len([r for r in results if r.status == "ERROR"]),
                "test_results": [r.to_dict() for r in results]
            }
            
            with open("category_g_patch_test_report.json", "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print("✅ 报告已生成: category_g_patch_test_report.json")
        
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        logger.error(f"主程序异常: {e}")
        print(f"❌ 程序执行失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
