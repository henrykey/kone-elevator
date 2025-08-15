#!/usr/bin/env python3
"""
KONE Service Robot API v2.0 Report Generator
生成符合要求的四宫格验证报告
"""

import json
import yaml
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path


class TestResult:
    """测试结果类 - 与 testall_v2.py 保持一致"""
    def __init__(self, test_id: int, name: str, expected: str):
        self.test_id = test_id
        self.name = name
        self.expected = expected
        self.request = None
        self.observed = []
        self.result = "NA"
        self.reason = ""
        self.start_time = None
        self.end_time = None
        
    def set_request(self, request: Dict[str, Any]):
        """设置请求数据"""
        self.request = request
        
    def add_observation(self, observation: Dict[str, Any]):
        """添加观察到的响应/事件"""
        self.observed.append(observation)
        
    def set_result(self, result: str, reason: str = ""):
        """设置测试结果"""
        self.result = result
        self.reason = reason
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'test_id': self.test_id,
            'name': self.name,
            'expected': self.expected,
            'request': self.request,
            'observed': self.observed,
            'result': self.result,
            'reason': self.reason,
            'duration': (self.end_time - self.start_time) if self.start_time and self.end_time else None
        }


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        self.config = self._load_config(config_path)
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception:
            return {}
    
    def _sanitize_token_info(self, data: Any) -> Any:
        """脱敏处理 - 移除敏感信息"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in ['token', 'secret', 'password', 'key']):
                    if key.lower() == 'access_token':
                        # 仅保留前6位和后4位
                        if isinstance(value, str) and len(value) > 10:
                            sanitized[key] = f"{value[:6]}...{value[-4:]}"
                        else:
                            sanitized[key] = "[REDACTED]"
                    else:
                        sanitized[key] = "[REDACTED]"
                else:
                    sanitized[key] = self._sanitize_token_info(value)
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_token_info(item) for item in data]
        else:
            return data
    
    def _format_json(self, data: Any, max_lines: int = 20) -> str:
        """格式化JSON，限制行数"""
        if data is None:
            return "null"
        
        # 脱敏处理
        sanitized = self._sanitize_token_info(data)
        
        try:
            formatted = json.dumps(sanitized, indent=2, ensure_ascii=False)
            lines = formatted.split('\n')
            
            if len(lines) > max_lines:
                truncated = lines[:max_lines-1] + ['  "...": "truncated"', '}']
                return '\n'.join(truncated)
            
            return formatted
        except Exception:
            return str(sanitized)
    
    def _extract_key_fields(self, observed: List[Dict[str, Any]]) -> str:
        """提取关键字段用于观察结果摘要"""
        key_info = []
        
        for obs in observed:
            phase = obs.get('phase', 'unknown')
            data = obs.get('data', {})
            
            # 提取关键信息
            if phase == 'call_response':
                status = data.get('status')
                session_id = data.get('sessionId')
                error = data.get('error')
                
                if status:
                    key_info.append(f"Status: {status}")
                if session_id:
                    key_info.append(f"Session: {session_id}")
                if error:
                    key_info.append(f"Error: {error}")
                    
            elif phase == 'status_event':
                lift_mode = data.get('payload', {}).get('lift_mode')
                if lift_mode:
                    key_info.append(f"Lift Mode: {lift_mode}")
                    
            elif 'response' in phase:
                status = data.get('status')
                if status:
                    key_info.append(f"{phase.title()}: {status}")
        
        return '; '.join(key_info) if key_info else "No key information extracted"
    
    def generate_markdown_report(self, results: List[TestResult], 
                                building_id: str = "N/A", 
                                group_id: str = "1",
                                ws_endpoint: str = "wss://dev.kone.com/stream-v2") -> str:
        """生成Markdown格式的四宫格报告"""
        
        report_lines = []
        
        # 封面信息
        solution_provider = self.config.get('solution_provider', {})
        kone_config = self.config.get('kone', {})
        
        report_lines.extend([
            "# KONE Service Robot API v2.0 Validation Test Report",
            "",
            "## Test Environment Information",
            "",
            f"**Solution Provider**: {solution_provider.get('company_name', 'N/A')}",
            f"**Contact Person**: {solution_provider.get('contact_person_name', 'N/A')}",
            f"**Contact Email**: {solution_provider.get('contact_email', 'N/A')}",
            f"**Contact Phone**: {solution_provider.get('contact_phone', 'N/A')}",
            f"**Company Address**: {solution_provider.get('company_address', 'N/A')}",
            f"**Tester**: {solution_provider.get('tester', 'Automated Test System')}",
            f"**Version**: {solution_provider.get('version', 'v2.0')}",
            "",
            f"**Test Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"**Building ID**: {building_id}",
            f"**Group ID**: {group_id}",
            f"**WebSocket Endpoint**: {ws_endpoint}",
            f"**Client ID**: {kone_config.get('client_id', '[REDACTED]')}",
            "",
            "---",
            ""
        ])
        
        # 测试摘要
        total = len(results)
        passed = len([r for r in results if r.result == "Pass"])
        failed = len([r for r in results if r.result == "Fail"])
        na = len([r for r in results if r.result == "NA"])
        
        report_lines.extend([
            "## Executive Summary",
            "",
            f"| Metric | Count | Percentage |",
            f"|--------|-------|------------|",
            f"| **Total Tests** | {total} | 100.0% |",
            f"| **Passed** | {passed} | {(passed/total*100):.1f}% |",
            f"| **Failed** | {failed} | {(failed/total*100):.1f}% |",
            f"| **Not Applicable** | {na} | {(na/total*100):.1f}% |",
            "",
            f"**Overall Success Rate**: {(passed/total*100):.1f}%",
            "",
            "---",
            ""
        ])
        
        # 目录
        report_lines.extend([
            "## Table of Contents",
            ""
        ])
        
        for result in results:
            status_emoji = {"Pass": "✅", "Fail": "❌", "NA": "⚠️"}
            emoji = status_emoji.get(result.result, "❓")
            report_lines.append(f"- [{emoji} Test {result.test_id}: {result.name}](#test-{result.test_id})")
        
        report_lines.extend([
            "",
            "---",
            ""
        ])
        
        # 详细测试结果 - 四宫格格式
        for result in results:
            status_emoji = {"Pass": "✅", "Fail": "❌", "NA": "⚠️"}
            emoji = status_emoji.get(result.result, "❓")
            
            report_lines.extend([
                f"## Test {result.test_id}",
                f"### {emoji} {result.name}",
                ""
            ])
            
            # 四宫格表格
            report_lines.extend([
                "| Section | Content |",
                "|---------|---------|"
            ])
            
            # 1. Expected (来自提示词的口径)
            expected_content = result.expected.replace('\n', '<br>').replace('|', '\\|')
            report_lines.append(f"| **Expected** | {expected_content} |")
            
            # 2. Request (JSON原文)
            request_json = self._format_json(result.request, max_lines=15)
            request_content = f"```json\n{request_json}\n```"
            report_lines.append(f"| **Request** | {request_content} |")
            
            # 3. Observed (响应与监控事件节选)
            if result.observed:
                # 提取关键字段摘要
                key_summary = self._extract_key_fields(result.observed)
                
                # 完整观察数据（截断）
                observed_details = []
                for i, obs in enumerate(result.observed[:3]):  # 最多显示3个观察结果
                    phase = obs.get('phase', f'observation_{i}')
                    data_json = self._format_json(obs.get('data'), max_lines=8)
                    observed_details.append(f"**{phase.title()}**:\n```json\n{data_json}\n```")
                
                if len(result.observed) > 3:
                    observed_details.append(f"*... and {len(result.observed) - 3} more observations*")
                
                observed_content = f"**Key Fields**: {key_summary}<br><br>" + "<br><br>".join(observed_details)
            else:
                observed_content = "No observations recorded"
            
            report_lines.append(f"| **Observed** | {observed_content} |")
            
            # 4. Result (Pass/Fail/NA + 原因)
            result_content = f"**{result.result}**"
            if result.reason:
                result_content += f"<br>**Reason**: {result.reason}"
            if result.start_time and result.end_time:
                duration = result.end_time - result.start_time
                result_content += f"<br>**Duration**: {duration:.3f}s"
            
            report_lines.append(f"| **Result** | {emoji} {result_content} |")
            
            report_lines.extend([
                "",
                "---",
                ""
            ])
        
        # 附录
        report_lines.extend([
            "## Appendix",
            "",
            "### Log Files and Evidence",
            "",
            "- **JSONL Evidence Log**: `kone_validation.log`",
            "- **Application Log**: `elevator.log`", 
            "- **Configuration File**: `config.yaml` (sanitized)",
            "",
            "### Test Execution Environment",
            "",
            f"- **Python Version**: 3.8+",
            f"- **WebSocket Library**: websockets",
            f"- **HTTP Client**: aiohttp",
            f"- **Validation Framework**: Pydantic",
            "",
            "### API Compliance",
            "",
            "This validation report demonstrates compliance with:",
            "- KONE Elevator Call API v2.0 Specification",
            "- WebSocket API v2 Message Format (elevator-websocket-api-v2.yaml)",
            "- Service Robot API Solution Validation Test Guide v2",
            "",
            "### Notes",
            "",
            "- All sensitive information (tokens, secrets) has been redacted for security",
            "- Test evidence is preserved in structured JSONL format",
            "- NA (Not Applicable) results indicate tests requiring specific building configurations",
            "- Message timestamps are in UTC format",
            "",
            f"**Report Generated**: {datetime.now().isoformat()}Z",
            "",
            "---",
            "",
            "*End of Report*"
        ])
        
        return '\n'.join(report_lines)
    
    def save_report(self, results: List[TestResult], 
                   output_path: str = "validation_report.md",
                   building_id: str = "N/A",
                   group_id: str = "1", 
                   ws_endpoint: str = "wss://dev.kone.com/stream-v2"):
        """保存报告到文件"""
        
        report_content = self.generate_markdown_report(
            results, building_id, group_id, ws_endpoint
        )
        
        # 确保输出目录存在
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return output_path
    
    def generate_summary_json(self, results: List[TestResult]) -> Dict[str, Any]:
        """生成JSON格式的测试摘要"""
        
        total = len(results)
        passed = len([r for r in results if r.result == "Pass"])
        failed = len([r for r in results if r.result == "Fail"])
        na = len([r for r in results if r.result == "NA"])
        
        summary = {
            "test_summary": {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "not_applicable": na,
                "success_rate": round(passed/total*100, 1) if total > 0 else 0
            },
            "test_results": [result.to_dict() for result in results],
            "environment": {
                "building_id": "building:L1QinntdEOg",
                "group_id": "1",
                "ws_endpoint": "wss://dev.kone.com/stream-v2",
                "test_timestamp": datetime.now().isoformat() + "Z"
            },
            "solution_provider": self.config.get('solution_provider', {}),
            "report_metadata": {
                "generator": "KONE API v2.0 Validation Suite",
                "version": "2.0",
                "format": "JSON Summary",
                "generated_at": datetime.now().isoformat() + "Z"
            }
        }
        
        return summary


# 为向后兼容保留的类
TestResult.__module__ = __name__  # 确保类可以被导入
