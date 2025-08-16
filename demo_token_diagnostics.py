#!/usr/bin/env python3
"""
演示Token权限验证在测试失败诊断中的作用
展示如何区分Token权限问题和代码问题
"""

import asyncio
import yaml
from drivers import KoneDriverV2
from report_generator import ReportGenerator, TestResult, AuthTokenInfo
from datetime import datetime

async def demo_token_validation_diagnostics():
    """演示Token验证在失败诊断中的价值"""
    
    print("🔧 KONE Token权限验证诊断演示")
    print("=" * 60)
    print("目的：当测试失败时，通过Token权限验证确定是权限问题还是代码问题")
    print("=" * 60)
    
    # 加载配置
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    kone_config = config.get('kone', {})
    
    # 创建驱动程序
    driver = KoneDriverV2(
        client_id=kone_config['client_id'],
        client_secret=kone_config['client_secret']
    )
    
    # 模拟测试结果
    test_results = []
    
    try:
        print("\n📊 1. 获取Token并验证权限...")
        token = await driver._get_access_token()
        auth_info_list = driver.get_auth_token_info()
        
        for auth_info in auth_info_list:
            print(f"   ✅ Token获取成功")
            print(f"   🔍 请求权限: {auth_info.requested_scope}")
            print(f"   🔍 Token权限: {auth_info.token_scopes}")
            print(f"   🔍 权限匹配: {'✅' if auth_info.is_match else '❌'}")
            if auth_info.error_message:
                print(f"   ⚠️  权限错误: {auth_info.error_message}")
        
        print("\n📊 2. 模拟测试场景...")
        
        # Test 1: 成功的测试（有正确权限）
        test_results.append(TestResult(
            test_id="Test 1",
            name="基础API访问测试",
            description="测试基础API访问功能",
            expected_result="成功获取building配置",
            test_result="PASS",
            status="PASS",
            duration_ms=200.0,
            request_parameters={"method": "GET", "endpoint": "/config"},
            error_message=None
        ))
        
        # Test 2: 失败的测试（可能权限不足）
        test_results.append(TestResult(
            test_id="Test 2", 
            name="保持开门测试",
            description="测试电梯保持开门功能",
            expected_result="成功执行保持开门指令",
            test_result="FAIL",
            status="FAIL",
            duration_ms=5000.0,
            request_parameters={"method": "POST", "endpoint": "/hold_open", "lift_deck": "1:1", "served_area": 1},
            error_message="Hold open command failed - may require additional permissions"
        ))
        
        # Test 3: 权限明确不足的测试
        test_results.append(TestResult(
            test_id="Test 3",
            name="管理员功能测试", 
            description="测试需要管理员权限的功能",
            expected_result="成功执行管理员操作",
            test_result="FAIL",
            status="FAIL",
            duration_ms=100.0,
            request_parameters={"method": "POST", "endpoint": "/admin/reset"},
            error_message="403 Forbidden - Insufficient permissions for admin operations"
        ))
        
        print("   ✅ Test 1: 基础API访问 - PASS")
        print("   ❌ Test 2: 保持开门 - FAIL (权限可能不足)")
        print("   ❌ Test 3: 管理员功能 - FAIL (明确权限不足)")
        
        print("\n📊 3. 生成包含Token权限分析的报告...")
        
        # 创建报告生成器并添加Token验证信息
        report_gen = ReportGenerator(company_name="IBC-AI CO.")
        for auth_info in auth_info_list:
            report_gen.add_auth_token_info(auth_info)
        
        # 添加更多权限验证信息来演示不同场景
        report_gen.add_auth_token_info(AuthTokenInfo(
            requested_scope="admin/management",
            token_scopes="application/inventory callgiving/*",
            is_match=False,
            error_message="Admin scope not found in token - requires elevated permissions",
            token_type="Bearer",
            expires_in=3600,
            timestamp=datetime.now().isoformat()
        ))
        
        # 生成报告
        metadata = {
            'building_id': 'L1QinntdEOg',
            'group_id': '1',
            'test_timestamp': datetime.now().isoformat(),
            'tester': 'Token权限诊断演示',
            'contact_email': 'demo@example.com'
        }
        
        reports = report_gen.generate_report(
            test_results=test_results,
            metadata=metadata
        )
        
        # 保存报告
        markdown_content = reports.get('markdown', '')
        json_content = reports.get('json', '')
        
        with open('token_diagnostics_demo_report.md', 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        with open('token_diagnostics_demo_report.json', 'w', encoding='utf-8') as f:
            f.write(json_content)
        
        print("   ✅ 报告已生成:")
        print("      - token_diagnostics_demo_report.md")
        print("      - token_diagnostics_demo_report.json")
        
        print("\n📊 4. Token权限诊断结果分析:")
        print("   ✅ Test 1成功 - Token权限充足，代码正常")
        print("   ❌ Test 2失败 - 需要检查是否需要特殊权限（如电梯控制权限）")
        print("   ❌ Test 3失败 - 明确权限不足，Token缺少admin scope")
        
        # 显示Token验证部分预览
        if 'Authentication & Token Scope Validation' in markdown_content:
            print("\n📋 Token权限验证部分预览:")
            print("-" * 50)
            lines = markdown_content.split('\n')
            in_auth_section = False
            shown_lines = 0
            
            for line in lines:
                if "## Authentication & Token Scope Validation" in line:
                    in_auth_section = True
                elif in_auth_section and line.startswith("## "):
                    break
                elif in_auth_section and shown_lines < 20:
                    print(line)
                    shown_lines += 1
            print("-" * 50)
        
        print("\n✅ 演示完成！")
        print("\n🎯 Token权限验证的价值:")
        print("   1. 明确区分权限问题和代码问题")
        print("   2. 提供具体的权限缺失信息")
        print("   3. 帮助快速定位测试失败根因")
        print("   4. 为权限申请提供明确依据")
        
    except Exception as e:
        print(f"❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(demo_token_validation_diagnostics())
