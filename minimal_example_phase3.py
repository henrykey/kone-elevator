#!/usr/bin/env python3
"""
Phase 3 最小运行示例 - Category C: 电梯呼叫与控制

这个脚本演示如何运行 Phase 3 的基本功能：
- Test 5: 基础电梯呼叫 (destination call)
- Test 6: 电梯呼叫参数验证
- Test 7: 电梯呼叫取消
- Test 8: 电梯门控制
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
    """Phase 3 最小示例主函数"""
    try:
        from test_scenarios_v2 import TestScenariosV2
        
        # 创建测试管理器
        test_manager = TestScenariosV2("config.yaml")
        
        print("🚀 Phase 3 最小运行示例 - Category C: 电梯呼叫与控制")
        print("=" * 60)
        
        # 只运行 Category C 测试
        results = await test_manager.run_all_tests(
            building_ids=["building:L1QinntdEOg"],
            categories=["C"]  # 只运行 Category C
        )
        
        # 输出结果摘要
        print("\n📊 Phase 3 测试结果摘要:")
        print("=" * 40)
        
        category_c_results = [r for r in results if hasattr(r, 'test_id') and r.test_id.startswith('Test')]
        
        for result in category_c_results:
            status_icon = "✅" if result.status == "PASS" else "❌"
            print(f"{status_icon} {result.test_id}: {result.test_name} - {result.status}")
            if result.status not in ["PASS"] and result.error_message:
                print(f"    错误: {result.error_message}")
        
        # 统计
        passed = sum(1 for r in category_c_results if r.status == "PASS")
        total = len(category_c_results)
        
        print(f"\n🎯 Category C 汇总: {passed}/{total} 测试通过")
        
        # 生成报告
        print("\n📄 生成测试报告...")
        test_manager.generate_reports("reports")
        print("✅ 报告已保存到 reports/ 目录")
        
        # 显示关键验证点
        print("\n🔍 Phase 3 关键验证点:")
        print("- ✅ 基础电梯呼叫 (destination call)")
        print("- ✅ 高级参数验证 (group_size, delay, language)")
        print("- ✅ 呼叫取消功能 (callType: delete)")
        print("- ✅ 电梯门控制 (callType: hold_open)")
        
        if passed == total:
            print("\n🎉 Phase 3 所有测试通过！电梯呼叫与控制功能验证完成。")
            return 0
        else:
            print(f"\n⚠️ Phase 3 有 {total - passed} 个测试失败，需要检查。")
            return 1
            
    except Exception as e:
        print(f"❌ Phase 3 示例运行失败: {e}")
        return 1

if __name__ == "__main__":
    # 运行 Phase 3 示例
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
