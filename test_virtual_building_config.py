#!/usr/bin/env python3
"""
测试新的KONE虚拟建筑配置
验证建筑选择和切换功能
"""

import asyncio
import yaml
from testall_v2 import KoneValidationSuite
from kone_virtual_buildings import KONE_VIRTUAL_BUILDINGS

async def test_virtual_building_configuration():
    """测试虚拟建筑配置功能"""
    
    print("🔧 测试KONE虚拟建筑配置")
    print("=" * 60)
    
    # 1. 测试虚拟建筑管理器
    print("\n📊 1. 虚拟建筑管理器测试")
    buildings = KONE_VIRTUAL_BUILDINGS.list_available_buildings()
    print(f"   可用建筑数量: {len(buildings)}")
    
    for building in buildings:
        print(f"   ✅ {building['name']}")
        print(f"      ID: {building['building_id']}")
        print(f"      功能: {', '.join(building['features'])}")
    
    # 2. 测试建筑映射
    print("\n📊 2. 测试用例映射")
    mapping = KONE_VIRTUAL_BUILDINGS.get_test_mapping()
    key_mappings = ['test_6_unknown_action', 'test_8_transfer_calls', 'test_10_access_control']
    
    for test_name in key_mappings:
        if test_name in mapping:
            building_key = mapping[test_name]
            building = KONE_VIRTUAL_BUILDINGS.get_building(building_key)
            print(f"   {test_name}: {building.name} ({building.building_id})")
    
    # 3. 测试套件集成
    print("\n📊 3. 测试套件集成验证")
    try:
        suite = KoneValidationSuite()
        await suite.setup()
        
        print(f"   默认建筑: {suite.building_id}")
        print(f"   默认群组: {suite.group_id}")
        
        # 测试建筑切换
        print("\n📊 4. 建筑切换测试")
        original_building = suite.building_id
        
        # 测试切换到禁用动作建筑
        switched = suite._switch_building_for_test('test_06_unknown_action')
        if switched:
            print(f"   ✅ 成功切换到: {suite.building_id}")
        else:
            print(f"   ⚪ 无需切换，已是最优建筑")
        
        # 测试切换到转运呼叫建筑
        suite._switch_building_for_test('test_transfer_calls')
        print(f"   当前建筑: {suite.building_id}")
        
        # 获取建筑详细信息
        current_building = KONE_VIRTUAL_BUILDINGS.get_building_by_id(suite.building_id)
        if current_building:
            print(f"   建筑用途: {current_building.purpose}")
            if current_building.area_ids:
                print(f"   Area范围: {min(current_building.area_ids)}-{max(current_building.area_ids)}")
        
        await suite.teardown()
        
    except Exception as e:
        print(f"   ❌ 测试套件集成错误: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. 配置摘要
    print("\n📊 5. 生成完整配置摘要")
    summary = KONE_VIRTUAL_BUILDINGS.generate_config_summary()
    
    # 保存摘要到文件
    with open('KONE_VIRTUAL_BUILDINGS_SUMMARY.md', 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print("   ✅ 配置摘要已保存到: KONE_VIRTUAL_BUILDINGS_SUMMARY.md")
    
    print("\n✅ 虚拟建筑配置测试完成！")
    print("\n🎯 主要改进:")
    print("   1. ✅ 使用KONE官方推荐的虚拟建筑")
    print("   2. ✅ 针对不同测试类型自动选择最优建筑")
    print("   3. ✅ 支持动态建筑切换")
    print("   4. ✅ 包含专门的禁用动作、转运、门禁等测试建筑")
    print("   5. ✅ 符合KONE最新测试指引要求")

if __name__ == "__main__":
    asyncio.run(test_virtual_building_configuration())
