#!/usr/bin/env python3
"""
KONE API v2.0 最小运行实例
Author: IBC-AI CO.

用于快速验证 Phase 1 实现的最小可复现示例
"""

import asyncio
import logging
import sys
from test_scenarios_v2 import TestScenariosV2


async def run_minimal_example():
    """运行最小示例"""
    print("🧪 KONE API v2.0 Minimal Example (Phase 1)")
    print("=" * 50)
    
    # 配置简单日志
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    try:
        # 创建测试管理器
        test_manager = TestScenariosV2()
        
        # 运行 Category A 测试（Test 1 & 4）
        results = await test_manager.run_all_tests(
            building_ids=["building:L1QinntdEOg"],  # 使用配置中的测试建筑
            categories=["A"]  # 只运行 Category A
        )
        
        print("\n📊 Results Summary:")
        print("-" * 30)
        
        for result in results:
            status_icon = "✅" if result.status == "PASS" else "❌" if result.status == "FAIL" else "🔥"
            print(f"{status_icon} Test {result.test_id}: {result.test_name}")
            print(f"   Status: {result.status}")
            print(f"   Duration: {result.duration_ms:.0f}ms")
            if result.error_message:
                print(f"   Error: {result.error_message}")
            print()
        
        # 生成报告（可选）
        test_manager.generate_reports("reports/phase1")
        
        # 检查是否所有测试都通过
        failed_tests = [r for r in results if r.status != "PASS"]
        
        if not failed_tests:
            print("🎉 All tests passed! Phase 1 implementation is working correctly.")
            return True
        else:
            print(f"⚠️  {len(failed_tests)} test(s) failed. Check the logs for details.")
            return False
            
    except Exception as e:
        print(f"❌ Example execution failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_minimal_example())
    sys.exit(0 if success else 1)
