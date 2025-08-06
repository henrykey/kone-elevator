# Author: IBC-AI CO.
"""
测试用例映射器验证脚本
"""

import sys
from test_case_mapper import TestCaseMapper, TestCategory


def test_mapper_functionality():
    """测试映射器基础功能"""
    print("🧩 Testing TestCaseMapper functionality...")
    
    # 初始化映射器
    mapper = TestCaseMapper()
    
    # 获取统计信息
    summary = mapper.get_test_summary()
    print(f"📊 Test Summary:")
    print(f"  Total Tests: {summary['total_tests']}")
    print(f"  Building ID: {summary['building_id']}")
    print(f"  Categories: {summary['category_distribution']}")
    print(f"  HTTP Methods: {summary['method_distribution']}")
    
    # 测试特定用例
    test_1 = mapper.get_test_case("Test_1")
    if test_1:
        print(f"\n✅ Test_1 Configuration:")
        print(f"  Name: {test_1.name}")
        print(f"  Method: {test_1.http_method.value}")
        print(f"  Endpoint: {test_1.endpoint}")
        print(f"  Expected Status: {test_1.expected_status}")
    
    # 验证测试用例
    validation = mapper.validate_test_case("Test_1")
    print(f"\n🔍 Test_1 Validation: {'✅ Valid' if validation['valid'] else '❌ Invalid'}")
    
    # 按分类获取测试
    init_tests = mapper.get_tests_by_category(TestCategory.INITIALIZATION)
    print(f"\n📋 Initialization Tests: {len(init_tests)} tests")
    
    return summary['total_tests'] == 37


if __name__ == "__main__":
    success = test_mapper_functionality()
    
    if success:
        print("\n✅ TestCaseMapper verification successful!")
        sys.exit(0)
    else:
        print("\n❌ TestCaseMapper verification failed!")
        sys.exit(1)
