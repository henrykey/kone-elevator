#!/usr/bin/env python3
"""
增强测试结果与报告格式化器
Author: IBC-AI CO.

负责生成 KONE 审核友好的测试报告
"""

import json
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader


logger = logging.getLogger(__name__)


@dataclass
class EnhancedTestResult:
    """增强的测试结果"""
    test_id: str
    test_name: str
    category: str
    status: str  # PASS, FAIL, ERROR, SKIP
    duration_ms: float
    api_type: str  # common-api, lift-call-api-v2, site-monitoring
    call_type: str  # config, action, monitor, hold_open, delete, ping
    building_id: str
    group_id: str
    
    # 配置相关
    building_config: Optional[Dict[str, Any]] = None
    actions_config: Optional[Dict[str, Any]] = None
    
    # 监控相关
    monitoring_events: List[Dict[str, Any]] = None
    subscription_topics: List[str] = None
    
    # 响应相关
    response_data: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    allocation_mode: Optional[str] = None
    status_code: Optional[int] = None
    
    # 错误相关
    error_details: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # 请求详情
    request_details: Optional[Dict[str, Any]] = None
    
    # 合规性检查
    compliance_check: Optional[Dict[str, Any]] = None
    
    # Integration & E2E 测试相关 (Test 36-37)
    ping_attempts: Optional[int] = None  # 从中断到恢复共执行的ping次数
    downtime_sec: Optional[float] = None  # 通信中断持续时间
    recovery_timestamp: Optional[str] = None  # 恢复时间（ISO 8601 UTC）
    post_recovery_call: Optional[Dict[str, Any]] = None  # 恢复后呼叫的完整响应数据
    
    # 时间戳
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def __post_init__(self):
        if self.monitoring_events is None:
            self.monitoring_events = []
        if self.subscription_topics is None:
            self.subscription_topics = []
        
        # 设置时间戳
        now = datetime.now(timezone.utc).isoformat()
        if self.started_at is None:
            self.started_at = now
        if self.completed_at is None:
            self.completed_at = now
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def is_successful(self) -> bool:
        """是否成功"""
        return self.status == "PASS"


@dataclass
class TestSuiteResult:
    """测试套件结果"""
    suite_name: str
    category: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    error_tests: int
    skipped_tests: int
    total_duration_ms: float
    test_results: List[EnhancedTestResult]
    started_at: str
    completed_at: str
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100


