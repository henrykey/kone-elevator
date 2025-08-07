# Author: IBC-AI CO.
"""
KONE 测试报告自动化系统 - 主执行脚本
这是一个完整的自动化系统，用于执行KONE电梯系统验证测试并生成符合指南格式的报告。

功能特性：
- 执行37项KONE SR-API v2.0验证测试
- 生成多格式测试报告（Markdown、JSON、HTML、Excel）
- 自动化三阶段执行流程
- 完整的错误处理和日志记录
- 一键运行支持

使用方法：
    python main.py                          # 使用默认配置
    python main.py --api-url http://localhost:8080  # 指定API地址
    python main.py --config custom_config.yml       # 指定配置文件
    python main.py --verbose                        # 详细日志输出
"""

import asyncio
import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# 导入项目模块
from test_coordinator import KoneValidationTestCoordinator
from test_execution_phases import phase_1_setup, phase_2_core_tests, phase_3_report_generation
from building_data_manager import BuildingDataManager
from test_case_mapper import TestCaseMapper
from report_generator import ReportGenerator


def setup_logging(verbose: bool = False) -> None:
    """
    配置日志系统
    
    Args:
        verbose: 是否启用详细日志
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # 配置根日志记录器
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('kone_validation.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 设置httpx日志级别
    logging.getLogger('httpx').setLevel(logging.WARNING)


def print_banner():
    """打印系统横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    KONE 测试报告自动化系统 v2.0                                    ║
║                                                                              ║
║                            Author: IBC-AI CO.                               ║
║                                                                              ║
║  🏢 电梯系统验证测试 | 📊 多格式报告生成 | 🔄 三阶段自动化流程                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_system_info(args):
    """打印系统配置信息"""
    print("🔧 系统配置信息:")
    print(f"   API地址: {args.api_url}")
    print(f"   配置文件: {args.config}")
    print(f"   详细日志: {'启用' if args.verbose else '禁用'}")
    print(f"   输出目录: {args.output_dir}")
    print(f"   执行模式: {args.mode}")
    
    # 显示要执行的测试用例
    if hasattr(args, 'tests') and args.tests:
        try:
            test_cases = parse_test_cases(args.tests)
            test_summary = format_test_list(test_cases)
            print(f"   测试范围: {test_summary} (共{len(test_cases)}项)")
        except ValueError as e:
            print(f"   测试范围: ❌ 格式错误 - {e}")
    else:
        print("   测试范围: 全部37项测试")
    
    print()


async def run_coordinated_validation(api_url: str, config_path: str, test_cases: List[int] = None) -> Dict[str, Any]:
    """
    运行协调式验证（使用TestCoordinator）
    
    Args:
        api_url: API服务地址
        config_path: 配置文件路径
        test_cases: 指定要执行的测试用例列表，None表示执行全部
        
    Returns:
        dict: 验证结果
    """
    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting coordinated validation using TestCoordinator...")
    
    if test_cases:
        logger.info(f"📋 Will execute {len(test_cases)} specific tests: {format_test_list(test_cases)}")
    
    async with KoneValidationTestCoordinator(api_url, config_path) as coordinator:
        if test_cases:
            # 检查是否支持部分验证，如果不支持则回退到全部验证
            if hasattr(coordinator, 'run_partial_validation'):
                result = await coordinator.run_partial_validation(test_cases)
            else:
                logger.warning("⚠️ TestCoordinator不支持部分验证，将执行全部测试")
                result = await coordinator.run_full_validation()
        else:
            result = await coordinator.run_full_validation()
        return result


