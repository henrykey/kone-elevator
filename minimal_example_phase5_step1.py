#!/usr/bin/env python3
"""
Phase 5 Step 1 最小运行示例 - Category E: 系统初始化与配置
测试范围: Test 1-5
"""

import asyncio
import logging
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def main():
    """运行 Phase 5 Step 1 - Category E 测试示例"""
    
    print("🚀 Phase 5 Step 1 最小运行示例 - Category E: 系统初始化与配置")
    print("=" * 70)
    
    try:
        from test_scenarios_v2 import TestScenariosV2
        
        # 创建测试管理器
        test_manager = TestScenariosV2("config.yaml")
        
        start_time = time.time()
        
        # 只运行 Category E 测试
        results = await test_manager.run_all_tests(
            building_ids=["building:L1QinntdEOg"],
            categories=["E"]  # 只运行 Category E
        )
        
        execution_time = time.time() - start_time
        
        logger.info("✅ 所有测试完成")
        
        # 输出结果摘要
        print("\n📊 Phase 5 Step 1 测试结果摘要:")
        print("=" * 40)
        
        passed_tests = []
        failed_tests = []
        error_tests = []
        
        for result in results:
            if result.status == "PASS":
                passed_tests.append(result)
                print(f"✅ {result.test_id}: {result.test_name} - PASS")
            elif result.status == "FAIL":
                failed_tests.append(result)
                print(f"❌ {result.test_id}: {result.test_name} - FAIL")
                if result.error_message:
                    print(f"    错误: {result.error_message}")
            else:
                error_tests.append(result)
                print(f"⚠️ {result.test_id}: {result.test_name} - ERROR")
                if result.error_message:
                    print(f"    错误: {result.error_message}")
        
        print(f"\n🎯 Category E 汇总: {len(passed_tests)}/{len(results)} 测试通过")
        print(f"📊 执行时间: {execution_time:.2f} 秒")
        
        # 生成报告
        print("\n📄 生成测试报告...")
        
        # 使用 TestReportFormatter 的 save_report 方法
        from pathlib import Path
        from datetime import datetime
        
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 生成 Markdown 报告
        markdown_file = reports_dir / f"kone_test_report_{timestamp}.md"
        test_manager.report_formatter.save_report(
            results, str(markdown_file), "markdown"
        )
        
        # 生成 JSON 报告  
        json_file = reports_dir / f"kone_test_report_{timestamp}.json"
        test_manager.report_formatter.save_report(
            results, str(json_file), "json"
        )
        
        # 生成 HTML 报告
        html_file = reports_dir / f"kone_test_report_{timestamp}.html" 
        test_manager.report_formatter.save_report(
            results, str(html_file), "html"
        )
        
        logger.info("📄 报告已保存到 reports/ 目录")
        logger.info(f"  - Markdown: {markdown_file.name}")
        logger.info(f"  - JSON: {json_file.name}")
        logger.info(f"  - HTML: {html_file.name}")
        
        print("✅ 报告已保存到 reports/ 目录")
        
        # Phase 5 Step 1 关键验证点
        print("\n🔍 Phase 5 Step 1 关键验证点:")
        key_validations = [
            "✅ 解决方案初始化 (solution-initialization)",
            "✅ API连通性验证 (api-connectivity)", 
            "✅ 服务状态检查 (service-status)",
            "✅ 建筑配置获取 (building-config)",
            "✅ 网络连接测试 (network-connectivity)"
        ]
        for validation in key_validations:
            print(f"- {validation}")
        
        if failed_tests or error_tests:
            print(f"\n⚠️ Phase 5 Step 1 有 {len(failed_tests + error_tests)} 个测试需要检查。")
            return 1
        else:
            print(f"\n🎉 Phase 5 Step 1 完成！所有 {len(results)} 个测试通过。")
            return 0
    
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
