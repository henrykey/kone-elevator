#!/usr/bin/env python3
"""
简单的WebSocket连接和会话测试
逐步调试KONE API连接问题
"""

import asyncio
import websockets
import json
import uuid
import yaml
import base64
import requests
from datetime import datetime

async def test_basic_websocket():
    """基础WebSocket连接和消息测试"""
    
    # 加载配置
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    kone_config = config['kone']
    
    try:
        print("🔍 基础WebSocket连接测试")
        print("=" * 50)
        
        # 1. 获取token
        print("\n1. 获取访问token...")
        credentials = f"{kone_config['client_id']}:{kone_config['client_secret']}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        token_response = requests.post(
            kone_config['token_endpoint'],
            data={'grant_type': 'client_credentials'},
            headers={
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )
        
        if token_response.status_code == 200:
            token_data = token_response.json()
            access_token = token_data['access_token']
            print(f"✅ Token获取成功: {access_token[:50]}...")
        else:
            print(f"❌ Token获取失败: {token_response.status_code}")
            return False
        
        # 2. 建立WebSocket连接
        print(f"\n2. 建立WebSocket连接...")
        ws_url = f"{kone_config['ws_endpoint']}?accessToken={access_token}"
        print(f"连接URL: {ws_url[:100]}...")
        
        async with websockets.connect(
            ws_url,
            subprotocols=['koneapi'],
            ping_interval=30,
            ping_timeout=10,
            close_timeout=10
        ) as websocket:
            print(f"✅ WebSocket连接成功")
            print(f"WebSocket状态: {websocket.state.name}")
            
            # 3. 发送create-session消息
            print(f"\n3. 发送create-session消息...")
            request_id = str(uuid.uuid4())
            
            create_session_msg = {
                "type": "create-session",
                "requestId": request_id
            }
            
            print(f"发送消息: {json.dumps(create_session_msg, indent=2)}")
            await websocket.send(json.dumps(create_session_msg))
            
            # 4. 等待响应
            print(f"\n4. 等待服务器响应...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                response_data = json.loads(response)
                print(f"✅ 收到响应: {json.dumps(response_data, indent=2)}")
                
                if response_data.get('statusCode') == 201:
                    session_id = response_data.get('data', {}).get('sessionId')
                    print(f"✅ 会话创建成功! Session ID: {session_id}")
                    
                    # 5. 测试ping消息
                    print(f"\n5. 测试ping消息...")
                    
                    # 尝试不同的建筑ID格式
                    test_buildings = [
                        "building:99900009301",
                        "building:9990000951", 
                        "building:demo",
                        "building:test"
                    ]
                    
                    for building_id in test_buildings:
                        print(f"\n  测试建筑: {building_id}")
                        
                        ping_msg = {
                            "type": "common-api",
                            "buildingId": building_id,
                            "callType": "ping",
                            "groupId": "1",
                            "payload": {
                                "request_id": int(datetime.now().timestamp() * 1000)
                            }
                        }
                        
                        print(f"  发送ping: {json.dumps(ping_msg)}")
                        await websocket.send(json.dumps(ping_msg))
                        
                        try:
                            ping_response = await asyncio.wait_for(websocket.recv(), timeout=5)
                            ping_data = json.loads(ping_response)
                            print(f"  ✅ Ping响应: {json.dumps(ping_data, indent=4)}")
                            
                            if ping_data.get('statusCode') == 200:
                                print(f"  ✅ 建筑 {building_id} 可用!")
                                
                                # 尝试获取配置
                                config_msg = {
                                    "type": "common-api",
                                    "buildingId": building_id,
                                    "callType": "config",
                                    "groupId": "1"
                                }
                                
                                print(f"  获取配置...")
                                await websocket.send(json.dumps(config_msg))
                                
                                try:
                                    config_response = await asyncio.wait_for(websocket.recv(), timeout=5)
                                    config_data = json.loads(config_response)
                                    print(f"  ✅ 配置响应: {json.dumps(config_data, indent=4)}")
                                except asyncio.TimeoutError:
                                    print(f"  ❌ 配置响应超时")
                                    
                            else:
                                print(f"  ❌ 建筑 {building_id} 不可用: {ping_data}")
                                
                        except asyncio.TimeoutError:
                            print(f"  ❌ Ping响应超时")
                        except json.JSONDecodeError as e:
                            print(f"  ❌ Ping响应格式错误: {e}")
                            
                else:
                    print(f"❌ 会话创建失败: {response_data}")
                    
            except asyncio.TimeoutError:
                print(f"❌ 响应超时")
            except json.JSONDecodeError as e:
                print(f"❌ 响应格式错误: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始基础WebSocket测试...")
    result = asyncio.run(test_basic_websocket())
    if result:
        print("\n✅ 基础测试完成!")
    else:
        print("\n❌ 基础测试失败!")