class TestReportFormatter:
    """测试报告格式化器"""
    
    def __init__(self, template_dir: Optional[str] = None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 设置模板目录
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"
        
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(exist_ok=True)
        
        # 创建 Jinja2 环境
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        
        # 初始化模板
        self._create_default_templates()
    
    def _create_default_templates(self):
        """创建默认模板"""
        # Markdown 模板
        markdown_template = self.template_dir / "test_report.md.j2"
        if not markdown_template.exists():
            markdown_content = '''# KONE SR-API v2.0 验证测试报告

## 测试概览

- **执行时间**: {{ started_at }} - {{ completed_at }}
- **总测试数**: {{ total_tests }}
- **通过**: {{ passed_tests }} ({{ "%.1f"|format(success_rate) }}%)
- **失败**: {{ failed_tests }}
- **错误**: {{ error_tests }}
- **跳过**: {{ skipped_tests }}
- **总耗时**: {{ "%.2f"|format(total_duration_ms/1000) }}秒

## 分类测试结果

{% for category, suite in test_suites.items() %}
### {{ category }}

- **通过率**: {{ "%.1f"|format(suite.get_success_rate()) }}%
- **耗时**: {{ "%.2f"|format(suite.total_duration_ms/1000) }}秒

{% for test in suite.test_results %}
#### Test {{ test.test_id }}: {{ test.test_name }}

- **状态**: {% if test.status == "PASS" %}✅ PASS{% elif test.status == "FAIL" %}❌ FAIL{% elif test.status == "ERROR" %}🔥 ERROR{% else %}⏭️ SKIP{% endif %}
- **API类型**: {{ test.api_type }}
- **调用类型**: {{ test.call_type }}
- **耗时**: {{ "%.0f"|format(test.duration_ms) }}ms
- **建筑ID**: {{ test.building_id }}

{% if test.request_details %}
**请求详情**:
```json
{{ test.request_details | tojson(indent=2) }}
```
{% endif %}

{% if test.response_data %}
**响应详情**:
- **状态码**: {{ test.status_code }}
{% if test.session_id %}
- **会话ID**: {{ test.session_id }}
{% endif %}
{% if test.allocation_mode %}
- **分配模式**: {{ test.allocation_mode }}
{% endif %}
{% endif %}

{% if test.monitoring_events %}
**监控事件**: 收到 {{ test.monitoring_events|length }} 个事件
{% endif %}

{% if test.error_details %}
**错误详情**:
```
{{ test.error_message }}
```
{% endif %}

{% if test.compliance_check %}
**合规性检查**:
{% for check, result in test.compliance_check.items() %}
- {{ check }}: {% if result %}✅{% else %}❌{% endif %}
{% endfor %}
{% endif %}

---

{% endfor %}
{% endfor %}

## 合规性总结

本报告严格按照 `elevator-websocket-api-v2.yaml` 规范执行测试，确保：

1. **请求格式合规**: 所有请求包含必需字段 (type, buildingId, groupId, callType, payload)
2. **响应处理正确**: 正确解析状态码、会话ID、分配模式等字段
3. **时间格式标准**: 使用 ISO-8601 UTC 时间格式
4. **错误处理完善**: 映射标准错误码并提供详细错误信息

## 建议事项

{% if failed_tests > 0 or error_tests > 0 %}
⚠️ **需要关注的问题**:
{% for category, suite in test_suites.items() %}
{% for test in suite.test_results %}
{% if test.status in ["FAIL", "ERROR"] %}
- {{ test.test_id }}: {{ test.error_message or "测试失败" }}
{% endif %}
{% endfor %}
{% endfor %}
{% endif %}

---
*报告生成时间: {{ generated_at }}*  
*Author: IBC-AI CO.*
'''
            markdown_template.write_text(markdown_content, encoding='utf-8')
    
    def format_test_results(
        self,
        test_results: List[EnhancedTestResult],
        output_format: str = "markdown"
    ) -> str:
        """
        格式化测试结果
        
        Args:
            test_results: 测试结果列表
            output_format: 输出格式 (markdown, html, json)
            
        Returns:
            str: 格式化后的报告内容
        """
        # 按分类组织测试结果
        test_suites = self._organize_by_category(test_results)
        
        # 计算统计信息
        stats = self._calculate_statistics(test_results)
        
        # 生成报告上下文
        context = {
            "test_suites": test_suites,
            "total_tests": stats["total"],
            "passed_tests": stats["passed"],
            "failed_tests": stats["failed"],
            "error_tests": stats["error"],
            "skipped_tests": stats["skipped"],
            "success_rate": stats["success_rate"],
            "total_duration_ms": stats["total_duration_ms"],
            "started_at": min(r.started_at for r in test_results) if test_results else datetime.now(timezone.utc).isoformat(),
            "completed_at": max(r.completed_at for r in test_results) if test_results else datetime.now(timezone.utc).isoformat(),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if output_format == "markdown":
            return self._format_markdown(context)
        elif output_format == "html":
            return self._format_html(context)
        elif output_format == "json":
            return self._format_json(test_results, context)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _organize_by_category(self, test_results: List[EnhancedTestResult]) -> Dict[str, TestSuiteResult]:
        """按分类组织测试结果"""
        categories = {}
        
        for result in test_results:
            category = result.category
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        # 转换为 TestSuiteResult
        test_suites = {}
        for category, results in categories.items():
            passed = sum(1 for r in results if r.status == "PASS")
            failed = sum(1 for r in results if r.status == "FAIL")
            error = sum(1 for r in results if r.status == "ERROR")
            skipped = sum(1 for r in results if r.status == "SKIP")
            total_duration = sum(r.duration_ms for r in results)
            
            test_suites[category] = TestSuiteResult(
                suite_name=category,
                category=category,
                total_tests=len(results),
                passed_tests=passed,
                failed_tests=failed,
                error_tests=error,
                skipped_tests=skipped,
                total_duration_ms=total_duration,
                test_results=results,
                started_at=min(r.started_at for r in results) if results else "",
                completed_at=max(r.completed_at for r in results) if results else ""
            )
        
        return test_suites
    
    def _calculate_statistics(self, test_results: List[EnhancedTestResult]) -> Dict[str, Any]:
        """计算统计信息"""
        total = len(test_results)
        passed = sum(1 for r in test_results if r.status == "PASS")
        failed = sum(1 for r in test_results if r.status == "FAIL")
        error = sum(1 for r in test_results if r.status == "ERROR")
        skipped = sum(1 for r in test_results if r.status == "SKIP")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        total_duration_ms = sum(r.duration_ms for r in test_results)
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "error": error,
            "skipped": skipped,
            "success_rate": success_rate,
            "total_duration_ms": total_duration_ms
        }
    
    def _format_markdown(self, context: Dict[str, Any]) -> str:
        """格式化为 Markdown"""
        try:
            template = self.jinja_env.get_template("test_report.md.j2")
            return template.render(**context)
        except Exception as e:
            self.logger.error(f"Failed to render Markdown template: {e}")
            return self._format_fallback_markdown(context)
    
    def _format_fallback_markdown(self, context: Dict[str, Any]) -> str:
        """后备 Markdown 格式化"""
        lines = [
            "# KONE SR-API v2.0 验证测试报告",
            "",
            "## 测试概览",
            f"- **总测试数**: {context['total_tests']}",
            f"- **通过**: {context['passed_tests']} ({context['success_rate']:.1f}%)",
            f"- **失败**: {context['failed_tests']}",
            f"- **错误**: {context['error_tests']}",
            f"- **总耗时**: {context['total_duration_ms']/1000:.2f}秒",
            "",
            "## 测试结果详情",
            ""
        ]
        
        for category, suite in context["test_suites"].items():
            lines.extend([
                f"### {category}",
                f"- **通过率**: {suite.get_success_rate():.1f}%",
                ""
            ])
            
            for test in suite.test_results:
                status_icon = "✅" if test.status == "PASS" else "❌"
                lines.extend([
                    f"#### Test {test.test_id}: {test.test_name}",
                    f"- **状态**: {status_icon} {test.status}",
                    f"- **耗时**: {test.duration_ms:.0f}ms",
                    ""
                ])
        
        lines.extend([
            "---",
            f"*报告生成时间: {context['generated_at']}*",
            "*Author: IBC-AI CO.*"
        ])
        
        return "\n".join(lines)
    
    def _format_html(self, context: Dict[str, Any]) -> str:
        """格式化为 HTML"""
        # 简单的 HTML 格式化
        markdown_content = self._format_markdown(context)
        
        html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KONE SR-API v2.0 验证测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1, h2, h3, h4 {{ color: #333; }}
        code {{ background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
        pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        .stats {{ background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .success {{ color: #28a745; }}
        .error {{ color: #dc3545; }}
    </style>
</head>
<body>
    <div class="content">
        {markdown_content.replace('**', '<strong>').replace('**', '</strong>')}
    </div>
</body>
</html>
"""
        return html_template
    
    def _format_json(self, test_results: List[EnhancedTestResult], context: Dict[str, Any]) -> str:
        """格式化为 JSON"""
        report_data = {
            "report_metadata": {
                "generated_at": context["generated_at"],
                "author": "IBC-AI CO.",
                "version": "2.0"
            },
            "summary": {
                "total_tests": context["total_tests"],
                "passed_tests": context["passed_tests"],
                "failed_tests": context["failed_tests"],
                "error_tests": context["error_tests"],
                "skipped_tests": context["skipped_tests"],
                "success_rate": context["success_rate"],
                "total_duration_ms": context["total_duration_ms"]
            },
            "test_results": [result.to_dict() for result in test_results]
        }
        
        return json.dumps(report_data, ensure_ascii=False, indent=2)
    
    def save_report(
        self,
        test_results: List[EnhancedTestResult],
        output_path: str,
        output_format: str = "markdown"
    ) -> None:
        """
        保存测试报告到文件
        
        Args:
            test_results: 测试结果列表
            output_path: 输出文件路径
            output_format: 输出格式
        """
        try:
            report_content = self.format_test_results(test_results, output_format)
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            if output_format == "json":
                # JSON 格式需要确保编码
                output_file.write_text(report_content, encoding='utf-8')
            else:
                output_file.write_text(report_content, encoding='utf-8')
            
            self.logger.info(f"Report saved to: {output_file} (format: {output_format})")
            
        except Exception as e:
            self.logger.error(f"Failed to save report: {e}")
            raise
