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
    """测试结果数据结构"""
    test_id: str
    name: str
    status: str  # PASS, FAIL, SKIP, ERROR
    duration_ms: float
    error_message: Optional[str] = None
    response_data: Optional[Dict] = None
    category: Optional[str] = None


class ReportGenerator:
    """
    KONE测试报告生成器
    支持生成Markdown、JSON、HTML、Excel格式的测试报告
    """
    
    def __init__(self, company_name: str = "IBC-AI CO."):
        """
        初始化报告生成器
        
        Args:
            company_name: 公司名称
        """
        self.company_name = company_name
        self.report_timestamp = datetime.now()
        logger.info(f"ReportGenerator initialized for {company_name}")
    
    def generate_report(self, test_results: List[TestResult], metadata: Dict[str, Any], output_dir: str = ".") -> Dict[str, str]:
        """
        生成多格式测试报告
        
        Args:
            test_results: 测试结果列表
            metadata: 测试元数据
            output_dir: 输出目录路径
            
        Returns:
            dict: 包含不同格式报告的字典
        """
        try:
            # 统计测试结果
            stats = self._calculate_statistics(test_results)
            
            # 生成报告数据
            report_data = {
                "metadata": metadata,
                "statistics": stats,
                "test_results": test_results,
                "generation_time": self.report_timestamp.isoformat(),
                "company": self.company_name
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
    
    def _generate_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """
        生成Markdown格式报告
        
        Args:
            report_data: 报告数据
            
        Returns:
            str: Markdown报告内容
        """
        if JINJA2_AVAILABLE:
            return self._generate_markdown_with_jinja(report_data)
        else:
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
        """使用简单字符串模板生成Markdown报告"""
        stats = report_data["statistics"]
        metadata = report_data["metadata"]
        
        report = f"""# KONE Service Robot API Validation Test Report

**Generated by:** {report_data["company"]}  
**Date:** {report_data["generation_time"]}  
**Test Framework:** {metadata.get("test_framework", "N/A")}  
**API Version:** {metadata.get("api_version", "N/A")}

---

## Executive Summary

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

## Test Environment

- **Building ID:** {metadata.get("building_id", "Unknown")}
- **API Endpoint:** {metadata.get("api_base_url", "http://localhost:8000")}
- **Test Session:** {metadata.get("test_session_id", "N/A")}
- **Company:** {report_data["company"]}

---

## Test Results by Category

"""
        
        # 添加分类统计
        for category, cat_stats in stats["category_breakdown"].items():
            success_rate = (cat_stats["passed"] / cat_stats["total"] * 100) if cat_stats["total"] > 0 else 0
            report += f"""### {category}
- Total: {cat_stats["total"]}
- Passed: {cat_stats["passed"]} 
- Failed: {cat_stats["failed"]}
- Success Rate: {success_rate:.1f}%

"""
        
        report += "\n---\n\n## Detailed Test Results\n\n"
        
        # 添加详细测试结果
        for result in report_data["test_results"]:
            status_icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "⚠️", "SKIP": "⏭️"}.get(result.status, "❓")
            
            report += f"""### {result.test_id}: {result.name}

**Status:** {status_icon} {result.status}  
**Category:** {result.category or 'Unknown'}  
**Duration:** {result.duration_ms:.2f} ms

"""
            
            if result.error_message:
                report += f"**Error:** `{result.error_message}`\n\n"
            
            if result.response_data:
                report += f"**Response Data:**\n```json\n{json.dumps(result.response_data, indent=2)}\n```\n\n"
            
            report += "---\n"
        
        # 添加建议
        report += "\n## Recommendations\n\n"
        
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
        生成JSON格式报告
        
        Args:
            report_data: 报告数据
            
        Returns:
            str: JSON报告内容
        """
        # 转换TestResult对象为字典
        json_data = {
            "report_info": {
                "company": report_data["company"],
                "generation_time": report_data["generation_time"],
                "report_version": "1.0"
            },
            "metadata": report_data["metadata"],
            "statistics": report_data["statistics"],
            "test_results": [
                {
                    "test_id": result.test_id,
                    "name": result.name,
                    "status": result.status,
                    "duration_ms": result.duration_ms,
                    "error_message": result.error_message,
                    "response_data": result.response_data,
                    "category": result.category
                }
                for result in report_data["test_results"]
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
        生成Excel格式报告
        
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
            
            # 概要工作表
            ws_summary = wb.active
            ws_summary.title = "Summary"
            
            # 添加标题
            ws_summary['A1'] = "KONE Service Robot API Validation Test Report"
            ws_summary['A1'].font = Font(bold=True, size=16)
            ws_summary.merge_cells('A1:E1')
            
            # 添加元数据
            ws_summary['A3'] = "Report Information"
            ws_summary['A3'].font = header_font
            ws_summary['A3'].fill = header_fill
            
            metadata_rows = [
                ("Company", report_data["company"]),
                ("Generation Time", report_data["generation_time"]),
                ("API Version", report_data["metadata"].get("api_version", "N/A")),
                ("Test Framework", report_data["metadata"].get("test_framework", "N/A")),
                ("Building ID", report_data["metadata"].get("building_id", "N/A"))
            ]
            
            for i, (key, value) in enumerate(metadata_rows, start=4):
                ws_summary[f'A{i}'] = key
                ws_summary[f'B{i}'] = value
            
            # 添加统计信息
            stats_start_row = len(metadata_rows) + 6
            ws_summary[f'A{stats_start_row}'] = "Test Statistics"
            ws_summary[f'A{stats_start_row}'].font = header_font
            ws_summary[f'A{stats_start_row}'].fill = header_fill
            
            stats = report_data["statistics"]
            stats_rows = [
                ("Total Tests", stats["total_tests"]),
                ("Passed Tests", stats["passed_tests"]),
                ("Failed Tests", stats["failed_tests"]),
                ("Error Tests", stats["error_tests"]),
                ("Skipped Tests", stats["skipped_tests"]),
                ("Success Rate (%)", stats["success_rate"]),
                ("Total Duration (ms)", stats["total_duration_ms"]),
                ("Average Duration (ms)", stats["average_duration_ms"])
            ]
            
            for i, (key, value) in enumerate(stats_rows, start=stats_start_row + 1):
                ws_summary[f'A{i}'] = key
                ws_summary[f'B{i}'] = value
            
            # 详细结果工作表
            ws_details = wb.create_sheet(title="Test Details")
            
            # 添加表头
            headers = ["Test ID", "Test Name", "Status", "Category", "Duration (ms)", "Error Message"]
            for col, header in enumerate(headers, start=1):
                cell = ws_details.cell(row=1, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_align
                cell.border = border
            
            # 添加测试结果数据
            for row, result in enumerate(report_data["test_results"], start=2):
                ws_details.cell(row=row, column=1, value=result.test_id).border = border
                ws_details.cell(row=row, column=2, value=result.name).border = border
                ws_details.cell(row=row, column=3, value=result.status).border = border
                ws_details.cell(row=row, column=4, value=result.category or "Unknown").border = border
                ws_details.cell(row=row, column=5, value=result.duration_ms).border = border
                ws_details.cell(row=row, column=6, value=result.error_message or "").border = border
                
                # 根据状态设置行颜色
                status_colors = {
                    "PASS": "C8E6C9",
                    "FAIL": "FFCDD2", 
                    "ERROR": "FFF3E0",
                    "SKIP": "F5F5F5"
                }
                
                if result.status in status_colors:
                    fill = PatternFill(start_color=status_colors[result.status], 
                                     end_color=status_colors[result.status], fill_type="solid")
                    for col in range(1, 7):
                        ws_details.cell(row=row, column=col).fill = fill
            
            # 自动调整列宽
            for ws in [ws_summary, ws_details]:
                for column in ws.columns:
                    max_length = 0
                    column_letter = None
                    for cell in column:
                        try:
                            # 跳过合并的单元格
                            if hasattr(cell, 'column_letter'):
                                if column_letter is None:
                                    column_letter = cell.column_letter
                                if cell.value and len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                        except:
                            pass
                    
                    if column_letter:
                        adjusted_width = min(max_length + 2, 50) if max_length > 0 else 15
                        ws.column_dimensions[column_letter].width = adjusted_width
            
            # 保存文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"KONE_Test_Report_{timestamp}.xlsx"
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            filepath = output_path / filename
            wb.save(filepath)
            
            logger.info(f"Excel report saved as {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to generate Excel report: {e}")
            return f"Excel generation failed: {str(e)}"
    
    def save_reports_to_files(self, reports: Dict[str, str], base_filename: str = "KONE_Test_Report") -> Dict[str, str]:
        """
        将报告保存到文件
        
        Args:
            reports: 报告内容字典
            base_filename: 基础文件名
            
        Returns:
            dict: 保存的文件路径字典
        """
        timestamp = self.report_timestamp.strftime("%Y%m%d_%H%M%S")
        saved_files = {}
        
        try:
            # 确保reports目录存在
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            
            # 保存各种格式的报告
            file_extensions = {
                "markdown": ".md",
                "json": ".json", 
                "html": ".html"
            }
            
            for format_name, content in reports.items():
                if format_name in file_extensions:
                    filename = f"{base_filename}_{timestamp}{file_extensions[format_name]}"
                    filepath = reports_dir / filename
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    saved_files[format_name] = str(filepath)
                    logger.info(f"Saved {format_name} report as {filepath}")
                elif format_name == "excel":
                    # Excel文件已经在生成时保存
                    saved_files[format_name] = content
            
            return saved_files
            
        except Exception as e:
            logger.error(f"Failed to save reports: {e}")
            return {"error": str(e)}
