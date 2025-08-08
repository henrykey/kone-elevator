# Author: IBC-AI CO.
"""
KONE 测试报告生成器
负责生成多种格式的测试报告：Markdown、JSON、HTML、Excel
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass

# Optional Excel support
try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

# Optional Jinja2 support - fallback to string templates
try:
    from jinja2 import Template
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """测试结果数据结构 - 符合KONE测试指南格式"""
    test_id: str  # Test编号 (如 "Test 1", "Test 2")
    name: str  # Test名称
    description: str  # Description描述
    expected_result: str  # Expected result期望结果
    test_result: str  # Test result测试结果 (PASS/FAIL/待填写)
    status: str  # 内部状态 (PASS, FAIL, SKIP, ERROR)
    duration_ms: float
    error_message: Optional[str] = None
    response_data: Optional[Dict] = None
    category: Optional[str] = None


class ReportGenerator:
    """
    KONE测试报告生成器
    支持生成符合《KONE Service Robot API Solution Validation Test Guide》格式的多种报告
    包含Setup、Pre-Test Setup、Date等元信息字段
    """
    
    def __init__(self, company_name: str = "IBC-AI CO."):
        """
        初始化报告生成器
        
        Args:
            company_name: 公司名称
        """
        self.company_name = company_name
        self.report_timestamp = datetime.now()
        
        # 从指南获取的测试用例映射
        self.test_guide_mapping = self._load_test_guide_mapping()
        logger.info(f"ReportGenerator initialized for {company_name}")
    
    def _load_test_guide_mapping(self) -> Dict[str, Dict[str, str]]:
        """加载测试指南中的测试用例映射"""
        return {
            "Test_1": {
                "name": "Solution initialization",
                "description": "Solution initialization",
                "expected_result": "- Connections established by solution to test environment (Virtual or Preproduction).\n- Authentication successful\n- Get resources successful\n- Building config can be obtained.\n- Response code 200\n- Response code 401 in case if there is issue with API Credentials\n- Building actions can be obtained.\n- Response code 200\n- Response code 401 in case if there is issue with API Credentials"
            },
            "Test_2": {
                "name": "Elevator mode check (non-operational)",
                "description": "Is the elevator mode operational or not? Note: elevator mode is set to non-operational. Use if applicable to robot use case",
                "expected_result": "- Elevator mode is true with any of the below\n- Fire mode (FRD)\n- Out of service mode (OSS)\n- Attendant mode (ATS)\n- Priority mode (PRC)\n- call is not made"
            },
            "Test_3": {
                "name": "Elevator mode check (operational)",
                "description": "Is the elevator mode operational or not? Note: elevator is set to operational; Source (any floor) – Destination (any floor)",
                "expected_result": "- Elevator mode is false with all below\n- Fire mode (FRD)\n- Out of service mode (OSS)\n- Attendant mode (ATS)\n- Priority mode (PRC)\n- Call accepted and elevator moving\n- Response code 201\n- Session id returned\n- Elevator destination is correct and as requested"
            },
            "Test_4": {
                "name": "Basic elevator call",
                "description": "Call: Basic call -> Source: any floor, Destination: any floor Note: Landing Call – Source only, Car Call – Destination only",
                "expected_result": "- Call accepted and elevator moving\n- Response code 201\n- Session id returned\n- Elevator tracking\n- Floor markings are as expected\n- Floor order is as expected\n- Elevator destination is correct as requested"
            },
            "Test_5": {
                "name": "Hold open elevator door",
                "description": "Call: hold open elevator door -> at Source floor, at Destination floor Note: Use if applicable to robot use case Landing Call – Source only, Car Call – Destination only",
                "expected_result": "- Elevator door stays open for\n- duration specified in hard time\n- optionally plus duration specified in soft time"
            },
            "Test_6": {
                "name": "Unlisted action call",
                "description": "Call: Action call with action id = 200, 0 [Unlisted action (range as in action payload)] -> Source: any floor, Destination: any floor. Note: Landing Call – Source only, Car Call – Destination only",
                "expected_result": "- Option 1: Illegal call prevented by robot controller\n- Option 2: Call allowed and Call cancelled\n- Response code 201\n- error message - \" Ignoring call, unknown call action: {action id}\"\n- error message - \" Ignoring call, unknown call action: UNDEFINED\" if 0"
            },
            "Test_7": {
                "name": "Mixed action call (first)",
                "description": "Call: Action call with action id = 3, 4 [Mixed action call] -> Source: any floor, Destination: any floor. Note: Landing Call – Source only, Car Call – Destination only",
                "expected_result": "- Option 1: Illegal call prevented by robot controller\n- Option 2: Call allowed and Call cancelled\n- Response code 201\n- error message - \" Ignoring call, unknown call action: {action id}\""
            },
            "Test_8": {
                "name": "Mixed action call (second)",
                "description": "Call: Action call with action id = 3, 4 [Mixed action call] -> Source: any floor, Destination: any floor. Note: Landing Call – Source only, Car Call – Destination only",
                "expected_result": "- Option 1: Illegal call prevented by robot controller\n- Option 2: Call allowed and Call cancelled\n- Response code 201\n- error message - \" Ignoring call, unknown call action: {action id}\""
            },
            "Test_9": {
                "name": "Delay call (valid)",
                "description": "Call: Delay call with delay = 5 -> Source: any floor, Destination: any floor. Note: Landing Call – Source only, Car Call – Destination only",
                "expected_result": "- Call accepted and elevator moving\n- Response code 201\n- Session id returned\n- Elevator tracking\n- Floor markings are as expected\n- Floor order is as expected\n- Elevator destination is correct as requested"
            },
            "Test_10": {
                "name": "Delay call (invalid)",
                "description": "Call: Delay call with delay = 40 -> Source: any floor, Destination: any floor. Note: Landing Call – Source only, Car Call – Destination only",
                "expected_result": "- Call allowed and Call cancelled\n- Response code 201\n- error message - \" Invalid json payload\""
            },
            # 继续其他测试用例映射...
        }
    
    def _get_test_info_from_guide(self, test_id: str) -> Dict[str, str]:
        """从测试指南获取测试信息"""
        guide_info = self.test_guide_mapping.get(test_id, {})
        return {
            "name": guide_info.get("name", "Unknown Test"),
            "description": guide_info.get("description", "To be filled"),
            "expected_result": guide_info.get("expected_result", "Test should execute successfully and return expected results")
        }
    
    def generate_report(self, test_results: List[TestResult], metadata: Dict[str, Any], output_dir: str = ".", config: Dict[str, Any] = None) -> Dict[str, str]:
        """
        生成符合KONE测试指南格式的多格式测试报告
        
        Args:
            test_results: 测试结果列表
            metadata: 测试元数据
            output_dir: 输出目录路径
            config: 配置信息（包含solution provider等）
            
        Returns:
            dict: 包含不同格式报告的字典
        """
        try:
            # 补充缺失的测试用例字段
            enhanced_test_results = self._enhance_test_results(test_results)
            
            # 补充报告元信息
            enhanced_metadata = self._enhance_metadata(metadata)
            
            # 统计测试结果
            stats = self._calculate_statistics(enhanced_test_results)
            
            # 生成报告数据
            report_data = {
                "metadata": enhanced_metadata,
                "statistics": stats,
                "test_results": enhanced_test_results,
                "generation_time": self.report_timestamp.isoformat(),
                "company": self.company_name,
                "config": config or {}
            }
            
            # 生成各种格式的报告
            reports = {
                "markdown": self._generate_markdown_report(report_data),
                "json": self._generate_json_report(report_data),
                "html": self._generate_html_report(report_data),
                "excel": self._generate_excel_report(report_data, output_dir)
            }
            
            logger.info(f"Generated reports in {len(reports)} formats")
            return reports
            
        except Exception as e:
            logger.error(f"Failed to generate reports: {e}")
            return {
                "error": f"Report generation failed: {str(e)}"
            }
    
    def _enhance_test_results(self, test_results: List[TestResult]) -> List[TestResult]:
        """根据测试指南补充测试结果字段"""
        enhanced_results = []
        
        for result in test_results:
            # 从指南获取标准信息
            guide_info = self._get_test_info_from_guide(result.test_id)
            
            # 如果字段缺失，从指南补充
            if not hasattr(result, 'description') or not result.description:
                result.description = guide_info["description"]
            if not hasattr(result, 'expected_result') or not result.expected_result:
                result.expected_result = guide_info["expected_result"]
            if not hasattr(result, 'test_result') or not result.test_result:
                result.test_result = "PASS" if result.status == "PASS" else "FAIL" if result.status == "FAIL" else "待填写"
                
            enhanced_results.append(result)
        
        return enhanced_results
    
    def _enhance_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """补充报告元信息"""
        enhanced = metadata.copy()
        
        # 补充指南要求的字段
        enhanced.setdefault("setup", "Get access to the equipment for testing:\n- Virtual equipment, available in KONE API portal\n- Preproduction equipment, by contacting KONE API Support")
        enhanced.setdefault("pre_test_setup", "Test environments available for the correct KONE API organization.\nBuilding id can be retrieved (/resource endpoint).")
        enhanced.setdefault("date", datetime.now().strftime("%d.%m.%Y"))
        enhanced.setdefault("solution_provider", "IBC-AI CO.")
        enhanced.setdefault("tested_system", "KONE Elevator Control Service")
        enhanced.setdefault("kone_sr_api_version", "v2.0")
        
        return enhanced
    
    def _calculate_statistics(self, test_results: List[TestResult]) -> Dict[str, Any]:
        """
        计算测试统计信息
        
        Args:
            test_results: 测试结果列表
            
        Returns:
            dict: 统计信息
        """
        total_tests = len(test_results)
        passed_tests = len([r for r in test_results if r.status == "PASS"])
        failed_tests = len([r for r in test_results if r.status == "FAIL"])
        error_tests = len([r for r in test_results if r.status == "ERROR"])
        skipped_tests = len([r for r in test_results if r.status == "SKIP"])
        
        total_duration = sum(r.duration_ms for r in test_results)
        avg_duration = total_duration / total_tests if total_tests > 0 else 0
        
        # 按分类统计
        category_stats = {}
        for result in test_results:
            category = result.category or "Unknown"
            if category not in category_stats:
                category_stats[category] = {"total": 0, "passed": 0, "failed": 0}
            
            category_stats[category]["total"] += 1
            if result.status == "PASS":
                category_stats[category]["passed"] += 1
            elif result.status in ["FAIL", "ERROR"]:
                category_stats[category]["failed"] += 1
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "error_tests": error_tests,
            "skipped_tests": skipped_tests,
            "success_rate": round(success_rate, 2),
            "total_duration_ms": total_duration,
            "average_duration_ms": round(avg_duration, 2),
            "category_breakdown": category_stats
        }
    
    def _get_solution_provider_info(self, config):
        """Get solution provider information from config or defaults"""
        provider_info = config.get('solution_provider', {})
        
        return {
            'company_name': provider_info.get('company_name', 'To be filled'),
            'company_address': provider_info.get('company_address', 'To be filled'),
            'contact_person_name': provider_info.get('contact_person_name', 'To be filled'),
            'contact_email': provider_info.get('contact_email', 'To be filled'),
            'contact_phone': provider_info.get('contact_phone', 'To be filled'),
            'tester': provider_info.get('tester', 'Automated Test System')
        }
    
    def _generate_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """
        生成符合KONE测试指南格式的Markdown格式报告
        
        Args:
            report_data: 报告数据
            
        Returns:
            str: Markdown报告内容
        """
        # 直接使用指南格式的模板，不依赖Jinja2
        return self._generate_markdown_simple(report_data)
    
    def _generate_markdown_with_jinja(self, report_data: Dict[str, Any]) -> str:
        """使用Jinja2模板生成Markdown报告"""
        template_str = """# KONE Service Robot API Validation Test Report

