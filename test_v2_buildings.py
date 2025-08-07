#!/usr/bin/env python
# Author: IBC-AI CO.
"""
KONE API ping测试 - 使用v2建筑筛选
优先选择纯v2版本的虚拟建筑进行测试
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from drivers import KoneDriver
import yaml

# 适中日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def ping_test_with_v2_buildings():
    """使用v2建筑进行ping测试"""
    
    print("🚀 KONE API Ping 测试 (v2建筑筛选)")
    print("=" * 45)
    
    try:
        # 加载配置
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        kone_config = config['kone']
        
        # 创建驱动
        driver = KoneDriver(
            client_id=kone_config['client_id'],
            client_secret=kone_config['client_secret']
        )
        
        try:
            # 获取可用的building IDs
            print("🔍 获取可用的building IDs...")
            resources = await driver.get_resources()
            
            if 'buildings' not in resources or not resources['buildings']:
                print("❌ 未找到可用的building IDs")
                return False
            
            # 筛选v2建筑
            pure_v2_buildings = []
            v2_supported_buildings = []
            
            print(f"📋 分析 {len(resources['buildings'])} 个建筑...")
            
            for building in resources['buildings']:
                building_id = building['id']
                building_name = building['name']
                building_desc = building.get('desc', '').lower()
                
                print(f"\n🏢 建筑: {building_id}")
                print(f"   名称: {building_name}")
                print(f"   描述: {building.get('desc', 'N/A')}")
                
                # 检查是否是纯v2建筑
                if 'v2' in building_desc:
                    pure_v2_buildings.append(building)
                    print(f"   ✅ 纯v2建筑")
                else:
                    # 检查组是否支持v2
                    has_v2_group = False
                    if 'groups' in building:
                        for group in building['groups']:
                            group_desc = group.get('desc', '').lower()
                            if 'v2' in group_desc:
                                v2_supported_buildings.append(building)
                                has_v2_group = True
                                print(f"   🔄 组支持v2: {group.get('desc')}")
                                break
                    
                    if not has_v2_group:
                        print(f"   ⚠️ 非v2建筑")
            
            print(f"\n📊 筛选结果:")
            print(f"🔥 纯v2建筑: {len(pure_v2_buildings)} 个")
            print(f"🔄 v2支持建筑: {len(v2_supported_buildings)} 个")
            
            # 选择测试建筑
            if pure_v2_buildings:
                test_building = pure_v2_buildings[0]
                print(f"\n🎯 选择纯v2建筑: {test_building['id']}")
            elif v2_supported_buildings:
                test_building = v2_supported_buildings[0]
                print(f"\n🔄 选择v2支持建筑: {test_building['id']}")
            else:
                print("\n❌ 未找到v2版本的建筑")
                return False
            
            building_id = test_building['id']
            building_name = test_building.get('name', 'N/A')
            building_desc = test_building.get('desc', 'N/A')
            
            print(f"📍 建筑名称: {building_name}")
            print(f"📝 建筑描述: {building_desc}")
            
            # 显示组信息
            if 'groups' in test_building:
                print(f"🏢 组信息:")
                for group in test_building['groups']:
                    group_id = group.get('id')
                    group_desc = group.get('desc', 'N/A')
                    products = group.get('products', [])
                    print(f"  - {group_id}: {group_desc}")
                    print(f"    产品: {', '.join(products)}")
                    if 'robotcall' in products:
                        print(f"    ✅ 支持robotcall")
            
            # 初始化WebSocket连接
            print("\n🔌 初始化WebSocket连接...")
            init_result = await driver.initialize()
            
            if not init_result['success']:
                print("❌ 初始化失败")
                return False
            
            print(f"✅ 会话创建成功: {init_result.get('session_id')}")
            
            # 执行ping测试
            print(f"\n📡 测试ping: {building_id}")
            
            start_time = time.time()
            result = await driver.ping(building_id)
            end_time = time.time()
            
            total_time = (end_time - start_time) * 1000
            
            print(f"📥 响应 (耗时: {total_time:.2f}ms):")
            print(json.dumps(result, indent=2))
            
            if result.get('success'):
                print("\n🎉 Ping成功!")
                print("✅ v2建筑筛选有效，API工作正常!")
                return True
            else:
                print("\n⚠️ Ping失败")
                status_code = result.get('status_code')
                error_msg = result.get('error', '')
                
                if status_code == 500 and 'timeout' in error_msg.lower():
                    print("🔍 超时分析:")
                    print("  - 建筑确实存在且支持v2")
                    print("  - WebSocket连接正常")
                    print("  - 可能是服务器端问题")
                
                return False
            
        except Exception as e:
            print(f"💥 测试异常: {e}")
            return False
        
        finally:
            await driver.close()
    
    except Exception as e:
        print(f"❌ 配置错误: {e}")
        return False


async def main():
    """主函数"""
    
    print("🚀 KONE API v2建筑测试")
    print("Author: IBC-AI CO.")
    print("=" * 40)
    
    success = await ping_test_with_v2_buildings()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 v2建筑测试成功!")
    else:
        print("⚠️ 测试完成，发现了一些问题")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
