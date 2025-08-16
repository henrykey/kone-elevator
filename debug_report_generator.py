#!/usr/bin/env python3
"""
调试ReportGenerator
"""

from datetime import datetime
from report_generator import ReportGenerator, TestResult, AuthTokenInfo

def test_report_generator():
    """测试ReportGenerator基本功能"""
    
    print("🔧 Testing ReportGenerator...")
    
    # 创建简单测试结果
    test_results = [
        TestResult(
            test_id="Test 1",
            name="Sample Test",
            description="A sample test for debugging",
            expected_result="Should pass successfully",
            test_result="PASS",
            status="PASS",
            duration_ms=100.5,
            category="Websocket"
        )
    ]
    
    # 创建ReportGenerator
    report_gen = ReportGenerator("IBC-AI")
    
    # 添加token验证信息
    auth_info = AuthTokenInfo(
        requested_scope="KONE.ORGANIZATION",
        token_scopes="KONE.ORGANIZATION",
        is_match=True,
        error_message=None
    )
    report_gen.add_auth_token_info(auth_info)
    
    # 生成报告
    metadata = {
        'building_id': 'TEST_BUILDING',
        'test_timestamp': datetime.now().isoformat()
    }
    
    try:
        # 生成测试报告
        reports = report_gen.generate_report(
            test_results=test_results,
            metadata=metadata,
            output_dir="./debug_reports"
        )
        
        # 显示生成的报告
        print(f"✅ Generated {len(reports)} report formats")
        for format_name, content in reports.items():
            if format_name == "error":
                print(f"  - {format_name}: {content}")
            else:
                print(f"  - {format_name}: {len(str(content))} chars")
        
        return reports
        
    except Exception as e:
        print(f"❌ Error in report generation: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

if __name__ == "__main__":
    test_report_generator()
