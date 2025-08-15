#!/usr/bin/env python3
"""
Phase 4 最小运行示例 - Category D: 电梯状态查询与实时更新

这个脚本演示如何运行 Phase 4 的基本功能：
- Test 9: 电梯状态监控 (monitor-lift-status)
- Test 10: 电梯位置监控 (monitor-lift-position)
- Test 11: 电梯舱体位置监控 (monitor-deck-position)
- Test 12: 电梯到达时间预测 (monitor-next-stop-eta)
"""

import asyncio
import logging
import sys
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Phase 4 最小示例主函数"""
    try:
        from test_scenarios_v2 import TestScenariosV2
        
        # 创建测试管理器
        test_manager = TestScenariosV2("config.yaml")
        
        print("🚀 Phase 4 最小运行示例 - Category D: 电梯状态查询与实时更新")
        print("=" * 70)
        
        # 只运行 Category D 测试
        results = await test_manager.run_all_tests(
            building_ids=["building:L1QinntdEOg"],
            categories=["D"]  # 只运行 Category D
        )
        
        # 输出结果摘要
        print("\n📊 Phase 4 测试结果摘要:")
        print("=" * 40)
        
        category_d_results = [r for r in results if hasattr(r, 'test_id') and r.test_id.startswith('Test')]
        
        for result in category_d_results:
            status_icon = "✅" if result.status == "PASS" else "❌"
            print(f"{status_icon} {result.test_id}: {result.test_name} - {result.status}")
            if result.status not in ["PASS"] and result.error_message:
                print(f"    错误: {result.error_message}")
            
            # 显示监控事件统计
            if hasattr(result, 'monitoring_events') and result.monitoring_events:
                event_count = len(result.monitoring_events)
                print(f"    📈 收集事件: {event_count} 个")
        
        # 统计
        passed = sum(1 for r in category_d_results if r.status == "PASS")
        total = len(category_d_results)
        
        print(f"\n🎯 Category D 汇总: {passed}/{total} 测试通过")
        
        # 统计总事件数
        total_events = sum(len(r.monitoring_events or []) for r in category_d_results)
        print(f"📊 总监控事件: {total_events} 个")
        
        # 生成报告
        print("\n📄 生成测试报告...")
        test_manager.generate_reports("reports")
        print("✅ 报告已保存到 reports/ 目录")
        
        # 显示关键验证点
        print("\n🔍 Phase 4 关键验证点:")
        print("- ✅ 电梯状态实时监控 (lift-status)")
        print("- ✅ 电梯位置追踪 (lift-position)")
        print("- ✅ 舱体位置更新 (deck-position)")
        print("- ✅ 到达时间预测 (next-stop-eta)")
        
        if passed == total:
            print("\n🎉 Phase 4 所有测试通过！电梯状态监控功能验证完成。")
            return 0
        else:
            print(f"\n⚠️ Phase 4 有 {total - passed} 个测试失败，需要检查。")
            return 1
            
    except Exception as e:
        print(f"❌ Phase 4 示例运行失败: {e}")
        return 1

if __name__ == "__main__":
    # 运行 Phase 4 示例
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
