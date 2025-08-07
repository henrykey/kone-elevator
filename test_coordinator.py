# Author: IBC-AI CO.
"""
KONE 验证测试协调器
负责协调和执行完整的37项KONE验证测试流程
"""

import asyncio
import httpx
import yaml
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class KoneValidationTestCoordinator:
    """
    KONE验证测试协调器
    负责初始化API连接、加载配置、执行测试流程并生成报告
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8000", config_path: str = "virtual_building_config.yml"):
        """
        初始化测试协调器
        
        Args:
            api_base_url: FastAPI服务的基础URL
            config_path: 虚拟建筑配置文件路径
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.config_path = config_path
        self.building_config = None
        self.test_session_id = None
        self.client = None
        self.metadata = {
            "company": "IBC-AI CO.",
            "test_date": datetime.now().isoformat(),
            "api_version": "2.0.0",
            "test_framework": "KONE SR-API v2.0",
            "total_tests": 37
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.client:
            await self.client.aclose()
    
    def load_building_config(self) -> bool:
        """
        加载虚拟建筑配置
        
        Returns:
            bool: 加载成功返回True，失败返回False
        """
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.error(f"Building config file not found: {self.config_path}")
                return False
            
            with open(config_file, 'r', encoding='utf-8') as f:
                self.building_config = yaml.safe_load(f)
            
            logger.info(f"Successfully loaded building config: {self.building_config.get('building', {}).get('id', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load building config: {e}")
            return False
    
    async def check_api_connectivity(self) -> Dict[str, Any]:
        """
        检查API连通性和服务状态
        
        Returns:
            dict: 连通性检查结果
        """
        try:
            response = await self.client.get(f"{self.api_base_url}/")
            
            if response.status_code == 200:
                api_info = response.json()
                logger.info(f"API connectivity check passed: {api_info.get('name', 'Unknown API')}")
                return {
                    "success": True,
                    "api_info": api_info,
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
            else:
                logger.error(f"API connectivity check failed with status: {response.status_code}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
                
        except Exception as e:
            logger.error(f"API connectivity check failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": None
            }
    
    async def initialize_test_session(self) -> Dict[str, Any]:
        """
        初始化测试会话
        
        Returns:
            dict: 初始化结果
        """
        try:
            response = await self.client.get(f"{self.api_base_url}/api/elevator/initialize")
            
            # 接受200 (OK) 和 201 (Created) 状态码
            if response.status_code in [200, 201]:
                result = response.json()
                if result.get('success'):
                    self.test_session_id = result.get('session_id', f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                    logger.info(f"Test session initialized: {self.test_session_id}")
                    return {
                        "success": True,
                        "session_id": self.test_session_id,
                        "initialization_data": result
                    }
            
            logger.error(f"Session initialization failed: {response.status_code}")
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "response": response.text
            }
            
        except Exception as e:
            logger.error(f"Session initialization error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def load_test_guide_templates(self) -> Dict[str, Any]:
        """
        加载测试指南模板
        
        Returns:
            dict: 模板加载结果
        """
        # 这里可以扩展加载外部测试指南模板
        # 目前返回基础模板结构
        templates = {
            "report_template": {
                "header": "KONE Service Robot API Validation Test Report",
                "company": self.metadata["company"],
                "sections": [
                    "Executive Summary",
                    "Test Environment",
                    "Test Results",
                    "Detailed Analysis",
                    "Recommendations"
                ]
            },
            "test_categories": [
                "Initialization Tests",
                "Call Management Tests", 
                "Status Monitoring Tests",
                "Error Handling Tests",
                "Performance Tests"
            ]
        }
        
        logger.info("Test guide templates loaded successfully")
        return {
            "success": True,
            "templates": templates
        }
    
    async def run_partial_validation(self, test_cases: List[int]) -> dict:
        """
        执行部分KONE验证测试（指定的测试用例）：
        1. 系统预检查
        2. 执行指定的测试用例
        3. 生成报告
        4. 返回多格式结果
        
        Args:
            test_cases: 要执行的测试用例编号列表
            
        Returns:
            dict: 部分测试结果和报告
        """
        logger.info(f"Starting KONE partial validation test suite for {len(test_cases)} test cases: {test_cases}")
        
        validation_result = {
            "metadata": self.metadata.copy(),
            "phases": {},
            "summary": {},
            "reports": {},
            "test_filter": {
                "mode": "partial",
                "selected_cases": test_cases,
                "total_selected": len(test_cases)
            }
        }
        
        try:
            # Phase 1: 系统预检查（与完整验证相同）
            logger.info("Phase 1: System pre-checks")
            
            # 加载建筑配置
            if not self.load_building_config():
                raise Exception("Failed to load building configuration")
            
            # 检查API连通性
            connectivity_result = await self.check_api_connectivity()
            if not connectivity_result["success"]:
                raise Exception(f"API connectivity failed: {connectivity_result.get('error')}")
            
            # 初始化测试会话
            session_result = await self.initialize_test_session()
            if not session_result["success"]:
                raise Exception(f"Session initialization failed: {session_result.get('error')}")
            
            # 加载测试模板
            template_result = await self.load_test_guide_templates()
            
            validation_result["phases"]["phase_1"] = {
                "name": "System Pre-checks",
                "status": "COMPLETED",
                "results": {
                    "building_config": {"success": True, "building_id": self.building_config.get('building', {}).get('id')},
                    "api_connectivity": connectivity_result,
                    "session_initialization": session_result,
                    "template_loading": template_result
                },
                "duration_ms": 0  # 这里可以添加实际计时
            }
            
            # Phase 2: 部分测试执行（只执行指定的测试用例）
            logger.info(f"Phase 2: Partial test execution for cases: {test_cases}")
            try:
                from test_execution_phases import phase_2_partial_tests
                from test_case_mapper import TestCaseMapper
                from building_data_manager import BuildingDataManager
                
                # 获取正确的building_id
                building_id = self.building_config.get('building', {}).get('id', 'L1QinntdEOg')
                
                # 准备阶段1的数据传递给阶段2
                phase1_data = {
                    "building_manager": BuildingDataManager(self.config_path),
                    "test_mapper": TestCaseMapper(building_id),
                    "test_filter": test_cases  # 传递测试过滤器
                }
                
                # 尝试调用部分测试函数，如果不存在则回退到核心测试但应用过滤器
                try:
                    phase2_result = await phase_2_partial_tests(phase1_data, self.api_base_url, test_cases)
                except (ImportError, AttributeError):
                    # 如果没有专门的部分测试函数，使用核心测试函数但传递过滤器
                    from test_execution_phases import phase_2_core_tests
                    logger.info("Using core tests with filtering for partial validation")
                    phase1_data["test_filter"] = test_cases
                    phase2_result = await phase_2_core_tests(phase1_data, self.api_base_url)
                
                validation_result["phases"]["phase_2"] = phase2_result
                
                if phase2_result["status"] == "COMPLETED":
                    executed_tests = phase2_result.get('statistics', {}).get('total_tests', 0)
                    logger.info(f"✅ Phase 2 completed: {executed_tests}/{len(test_cases)} selected tests executed")
                else:
                    logger.error(f"❌ Phase 2 failed: {phase2_result.get('error', 'Unknown error')}")
                    
            except ImportError:
                validation_result["phases"]["phase_2"] = {
                    "name": "Partial Test Execution", 
                    "status": "PENDING",
                    "message": "Test execution phases module not available",
                    "test_count": len(test_cases)
                }
            except Exception as e:
                logger.error(f"❌ Phase 2 execution error: {e}")
                validation_result["phases"]["phase_2"] = {
                    "name": "Partial Test Execution",
                    "status": "ERROR", 
                    "error": str(e)
                }
            
            # Phase 3: 报告生成
            logger.info("Phase 3: Report generation")
            try:
                from test_execution_phases import phase_3_report_generation
                from report_generator import ReportGenerator
                
                # 只有当阶段2成功时才执行报告生成
                if validation_result["phases"]["phase_2"].get("status") == "COMPLETED":
                    # 获取正确的building_id  
                    building_id = self.building_config.get('building', {}).get('id', 'L1QinntdEOg')
                    
                    # 准备阶段1的数据传递给阶段3，包含报告生成器
                    phase1_data_for_phase3 = {
                        "building_manager": BuildingDataManager(self.config_path),
                        "test_mapper": TestCaseMapper(building_id),
                        "report_generator": ReportGenerator(),
                        "test_filter": test_cases  # 报告生成也需要知道过滤器
                    }
                    
                    phase3_result = await phase_3_report_generation(
                        validation_result["phases"]["phase_2"],
                        phase1_data_for_phase3,
                        self.metadata
                    )
                    validation_result["phases"]["phase_3"] = phase3_result
                    
                    if phase3_result["status"] == "COMPLETED":
                        validation_result["reports"] = phase3_result.get("reports", {})
                        logger.info("✅ Phase 3 completed: Partial test reports generated")
                    else:
                        logger.error(f"❌ Phase 3 failed: {phase3_result.get('error', 'Unknown error')}")
                else:
                    validation_result["phases"]["phase_3"] = {
                        "name": "Report Generation",
                        "status": "SKIPPED",
                        "message": "Skipped due to Phase 2 failure"
                    }
                    
            except ImportError:
                validation_result["phases"]["phase_3"] = {
                    "name": "Report Generation",
                    "status": "PENDING", 
                    "message": "Test execution phases module not available"
                }
            except Exception as e:
                validation_result["phases"]["phase_3"] = {
                    "name": "Report Generation",
                    "status": "ERROR",
                    "error": str(e)
                }
            
            # 计算总体结果
            completed_phases = sum(1 for phase in validation_result["phases"].values() 
                                 if phase.get("status") == "COMPLETED")
            
            validation_result["summary"] = {
                "total_phases": 3,
                "completed_phases": completed_phases,
                "overall_status": "COMPLETED" if completed_phases == 3 else "PARTIALLY_COMPLETED",
                "has_reports": bool(validation_result.get("reports")),
                "execution_mode": "partial",
                "selected_tests": test_cases,
                "execution_summary": {
                    "phase_1": validation_result["phases"]["phase_1"].get("status"),
                    "phase_2": validation_result["phases"]["phase_2"].get("status"), 
                    "phase_3": validation_result["phases"]["phase_3"].get("status")
                }
            }
            
            if completed_phases == 3:
                logger.info(f"✅ KONE partial validation completed successfully for {len(test_cases)} test cases")
            else:
                logger.info(f"⚠️ KONE partial validation partially completed: {completed_phases}/3 phases")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Partial validation test failed: {e}")
            validation_result["summary"] = {
                "overall_status": "FAILED",
                "error": str(e),
                "failed_at": "Phase 1",
                "execution_mode": "partial",
                "selected_tests": test_cases
            }
            return validation_result

    async def run_full_validation(self) -> dict:
        """
        执行完整的37项KONE验证测试：
        1. 系统预检查
        2. 执行测试套件
        3. 生成报告
        4. 返回多格式结果
        
        Returns:
            dict: 完整测试结果和报告
        """
        logger.info("Starting KONE validation test suite...")
        
        validation_result = {
            "metadata": self.metadata.copy(),
            "phases": {},
            "summary": {},
            "reports": {}
        }
        
        try:
            # Phase 1: 系统预检查
            logger.info("Phase 1: System pre-checks")
            
            # 加载建筑配置
            if not self.load_building_config():
                raise Exception("Failed to load building configuration")
            
            # 检查API连通性
            connectivity_result = await self.check_api_connectivity()
            if not connectivity_result["success"]:
                raise Exception(f"API connectivity failed: {connectivity_result.get('error')}")
            
            # 初始化测试会话
            session_result = await self.initialize_test_session()
            if not session_result["success"]:
                raise Exception(f"Session initialization failed: {session_result.get('error')}")
            
            # 加载测试模板
            template_result = await self.load_test_guide_templates()
            
            validation_result["phases"]["phase_1"] = {
                "name": "System Pre-checks",
                "status": "COMPLETED",
                "results": {
                    "building_config": {"success": True, "building_id": self.building_config.get('building', {}).get('id')},
                    "api_connectivity": connectivity_result,
                    "session_initialization": session_result,
                    "template_loading": template_result
                },
                "duration_ms": 0  # 这里可以添加实际计时
            }
            
            # Phase 2: 核心测试执行
            logger.info("Phase 2: Core test execution")
            try:
                from test_execution_phases import phase_2_core_tests
                from test_case_mapper import TestCaseMapper
                from building_data_manager import BuildingDataManager
                
                # 获取正确的building_id
                building_id = self.building_config.get('building', {}).get('id', 'L1QinntdEOg')
                
                # 准备阶段1的数据传递给阶段2 - 创建实际实例
                phase1_data = {
                    "building_manager": BuildingDataManager(self.config_path),
                    "test_mapper": TestCaseMapper(building_id),
                }
                
                phase2_result = await phase_2_core_tests(phase1_data, self.api_base_url)
                validation_result["phases"]["phase_2"] = phase2_result
                
                if phase2_result["status"] == "COMPLETED":
                    logger.info(f"✅ Phase 2 completed: {phase2_result.get('statistics', {}).get('total_tests', 0)} tests executed")
                else:
                    logger.error(f"❌ Phase 2 failed: {phase2_result.get('error', 'Unknown error')}")
                    
            except ImportError:
                validation_result["phases"]["phase_2"] = {
                    "name": "Core Test Execution", 
                    "status": "PENDING",
                    "message": "Test execution phases module not available",
                    "test_count": 37
                }
            except Exception as e:
                logger.error(f"❌ Phase 2 execution error: {e}")
                validation_result["phases"]["phase_2"] = {
                    "name": "Core Test Execution",
                    "status": "ERROR", 
                    "error": str(e)
                }
            
            # Phase 3: 报告生成
            logger.info("Phase 3: Report generation")
            try:
                from test_execution_phases import phase_3_report_generation
                from report_generator import ReportGenerator
                
                # 只有当阶段2成功时才执行报告生成
                if validation_result["phases"]["phase_2"].get("status") == "COMPLETED":
                    # 获取正确的building_id
                    building_id = self.building_config.get('building', {}).get('id', 'L1QinntdEOg')
                    
                    # 准备阶段1的数据传递给阶段3，包含报告生成器
                    phase1_data_for_phase3 = {
                        "building_manager": BuildingDataManager(self.config_path),
                        "test_mapper": TestCaseMapper(building_id),
                        "report_generator": ReportGenerator()
                    }
                    
                    phase3_result = await phase_3_report_generation(
                        validation_result["phases"]["phase_2"],
                        phase1_data_for_phase3,
                        self.metadata
                    )
                    validation_result["phases"]["phase_3"] = phase3_result
                    
                    if phase3_result["status"] == "COMPLETED":
                        validation_result["reports"] = phase3_result.get("reports", {})
                        logger.info("✅ Phase 3 completed: Reports generated")
                    else:
                        logger.error(f"❌ Phase 3 failed: {phase3_result.get('error', 'Unknown error')}")
                else:
                    validation_result["phases"]["phase_3"] = {
                        "name": "Report Generation",
                        "status": "SKIPPED",
                        "message": "Skipped due to Phase 2 failure"
                    }
                    
            except ImportError:
                validation_result["phases"]["phase_3"] = {
                    "name": "Report Generation",
                    "status": "PENDING", 
                    "message": "Test execution phases module not available"
                }
            except Exception as e:
                validation_result["phases"]["phase_3"] = {
                    "name": "Report Generation",
                    "status": "ERROR",
                    "error": str(e)
                }
            
            # 计算总体结果
            completed_phases = sum(1 for phase in validation_result["phases"].values() 
                                 if phase.get("status") == "COMPLETED")
            
            validation_result["summary"] = {
                "total_phases": 3,
                "completed_phases": completed_phases,
                "overall_status": "COMPLETED" if completed_phases == 3 else "PARTIALLY_COMPLETED",
                "has_reports": bool(validation_result.get("reports")),
                "execution_summary": {
                    "phase_1": validation_result["phases"]["phase_1"].get("status"),
                    "phase_2": validation_result["phases"]["phase_2"].get("status"), 
                    "phase_3": validation_result["phases"]["phase_3"].get("status")
                }
            }
            
            if completed_phases == 3:
                logger.info("✅ KONE validation test suite completed successfully")
            else:
                logger.info(f"⚠️ KONE validation partially completed: {completed_phases}/3 phases")
            
            logger.info("KONE validation test coordination completed (Phase 1)")
            return validation_result
            
        except Exception as e:
            logger.error(f"Validation test failed: {e}")
            validation_result["summary"] = {
                "overall_status": "FAILED",
                "error": str(e),
                "failed_at": "Phase 1"
            }
            return validation_result