async def run_direct_validation(api_url: str, config_path: str, test_cases: List[int] = None) -> Dict[str, Any]:
    """
    运行直接验证（直接使用三阶段执行）
    
    Args:
        api_url: API服务地址
        config_path: 配置文件路径
        test_cases: 指定要执行的测试用例列表，None表示执行全部
        
    Returns:
        dict: 验证结果
    """
    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting direct validation using three-phase execution...")
    
    if test_cases:
        logger.info(f"📋 Will execute {len(test_cases)} specific tests: {format_test_list(test_cases)}")
    
    total_start_time = time.time()
    
    validation_result = {
        "execution_mode": "direct",
        "start_time": datetime.now().isoformat(),
        "phases": {},
        "summary": {},
        "reports": {},
        "test_scope": {
            "specified_tests": test_cases,
            "total_tests": len(test_cases) if test_cases else 37
        }
    }
    
    try:
        # 阶段1：系统预检查
        logger.info("=" * 60)
        logger.info("🔧 PHASE 1: System Setup and Pre-checks")
        logger.info("=" * 60)
        
        phase1_result = await phase_1_setup(api_url, config_path)
        validation_result["phases"]["phase_1"] = phase1_result
        
        if phase1_result["status"] != "COMPLETED":
            raise Exception(f"Phase 1 failed: {phase1_result.get('error', 'Unknown error')}")
        
        logger.info(f"✅ Phase 1 completed in {phase1_result['duration_ms']:.2f} ms")
        
        # 阶段2：核心测试执行
        logger.info("=" * 60)
        logger.info("🧪 PHASE 2: Core Test Execution")
        logger.info("=" * 60)
        
        phase2_result = await phase_2_core_tests(phase1_result["data"], api_url, test_cases)
        validation_result["phases"]["phase_2"] = phase2_result
        
        if phase2_result["status"] == "COMPLETED":
            stats = phase2_result.get("statistics", {})
            logger.info(f"✅ Phase 2 completed: {stats.get('total_tests', 0)} tests, "
                       f"{stats.get('success_rate', 0)}% success rate")
        else:
            logger.warning(f"⚠️ Phase 2 issues: {phase2_result.get('error', 'Unknown error')}")
        
        # 阶段3：报告生成
        logger.info("=" * 60)
        logger.info("📝 PHASE 3: Report Generation")
        logger.info("=" * 60)
        
        metadata = {
            "company": "IBC-AI CO.",
            "test_date": validation_result["start_time"],
            "api_version": "2.0.0",
            "test_framework": "KONE SR-API v2.0",
            "api_base_url": api_url,
            "config_path": config_path
        }
        
        phase3_result = await phase_3_report_generation(
            phase2_result, 
            phase1_result["data"], 
            metadata
        )
        validation_result["phases"]["phase_3"] = phase3_result
        
        if phase3_result["status"] == "COMPLETED":
            validation_result["reports"] = phase3_result.get("reports", {})
            validation_result["saved_files"] = phase3_result.get("saved_files", {})
            logger.info(f"✅ Phase 3 completed: {len(validation_result['reports'])} report formats generated")
        else:
            logger.error(f"❌ Phase 3 failed: {phase3_result.get('error', 'Unknown error')}")
        
        # 计算总体结果
        completed_phases = sum(1 for phase in validation_result["phases"].values() 
                             if phase.get("status") == "COMPLETED")
        
        validation_result["summary"] = {
            "total_phases": 3,
            "completed_phases": completed_phases,
            "overall_status": "COMPLETED" if completed_phases == 3 else "PARTIALLY_COMPLETED",
            "total_duration_ms": (time.time() - total_start_time) * 1000,
            "has_reports": bool(validation_result.get("reports"))
        }
        
        if completed_phases == 3:
            logger.info("🎉 All phases completed successfully!")
        else:
            logger.info(f"⚠️ Partial completion: {completed_phases}/3 phases completed")
        
        return validation_result
        
    except Exception as e:
        logger.error(f"❌ Direct validation failed: {e}")
        validation_result["summary"] = {
            "overall_status": "FAILED",
            "error": str(e),
            "total_duration_ms": (time.time() - total_start_time) * 1000
        }
        return validation_result


