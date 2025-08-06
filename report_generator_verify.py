# Author: IBC-AI CO.
"""
报告生成器验证脚本
"""

import sys
from report_generator import ReportGenerator, TestResult


def create_sample_test_results():
    """创建示例测试结果"""
    return [
        TestResult(
            test_id="Test_1",
            name="Solution initialization",
            status="PASS",
            duration_ms=150.5,
            category="initialization"
        ),
        TestResult(
            test_id="Test_2", 
            name="API connectivity verification",
            status="PASS",
            duration_ms=89.3,
            category="initialization"
        ),
        TestResult(
            test_id="Test_6",
            name="Basic elevator call",
            status="FAIL",
            duration_ms=2300.1,
            error_message="Connection timeout",
            category="call_management"
        ),
        TestResult(
            test_id="Test_16",
            name="Invalid floor call",
            status="PASS",
            duration_ms=45.8,
            category="error_handling"
        ),
        TestResult(
            test_id="Test_21",
            name="Response time measurement",
            status="SKIP",
            duration_ms=0,
            category="performance"
        )
    ]


def test_report_generator():
    """测试报告生成器功能"""
    print("📝 Testing ReportGenerator functionality...")
    
    # 创建报告生成器
    generator = ReportGenerator()
    
    # 创建测试数据
    test_results = create_sample_test_results()
    metadata = {
        "company": "IBC-AI CO.",
        "test_date": "2025-08-06T10:30:00",
        "api_version": "2.0.0",
        "test_framework": "KONE SR-API v2.0",
        "building_id": "fWlfHyPlaca",
        "api_base_url": "http://localhost:8000",
        "test_session_id": "session_20250806_103000"
    }
    
    # 生成报告
    reports = generator.generate_report(test_results, metadata)
    
    print(f"📊 Generated Reports:")
    for format_name in reports.keys():
        if format_name != "error":
            print(f"  ✅ {format_name.upper()} report generated")
            
            # 显示部分内容
            content = reports[format_name]
            if isinstance(content, str):
                preview = content[:200] + "..." if len(content) > 200 else content
                print(f"     Preview: {preview.replace(chr(10), ' ')}")
    
    # 保存报告文件
    if "error" not in reports:
        saved_files = generator.save_reports_to_files(reports, "KONE_Test_Sample")
        print(f"\n💾 Saved Files:")
        for format_name, filepath in saved_files.items():
            if "error" not in filepath:
                print(f"  📄 {format_name}: {filepath}")
    
    return "error" not in reports


if __name__ == "__main__":
    success = test_report_generator()
    
    if success:
        print("\n✅ ReportGenerator verification successful!")
        sys.exit(0)
    else:
        print("\n❌ ReportGenerator verification failed!")
        sys.exit(1)