**Generated by:** {{ company }}  
**Date:** {{ generation_time }}  
**Test Framework:** {{ metadata.test_framework or "N/A" }}  
**API Version:** {{ metadata.api_version or "N/A" }}

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Tests | {{ statistics.total_tests }} |
| Passed | {{ statistics.passed_tests }} ✅ |
| Failed | {{ statistics.failed_tests }} ❌ |
| Errors | {{ statistics.error_tests }} ⚠️ |
| Skipped | {{ statistics.skipped_tests }} ⏭️ |
| Success Rate | {{ "%.1f"|format(statistics.success_rate) }}% |
| Total Duration | {{ "%.2f"|format(statistics.total_duration_ms / 1000) }} seconds |

---

## Test Results by Category

{% for category, tests in test_results|groupby('category') %}
### {{ category or "Uncategorized" }}

| Test ID | Test Name | Status | Duration (ms) | Error |
|---------|-----------|--------|---------------|-------|
{% for test in tests %}
| {{ test.test_id }} | {{ test.name }} | {{ test.status }} | {{ "%.1f"|format(test.duration_ms) }} | {{ test.error_message or "-" }} |
{% endfor %}

{% endfor %}

---

## Detailed Test Results

{% for test in test_results %}
### {{ test.test_id }}: {{ test.name }}

