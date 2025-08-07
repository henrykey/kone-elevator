#!/usr/bin/env python3
"""
简单的 KONE API ping 测试脚本
复制 TypeScript 版本的成功结果
"""

import asyncio
import websockets
import json
import yaml
import base64
import requests
import random
from datetime import datetime

def load_config():
    """加载配置文件"""
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    return config['kone']

def get_access_token(client_id, client_secret, token_endpoint):
    """获取访问令牌"""
    print(f'[DEBUG] 请求TOKEN: {token_endpoint}')
    
    # Basic Authentication
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    print(f'[DEBUG] 请求HEADER: {headers}')
    
    data = {
        'grant_type': 'client_credentials',
        'scope': 'application/inventory callgiving/*'
    }
    
    response = requests.post(token_endpoint, data=data, headers=headers)
    
    if response.status_code == 200:
        token_data = response.json()
        print(f'[DEBUG] TOKEN响应: {token_data}')
        return token_data['access_token']
    else:
        raise Exception(f"Token request failed: {response.status_code}, {response.text}")

def get_request_id():
    """生成请求ID"""
    return random.randint(100000000, 999999999)

async def ping_test():
    """执行 ping 测试"""
    print("🚀 KONE API Ping 测试 (Python版本)")
    print("=" * 40)
    
    try:
        # 加载配置
        config = load_config()
        client_id = config['client_id']
        client_secret = config['client_secret']
        token_endpoint = config.get('token_endpoint', 'https://dev.kone.com/api/v2/oauth2/token')
        ws_endpoint = config.get('ws_endpoint', 'wss://dev.kone.com/stream-v2')
        
        # 获取访问令牌
        token = get_access_token(client_id, client_secret, token_endpoint)
        print('[✅] Token fetched.')
        
        # 使用固定的纯v2建筑ID
        building_id = 'L1QinntdEOg'  # Virtual Building for V2
        print(f'[🏢] BuildingId (纯v2建筑): {building_id}')
        
        # 建立WebSocket连接
        uri = f"{ws_endpoint}?accessToken={token}"
        
        async with websockets.connect(uri, subprotocols=['koneapi']) as websocket:
            print('[🔌] WebSocket connected.')
            
            # 构造ping消息
            ping_payload = {
                'type': 'common-api',
                'buildingId': f'building:{building_id}' if not building_id.startswith('building:') else building_id,
                'callType': 'ping',
                'groupId': '1',
                'payload': {
                    'request_id': get_request_id()
                }
            }
            
            print('[📤] Sending ping...')
            await websocket.send(json.dumps(ping_payload))
            
            # 接收消息
            ping_received = False
            while not ping_received:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    
                    print('[📩] Received message:')
                    print(json.dumps(data, indent=2))
                    
                    # 检查是否收到ping响应
                    if data.get('callType') == 'ping':
                        print('[✅] Ping 响应收到，测试完成！')
                        ping_received = True
                        
                except asyncio.TimeoutError:
                    print('[⚠️] 等待响应超时')
                    break
                except Exception as e:
                    print(f'[❌] 接收消息错误: {e}')
                    break
        
        if ping_received:
            print('\n🎉 Python ping 测试成功!')
            return True
        else:
            print('\n⚠️ 未收到ping响应')
            return False
            
    except Exception as e:
        print(f'[💥] Error: {e}')
        return False

async def main():
    """主函数"""
    success = await ping_test()
    exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
