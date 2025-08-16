#!/usr/bin/env python3
"""
逐步调试ReportGenerator
"""

from report_generator import ReportGenerator, TestResult
import traceback

def debug_step_by_step():
    """逐步调试报告生成"""
    
    print("🔧 Step-by-step debugging...")
    
    # 1. 创建简单测试结果
    test_results = [
        TestResult(
            test_id="Test 1",
            name="Sample Test",
            description="A sample test",
            expected_result="Should pass",
            test_result="PASS", 
            status="PASS",
            duration_ms=100.0
        )
    ]
    
    report_gen = ReportGenerator()
    
    try:
        print("Step 1: _enhance_test_results")
        enhanced_results = report_gen._enhance_test_results(test_results)
        print(f"✅ Enhanced {len(enhanced_results)} results")
        
        print("Step 2: _calculate_statistics") 
        stats = report_gen._calculate_statistics(enhanced_results)
        print(f"✅ Calculated stats: {stats}")
        
        print("Step 3: _generate_auth_section")
        auth_section = report_gen._generate_auth_section()
        print(f"✅ Auth section: {len(auth_section)} chars")
        
        print("Step 4: Create report_data")
        metadata = {'building_id': 'TEST', 'test_timestamp': '2025-08-16'}
        report_data = {
            "metadata": metadata,
            "statistics": stats,
            "test_results": enhanced_results,
            "generation_time": "2025-08-16T11:00:00",
            "company": "Test Co",
            "config": {}
        }
        print("✅ Report data created")
        
        print("Step 5: _generate_markdown_report")
        markdown = report_gen._generate_markdown_report(report_data)
        print(f"✅ Markdown generated: {len(markdown)} chars")
        
        # 保存结果查看
        with open('debug_report.md', 'w') as f:
            f.write(markdown)
        print("✅ Debug report saved to debug_report.md")
        
    except Exception as e:
        print(f"❌ Error at step: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_step_by_step()