- **Status:** {{ test.status }}
- **Category:** {{ test.category or "N/A" }}
- **Duration:** {{ "%.2f"|format(test.duration_ms) }} ms
{% if test.error_message %}
- **Error:** {{ test.error_message }}
{% endif %}
{% if test.response_data %}
- **Response Data:** 
```json
{{ test.response_data|tojson(indent=2) }}
```
{% endif %}

{% endfor %}

---

*Report generated by KONE Test Automation System v2.0*  
*{{ company }} - {{ generation_time }}*
"""
        
        template = Template(template_str)
        return template.render(**report_data)
    
    def _generate_markdown_simple(self, report_data: Dict[str, Any]) -> str:
        """使用简单字符串模板生成符合KONE测试指南格式的Markdown报告"""
        stats = report_data["statistics"]
        metadata = report_data["metadata"]
        config = report_data.get("config", {})
        
        # Get provider info from config
        provider_info = self._get_solution_provider_info(config)
        
        report = f"""# KONE Service Robot API Solution Validation Test Report

**SR-API (Service Robot API)**  
**Version**: 2.0  
**Author**: {report_data["company"]}

---

## Document Purpose

Ensuring the quality and security of a solution is every developer's responsibility. This document gives guidance on evaluating the readiness of those solutions that use Service Robot API.

---

## Test Information

### Setup
{metadata.get("setup", "To be filled")}

### Pre-Test Setup  
{metadata.get("pre_test_setup", "To be filled")}

### Date
| Test Date (dd.mm.yyyy) | Value |
|-------------------------|-------|
| Test execution date     | {metadata.get("date", datetime.now().strftime("%d.%m.%Y"))} |

### Solution Provider
| Item                 | Value |
|----------------------|-------|
| Company name         | {provider_info['company_name']} |
| Company address      | {provider_info['company_address']} |
| Contact person name  | {provider_info['contact_person_name']} |
| Email                | {provider_info['contact_email']} |
| Telephone number     | {provider_info['contact_phone']} |
| Tester               | {provider_info['tester']} |

