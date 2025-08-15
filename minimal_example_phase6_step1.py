#!/usr/bin/env python3
"""
Phase 6 Step 1: Integration & E2E Tests (Test 36-37) 最小运行示例

修正版Category G - 严格对齐官方指南：
- Test 36: Call failure, communication interrupted – Ping building or group  
- Test 37: End-to-end communication enabled (DTU connected)

验证DTU断开/恢复场景下的通信检测、ping操作、呼叫恢复

作者: GitHub Copilot
时间: 2025-08-15 Phase 6
版本: v1.0 - Integration & E2E修正版
"""

import asyncio
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('integration_e2e_test.log')
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """运行 Phase 6 Step 1 - Integration & E2E 测试示例"""
    try:
        from test_scenarios_v2 import TestScenariosV2
        from reporting.formatter import TestReportFormatter
        
        print("🔗 Phase 6 Step 1: Integration & E2E 测试示例")
        print("=" * 70)
        print("修正版 Category G - Test 36-37")
        print("- Test 36: Call failure, communication interrupted – Ping building or group")
        print("- Test 37: End-to-end communication enabled (DTU connected)")
        print("=" * 70)
        
        # 创建测试管理器
        test_manager = TestScenariosV2("config.yaml")
        
        # 只运行修正后的 Category G 测试
        results = await test_manager.run_all_tests(
            building_ids=["building:L1QinntdEOg"],
            categories=["G"]  # 只运行修正后的 Category G
        )
        
        # 过滤出Test 36-37的结果
        integration_results = [
            r for r in results 
            if hasattr(r, 'test_id') and r.test_id in ["Test 36", "Test 37"]
        ]
        
        # 输出测试结果摘要
        print("\n🔗 Integration & E2E 测试结果摘要:")
        print("=" * 50)
        
        for result in integration_results:
            status_icon = "✅" if result.status == "PASS" else "❌" if result.status == "FAIL" else "⚠️"
            print(f"{status_icon} {result.test_id}: {result.test_name}")
            print(f"   状态: {result.status} | 耗时: {result.duration_ms:.0f}ms")
            
            # 显示详细信息
            if hasattr(result, 'response_data') and result.response_data:
                if result.test_id == "Test 36":
                    # Test 36: 通信中断测试详情
                    details = result.response_data
                    print(f"   📊 Ping尝试次数: {details.get('ping_attempts', 'N/A')}")
                    print(f"   ⏱️ 中断持续时间: {details.get('downtime_sec', 'N/A')}秒")
                    if details.get('recovery_timestamp'):
                        print(f"   🔄 恢复时间: {details['recovery_timestamp']}")
                        
                elif result.test_id == "Test 37":
                    # Test 37: 端到端通信恢复详情
                    details = result.response_data
                    if details.get('post_recovery_call'):
                        call_info = details['post_recovery_call']
                        print(f"   📞 恢复后呼叫: {call_info.get('from_floor')}F → {call_info.get('to_floor')}F")
                        print(f"   🎫 Session ID: {call_info.get('session_id', 'N/A')[:16]}...")
                        print(f"   📈 响应时间: {call_info.get('response_time_ms', 'N/A')}ms")
            
            print()
        
        # 统计摘要
        total_count = len(integration_results)
        passed_count = sum(1 for r in integration_results if r.status == "PASS")
        failed_count = sum(1 for r in integration_results if r.status == "FAIL") 
        error_count = sum(1 for r in integration_results if r.status == "ERROR")
        
        print("📊 Integration & E2E 测试统计:")
        print(f"   总计: {total_count} | 通过: {passed_count} | 失败: {failed_count} | 错误: {error_count}")
        print(f"   通过率: {(passed_count/total_count*100):.1f}%" if total_count > 0 else "   通过率: N/A")
        
        # 生成报告
        print("\n📄 生成测试报告...")
        formatter = TestReportFormatter()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        # Markdown报告
        markdown_file = reports_dir / f"integration_e2e_test_report_{timestamp}.md"
        json_file = reports_dir / f"integration_e2e_test_report_{timestamp}.json"
        html_file = reports_dir / f"integration_e2e_test_report_{timestamp}.html"
        
        formatter.save_report(
            integration_results, str(markdown_file), "markdown"
        )
        formatter.save_report(
            integration_results, str(json_file), "json"
        )
        formatter.save_report(
            integration_results, str(html_file), "html"
        )
        
        logger.info("📄 报告已保存到 reports/ 目录")
        logger.info(f"  - Markdown: {markdown_file.name}")
        logger.info(f"  - JSON: {json_file.name}")
        logger.info(f"  - HTML: {html_file.name}")
        
        print("✅ 报告已保存到 reports/ 目录")
        
        # Phase 6 Step 1 关键验证点
        print("\n🔍 Phase 6 Step 1 关键验证点:")
        key_validations = [
            "🔌 DTU通信中断模拟 (simulate-comm-interruption)",
            "📡 中断期间ping失败检测 (ping-during-interruption)", 
            "🔄 ping循环直到恢复成功 (ping-until-recovery)",
            "🔗 端到端通信恢复验证 (e2e-communication-recovery)",
            "📞 恢复后标准电梯呼叫 (post-recovery-call)",
            "✅ Session ID与响应验证 (response-validation)"
        ]
        
        for validation in key_validations:
            print(f"   {validation}")
        
        print("\n🎊 Phase 6 Step 1 完成！Integration & E2E测试框架已就绪")
        
        if passed_count == total_count and total_count > 0:
            print("🌟 所有Integration & E2E测试通过，可以进入Phase 6 Step 2")
        else:
            print("⚠️ 部分测试需要优化，建议先解决问题后再进入下一步")
            
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保所有依赖模块都可用")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 运行出错: {e}")
        logger.exception("Integration & E2E测试运行异常")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
