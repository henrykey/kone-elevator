#!/usr/bin/env python
# Author: IBC-AI CO.
"""
独立的报告生成测试脚本
测试KONE验证系统的报告生成功能，不依赖API    for test_id, name, category, duration in skip_tests:
        test_results.append(TestResult(
            test_id=test_id,
            name=name,
            description=f"Test case for {name.lower()}",
            expected_result="Test execution should be successful and return expected results",
            test_result="SKIP",
            status=TestStatus.SKIP,
            duration_ms=duration,
            category=category.value
        ))import asyncio
import logging
from datetime import datetime
from pathlib import Path
from report_generator import ReportGenerator, TestResult
from test_case_mapper import TestCaseMapper, TestCategory
from building_data_manager import BuildingDataManager

# 定义测试状态常量
class TestStatus:
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_mock_test_results() -> list:
    """创建模拟的测试结果数据"""
    test_results = []
    
    # 成功的测试用例
    success_tests = [
        ("TC001", "API初始化测试", TestCategory.INITIALIZATION, 125.5),
        ("TC002", "WebSocket连接测试", TestCategory.INITIALIZATION, 89.2),
        ("TC003", "基础呼叫测试", TestCategory.CALL_MANAGEMENT, 234.1),
        ("TC004", "楼层状态查询", TestCategory.STATUS_MONITORING, 45.8),
        ("TC005", "电梯状态监控", TestCategory.STATUS_MONITORING, 67.3),
        ("TC006", "性能基准测试", TestCategory.PERFORMANCE, 1250.0),
        ("TC007", "并发呼叫测试", TestCategory.PERFORMANCE, 2100.5),
    ]
    
    for test_id, name, category, duration in success_tests:
        test_results.append(TestResult(
            test_id=test_id,
            name=name,
            description=f"Test case for {name.lower()}",
            expected_result="Test execution should be successful and return expected results",
            test_result="PASS",
            status=TestStatus.PASS,
            duration_ms=duration,
            category=category.value,
            response_data={"response_time": duration, "status_code": 200}
        ))
    
    # 失败的测试用例
    failed_tests = [
        ("TC008", "错误代码处理", TestCategory.ERROR_HANDLING, 78.9, "API返回错误代码500"),
        ("TC009", "超时处理测试", TestCategory.ERROR_HANDLING, 5000.0, "请求超时"),
    ]
    
    for test_id, name, category, duration, error in failed_tests:
        test_results.append(TestResult(
            test_id=test_id,
            name=name,
            description=f"Test case for {name.lower()}",
            expected_result="Test execution should be successful and return expected results",
            test_result="FAIL",
            status=TestStatus.FAIL,
            duration_ms=duration,
            category=category.value,
            error_message=error
        ))
    
    # 跳过的测试用例
    skipped_tests = [
        ("TC010", "高级安全测试", TestCategory.ERROR_HANDLING, 0),
        ("TC011", "负载压力测试", TestCategory.PERFORMANCE, 0),
    ]
    
    for test_id, name, category, duration in skipped_tests:
        test_results.append(TestResult(
            test_id=test_id,
            name=name,
            status=TestStatus.SKIP,
            duration_ms=duration,
            category=category.value
        ))
    
    return test_results


async def test_report_generation():
    """测试报告生成功能"""
    
    print("🚀 开始测试KONE报告生成系统...")
    print("=" * 60)
    
    # 1. 创建测试数据
    print("📊 Step 1: 创建模拟测试数据...")
    test_results = create_mock_test_results()
    print(f"   生成了 {len(test_results)} 个测试结果")
    
    # 统计
    passed = sum(1 for t in test_results if t.status == TestStatus.PASS)
    failed = sum(1 for t in test_results if t.status == TestStatus.FAIL)
    skipped = sum(1 for t in test_results if t.status == TestStatus.SKIP)
    
    print(f"   - 通过: {passed}")
    print(f"   - 失败: {failed}")
    print(f"   - 跳过: {skipped}")
    
    # 2. 准备元数据
    print("\n📋 Step 2: 准备测试元数据...")
    metadata = {
        "company": "IBC-AI CO.",
        "test_date": datetime.now().isoformat(),
        "api_version": "2.0.0",
        "test_framework": "KONE SR-API v2.0",
        "total_tests": len(test_results),
        "building_id": "DEMO_BUILDING_001",
        "test_environment": "Simulation Mode",
        "tester": "Automation System",
        "version": "2.0.0"
    }
    
    # 3. 生成报告
    print("\n📄 Step 3: 生成多格式报告...")
    output_dir = Path("./reports")
    output_dir.mkdir(exist_ok=True)
    
    generator = ReportGenerator("IBC-AI CO.")
    
    reports = generator.generate_report(test_results, metadata, str(output_dir))
    
    # 4. 保存报告
    print("\n💾 Step 4: 保存报告文件...")
    
    report_files = {}
    
    for format_type, content in reports.items():
        if format_type == "error":
            print(f"   ❌ 报告生成错误: {content}")
            continue
            
        if format_type == "excel":
            # Excel文件已经保存，content是文件路径
            if "not available" in content:
                print(f"   ⚠️ Excel: {content}")
                continue
            else:
                report_files[format_type] = content
                filepath = Path(content)
                print(f"   ✅ {format_type.upper()}: {filepath} ({filepath.stat().st_size} 字节)")
                continue
                
        # 保存其他格式文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"kone_validation_report_{timestamp}.{format_type}"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        report_files[format_type] = str(filepath)
        print(f"   ✅ {format_type.upper()}: {filepath} ({len(content)} 字符)")
    
    # 5. 显示报告预览
    print("\n📖 Step 5: 报告内容预览...")
    
    if "markdown" in reports:
        print("\n--- Markdown 报告预览 ---")
        lines = reports["markdown"].split('\n')
        for i, line in enumerate(lines[:20]):  # 显示前20行
            print(line)
        if len(lines) > 20:
            print("...")
    
    # 6. 生成总结
    print("\n" + "=" * 60)
    print("✅ 报告生成测试完成!")
    print(f"📁 报告保存位置: {output_dir.absolute()}")
    print(f"📄 生成的文件:")
    for format_type, filepath in report_files.items():
        print(f"   - {format_type.upper()}: {Path(filepath).name}")
    
    return report_files


async def test_building_integration():
    """测试与建筑数据管理器的集成"""
    
    print("\n🏢 测试建筑数据集成...")
    
    try:
        # 初始化建筑数据管理器
        building_manager = BuildingDataManager()
        
        if building_manager.building_config:
            building_id = building_manager.building_config.get('building', {}).get('id', 'Unknown')
            floors = len(building_manager.floor_area_map)
            print(f"   ✅ 建筑配置加载成功: {building_id}")
            print(f"   🏗️ 楼层数量: {floors}")
            
            # 测试数据生成
            test_data = building_manager.generate_test_data("call_elevator", 5)
            print(f"   📊 生成测试数据: {len(test_data)} 条记录")
            
        else:
            print("   ⚠️ 建筑配置文件未找到，使用默认配置")
            
    except Exception as e:
        print(f"   ❌ 建筑数据集成错误: {e}")


async def test_mapper_integration():
    """测试与测试用例映射器的集成"""
    
    print("\n🗺️ 测试用例映射器集成...")
    
    try:
        mapper = TestCaseMapper()
        
        # 获取所有测试用例
        all_tests = mapper.get_all_test_cases()
        print(f"   ✅ 测试用例总数: {len(all_tests)}")
        
        # 按类别统计
        by_category = {}
        for test in all_tests:
            category = test.category.value
            by_category[category] = by_category.get(category, 0) + 1
        
        print("   📋 按类别分布:")
        for category, count in by_category.items():
            print(f"      - {category}: {count} 个测试")
            
        # 验证特定测试用例
        test_case = mapper.get_test_case("initialization_001") 
        if test_case:
            print(f"   🔍 示例测试用例: {test_case.name}")
        
    except Exception as e:
        print(f"   ❌ 测试映射器集成错误: {e}")


async def main():
    """主测试函数"""
    
    print("🎯 KONE 报告生成系统 - 集成测试")
    print("Author: IBC-AI CO.")
    print("=" * 60)
    
    try:
        # 测试建筑数据集成
        await test_building_integration()
        
        # 测试映射器集成
        await test_mapper_integration()
        
        # 测试报告生成
        report_files = await test_report_generation()
        
        print("\n🎉 所有测试完成!")
        print("系统运行正常，报告生成功能可用。")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