### Tested System
| Item                     | Value |
|--------------------------|-------|
| System name              | {metadata.get("tested_system", "KONE Elevator Control Service")} |
| System version           | {metadata.get("system_version", "待填写")} |
| Software name            | {metadata.get("software_name", "待填写")} |
| Software version         | {metadata.get("software_version", "待填写")} |
| KONE SR-API              | {metadata.get("kone_sr_api_version", "v2.0")} |
| KONE test assistant email | {metadata.get("kone_assistant_email", "待填写")} |

---

## Test Summary

| Metric | Value |
|--------|-------|
| Total Tests | {stats["total_tests"]} |
| Passed | {stats["passed_tests"]} ✅ |
| Failed | {stats["failed_tests"]} ❌ |
| Errors | {stats["error_tests"]} ⚠️ |
| Skipped | {stats["skipped_tests"]} ⏭️ |
| Success Rate | {stats["success_rate"]}% |
| Total Duration | {stats["total_duration_ms"] / 1000:.2f} seconds |

---

## Service Robot API Solution Validation Test Results

| Test | Description | Expected result | Test result |
|------|-------------|-----------------|-------------|
"""
        
        # 按测试ID排序并添加详细测试结果表格
        sorted_results = sorted(report_data["test_results"], key=lambda x: int(x.test_id.replace("Test_", "")))
        
        for result in sorted_results:
            # 格式化期望结果和测试结果，处理多行文本
            expected_formatted = result.expected_result.replace('\n', '<br>')
            test_result_formatted = result.test_result.replace('\n', '<br>') if hasattr(result, 'test_result') else "待填写"
            
            report += f"| {result.test_id} | {result.description} | {expected_formatted} | {test_result_formatted} |\n"
        
        # 添加建议
        report += "\n---\n\n## Test Analysis and Recommendations\n\n"
        
        if stats["success_rate"] >= 90:
            report += f"✅ **Excellent Performance**: The system demonstrates high reliability with {stats['success_rate']}% success rate.\n"
        elif stats["success_rate"] >= 70:
            report += "⚠️ **Good Performance**: The system shows acceptable performance but may need minor improvements.\n"
        else:
            report += f"❌ **Needs Improvement**: The system requires significant attention with {stats['success_rate']}% success rate.\n"
        
        report += "\n### Key Areas for Improvement:\n"
        for category, cat_stats in stats["category_breakdown"].items():
            if cat_stats["failed"] > 0:
                report += f"- **{category}**: {cat_stats['failed']} failed tests need attention\n"
        
        report += f"\n---\n\n*Report generated on {report_data['generation_time']} by {report_data['company']}*\n"
        
        return report
    
        template_str = """# KONE Service Robot API Validation Test Report

**Generated by:** {{ company }}  
**Date:** {{ generation_time }}  
**Test Framework:** {{ metadata.test_framework }}  
**API Version:** {{ metadata.api_version }}

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Tests | {{ statistics.total_tests }} |
| Passed | {{ statistics.passed_tests }} ✅ |
| Failed | {{ statistics.failed_tests }} ❌ |
| Errors | {{ statistics.error_tests }} ⚠️ |
| Skipped | {{ statistics.skipped_tests }} ⏭️ |
| Success Rate | {{ statistics.success_rate }}% |
| Total Duration | {{ "%.2f"|format(statistics.total_duration_ms / 1000) }} seconds |

---

## Test Environment

- **Building ID:** {{ metadata.building_id or 'Unknown' }}
- **API Endpoint:** {{ metadata.api_base_url or 'http://localhost:8000' }}
- **Test Session:** {{ metadata.test_session_id or 'N/A' }}
- **Company:** {{ company }}

---

## Test Results by Category

{% for category, stats in statistics.category_breakdown.items() %}
### {{ category }}
- Total: {{ stats.total }}
- Passed: {{ stats.passed }} 
- Failed: {{ stats.failed }}
- Success Rate: {{ "%.1f"|format((stats.passed / stats.total * 100) if stats.total > 0 else 0) }}%

{% endfor %}

---

## Detailed Test Results

{% for result in test_results %}
### {{ result.test_id }}: {{ result.name }}

**Status:** {% if result.status == "PASS" %}✅ PASS{% elif result.status == "FAIL" %}❌ FAIL{% elif result.status == "ERROR" %}⚠️ ERROR{% else %}⏭️ SKIP{% endif %}  
**Category:** {{ result.category or 'Unknown' }}  
**Duration:** {{ "%.2f"|format(result.duration_ms) }} ms

{% if result.error_message %}
**Error:** `{{ result.error_message }}`
{% endif %}

{% if result.response_data %}
**Response Data:**
```json
{{ result.response_data | tojson(indent=2) }}
```
{% endif %}

---
{% endfor %}

## Recommendations

{% if statistics.success_rate >= 90 %}
✅ **Excellent Performance**: The system demonstrates high reliability with {{ statistics.success_rate }}% success rate.
{% elif statistics.success_rate >= 70 %}
⚠️ **Good Performance**: The system shows acceptable performance but may need minor improvements.
{% else %}
❌ **Needs Improvement**: The system requires significant attention with {{ statistics.success_rate }}% success rate.
{% endif %}

