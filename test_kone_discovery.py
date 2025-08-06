#!/usr/bin/env python3
"""
KONE API 发现和探索测试
用于发现可用的建筑ID、配置和测试数据
"""

import asyncio
import yaml
import json
from datetime import datetime
from drivers import KoneDriver

async def test_kone_discovery():
    """探索KONE API的可用资源"""
    
    # 加载配置
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    kone_config = config['kone']
    driver = KoneDriver(
        client_id=kone_config['client_id'],
        client_secret=kone_config['client_secret'],
        token_endpoint=kone_config['token_endpoint'],
        ws_endpoint=kone_config['ws_endpoint']
    )
    
    try:
        print("🔍 KONE API 资源发现测试")
        print("=" * 60)
        
        # 1. 测试token获取和缓存
        print("\n1. 测试Token获取和缓存...")
        token = await driver.get_access_token()
        print(f"✅ Token获取成功: {token[:50]}...")
        
        # 2. 测试WebSocket连接
        print("\n2. 测试WebSocket连接...")
        if await driver._connect_websocket():
            print("✅ WebSocket连接成功")
        else:
            print("❌ WebSocket连接失败")
            return False
        
        # 3. 创建会话
        print("\n3. 创建会话...")
        session_result = await driver.initialize()
        if session_result.get('success'):
            print(f"✅ 会话创建成功: {session_result.get('session_id')}")
        else:
            print(f"❌ 会话创建失败: {session_result}")
            return False
        
        # 4. 测试不同的建筑ID（常见的测试格式）
        test_building_ids = [
            "building:99900009301",  # 文档示例
            "building:9990000951",   # 另一个文档示例
            "building:test",         # 测试格式
            "building:demo",         # 演示格式
            "test-building",         # 简单格式
            "demo-building",         # 演示格式
        ]
        
        print("\n4. 测试不同建筑ID的可用性...")
        valid_buildings = []
        
        for building_id in test_building_ids:
            try:
                print(f"\n  测试建筑: {building_id}")
                
                # 测试ping
                ping_result = await driver.ping(building_id)
                if ping_result.get('success'):
                    print(f"    ✅ Ping成功 - 延迟: {ping_result.get('latency_ms', 'N/A')}ms")
                    valid_buildings.append(building_id)
                    
                    # 如果ping成功，尝试获取配置
                    config_result = await driver.get_config(building_id)
                    if config_result.get('success'):
                        print(f"    ✅ 配置获取成功")
                        print(f"    配置数据: {json.dumps(config_result.get('config', {}), indent=6)}")
                        
                        # 尝试获取actions
                        actions_result = await driver.get_actions(building_id)
                        if actions_result.get('success'):
                            print(f"    ✅ Actions获取成功")
                            print(f"    Actions: {json.dumps(actions_result.get('actions', {}), indent=6)}")
                        else:
                            print(f"    ❌ Actions获取失败: {actions_result.get('error')}")
                    else:
                        print(f"    ❌ 配置获取失败: {config_result.get('error')}")
                else:
                    print(f"    ❌ Ping失败: {ping_result.get('error')}")
                    
            except Exception as e:
                print(f"    ❌ 测试异常: {e}")
        
        # 5. 总结发现的资源
        print(f"\n5. 发现总结")
        print("=" * 60)
        if valid_buildings:
            print(f"✅ 发现 {len(valid_buildings)} 个可用建筑:")
            for building in valid_buildings:
                print(f"  - {building}")
            
            # 使用第一个有效建筑进行更详细的测试
            main_building = valid_buildings[0]
            print(f"\n6. 使用建筑 '{main_building}' 进行详细测试...")
            
            # 测试电梯组
            test_groups = ["1", "2", "A", "B"]
            for group_id in test_groups:
                try:
                    mode_result = await driver.get_mode(main_building, group_id)
                    if mode_result.get('success'):
                        print(f"  ✅ 组 {group_id}: {mode_result.get('mode')} - 模式: {mode_result.get('lift_mode')}")
                    else:
                        print(f"  ❌ 组 {group_id}: {mode_result.get('error')}")
                except Exception as e:
                    print(f"  ❌ 组 {group_id} 测试异常: {e}")
        else:
            print("❌ 未发现任何可用的建筑ID")
            print("\n可能的原因:")
            print("- 需要特定的建筑ID授权")
            print("- 测试环境中没有虚拟建筑")
            print("- 需要联系KONE获取测试建筑ID")
        
        return len(valid_buildings) > 0
        
    except Exception as e:
        print(f"❌ 发现测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await driver.close()

async def test_token_caching():
    """测试token缓存功能"""
    print("\n" + "=" * 60)
    print("Token缓存功能测试")
    print("=" * 60)
    
    # 加载配置
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    kone_config = config['kone']
    
    # 第一次获取token
    print("\n1. 第一次获取token...")
    driver1 = KoneDriver(
        client_id=kone_config['client_id'],
        client_secret=kone_config['client_secret'],
        token_endpoint=kone_config['token_endpoint'],
        ws_endpoint=kone_config['ws_endpoint']
    )
    
    token1 = await driver1.get_access_token()
    print(f"✅ Token1: {token1[:50]}...")
    
    # 第二次获取token（应该使用缓存）
    print("\n2. 第二次获取token（应该使用缓存）...")
    driver2 = KoneDriver(
        client_id=kone_config['client_id'],
        client_secret=kone_config['client_secret'],
        token_endpoint=kone_config['token_endpoint'],
        ws_endpoint=kone_config['ws_endpoint']
    )
    
    token2 = await driver2.get_access_token()
    print(f"✅ Token2: {token2[:50]}...")
    
    if token1 == token2:
        print("✅ Token缓存工作正常 - 两次获取的token相同")
    else:
        print("❌ Token缓存可能有问题 - 两次获取的token不同")
    
    # 检查配置文件中的缓存
    print("\n3. 检查配置文件中的token缓存...")
    with open('config.yaml', 'r') as f:
        updated_config = yaml.safe_load(f)
    
    cached_token = updated_config.get('kone', {}).get('cached_token', {})
    if cached_token.get('access_token'):
        print(f"✅ 配置文件中存在缓存token: {cached_token['access_token'][:50]}...")
        print(f"✅ 过期时间: {cached_token.get('expires_at')}")
    else:
        print("❌ 配置文件中没有找到缓存token")

if __name__ == "__main__":
    print("🚀 开始KONE API发现和测试...")
    
    # 运行发现测试
    asyncio.run(test_kone_discovery())
    
    # 运行token缓存测试
    asyncio.run(test_token_caching())
    
    print("\n🏁 测试完成!")
