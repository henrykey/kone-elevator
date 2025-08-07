#!/usr/bin/env python3
"""
简单测试：KONE API 是否支持获取建筑配置
目标：仅验证 API 能力，不修改现有代码
"""

import asyncio
import json
import yaml
from drivers import KoneDriver

async def test_building_config_api():
    """测试是否能从 KONE API 获取建筑配置"""
    print("🔍 测试 KONE API 建筑配置获取能力")
    print("=" * 50)
    
    # 1. 加载现有配置
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    kone_config = config['kone']
    
    # 2. 创建驱动程序（不修改）
    driver = KoneDriver(
        client_id=kone_config['client_id'],
        client_secret=kone_config['client_secret']
    )
    
    # 3. 初始化连接
    print("🔌 初始化连接...")
    init_result = await driver.initialize()
    if not init_result['success']:
        print(f"❌ 连接失败: {init_result}")
        return
    
    print("✅ 连接成功")
    
    # 4. 测试不同的配置请求格式
    building_id = "L1QinntdEOg"
    test_formats = [
        {
            "name": "格式1: common-api + config (带groupId)",
            "message": {
                "type": "common-api",
                "callType": "config", 
                "buildingId": f"building:{building_id}",
                "groupId": "1"
            }
        },
        {
            "name": "格式2: common-api + actions (带groupId)",
            "message": {
                "type": "common-api",
                "callType": "actions",
                "buildingId": f"building:{building_id}",
                "groupId": "1"
            }
        },
        {
            "name": "格式3: common-api + ping (带groupId)",
            "message": {
                "type": "common-api",
                "callType": "ping",
                "buildingId": f"building:{building_id}",
                "groupId": "1"
            }
        }
    ]
    
    # 5. 逐个测试
    for i, test in enumerate(test_formats, 1):
        print(f"\n📋 测试 {i}: {test['name']}")
        print(f"请求: {json.dumps(test['message'], indent=2)}")
        
        try:
            # 使用现有的私有方法（仅测试用），增加超时时间
            response = await driver._send_message(test['message'], timeout=30)
            print("响应:")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            
            # 简单分析响应
            if response.get('type') == 'reply' and 'data' in response:
                data = response['data']
                print(f"✅ 成功! 数据键: {list(data.keys())}")
                
                # 检查是否包含建筑配置信息
                if any(key in data for key in ['floors', 'areas', 'groups', 'elevators', 'topology']):
                    print(f"🎉 发现建筑配置数据!")
                    return test, response
                    
            elif response.get('type') == 'error':
                print(f"❌ 错误: {response.get('message', 'Unknown error')}")
            else:
                print(f"⚠️  非预期响应类型: {response.get('type')}")
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")
    
    print(f"\n📊 测试完成 - 没有找到有效的建筑配置 API")
    return None, None

async def main():
    """主函数"""
    try:
        success_format, response = await test_building_config_api()
        
        if success_format:
            print(f"\n🎉 结论: KONE API 支持获取建筑配置!")
            print(f"✅ 成功格式: {success_format['name']}")
            print(f"📋 可用于获取楼层、电梯等信息")
        else:
            print(f"\n🤔 结论: 未找到支持建筑配置的 API 格式")
            print(f"💡 可能需要查阅更详细的 API 文档")
            
    except Exception as e:
        print(f"❌ 测试出错: {e}")

if __name__ == "__main__":
    asyncio.run(main())