### Key Areas for Improvement:
{% for category, stats in statistics.category_breakdown.items() %}
{% if stats.failed > 0 %}
- **{{ category }}**: {{ stats.failed }} failed tests need attention
{% endif %}
{% endfor %}

---

*Report generated on {{ generation_time }} by {{ company }}*
"""
        
        template = Template(template_str)
        return template.render(**report_data)
        template_str = """# KONE Service Robot API Validation Test Report

**Generated by:** {{ company }}  
**Date:** {{ generation_time }}  
**Test Framework:** {{ metadata.test_framework }}  
**API Version:** {{ metadata.api_version }}

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Tests | {{ statistics.total_tests }} |
| Passed | {{ statistics.passed_tests }} ✅ |
| Failed | {{ statistics.failed_tests }} ❌ |
| Errors | {{ statistics.error_tests }} ⚠️ |
| Skipped | {{ statistics.skipped_tests }} ⏭️ |
| Success Rate | {{ statistics.success_rate }}% |
| Total Duration | {{ "%.2f"|format(statistics.total_duration_ms / 1000) }} seconds |

---

## Test Environment

- **Building ID:** {{ metadata.building_id or 'Unknown' }}
- **API Endpoint:** {{ metadata.api_base_url or 'http://localhost:8000' }}
- **Test Session:** {{ metadata.test_session_id or 'N/A' }}
- **Company:** {{ company }}

---

## Test Results by Category

{% for category, stats in statistics.category_breakdown.items() %}
### {{ category }}
- Total: {{ stats.total }}
- Passed: {{ stats.passed }} 
- Failed: {{ stats.failed }}
- Success Rate: {{ "%.1f"|format((stats.passed / stats.total * 100) if stats.total > 0 else 0) }}%

{% endfor %}

---

## Detailed Test Results

{% for result in test_results %}
### {{ result.test_id }}: {{ result.name }}

**Status:** {% if result.status == "PASS" %}✅ PASS{% elif result.status == "FAIL" %}❌ FAIL{% elif result.status == "ERROR" %}⚠️ ERROR{% else %}⏭️ SKIP{% endif %}  
**Category:** {{ result.category or 'Unknown' }}  
**Duration:** {{ "%.2f"|format(result.duration_ms) }} ms

{% if result.error_message %}
**Error:** `{{ result.error_message }}`
{% endif %}

{% if result.response_data %}
**Response Data:**
```json
{{ result.response_data | tojson(indent=2) }}
```
{% endif %}

---
{% endfor %}

## Recommendations

{% if statistics.success_rate >= 90 %}
✅ **Excellent Performance**: The system demonstrates high reliability with {{ statistics.success_rate }}% success rate.
{% elif statistics.success_rate >= 70 %}
⚠️ **Good Performance**: The system shows acceptable performance but may need minor improvements.
{% else %}
❌ **Needs Improvement**: The system requires significant attention with {{ statistics.success_rate }}% success rate.
{% endif %}

### Key Areas for Improvement:
{% for category, stats in statistics.category_breakdown.items() %}
{% if stats.failed > 0 %}
- **{{ category }}**: {{ stats.failed }} failed tests need attention
{% endif %}
{% endfor %}

---

