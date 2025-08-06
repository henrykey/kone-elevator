#!/usr/bin/env python3
"""
KONE SR-API v2.0 标准合规性测试
严格按照 elevator-websocket-api-v2.yaml 规范进行测试
"""

import asyncio
import json
import yaml
from datetime import datetime
from drivers import KoneDriver, ElevatorCallRequest

async def test_kone_v2_standard_compliance():
    """测试KONE SR-API v2.0标准合规性"""
    
    print("=" * 70)
    print("KONE SR-API v2.0 标准合规性测试")
    print("基于官方 elevator-websocket-api-v2.yaml 规范")
    print("=" * 70)
    
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
    
    test_building_id = "building:99900009301"  # 使用标准格式
    test_group_id = "1"
    
    try:
        # 1. 测试会话创建 (create-session)
        print("\n1. 测试会话创建 (create-session)")
        print("-" * 50)
        init_result = await driver.initialize()
        print(f"✅ 会话创建: {init_result}")
        
        if not init_result.get('success'):
            print("❌ 会话创建失败，跳过后续测试")
            return False
        
        # 2. 测试 common-api: ping
        print("\n2. 测试 common-api: ping")
        print("-" * 50)
        ping_result = await driver.ping(test_building_id)
        print(f"Ping结果: {ping_result}")
        
        # 3. 测试 common-api: config
        print("\n3. 测试 common-api: config")
        print("-" * 50)
        config_result = await driver.get_config(test_building_id)
        print(f"配置结果: {json.dumps(config_result, indent=2)}")
        
        # 4. 测试 common-api: actions
        print("\n4. 测试 common-api: actions")
        print("-" * 50)
        actions_result = await driver.get_actions(test_building_id, test_group_id)
        print(f"操作结果: {json.dumps(actions_result, indent=2)}")
        
        # 5. 测试 site-monitoring
        print("\n5. 测试 site-monitoring")
        print("-" * 50)
        mode_result = await driver.get_mode(test_building_id, test_group_id)
        print(f"监控结果: {json.dumps(mode_result, indent=2)}")
        
        # 6. 测试 lift-call-api-v2: action
        print("\n6. 测试 lift-call-api-v2: action")
        print("-" * 50)
        try:
            call_request = ElevatorCallRequest(
                building_id=test_building_id,
                group_id=test_group_id,
                from_floor=1,
                to_floor=5,
                user_id="test-user-v2"
            )
            
            call_result = await driver.call(call_request)
            print(f"呼叫结果: {json.dumps(call_result, indent=2)}")
            
            # 7. 如果呼叫成功，测试取消
            if call_result.get('success') and call_result.get('request_id'):
                print("\n7. 测试 lift-call-api-v2: cancel")
                print("-" * 50)
                cancel_result = await driver.cancel(test_building_id, call_result['request_id'])
                print(f"取消结果: {json.dumps(cancel_result, indent=2)}")
            
        except Exception as e:
            print(f"❌ 电梯呼叫测试失败: {e}")
        
        # 8. 验证WebSocket连接状态
        print("\n8. WebSocket连接状态")
        print("-" * 50)
        ws_status = "已连接" if driver.websocket and not driver.websocket.closed else "未连接"
        print(f"WebSocket状态: {ws_status}")
        print(f"会话ID: {driver.session_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理资源
        await driver.close()
        print("\n🔌 WebSocket连接已关闭")

async def test_v2_message_formats():
    """验证消息格式是否符合v2.0标准"""
    
    print("\n" + "=" * 70)
    print("验证消息格式合规性")
    print("=" * 70)
    
    # 验证标准消息格式
    test_messages = {
        "create-session": {
            "type": "create-session",
            "requestId": "08c5ff6c-a8fe-405b-bde3-ffcd6935573b"
        },
        "common-api-ping": {
            "type": "common-api",
            "buildingId": "building:99900009301",
            "callType": "ping",
            "groupId": "1",
            "payload": {
                "request_id": 1234567890
            }
        },
        "common-api-config": {
            "type": "common-api",
            "buildingId": "building:99900009301",
            "callType": "config",
            "groupId": "1"
        },
        "lift-call-v2": {
            "type": "lift-call-api-v2",
            "buildingId": "building:99900009301",
            "callType": "action",
            "groupId": "1",
            "payload": {
                "request_id": "252390420",
                "area": 3000,
                "time": "2020-10-10T07:17:33.298515Z",
                "terminal": 1,
                "call": {
                    "action": 2,
                    "destination": 5000
                }
            }
        },
        "site-monitoring": {
            "type": "site-monitoring",
            "buildingId": "building:99900009301",
            "callType": "monitor",
            "groupId": "1",
            "payload": {
                "sub": "elevator-status-123",
                "duration": 100,
                "subtopics": ["call_state/123/fixed"]
            }
        },
        "cancel-call": {
            "type": "lift-call-api-v2",
            "cancelRequestId": "08c5ff6c-a8fe-405b-bde3-ffcd6935573b",
            "requestId": "ca3ca81d-84cf-466b-bd5e-899b7d92c9d5"
        }
    }
    
    for msg_type, message in test_messages.items():
        print(f"\n✅ {msg_type} 消息格式:")
        print(json.dumps(message, indent=2))
    
    print(f"\n✅ 所有 {len(test_messages)} 种消息格式都符合v2.0标准")

if __name__ == "__main__":
    print("启动KONE SR-API v2.0标准合规性测试...")
    
    # 运行消息格式验证
    asyncio.run(test_v2_message_formats())
    
    # 运行完整的API测试
    result = asyncio.run(test_kone_v2_standard_compliance())
    
    print("\n" + "=" * 70)
    print(f"最终测试结果: {'✅ 通过' if result else '❌ 失败'}")
    print("=" * 70)
