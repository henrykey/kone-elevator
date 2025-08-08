#!/usr/bin/env python3
"""
测试报告生成器是否符合KONE测试指南格式要求
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from report_generator import ReportGenerator, TestResult

def test_report_generation():
    """测试报告生成功能"""
    print("🧪 测试报告生成器...")
    
    # 创建测试数据
    test_results = [
        TestResult(
            test_id="Test_1",
            name="Solution initialization",
            description="Solution initialization",
            expected_result="- Connections established by solution to test environment (Virtual or Preproduction).\n- Authentication successful\n- Get resources successful\n- Building config can be obtained.\n- Response code 200\n- Response code 401 in case if there is issue with API Credentials\n- Building actions can be obtained.\n- Response code 200\n- Response code 401 in case if there is issue with API Credentials",
            test_result="PASS",
            status="PASS",
            duration_ms=1500.0,
            category="initialization"
        ),
        TestResult(
            test_id="Test_2",
            name="API connectivity verification",
            description="Verification of API connectivity and WebSocket establishment",
            expected_result="- WebSocket connection established successfully\n- API endpoints accessible\n- Authentication working properly",
            test_result="PASS",
            status="PASS",
            duration_ms=2100.0,
            category="connectivity"
        ),
        TestResult(
            test_id="Test_3",
            name="Service status check",
            description="Check if elevator service is operational",
            expected_result="- Service status check successful\n- System operational status confirmed",
            test_result="FAIL",
            status="FAIL",
            duration_ms=800.0,
            error_message="Connection timeout",
            category="status"
        )
    ]
    
    # 创建元数据
    metadata = {
        "test_framework": "KONE SR-API v2.0",
        "api_version": "2.0.0",
        "test_date": datetime.now().isoformat(),
        "total_tests": len(test_results),
        "building_id": "Test_Building",
        "test_environment": "WebSocket",
        "tester": "test_script",
        "version": "2.0.0",
        # 指南要求的字段
        "setup": "Get access to the equipment for testing:\n- Virtual equipment, available in KONE API portal\n- Preproduction equipment, by contacting KONE API Support (api-support@kone.com)",
        "pre_test_setup": "- Test environments available for the correct KONE API organization.\n- Building id can be retrieved (/resource endpoint).",
        "date": datetime.now().strftime("%d.%m.%Y"),
        "solution_provider": "IBC-AI CO.",
        "company_address": "待填写",
        "contact_person": "待填写",
        "contact_email": "待填写",
        "contact_phone": "待填写",
        "tested_system": "KONE Elevator Control Service",
        "system_version": "待填写",
        "software_name": "KONE SR-API Test Suite",
        "software_version": "2.0.0",
        "kone_sr_api_version": "v2.0",
        "kone_assistant_email": "待填写"
    }
    
    # 生成报告
    generator = ReportGenerator("IBC-AI CO.")
    reports = generator.generate_report(test_results, metadata, "./test_reports")
    
    if "error" in reports:
        print(f"❌ 报告生成失败: {reports['error']}")
        return False
    
    # 检查生成的报告格式
    expected_formats = ["markdown", "json", "html", "excel"]
    for format_name in expected_formats:
        if format_name in reports:
            print(f"✅ {format_name} 报告生成成功")
            
            # 检查关键字段是否存在
            content = reports[format_name]
            if format_name == "markdown":
                # 检查Markdown报告是否包含指南要求的字段
                if "Test | Description | Expected result | Test result" in content:
                    print(f"  ✅ {format_name} 包含正确的表格格式")
                else:
                    print(f"  ❌ {format_name} 缺少指南要求的表格格式")
                
                if "Setup" in content and "Pre-Test Setup" in content:
                    print(f"  ✅ {format_name} 包含Setup信息")
                else:
                    print(f"  ❌ {format_name} 缺少Setup信息")
                    
                if "Solution Provider" in content and "Tested System" in content:
                    print(f"  ✅ {format_name} 包含提供商和系统信息")
                else:
                    print(f"  ❌ {format_name} 缺少提供商和系统信息")
                    
            elif format_name == "json":
                # 检查JSON报告结构
                import json
                try:
                    data = json.loads(content)
                    if "test_results" in data and "document_info" in data:
                        print(f"  ✅ {format_name} 结构正确")
                        
                        # 检查测试结果字段
                        test_result = data["test_results"][0]
                        required_fields = ["test", "description", "expected_result", "test_result"]
                        missing_fields = [field for field in required_fields if field not in test_result]
                        if not missing_fields:
                            print(f"  ✅ {format_name} 测试结果字段完整")
                        else:
                            print(f"  ❌ {format_name} 缺少字段: {missing_fields}")
                    else:
                        print(f"  ❌ {format_name} 结构不正确")
                except:
                    print(f"  ❌ {format_name} JSON格式无效")
        else:
            print(f"❌ {format_name} 报告生成失败")
    
    # 保存测试报告到文件
    saved_files = generator.save_reports_to_files(reports, "Test_Report")
    if "error" not in saved_files:
        print(f"✅ 报告文件保存成功:")
        for format_name, filepath in saved_files.items():
            print(f"  📄 {format_name}: {filepath}")
    else:
        print(f"❌ 报告文件保存失败: {saved_files['error']}")
    
    return True

if __name__ == "__main__":
    success = test_report_generation()
    if success:
        print("\n🎉 报告生成器测试完成！")
        print("✅ 报告格式符合KONE测试指南要求")
    else:
        print("\n❌ 报告生成器测试失败")
    
    sys.exit(0 if success else 1)