*Report generated on {{ generation_time }} by {{ company }}*
"""
        
        template = Template(template_str)
        return template.render(**report_data)
    
    def _generate_json_report(self, report_data: Dict[str, Any]) -> str:
        """
        生成符合KONE测试指南格式的JSON格式报告
        
        Args:
            report_data: 报告数据
            
        Returns:
            str: JSON报告内容
        """
        # 转换TestResult对象为符合指南格式的字典
        json_data = {
            "document_info": {
                "title": "KONE Service Robot API Solution Validation Test Report",
                "sr_api_version": "2.0",
                "author": report_data["company"],
                "generation_time": report_data["generation_time"],
                "report_version": "1.0"
            },
            "setup": {
                "setup_description": report_data["metadata"].get("setup", "待填写"),
                "pre_test_setup": report_data["metadata"].get("pre_test_setup", "待填写")
            },
            "test_information": {
                "date": report_data["metadata"].get("date", "待填写"),
                "solution_provider": {
                    "company_name": report_data["metadata"].get("solution_provider", "IBC-AI CO."),
                    "company_address": report_data["metadata"].get("company_address", "待填写"),
                    "contact_person_name": report_data["metadata"].get("contact_person", "待填写"),
                    "email": report_data["metadata"].get("contact_email", "待填写"),
                    "telephone_number": report_data["metadata"].get("contact_phone", "待填写"),
                    "tester": report_data["metadata"].get("tester", "待填写")
                },
                "tested_system": {
                    "system_name": report_data["metadata"].get("tested_system", "KONE Elevator Control Service"),
                    "system_version": report_data["metadata"].get("system_version", "待填写"),
                    "software_name": report_data["metadata"].get("software_name", "待填写"),
                    "software_version": report_data["metadata"].get("software_version", "待填写"),
                    "kone_sr_api": report_data["metadata"].get("kone_sr_api_version", "v2.0"),
                    "kone_test_assistant_email": report_data["metadata"].get("kone_assistant_email", "待填写")
                }
            },
            "test_summary": report_data["statistics"],
            "test_results": [
                {
                    "test": result.test_id,
                    "description": getattr(result, 'description', '待填写'),
                    "expected_result": getattr(result, 'expected_result', '待填写'),
                    "test_result": getattr(result, 'test_result', '待填写'),
                    "status": result.status,
                    "duration_ms": result.duration_ms,
                    "error_message": result.error_message,
                    "response_data": result.response_data,
                    "category": result.category
                }
                for result in sorted(report_data["test_results"], key=lambda x: int(x.test_id.replace("Test_", "")))
            ]
        }
        
        return json.dumps(json_data, indent=2, ensure_ascii=False)
    
    def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """
        生成HTML格式报告
        
        Args:
            report_data: 报告数据
            
        Returns:
            str: HTML报告内容
        """
        template_str = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KONE API Validation Test Report</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            border-bottom: 3px solid #0066cc;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #0066cc;
            margin: 0;
        }
        .meta-info {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-card.success { background: linear-gradient(135deg, #4CAF50, #45a049); }
        .stat-card.failure { background: linear-gradient(135deg, #f44336, #da190b); }
        .stat-card.warning { background: linear-gradient(135deg, #ff9800, #e68900); }
        
        .test-result {
            border: 1px solid #ddd;
            margin: 10px 0;
            border-radius: 5px;
            overflow: hidden;
        }
        .test-header {
            padding: 15px;
            font-weight: bold;
            cursor: pointer;
        }
        .test-header.pass { background: #d4edda; color: #155724; }
        .test-header.fail { background: #f8d7da; color: #721c24; }
        .test-header.error { background: #fff3cd; color: #856404; }
        .test-header.skip { background: #e2e3e5; color: #6c757d; }
        
        .test-details {
            padding: 15px;
            background: #f8f9fa;
            display: none;
        }
        .test-details.show { display: block; }
        
        pre {
            background: #f1f3f4;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }
        
        .progress-bar {
            width: 100%;
            background: #e0e0e0;
            border-radius: 25px;
            overflow: hidden;
            height: 20px;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4CAF50, #45a049);
            transition: width 0.3s ease;
        }
    </style>
    <script>
        function toggleDetails(testId) {
            const details = document.getElementById('details-' + testId);
            details.classList.toggle('show');
        }
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏢 KONE Service Robot API Validation Test Report</h1>
            <p><strong>Generated by:</strong> {{ company }} | <strong>Date:</strong> {{ generation_time }}</p>
        </div>
        
        <div class="meta-info">
            <h3>📋 Test Environment</h3>
            <p><strong>API Version:</strong> {{ metadata.api_version }}</p>
            <p><strong>Test Framework:</strong> {{ metadata.test_framework }}</p>
            <p><strong>Building ID:</strong> {{ metadata.building_id or 'Unknown' }}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>{{ statistics.total_tests }}</h3>
                <p>Total Tests</p>
            </div>
            <div class="stat-card success">
                <h3>{{ statistics.passed_tests }}</h3>
                <p>Passed ✅</p>
            </div>
            <div class="stat-card failure">
                <h3>{{ statistics.failed_tests + statistics.error_tests }}</h3>
                <p>Failed ❌</p>
            </div>
            <div class="stat-card">
                <h3>{{ statistics.success_rate }}%</h3>
                <p>Success Rate</p>
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill" style="width: {{ statistics.success_rate }}%"></div>
        </div>
        
        <h3>📊 Test Results</h3>
        {% for result in test_results %}
        <div class="test-result">
            <div class="test-header {{ result.status.lower() }}" onclick="toggleDetails('{{ result.test_id }}')">
                {{ result.test_id }}: {{ result.name }}
                <span style="float: right;">
                    {% if result.status == "PASS" %}✅{% elif result.status == "FAIL" %}❌{% elif result.status == "ERROR" %}⚠️{% else %}⏭️{% endif %}
                    {{ result.status }}
                </span>
            </div>
            <div id="details-{{ result.test_id }}" class="test-details">
                <p><strong>Category:</strong> {{ result.category or 'Unknown' }}</p>
                <p><strong>Duration:</strong> {{ "%.2f"|format(result.duration_ms) }} ms</p>
                {% if result.error_message %}
                <p><strong>Error:</strong> {{ result.error_message }}</p>
                {% endif %}
                {% if result.response_data %}
                <p><strong>Response Data:</strong></p>
                <pre>{{ result.response_data | tojson(indent=2) }}</pre>
                {% endif %}
            </div>
        </div>
        {% endfor %}
        
        <div class="meta-info" style="margin-top: 30px;">
            <h3>💡 Recommendations</h3>
            {% if statistics.success_rate >= 90 %}
            <p>✅ <strong>Excellent Performance:</strong> The system demonstrates high reliability with {{ statistics.success_rate }}% success rate.</p>
            {% elif statistics.success_rate >= 70 %}
            <p>⚠️ <strong>Good Performance:</strong> The system shows acceptable performance but may need minor improvements.</p>
            {% else %}
            <p>❌ <strong>Needs Improvement:</strong> The system requires significant attention with {{ statistics.success_rate }}% success rate.</p>
            {% endif %}
        </div>
        
        <footer style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666;">
            <p>Report generated on {{ generation_time }} by {{ company }}</p>
        </footer>
    </div>
</body>
</html>"""
        
        template = Template(template_str)
        return template.render(**report_data)
    
    def _generate_excel_report(self, report_data: Dict[str, Any], output_dir: str = ".") -> str:
        """
        生成符合KONE测试指南格式的Excel格式报告
        
        Args:
            report_data: 报告数据
            output_dir: 输出目录路径
            
        Returns:
            str: Excel文件路径或错误信息
        """
        if not EXCEL_AVAILABLE:
            return "Excel generation not available - openpyxl package not installed"
        
        try:
            # 创建工作簿
            wb = openpyxl.Workbook()
            
            # 设置样式
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            center_align = Alignment(horizontal="center", vertical="center")
            border = Border(left=Side(style='thin'), right=Side(style='thin'), 
                          top=Side(style='thin'), bottom=Side(style='thin'))
            
            # 主报告工作表 - 符合测试指南格式
            ws_main = wb.active
            ws_main.title = "Test Report"
            
            # 添加标题
            ws_main['A1'] = "KONE Service Robot API Solution Validation Test Report"
            ws_main['A1'].font = Font(bold=True, size=16)
            ws_main.merge_cells('A1:D1')
            
            # 添加文档信息
            current_row = 3
            ws_main[f'A{current_row}'] = "SR-API (Service Robot API)"
            ws_main[f'A{current_row+1}'] = "Version: 2.0"
            ws_main[f'A{current_row+2}'] = f"Author: {report_data['company']}"
            current_row += 5
            
            # 添加测试信息部分
            metadata = report_data["metadata"]
            
            # Setup信息
            ws_main[f'A{current_row}'] = "Setup"
            ws_main[f'A{current_row}'].font = header_font
            ws_main[f'A{current_row}'].fill = header_fill
            current_row += 1
            ws_main[f'A{current_row}'] = metadata.get("setup", "待填写")
            current_row += 3
            
            # Pre-Test Setup
            ws_main[f'A{current_row}'] = "Pre-Test Setup"
            ws_main[f'A{current_row}'].font = header_font
            ws_main[f'A{current_row}'].fill = header_fill
            current_row += 1
            ws_main[f'A{current_row}'] = metadata.get("pre_test_setup", "待填写")
            current_row += 3
            
            # Date
            ws_main[f'A{current_row}'] = "Date"
            ws_main[f'B{current_row}'] = "Value"
            ws_main[f'A{current_row}'].font = header_font
            ws_main[f'B{current_row}'].font = header_font
            ws_main[f'A{current_row}'].fill = header_fill
            ws_main[f'B{current_row}'].fill = header_fill
            current_row += 1
            ws_main[f'A{current_row}'] = "Test Date (dd.mm.yyyy)"
            ws_main[f'B{current_row}'] = metadata.get("date", datetime.now().strftime("%d.%m.%Y"))
            current_row += 3
            
            # Solution Provider
            ws_main[f'A{current_row}'] = "Solution Provider"
            ws_main[f'B{current_row}'] = "Value"
            ws_main[f'A{current_row}'].font = header_font
            ws_main[f'B{current_row}'].font = header_font
            ws_main[f'A{current_row}'].fill = header_fill
            ws_main[f'B{current_row}'].fill = header_fill
            current_row += 1
            
            provider_info = [
                ("Company name", metadata.get("solution_provider", "IBC-AI CO.")),
                ("Company address", metadata.get("company_address", "待填写")),
                ("Contact person name", metadata.get("contact_person", "待填写")),
                ("Email", metadata.get("contact_email", "待填写")),
                ("Telephone number", metadata.get("contact_phone", "待填写")),
                ("Tester", metadata.get("tester", "待填写"))
            ]
            
            for item, value in provider_info:
                ws_main[f'A{current_row}'] = item
                ws_main[f'B{current_row}'] = value
                current_row += 1
            current_row += 2
            
            # Tested System
            ws_main[f'A{current_row}'] = "Tested System"
            ws_main[f'B{current_row}'] = "Value"
            ws_main[f'A{current_row}'].font = header_font
            ws_main[f'B{current_row}'].font = header_font
            ws_main[f'A{current_row}'].fill = header_fill
            ws_main[f'B{current_row}'].fill = header_fill
            current_row += 1
            
            system_info = [
                ("System name", metadata.get("tested_system", "KONE Elevator Control Service")),
                ("System version", metadata.get("system_version", "待填写")),
                ("Software name", metadata.get("software_name", "待填写")),
                ("Software version", metadata.get("software_version", "待填写")),
                ("KONE SR-API", metadata.get("kone_sr_api_version", "v2.0")),
                ("KONE test assistant email", metadata.get("kone_assistant_email", "待填写"))
            ]
            
            for item, value in system_info:
                ws_main[f'A{current_row}'] = item
                ws_main[f'B{current_row}'] = value
                current_row += 1
            current_row += 3
            
            # 测试结果表格
            ws_main[f'A{current_row}'] = "Service Robot API Solution Validation Test Results"
            ws_main[f'A{current_row}'].font = Font(bold=True, size=14)
            current_row += 2
            
            # 表头
            headers = ["Test", "Description", "Expected result", "Test result"]
            for col, header in enumerate(headers, start=1):
                cell = ws_main.cell(row=current_row, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_align
                cell.border = border
            current_row += 1
            
            # 添加测试结果数据 - 按测试ID排序
            sorted_results = sorted(report_data["test_results"], key=lambda x: int(x.test_id.replace("Test_", "")))
            
            for result in sorted_results:
                ws_main.cell(row=current_row, column=1, value=result.test_id).border = border
                ws_main.cell(row=current_row, column=2, value=getattr(result, 'description', '待填写')).border = border
                ws_main.cell(row=current_row, column=3, value=getattr(result, 'expected_result', '待填写')).border = border
                ws_main.cell(row=current_row, column=4, value=getattr(result, 'test_result', '待填写')).border = border
                
                # 根据状态设置行颜色
                if result.status == "PASS":
                    fill = PatternFill(start_color="C8E6C9", end_color="C8E6C9", fill_type="solid")
                elif result.status == "FAIL":
                    fill = PatternFill(start_color="FFCDD2", end_color="FFCDD2", fill_type="solid")
                else:
                    fill = PatternFill(start_color="FFF3E0", end_color="FFF3E0", fill_type="solid")
                
                for col in range(1, 5):
                    ws_main.cell(row=current_row, column=col).fill = fill
                
                current_row += 1
            
            # 创建统计汇总工作表
            ws_summary = wb.create_sheet(title="Test Summary")
            
            # 统计信息
            stats = report_data["statistics"]
            summary_data = [
                ("Total Tests", stats["total_tests"]),
                ("Passed Tests", stats["passed_tests"]),
                ("Failed Tests", stats["failed_tests"]),
                ("Error Tests", stats["error_tests"]),
                ("Skipped Tests", stats["skipped_tests"]),
                ("Success Rate (%)", stats["success_rate"]),
                ("Total Duration (ms)", stats["total_duration_ms"]),
                ("Average Duration (ms)", stats["average_duration_ms"])
            ]
            
            ws_summary['A1'] = "Test Statistics"
            ws_summary['A1'].font = Font(bold=True, size=14)
            
            for i, (key, value) in enumerate(summary_data, start=3):
                ws_summary[f'A{i}'] = key
                ws_summary[f'B{i}'] = value
            
            # 自动调整列宽
            for ws in [ws_main, ws_summary]:
                for column in ws.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
            # 简化列宽处理 - 直接设置而不遍历列
            try:
                # 为主报告工作表设置列宽
                ws_main.column_dimensions['A'].width = 15  # Test列
                ws_main.column_dimensions['B'].width = 40  # Description列  
                ws_main.column_dimensions['C'].width = 50  # Expected result列
                ws_main.column_dimensions['D'].width = 20  # Test result列
                
                # 为统计工作表设置列宽
                ws_summary.column_dimensions['A'].width = 25  # 统计项目
                ws_summary.column_dimensions['B'].width = 15  # 数值
            except Exception as e:
                logger.warning(f"Column width adjustment failed: {e}")
            
            # 保存文件
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"KONE_Validation_Report_{timestamp}.xlsx"
            filepath = output_path / filename
            
            wb.save(str(filepath))
            
            logger.info(f"Excel report saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to generate Excel report: {e}")
            return f"Excel generation failed: {str(e)}"
    
    def save_reports_to_files(self, reports: Dict[str, str], base_filename: str) -> Dict[str, str]:
        """
        将报告保存到文件
        
        Args:
            reports: 报告字典
            base_filename: 基础文件名
            
        Returns:
            dict: 保存的文件路径字典
        """
        saved_files = {}
        
        try:
            reports_dir = Path("./reports")
            reports_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 保存各种格式的报告
            if "markdown" in reports:
                md_filename = f"{base_filename}_{timestamp}.md"
                md_filepath = reports_dir / md_filename
                with open(md_filepath, 'w', encoding='utf-8') as f:
                    f.write(reports["markdown"])
                saved_files["markdown"] = str(md_filepath)
                logger.info(f"Markdown report saved: {md_filepath}")
            
            if "json" in reports:
                json_filename = f"{base_filename}_{timestamp}.json"
                json_filepath = reports_dir / json_filename
                with open(json_filepath, 'w', encoding='utf-8') as f:
                    f.write(reports["json"])
                saved_files["json"] = str(json_filepath)
                logger.info(f"JSON report saved: {json_filepath}")
            
            if "html" in reports:
                html_filename = f"{base_filename}_{timestamp}.html"
                html_filepath = reports_dir / html_filename
                with open(html_filepath, 'w', encoding='utf-8') as f:
                    f.write(reports["html"])
                saved_files["html"] = str(html_filepath)
                logger.info(f"HTML report saved: {html_filepath}")
            
            # Excel文件路径已在_generate_excel_report中处理
            if "excel" in reports and not reports["excel"].startswith("Excel generation"):
                saved_files["excel"] = reports["excel"]
            
            return saved_files
            
        except Exception as e:
            logger.error(f"Failed to save reports: {e}")
            return {"error": f"File saving failed: {str(e)}"}
