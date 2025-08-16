#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Token验证报告生成功能
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from report_generator import ReportGenerator, TestResult, AuthTokenInfo

def test_auth_report_generation():
    """测试Token验证报告生成"""
    
    # 创建报告生成器
    generator = ReportGenerator("IBC-AI CO.")
    
    # 添加一些测试的Token验证信息
    auth_infos = [
        AuthTokenInfo(
            requested_scope="callv2/group:L1QinntdEOg:1",
            token_scopes="callv2/group:L1QinntdEOg:1 application/inventory",
            is_match=True,
            token_type="Bearer",
            expires_in=3600,
            timestamp=datetime.now().isoformat()
        ),
        AuthTokenInfo(
            requested_scope="callgiving/group:L1QinntdEOg:1", 
            token_scopes="callgiving/group:L1QinntdEOg:1",
            is_match=True,
            token_type="Bearer",
            expires_in=3600,
            timestamp=datetime.now().isoformat()
        ),
        AuthTokenInfo(
            requested_scope="topology/group:L1QinntdEOg:1",
            token_scopes="application/inventory",
            is_match=False,
            error_message="Token does not contain required scope topology/group:L1QinntdEOg:1",
            token_type="Bearer", 
            expires_in=3600,
            timestamp=datetime.now().isoformat()
        )
    ]
    
    # 添加Token验证信息到报告生成器
    for auth_info in auth_infos:
        generator.add_auth_token_info(auth_info)
    
    # 创建一些示例测试结果
    test_results = [
        TestResult(
            test_id="Test_1",
            name="Solution initialization", 
            description="Initialize solution and establish connections",
            expected_result="Authentication successful, connections established",
            test_result="PASS - All authentication steps completed successfully",
            status="PASS",
            duration_ms=1500.0,
            category="Authentication"
        ),
        TestResult(
            test_id="Test_2",
            name="Token scope validation",
            description="Validate token scopes for API access", 
            expected_result="Token contains required scopes",
            test_result="FAIL - Missing topology scope",
            status="FAIL",
            duration_ms=800.0,
            error_message="Token validation failed for topology scope",
            category="Authentication"
        )
    ]
    
    # 生成报告
    metadata = {
        "test_framework": "KONE SR-API Validator v2.0",
        "api_version": "v2.0",
        "test_environment": "Virtual Environment"
    }
    
    config = {
        "solution_provider": {
            "company_name": "IBC-AI CO.",
            "company_address": "123 Test Street, Test City",
            "contact_person_name": "Test Engineer",
            "contact_email": "test@ibc-ai.com", 
            "contact_phone": "+1-555-0123",
            "tester": "Automated Test System"
        }
    }
    
    reports = generator.generate_report(test_results, metadata, ".", config)
    
    # 输出Markdown报告到文件
    if "markdown" in reports:
        output_file = Path("test_auth_validation_report.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(reports["markdown"])
        print(f"✅ Generated authentication report: {output_file}")
        
        # 显示Token验证部分
        lines = reports["markdown"].split('\n')
        auth_start = next((i for i, line in enumerate(lines) if "Authentication & Token Scope Validation" in line), -1)
        if auth_start >= 0:
            auth_end = next((i for i, line in enumerate(lines[auth_start+1:], auth_start+1) if line.startswith("---")), len(lines))
            print("\n" + "="*60)
            print("AUTHENTICATION SECTION PREVIEW:")
            print("="*60)
            print('\n'.join(lines[auth_start:auth_end]))
    
    # 输出JSON报告用于调试
    if "json" in reports:
        output_file = Path("test_auth_validation_report.json") 
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(reports["json"])
        print(f"✅ Generated JSON report: {output_file}")

if __name__ == "__main__":
    test_auth_report_generation()
