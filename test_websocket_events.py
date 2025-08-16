#!/usr/bin/env python3
"""
专门测试WebSocket事件流 - 使用直接WebSocket监听
"""

import asyncio
import json
import yaml
from drivers import KoneDriverV2

async def test_websocket_events():
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    client_id = config['kone']['client_id']
    client_secret = config['kone']['client_secret']
    
    driver = KoneDriverV2(client_id, client_secret)
    
    try:
        # 确保连接
        await driver._ensure_connection()
        print("✅ WebSocket connected")
        
        # 创建一个任务来监听WebSocket消息
        events = []
        session_id = None
        
        async def listen_messages():
            nonlocal session_id, events
            try:
                async for message in driver.websocket:
                    data = json.loads(message)
                    events.append(data)
                    print(f"📩 WebSocket message: {json.dumps(data, indent=2)}")
                    
                    # 检查session_id
                    if 'data' in data and 'session_id' in data['data']:
                        session_id = data['data']['session_id']
                        print(f"🎯 Found session_id: {session_id}")
                        
                        # 发送delete请求
                        delete_message = {
                            'type': 'lift-call-api-v2',
                            'buildingId': "building:4TFxWRCv23D",
                            'callType': 'delete',
                            'groupId': "1",
                            'payload': {
                                'session_id': session_id
                            }
                        }
                        
                        print(f"\n❌ Sending delete call: {json.dumps(delete_message, indent=2)}")
                        await driver.websocket.send(json.dumps(delete_message))
                        
            except Exception as e:
                print(f"❌ WebSocket listener error: {e}")
        
        # 启动监听任务
        listen_task = asyncio.create_task(listen_messages())
        
        # 等待一下让监听启动
        await asyncio.sleep(0.5)
        
        # 发起呼叫
        print("\n🚀 Making a call...")
        call_message = {
            'type': 'lift-call-api-v2',
            'buildingId': "building:4TFxWRCv23D",
            'callType': 'action',
            'groupId': "1",
            'payload': {
                'request_id': 12345,
                'area': 1000,
                'time': '2020-10-10T07:17:33.298515Z',
                'terminal': 1,
                'call': {'action': 2, 'destination': 2000}
            }
        }
        
        await driver.websocket.send(json.dumps(call_message))
        print(f"� Call sent: {json.dumps(call_message, indent=2)}")
        
        # 等待事件
        print("\n👂 Waiting for events...")
        await asyncio.sleep(10)  # 等待10秒收集事件
        
        # 取消监听任务
        listen_task.cancel()
        
        print(f"\n📊 Total events received: {len(events)}")
        if session_id:
            print(f"🎯 Session ID found: {session_id}")
        else:
            print("❌ No session_id found")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if hasattr(driver, 'websocket') and driver.websocket:
            await driver.websocket.close()

if __name__ == "__main__":
    asyncio.run(test_websocket_events())
