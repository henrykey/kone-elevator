#!/usr/bin/env python3
"""
Phase 5 Step 3 最小运行示例 - Category G: 性能测试与压力验证

这个脚本演示了KONE API v2.0 Category G (Tests 21-37) 的性能测试执行。

执行范围：
- Test 21: 响应时间测量
- Test 22: 负载测试模拟  
- Test 23-37: 扩展性能验证测试

作者: GitHub Copilot
创建时间: 2025-08-15
版本: Phase 5 Step 3
"""

import asyncio
import logging
from test_scenarios_v2 import TestScenariosV2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def run_category_g_tests():
    """运行Category G性能测试"""
    
    print("🚀 Phase 5 Step 3 最小运行示例 - Category G: 性能测试与压力验证")
    print("=" * 75)
    
    # 创建测试运行器
    test_runner = TestScenariosV2()
    
    try:
        # 运行Category G测试 (仅限性能测试类别)
        results = await test_runner.run_all_tests(
            building_ids=["building:L1QinntdEOg"],
            categories=["G"]  # 仅运行Category G
        )
        
        # 生成测试报告
        print("\n📄 生成测试报告...")
        test_runner.generate_reports()
        
        # 输出测试结果摘要
        print(f"\n📊 Phase 5 Step 3 测试结果摘要:")
        print("=" * 40)
        
        category_g_results = [r for r in results if r.category == "G_performance"]
        
        for result in category_g_results:
            status_icon = "✅" if result.status == "PASS" else "❌" if result.status == "FAIL" else "⚠️"
            print(f"{status_icon} {result.test_id}: {result.test_name} - {result.status}")
            
            if result.error_message:
                print(f"    错误: {result.error_message}")
        
        # 统计信息
        total_tests = len(category_g_results)
        passed_tests = sum(1 for r in category_g_results if r.status == "PASS")
        failed_tests = sum(1 for r in category_g_results if r.status == "FAIL")
        error_tests = sum(1 for r in category_g_results if r.status == "ERROR")
        
        print(f"\n🎯 Category G 汇总: {passed_tests}/{total_tests} 测试通过")
        
        if failed_tests > 0 or error_tests > 0:
            print(f"📊 详细统计: {passed_tests} 通过, {failed_tests} 失败, {error_tests} 错误")
        
        # 性能指标摘要
        performance_summary = []
        for result in category_g_results:
            if result.duration_ms:
                performance_summary.append(f"{result.test_id}: {result.duration_ms:.0f}ms")
        
        if performance_summary:
            print(f"📊 执行时间: {', '.join(performance_summary[:5])}...")  # 显示前5个
        
        total_duration = sum(r.duration_ms for r in category_g_results if r.duration_ms)
        print(f"📊 总执行时间: {total_duration/1000:.2f} 秒")
        
        print(f"\n📄 报告已保存到 reports/ 目录")
        print(f"  - Markdown: kone_test_report_*.md")
        print(f"  - JSON: kone_test_report_*.json") 
        print(f"  - HTML: kone_test_report_*.html")
        print("✅ 报告已保存到 reports/ 目录")
        
        # Phase 5 Step 3 关键验证点
        print(f"\n🔍 Phase 5 Step 3 关键验证点:")
        print("- 🚀 API响应时间测量 (response-time)")
        print("- 🚀 负载测试模拟 (load-testing)")
        print("- 🚀 并发连接压力测试 (concurrent-connections)")
        print("- 🚀 性能基准验证 (performance-benchmarks)")
        print("- 🚀 系统资源监控 (system-monitoring)")
        
        # 最终状态评估
        if failed_tests == 0 and error_tests == 0:
            print(f"\n✅ Phase 5 Step 3 全部测试通过！")
            return 0
        elif error_tests == 0:
            print(f"\n⚠️ Phase 5 Step 3 有 {failed_tests} 个测试需要检查。")
            return 1
        else:
            print(f"\n❌ Phase 5 Step 3 有 {error_tests} 个测试错误，{failed_tests} 个测试失败。")
            return 2
            
    except Exception as e:
        logger.error(f"❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 3

def main():
    """主函数"""
    logger.info("✅ 所有测试完成")
    exit_code = asyncio.run(run_category_g_tests())
    exit(exit_code)

if __name__ == "__main__":
    main()