def print_execution_summary(result: Dict[str, Any]) -> None:
    """
    打印执行摘要
    
    Args:
        result: 执行结果
    """
    print("\n" + "=" * 80)
    print("📊 EXECUTION SUMMARY")
    print("=" * 80)
    
    summary = result.get("summary", {})
    phases = result.get("phases", {})
    
    print(f"Overall Status: {summary.get('overall_status', 'Unknown')}")
    print(f"Completed Phases: {summary.get('completed_phases', 0)}/3")
    
    if "total_duration_ms" in summary:
        duration_seconds = summary["total_duration_ms"] / 1000
        print(f"Total Duration: {duration_seconds:.2f} seconds")
    
    print("\nPhase Status:")
    for phase_name, phase_data in phases.items():
        status = phase_data.get("status", "Unknown")
        status_icon = {"COMPLETED": "✅", "ERROR": "❌", "FAILED": "❌", "SKIPPED": "⏭️"}.get(status, "❓")
        print(f"  {phase_name}: {status_icon} {status}")
        
        if phase_data.get("statistics"):
            stats = phase_data["statistics"]
            print(f"    → Tests: {stats.get('total_tests', 0)}, "
                  f"Success Rate: {stats.get('success_rate', 0)}%")
    
    # 报告文件信息
    if result.get("reports"):
        print(f"\nGenerated Reports: {list(result['reports'].keys())}")
    
    if result.get("saved_files"):
        print("\nSaved Files:")
        for format_name, filepath in result["saved_files"].items():
            print(f"  📄 {format_name}: {filepath}")
    
    print("=" * 80)


def parse_test_cases(test_string: str) -> List[int]:
    """
    解析测试用例字符串，支持多种格式
    
    Args:
        test_string: 测试用例字符串，如 "1,2,5" 或 "1-10" 或 "1,3-5,8"
        
    Returns:
        list: 测试用例编号列表
        
    Examples:
        parse_test_cases("1") -> [1]
        parse_test_cases("1,2,5") -> [1, 2, 5]
        parse_test_cases("1-5") -> [1, 2, 3, 4, 5]
        parse_test_cases("1,3-5,8") -> [1, 3, 4, 5, 8]
    """
    if not test_string:
        return list(range(1, 38))  # 默认全部37项测试
    
    test_cases = set()
    
    # 按逗号分割各个部分
    parts = test_string.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            # 处理范围，如 "1-5"
            try:
                start, end = part.split('-', 1)
                start_num = int(start.strip())
                end_num = int(end.strip())
                
                if start_num > end_num:
                    raise ValueError(f"Invalid range: {part} (start > end)")
                if start_num < 1 or end_num > 37:
                    raise ValueError(f"Test number out of range: {part} (valid: 1-37)")
                
                test_cases.update(range(start_num, end_num + 1))
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError(f"Invalid range format: {part}")
                raise
        else:
            # 处理单个数字
            try:
                test_num = int(part)
                if test_num < 1 or test_num > 37:
                    raise ValueError(f"Test number out of range: {test_num} (valid: 1-37)")
                test_cases.add(test_num)
            except ValueError:
                raise ValueError(f"Invalid test number: {part}")
    
    return sorted(list(test_cases))


def format_test_list(test_cases: List[int]) -> str:
    """
    格式化测试用例列表为易读的字符串
    
    Args:
        test_cases: 测试用例编号列表
        
    Returns:
        str: 格式化的字符串
    """
    if not test_cases:
        return "无"
    
    if len(test_cases) == 37:
        return "全部37项测试"
    
    # 将连续的数字组合成范围
    ranges = []
    start = test_cases[0]
    end = start
    
    for i in range(1, len(test_cases)):
        if test_cases[i] == end + 1:
            end = test_cases[i]
        else:
            if start == end:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{end}")
            start = end = test_cases[i]
    
    # 添加最后一个范围
    if start == end:
        ranges.append(str(start))
    else:
        ranges.append(f"{start}-{end}")
    
    return ", ".join(ranges)


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="KONE测试报告自动化系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py                                    # 使用默认配置，执行全部测试
  python main.py --api-url http://localhost:8080    # 指定API地址
  python main.py --config custom_config.yml         # 指定配置文件
  python main.py --mode direct --verbose            # 使用直接模式，详细日志
  
