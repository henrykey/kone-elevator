#!/usr/bin/env python3
"""
专门测试 KONE API 配置获取
目标：验证是否能从 API 获取楼层、电梯等建筑配置信息
"""

import asyncio
import json
import yaml
from drivers import KoneDriver

async def test_kone_config_detailed():
    """详细测试 KONE API 配置获取"""
    print("🔧 KONE API 配置获取详细测试")
    print("=" * 50)
    
    # 1. 加载配置
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    kone_config = config['kone']
    
    # 2. 创建驱动程序
    driver = KoneDriver(
        client_id=kone_config['client_id'],
        client_secret=kone_config['client_secret']
    )
    
    # 3. 初始化连接
    print("🔌 正在连接...")
    init_result = await driver.initialize()
    if not init_result['success']:
        print(f"❌ 连接失败: {init_result}")
        return
    print("✅ 连接成功")
    
    # 4. 测试建筑ID
    building_id = "L1QinntdEOg"
    
    # 5. 测试各种配置调用
    test_calls = [
        {
            "name": "🏗️  配置获取 (config)",
            "message": {
                "type": "common-api",
                "callType": "config",
                "buildingId": f"building:{building_id}",
                "groupId": "1"
            }
        },
        {
            "name": "🎯 操作列表 (actions)",
            "message": {
                "type": "common-api", 
                "callType": "actions",
                "buildingId": f"building:{building_id}",
                "groupId": "1"
            }
        },
        {
            "name": "📍 Ping 测试",
            "message": {
                "type": "common-api",
                "callType": "ping", 
                "buildingId": f"building:{building_id}",
                "groupId": "1"
            }
        }
    ]
    
    results = []
    
    for test in test_calls:
        print(f"\n{test['name']}")
        print("-" * 30)
        print(f"📤 请求: {json.dumps(test['message'], indent=2)}")
        
        try:
            # 发送请求
            response = await driver._send_message(test['message'], timeout=20)
            print(f"📥 响应: {json.dumps(response, indent=2, ensure_ascii=False)}")
            
            # 分析响应
            status = response.get('statusCode', 'N/A')
            if status == 201:
                print(f"✅ 状态: 成功 ({status})")
                data = response.get('data', {})
                
                # 检查数据内容
                if len(data) > 1:  # 不只是时间戳
                    print(f"📊 数据键: {list(data.keys())}")
                    if any(key in data for key in ['floors', 'areas', 'config', 'groups', 'elevators', 'call_types']):
                        print(f"🎉 发现建筑配置相关数据!")
                        results.append((test['name'], response))
                else:
                    print(f"⚠️  只收到基础响应，无详细配置数据")
            else:
                print(f"⚠️  状态: {status}")
                
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    # 6. 尝试获取更多详细信息
    print(f"\n🔍 尝试获取更详细信息...")
    
    # 测试不同的参数组合
    advanced_tests = [
        {
            "name": "配置 + 详细参数",
            "message": {
                "type": "common-api",
                "callType": "config",
                "buildingId": f"building:{building_id}",
                "groupId": "1",
                "payload": {
                    "includeFloors": True,
                    "includeElevators": True,
                    "detailed": True
                }
            }
        },
        {
            "name": "拓扑结构 (topology)",
            "message": {
                "type": "common-api",
                "callType": "topology", 
                "buildingId": f"building:{building_id}",
                "groupId": "1"
            }
        }
    ]
    
    for test in advanced_tests:
        print(f"\n🧪 {test['name']}")
        try:
            response = await driver._send_message(test['message'], timeout=15)
            status = response.get('statusCode')
            print(f"状态: {status}")
            if status in [200, 201]:
                data = response.get('data', {})
                if data and len(data) > 1:
                    print(f"📊 响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"❌ {e}")
    
    # 7. 总结
    print(f"\n📋 测试总结")
    print("=" * 30)
    
    if results:
        print(f"✅ 发现 {len(results)} 个成功的配置调用:")
        for name, response in results:
            print(f"   - {name}")
        print(f"\n💡 KONE API 确实支持配置获取，但返回的数据有限")
    else:
        print(f"❌ 未发现包含详细配置数据的调用")
        print(f"💡 API 虽然响应成功，但不提供详细的楼层/电梯配置")
    
    print(f"\n🎯 结论: 静态 YAML 配置仍然是最可靠的选择")
    
    await driver.close()

if __name__ == "__main__":
    asyncio.run(test_kone_config_detailed())
