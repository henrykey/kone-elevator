# Author: IBC-AI CO.
"""
KONE 测试执行流程
实现三阶段测试执行：系统预检查、核心测试、报告生成
"""

import asyncio
import httpx
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from test_case_mapper import TestCaseMapper, TestCaseConfig
from building_data_manager import BuildingDataManager
from report_generator import ReportGenerator, TestResult

logger = logging.getLogger(__name__)


async def phase_1_setup(api_base_url: str = "http://localhost:8000", 
                       config_path: str = "virtual_building_config.yml") -> Dict[str, Any]:
    """
    阶段1：系统预检查
    检查API、加载配置、连接验证
    
    Args:
        api_base_url: API服务地址
        config_path: 配置文件路径
        
    Returns:
        dict: 预检查结果
    """
    logger.info("🚀 Phase 1: System Setup and Pre-checks")
    start_time = time.time()
    
    setup_result = {
        "phase": "phase_1_setup",
        "status": "IN_PROGRESS",
        "start_time": datetime.now().isoformat(),
        "checks": {},
        "data": {}
    }
    
    try:
        # 1. API连通性检查
        logger.info("1️⃣ Checking API connectivity...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(f"{api_base_url.rstrip('/')}/")
                if response.status_code == 200:
                    api_info = response.json()
                    setup_result["checks"]["api_connectivity"] = {
                        "status": "PASS",
                        "response_time_ms": response.elapsed.total_seconds() * 1000,
                        "api_info": api_info
                    }
                    logger.info(f"✅ API connectivity check passed: {api_info.get('name')}")
                else:
                    setup_result["checks"]["api_connectivity"] = {
                        "status": "FAIL",
                        "error": f"HTTP {response.status_code}",
                        "response_time_ms": response.elapsed.total_seconds() * 1000
                    }
                    logger.error(f"❌ API connectivity failed: {response.status_code}")
            except Exception as e:
                setup_result["checks"]["api_connectivity"] = {
                    "status": "ERROR",
                    "error": str(e)
                }
                logger.error(f"❌ API connectivity error: {e}")
        
        # 2. 建筑数据管理器初始化
        logger.info("2️⃣ Initializing Building Data Manager...")
        try:
            building_manager = BuildingDataManager(config_path)
            building_summary = building_manager.get_building_summary()
            
            setup_result["checks"]["building_config"] = {
                "status": "PASS",
                "building_summary": building_summary
            }
            setup_result["data"]["building_manager"] = building_manager
            logger.info(f"✅ Building config loaded: {building_summary['building_id']}")
        except Exception as e:
            setup_result["checks"]["building_config"] = {
                "status": "ERROR",
                "error": str(e)
            }
            logger.error(f"❌ Building config error: {e}")
        
        # 3. 测试用例映射器初始化
        logger.info("3️⃣ Initializing Test Case Mapper...")
        try:
            building_id = setup_result["data"].get("building_manager", BuildingDataManager()).get_building_id()
            test_mapper = TestCaseMapper(building_id)
            mapper_summary = test_mapper.get_test_summary()
            
            setup_result["checks"]["test_mapper"] = {
                "status": "PASS",
                "test_summary": mapper_summary
            }
            setup_result["data"]["test_mapper"] = test_mapper
            logger.info(f"✅ Test mapper initialized: {mapper_summary['total_tests']} tests")
        except Exception as e:
            setup_result["checks"]["test_mapper"] = {
                "status": "ERROR",
                "error": str(e)
            }
            logger.error(f"❌ Test mapper error: {e}")
        
        # 4. 报告生成器初始化
        logger.info("4️⃣ Initializing Report Generator...")
        try:
            report_generator = ReportGenerator("IBC-AI CO.")
            setup_result["checks"]["report_generator"] = {
                "status": "PASS",
                "company": "IBC-AI CO."
            }
            setup_result["data"]["report_generator"] = report_generator
            logger.info("✅ Report generator initialized")
        except Exception as e:
            setup_result["checks"]["report_generator"] = {
                "status": "ERROR",
                "error": str(e)
            }
            logger.error(f"❌ Report generator error: {e}")
        
        # 5. API服务状态检查
        logger.info("5️⃣ Checking API service status...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(f"{api_base_url.rstrip('/')}/api/elevator/status")
                if response.status_code == 200:
                    status_info = response.json()
                    setup_result["checks"]["service_status"] = {
                        "status": "PASS",
                        "service_info": status_info
                    }
                    logger.info("✅ Service status check passed")
                else:
                    setup_result["checks"]["service_status"] = {
                        "status": "FAIL",
                        "error": f"HTTP {response.status_code}"
                    }
                    logger.warning(f"⚠️ Service status check failed: {response.status_code}")
            except Exception as e:
                setup_result["checks"]["service_status"] = {
                    "status": "ERROR",
                    "error": str(e)
                }
                logger.warning(f"⚠️ Service status error: {e}")
        
        # 计算总体状态
        all_checks = setup_result["checks"]
        critical_checks = ["api_connectivity", "building_config", "test_mapper", "report_generator"]
        
        failed_critical = [check for check in critical_checks 
                          if all_checks.get(check, {}).get("status") not in ["PASS"]]
        
        if not failed_critical:
            setup_result["status"] = "COMPLETED"
            logger.info("✅ Phase 1 completed successfully")
        else:
            setup_result["status"] = "FAILED"
            setup_result["failed_checks"] = failed_critical
            logger.error(f"❌ Phase 1 failed: {failed_critical}")
        
        # 添加执行时间
        setup_result["duration_ms"] = (time.time() - start_time) * 1000
        setup_result["end_time"] = datetime.now().isoformat()
        
        return setup_result
        
    except Exception as e:
        setup_result["status"] = "ERROR"
        setup_result["error"] = str(e)
        setup_result["duration_ms"] = (time.time() - start_time) * 1000
        setup_result["end_time"] = datetime.now().isoformat()
        logger.error(f"❌ Phase 1 setup error: {e}")
        return setup_result


async def phase_2_core_tests(setup_data: Dict[str, Any], 
                           api_base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    阶段2：核心测试执行
    执行37项测试，组织结果
    
    Args:
        setup_data: 阶段1的设置数据
        api_base_url: API服务地址
        
    Returns:
        dict: 测试执行结果
    """
    logger.info("🧪 Phase 2: Core Test Execution")
    start_time = time.time()
    
    test_result = {
        "phase": "phase_2_core_tests",
        "status": "IN_PROGRESS",
        "start_time": datetime.now().isoformat(),
        "test_results": [],
        "statistics": {},
        "errors": []
    }
    
    try:
        # 从设置数据中获取必要组件
        test_mapper = setup_data.get("test_mapper")
        building_manager = setup_data.get("building_manager")
        test_filter = setup_data.get("test_filter")  # 新增：测试过滤器
        
        if not test_mapper or not building_manager:
            raise Exception("Missing required components from phase 1 setup")
        
        # 获取测试用例（支持过滤）
        if test_filter:
            # 如果有过滤器，只执行指定的测试
            # 将整数测试用例转换为字符串格式
            string_test_filter = []
            for test_case in test_filter:
                if isinstance(test_case, int):
                    string_test_filter.append(f"Test_{test_case}")
                else:
                    string_test_filter.append(str(test_case))
            
            all_test_ids = [tid for tid in test_mapper.get_all_test_ids() if tid in string_test_filter]
            logger.info(f"📋 Executing {len(all_test_ids)}/{len(test_filter)} filtered tests...")
        else:
            # 否则执行所有测试
            all_test_ids = test_mapper.get_all_test_ids()
            logger.info(f"📋 Executing all {len(all_test_ids)} tests...")
        
        # 初始化HTTP客户端
        async with httpx.AsyncClient(timeout=30.0) as client:
            
            # 批量执行测试
            for i, test_id in enumerate(all_test_ids, 1):
                logger.info(f"🔍 Executing test {i}/{len(all_test_ids)}: {test_id}")
                
                test_config = test_mapper.get_test_case(test_id)
                if not test_config:
                    logger.warning(f"⚠️ Test config not found for {test_id}")
                    continue
                
                # 执行单个测试
                result = await _execute_single_test(client, test_config, building_manager, api_base_url, test_id)
                test_result["test_results"].append(result)
                
                # 记录进度
                if i % 5 == 0:
                    logger.info(f"📊 Progress: {i}/{len(all_test_ids)} tests completed")
        
        # 计算统计信息
        test_result["statistics"] = _calculate_test_statistics(test_result["test_results"])
        test_result["status"] = "COMPLETED"
        
        execution_mode = "filtered" if test_filter else "full"
        logger.info(f"✅ Phase 2 completed ({execution_mode}): {test_result['statistics']['total_tests']} tests executed")
        
    except Exception as e:
        test_result["status"] = "ERROR"
        test_result["error"] = str(e)
        test_result["errors"].append(str(e))
        logger.error(f"❌ Phase 2 execution error: {e}")
    
    # 添加执行时间
    test_result["duration_ms"] = (time.time() - start_time) * 1000
    test_result["end_time"] = datetime.now().isoformat()
    
    return test_result


async def phase_2_partial_tests(setup_data: Dict[str, Any], 
                               api_base_url: str = "http://localhost:8000",
                               test_cases: List[int] = None) -> Dict[str, Any]:
    """
    阶段2：部分测试执行
    只执行指定的测试用例
    
    Args:
        setup_data: 阶段1的设置数据
        api_base_url: API服务地址
        test_cases: 要执行的测试用例编号列表
        
    Returns:
        dict: 测试执行结果
    """
    logger.info(f"🧪 Phase 2: Partial Test Execution for {len(test_cases) if test_cases else 0} test cases")
    start_time = time.time()
    
    test_result = {
        "phase": "phase_2_partial_tests",
        "status": "IN_PROGRESS",
        "start_time": datetime.now().isoformat(),
        "test_results": [],
        "statistics": {},
        "errors": [],
        "execution_mode": "partial",
        "selected_tests": test_cases or []
    }
    
    try:
        # 从设置数据中获取必要组件
        test_mapper = setup_data.get("test_mapper")
        building_manager = setup_data.get("building_manager")
        
        if not test_mapper or not building_manager:
            raise Exception("Missing required components from phase 1 setup")
        
        if not test_cases:
            raise Exception("No test cases specified for partial execution")
        
        # 获取所有可用的测试ID
        all_available_ids = test_mapper.get_all_test_ids()
        
        # 将整数测试用例转换为字符串格式
        string_test_cases = []
        for test_case in test_cases:
            if isinstance(test_case, int):
                string_test_cases.append(f"Test_{test_case}")
            else:
                string_test_cases.append(str(test_case))
        
        # 过滤出存在的测试用例
        valid_test_ids = [tid for tid in string_test_cases if tid in all_available_ids]
        invalid_test_ids = [tid for tid in string_test_cases if tid not in all_available_ids]
        
        if invalid_test_ids:
            logger.warning(f"⚠️ Invalid test IDs will be skipped: {invalid_test_ids}")
        
        if not valid_test_ids:
            raise Exception("No valid test cases found in the specified list")
        
        logger.info(f"📋 Executing {len(valid_test_ids)} valid tests out of {len(test_cases)} requested...")
        
        # 初始化HTTP客户端
        async with httpx.AsyncClient(timeout=30.0) as client:
            
            # 批量执行指定的测试
            for i, test_id in enumerate(valid_test_ids, 1):
                logger.info(f"🔍 Executing test {i}/{len(valid_test_ids)}: {test_id}")
                
                test_config = test_mapper.get_test_case(test_id)
                if not test_config:
                    logger.warning(f"⚠️ Test config not found for {test_id}")
                    continue
                
                # 执行单个测试
                result = await _execute_single_test(client, test_config, building_manager, api_base_url, test_id)
                test_result["test_results"].append(result)
                
                # 记录进度
                if i % 3 == 0 or i == len(valid_test_ids):
                    logger.info(f"📊 Progress: {i}/{len(valid_test_ids)} tests completed")
        
        # 计算统计信息
        test_result["statistics"] = _calculate_test_statistics(test_result["test_results"])
        test_result["statistics"]["requested_tests"] = len(test_cases)
        test_result["statistics"]["valid_tests"] = len(valid_test_ids)
        test_result["statistics"]["invalid_tests"] = len(invalid_test_ids)
        test_result["status"] = "COMPLETED"
        
        logger.info(f"✅ Phase 2 partial execution completed: {test_result['statistics']['total_tests']} tests executed")
        
    except Exception as e:
        test_result["status"] = "ERROR"
        test_result["error"] = str(e)
        test_result["errors"].append(str(e))
        logger.error(f"❌ Phase 2 partial execution error: {e}")
    
    # 添加执行时间
    test_result["duration_ms"] = (time.time() - start_time) * 1000
    test_result["end_time"] = datetime.now().isoformat()
    
    return test_result


async def phase_3_report_generation(test_results: Dict[str, Any], 
                                  setup_data: Dict[str, Any],
                                  metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    阶段3：报告生成
    根据metadata和测试结果生成报告并返回
    
    Args:
        test_results: 阶段2的测试结果
        setup_data: 阶段1的设置数据
        metadata: 测试元数据
        
    Returns:
        dict: 报告生成结果
    """
    logger.info("📝 Phase 3: Report Generation")
    start_time = time.time()
    
    report_result = {
        "phase": "phase_3_report_generation",
        "status": "IN_PROGRESS",
        "start_time": datetime.now().isoformat(),
        "reports": {},
        "saved_files": {}
    }
    
    try:
        # 从设置数据中获取报告生成器
        report_generator = setup_data.get("report_generator")
        if not report_generator:
            raise Exception("Report generator not available from phase 1 setup")
        
        # 转换测试结果为ReportGenerator期望的格式
        formatted_results = []
        for result_data in test_results.get("test_results", []):
            test_result = TestResult(
                test_id=result_data["test_id"],
                name=result_data["name"],
                status=result_data["status"],
                duration_ms=result_data["duration_ms"],
                error_message=result_data.get("error_message"),
                response_data=result_data.get("response_data"),
                category=result_data.get("category")
            )
            formatted_results.append(test_result)
        
        # 准备完整的元数据
        complete_metadata = {
            **metadata,
            "building_id": setup_data.get("building_manager", {}).get_building_id() if setup_data.get("building_manager") else "Unknown",
            "total_test_duration_ms": test_results.get("duration_ms", 0),
            "test_execution_time": test_results.get("end_time"),
            "setup_duration_ms": setup_data.get("duration_ms", 0) if isinstance(setup_data, dict) else 0
        }
        
        # 生成多格式报告
        logger.info("📊 Generating multi-format reports...")
        reports = report_generator.generate_report(formatted_results, complete_metadata, "reports")
        
        if "error" in reports:
            raise Exception(f"Report generation failed: {reports['error']}")
        
        report_result["reports"] = reports
        
        # 保存报告文件
        logger.info("💾 Saving report files...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_files = report_generator.save_reports_to_files(reports, f"KONE_Validation_Report_{timestamp}")
        
        if "error" in saved_files:
            logger.warning(f"⚠️ File saving warning: {saved_files['error']}")
        else:
            report_result["saved_files"] = saved_files
            logger.info(f"✅ Reports saved: {list(saved_files.keys())}")
        
        report_result["status"] = "COMPLETED"
        
        # 输出报告摘要
        stats = test_results.get("statistics", {})
        logger.info(f"📈 Report Summary:")
        logger.info(f"   Total Tests: {stats.get('total_tests', 0)}")
        logger.info(f"   Success Rate: {stats.get('success_rate', 0)}%")
        logger.info(f"   Generated Formats: {len(reports)}")
        
    except Exception as e:
        report_result["status"] = "ERROR"
        report_result["error"] = str(e)
        logger.error(f"❌ Phase 3 report generation error: {e}")
    
    # 添加执行时间
    report_result["duration_ms"] = (time.time() - start_time) * 1000
    report_result["end_time"] = datetime.now().isoformat()
    
    return report_result


async def _execute_single_test(client: httpx.AsyncClient, 
                             test_config: TestCaseConfig,
                             building_manager: BuildingDataManager,
                             api_base_url: str,
                             test_id: str = None) -> Dict[str, Any]:
    """
    执行单个测试用例
    
    Args:
        client: HTTP客户端
        test_config: 测试配置
        building_manager: 建筑数据管理器
        api_base_url: API基础URL
        test_id: 测试ID（如 Test_1, Test_2等）
        
    Returns:
        dict: 测试结果
    """
    start_time = time.time()
    
    result = {
        "test_id": test_id or test_config.name,  # 优先使用传入的test_id
        "name": test_config.name,
        "category": test_config.category.value,
        "status": "UNKNOWN",
        "duration_ms": 0,
        "error_message": None,
        "response_data": None,
        "request_data": None
    }
    
    try:
        # 准备请求参数
        params = test_config.parameters.copy()
        
        # 为需要随机数据的测试生成参数
        if test_config.name in ["Test_6", "Test_7", "Test_8", "Test_10", "Test_22"]:  # 呼叫测试
            if "source" in params and "destination" in params:
                source, dest = building_manager.get_random_floor_pair()
                params["source"] = source
                params["destination"] = dest
        
        # 构建请求URL
        url = f"{api_base_url.rstrip('/')}{test_config.endpoint}"
        
        # 记录请求数据
        result["request_data"] = {
            "method": test_config.http_method.value,
            "url": url,
            "parameters": params
        }
        
        # 执行HTTP请求
        if test_config.http_method.value == "GET":
            response = await client.get(url, params=params)
        elif test_config.http_method.value == "POST":
            # 特殊处理取消功能 - 使用查询参数而不是JSON body
            if test_config.endpoint == "/api/elevator/cancel":
                response = await client.post(url, params=params)
            else:
                response = await client.post(url, json=params)
        else:
            raise Exception(f"Unsupported HTTP method: {test_config.http_method.value}")
        
        # 记录响应数据
        try:
            response_json = response.json()
            result["response_data"] = response_json
        except:
            result["response_data"] = {"raw_response": response.text}
        
        # 验证响应状态
        if response.status_code == test_config.expected_status:
            result["status"] = "PASS"
        else:
            result["status"] = "FAIL"
            result["error_message"] = f"Expected status {test_config.expected_status}, got {response.status_code}"
        
        # 执行特定验证逻辑
        validation_result = _validate_test_response(test_config, response, result["response_data"])
        if not validation_result["valid"]:
            result["status"] = "FAIL"
            if result["error_message"]:
                result["error_message"] += f" | {validation_result['message']}"
            else:
                result["error_message"] = validation_result["message"]
        
    except Exception as e:
        result["status"] = "ERROR"
        result["error_message"] = str(e)
        logger.error(f"❌ Test {test_config.name} execution error: {e}")
    
    # 计算执行时间
    result["duration_ms"] = (time.time() - start_time) * 1000
    
    return result


def _validate_test_response(test_config: TestCaseConfig, 
                          response: httpx.Response,
                          response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证测试响应
    
    Args:
        test_config: 测试配置
        response: HTTP响应
        response_data: 响应数据
        
    Returns:
        dict: 验证结果
    """
    validation_method = test_config.validation_method
    
    # 基础验证方法
    if validation_method == "check_session_creation":
        if response_data and response_data.get("success"):
            return {"valid": True, "message": "Session creation validated"}
        else:
            return {"valid": False, "message": "Session creation failed"}
    
    elif validation_method == "check_api_info":
        if response_data and "name" in response_data:
            return {"valid": True, "message": "API info validated"}
        else:
            return {"valid": False, "message": "API info missing"}
    
    elif validation_method == "check_call_response":
        if response_data and response_data.get("success"):
            return {"valid": True, "message": "Call response validated"}
        else:
            return {"valid": False, "message": "Call response invalid"}
    
    elif validation_method in ["check_same_floor_error", "check_invalid_floor_error", "check_excessive_delay_error"]:
        # 错误处理测试应该返回失败状态
        if response.status_code >= 400:
            return {"valid": True, "message": "Error handling validated"}
        else:
            return {"valid": False, "message": "Expected error response not received"}
    
    # 默认验证：只检查HTTP状态码
    return {"valid": True, "message": "Basic validation passed"}


def _calculate_test_statistics(test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    计算测试统计信息
    
    Args:
        test_results: 测试结果列表
        
    Returns:
        dict: 统计信息
    """
    total_tests = len(test_results)
    if total_tests == 0:
        return {"total_tests": 0}
    
    # 按状态统计
    status_counts = {}
    category_stats = {}
    total_duration = 0
    
    for result in test_results:
        status = result.get("status", "UNKNOWN")
        category = result.get("category", "Unknown")
        duration = result.get("duration_ms", 0)
        
        # 状态统计
        status_counts[status] = status_counts.get(status, 0) + 1
        
        # 分类统计
        if category not in category_stats:
            category_stats[category] = {"total": 0, "passed": 0, "failed": 0}
        
        category_stats[category]["total"] += 1
        if status == "PASS":
            category_stats[category]["passed"] += 1
        elif status in ["FAIL", "ERROR"]:
            category_stats[category]["failed"] += 1
        
        total_duration += duration
    
    # 计算成功率
    passed_tests = status_counts.get("PASS", 0)
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    return {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": status_counts.get("FAIL", 0),
        "error_tests": status_counts.get("ERROR", 0),
        "skipped_tests": status_counts.get("SKIP", 0),
        "success_rate": round(success_rate, 2),
        "total_duration_ms": total_duration,
        "average_duration_ms": round(total_duration / total_tests, 2) if total_tests > 0 else 0,
        "category_breakdown": category_stats,
        "status_distribution": status_counts
    }