测试用例选择:
  python main.py --tests 1                          # 只执行测试1
  python main.py --tests 1,2,5                      # 执行测试1、2、5
  python main.py --tests 1-10                       # 执行测试1到10
  python main.py --tests 1,3-5,8,10-12             # 混合格式：1、3到5、8、10到12
  python main.py --dry-run --tests 1-5              # 模拟运行测试1到5
        """
    )
    
    parser.add_argument(
        "--api-url", 
        default="http://localhost:8000",
        help="FastAPI服务地址 (默认: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--config",
        default="virtual_building_config.yml", 
        help="虚拟建筑配置文件路径 (默认: virtual_building_config.yml)"
    )
    
    parser.add_argument(
        "--mode",
        choices=["coordinated", "direct"],
        default="coordinated",
        help="执行模式: coordinated(使用TestCoordinator) 或 direct(直接三阶段) (默认: coordinated)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="./reports",
        help="报告输出目录 (默认: ./reports)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="启用详细日志输出"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true", 
        help="模拟运行，不执行实际测试"
    )
    
    parser.add_argument(
        "--tests", "-t",
        type=str,
        help="指定要执行的测试用例，支持多种格式:\n"
             "  单个测试: --tests 1\n"
             "  多个测试: --tests 1,2,5\n"
             "  范围测试: --tests 1-10\n"
             "  混合格式: --tests 1,3-5,8,10-12\n"
             "  如不指定，则执行全部37项测试"
    )
    
    return parser.parse_args()


async def main():
    """
    主执行函数
    执行三阶段测试流程：
    1. 系统预检查
    2. 执行测试套件  
    3. 生成报告
    """
    # 解析命令行参数
    args = parse_arguments()
    
    # 设置日志
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # 打印横幅和配置信息
    print_banner()
    print_system_info(args)
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # 解析测试用例
    test_cases = None
    if hasattr(args, 'tests') and args.tests:
        try:
            test_cases = parse_test_cases(args.tests)
            logger.info(f"📋 将执行指定的{len(test_cases)}项测试: {format_test_list(test_cases)}")
        except ValueError as e:
            logger.error(f"❌ 测试用例格式错误: {e}")
            print(f"\n❌ 错误: {e}")
            print("\n✅ 正确格式示例:")
            print("   --tests 1          # 单个测试")
            print("   --tests 1,2,5      # 多个测试") 
            print("   --tests 1-10       # 范围测试")
            print("   --tests 1,3-5,8    # 混合格式")
            sys.exit(1)
    
    # 验证配置文件存在
    if not Path(args.config).exists():
        logger.error(f"❌ 配置文件不存在: {args.config}")
        sys.exit(1)
    
    # 模拟运行模式
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - 不会执行实际测试")
        print("✅ 配置验证通过，所有必需文件都存在")
        print("📋 将执行以下操作:")
        print("   1. 系统预检查和组件初始化")
        
        if test_cases:
            print(f"   2. 执行指定的{len(test_cases)}项KONE验证测试: {format_test_list(test_cases)}")
        else:
            print("   2. 执行全部37项KONE验证测试")
            
        print("   3. 生成多格式测试报告")
        print(f"   4. 保存报告到: {output_dir}")
        return
    
    start_time = time.time()
    
    try:
        # 根据模式选择执行方式
        if args.mode == "coordinated":
            result = await run_coordinated_validation(args.api_url, args.config, test_cases)
        else:
            result = await run_direct_validation(args.api_url, args.config, test_cases)
        
        # 打印执行摘要
        print_execution_summary(result)
        
        # 判断执行结果
        overall_status = result.get("summary", {}).get("overall_status", "UNKNOWN")
        
        if overall_status == "COMPLETED":
            logger.info("🎉 KONE验证测试系统执行完成！")
            
            # 输出报告文件位置
            if result.get("saved_files"):
                print("\n📁 报告文件已生成:")
                for format_name, filepath in result["saved_files"].items():
                    print(f"   {format_name}: {filepath}")
            
            sys.exit(0)
            
        elif overall_status == "PARTIALLY_COMPLETED":
            logger.warning("⚠️ KONE验证测试部分完成")
            sys.exit(0)
            
        else:
            logger.error("❌ KONE验证测试执行失败")
            error_msg = result.get("summary", {}).get("error", "Unknown error")
            print(f"错误信息: {error_msg}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⏹️ 用户中断执行")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"❌ 系统执行错误: {e}", exc_info=True)
        sys.exit(1)
        
    finally:
        total_time = time.time() - start_time
        logger.info(f"⏱️ 总执行时间: {total_time:.2f} 秒")


if __name__ == "__main__":
    """
    程序入口点
    支持一键运行KONE测试报告自动化系统
    """
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")
        sys.exit(1)
