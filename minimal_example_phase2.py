#!/usr/bin/env python3
"""
KONE API v2.0 Phase 2 最小运行实例
Author: IBC-AI CO.

用于快速验证 Phase 2 实现的最小可复现示例（Category A + B）
"""

import asyncio
import logging
import sys
from test_scenarios_v2 import TestScenariosV2


async def run_phase2_example():
    """运行 Phase 2 示例"""
    print("🧪 KONE API v2.0 Phase 2 Example (Category A + B)")
    print("=" * 60)
    print("Category A: Configuration & Basic API")
    print("Category B: Monitoring & Events")
    print("Tests: 1, 2, 3, 4, 11, 12, 13, 14, 15")
    print("=" * 60)
    
    # 配置简单日志
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    try:
        # 创建测试管理器
        test_manager = TestScenariosV2()
        
        # 运行 Category A & B 测试
        results = await test_manager.run_all_tests(
            building_ids=["building:L1QinntdEOg"],  # 恢复原来的测试建筑
            categories=["A", "B"]  # 运行 Category A 和 B
        )
        
        print("\n📊 Results Summary:")
        print("-" * 50)
        
        # 按分类显示结果
        category_results = {}
        for result in results:
            cat = result.category
            if cat not in category_results:
                category_results[cat] = []
            category_results[cat].append(result)
        
        for category, cat_results in category_results.items():
            print(f"\n📋 {category}:")
            for result in cat_results:
                status_icon = "✅" if result.status == "PASS" else "❌" if result.status == "FAIL" else "🔥"
                print(f"  {status_icon} Test {result.test_id}: {result.test_name}")
                print(f"     Status: {result.status} | Duration: {result.duration_ms:.0f}ms")
                
                # 显示监控事件信息
                if result.monitoring_events:
                    print(f"     Events: {len(result.monitoring_events)} collected")
                
                if result.error_message:
                    print(f"     Error: {result.error_message}")
                print()
        
        # 统计摘要
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.status == "PASS")
        failed_tests = sum(1 for r in results if r.status == "FAIL")
        error_tests = sum(1 for r in results if r.status == "ERROR")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 Overall Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   🔥 Error: {error_tests}")
        print(f"   📊 Success Rate: {success_rate:.1f}%")
        
        # 监控事件统计
        total_events = sum(len(r.monitoring_events) for r in results if r.monitoring_events)
        if total_events > 0:
            print(f"   📡 Total Events Collected: {total_events}")
        
        # 生成报告（可选）
        test_manager.generate_reports("reports/phase2")
        print(f"\n📄 Reports generated in: reports/phase2/")
        
        # 检查是否所有测试都通过
        if failed_tests == 0 and error_tests == 0:
            print("\n🎉 All tests passed! Phase 2 implementation is working correctly.")
            return True
        else:
            print(f"\n⚠️  {failed_tests + error_tests} test(s) failed. Check the logs for details.")
            return False
            
    except Exception as e:
        print(f"❌ Example execution failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_phase2_example())
    sys.exit(0 if success else 1)
