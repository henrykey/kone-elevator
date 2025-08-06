# Author: IBC-AI CO.
"""
虚拟建筑数据管理器验证脚本
"""

import sys
from building_data_manager import BuildingDataManager


def test_building_manager():
    """测试建筑数据管理器功能"""
    print("🏢 Testing BuildingDataManager functionality...")
    
    # 初始化管理器
    manager = BuildingDataManager()
    
    # 获取建筑概要
    summary = manager.get_building_summary()
    print(f"📊 Building Summary:")
    print(f"  Building ID: {summary['building_id']}")
    print(f"  Total Floors: {summary['total_floors']}")
    print(f"  Total Area IDs: {summary['total_area_ids']}")
    print(f"  Elevator Groups: {summary['elevator_groups']}")
    
    if summary['floor_range']['min_area_id']:
        print(f"  Floor Range: {summary['floor_range']['min_area_id']} - {summary['floor_range']['max_area_id']}")
    
    # 测试楼层转换
    test_floor = 3
    area_id = manager.floor_to_area_id(test_floor)
    back_to_floor = manager.area_id_to_floor(area_id)
    print(f"\n🔄 Floor Conversion Test:")
    print(f"  Floor {test_floor} -> Area ID {area_id} -> Floor {back_to_floor}")
    
    # 测试随机楼层对
    print(f"\n🎲 Random Floor Pairs:")
    for i in range(3):
        source, dest = manager.get_random_floor_pair()
        print(f"  Pair {i+1}: {source} -> {dest}")
    
    # 测试楼层序列
    sequence = manager.get_random_floor_sequence(4)
    print(f"\n📋 Random Floor Sequence: {sequence}")
    
    # 测试无效楼层
    invalid_floor = manager.get_invalid_floor_id()
    print(f"\n❌ Invalid Floor ID for testing: {invalid_floor}")
    
    # 测试楼层验证
    valid_floors = manager.get_valid_floors()
    if valid_floors:
        test_valid = manager.validate_area_id(valid_floors[0])
        test_invalid = manager.validate_area_id(invalid_floor)
        print(f"\n✅ Validation Tests:")
        print(f"  Valid floor {valid_floors[0]}: {test_valid}")
        print(f"  Invalid floor {invalid_floor}: {test_invalid}")
    
    # 获取测试数据集
    test_data = manager.get_test_data_set()
    print(f"\n🧪 Test Data Set:")
    print(f"  Valid floors: {test_data['valid_floors']}")
    print(f"  Random pairs: {test_data['random_pairs']}")
    print(f"  Elevator groups: {test_data['elevator_groups']}")
    
    return summary['total_area_ids'] > 0


if __name__ == "__main__":
    success = test_building_manager()
    
    if success:
        print("\n✅ BuildingDataManager verification successful!")
        sys.exit(0)
    else:
        print("\n❌ BuildingDataManager verification failed!")
        sys.exit(1)
