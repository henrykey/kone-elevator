#!/usr/bin/env python
# Author: IBC-AI CO.
"""
KONE API /resource endpoint 查询可用 building id
使用新的 get_resources() 方法
"""

import asyncio
import yaml
import json
from drivers import KoneDriver

async def get_building_ids():
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
        # 查询 /resource endpoint
        print("查询可用 building id ...")
        result = await driver.get_resources()

        # 输出结果
        print("API返回的原始数据:")
        print(json.dumps(result, indent=2))
        
        # 尝试解析 building id
        if isinstance(result, dict):
            if 'buildings' in result:
                print("\n可用 building id 列表:")
                for building in result['buildings']:
                    building_id = building.get('id')
                    building_name = building.get('name', 'N/A')
                    building_desc = building.get('desc', 'N/A')
                    print(f"- ID: {building_id}")
                    print(f"  名称: {building_name}")
                    print(f"  描述: {building_desc}")
                    
                    # 显示组信息
                    if 'groups' in building:
                        for group in building['groups']:
                            group_id = group.get('id')
                            print(f"  组ID: {group_id}")
                    print()
            elif 'building_ids' in result:
                print("\n可用 building id 列表:")
                for bid in result['building_ids']:
                    print(f"- {bid}")
            elif 'building_id' in result:
                print(f"\n可用 building id: {result['building_id']}")
            else:
                print("\n未找到 building_id 或 building_ids 字段")
                print("可用字段:", list(result.keys()))
        else:
            print("\n返回数据不是字典格式")

    except Exception as e:
        print(f"查询失败: {e}")
    
    finally:
        await driver.close()

if __name__ == "__main__":
    asyncio.run(get_building_ids())
