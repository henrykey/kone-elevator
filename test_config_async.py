#!/usr/bin/env python3
"""
测试异步配置消息：等待额外的WebSocket消息
"""

import asyncio
import json
import yaml
from drivers import KoneDriver

async def test_config_with_monitoring():
    """测试配置API并监听后续消息"""
    print("🔍 测试 KONE API 异步配置获取")
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
    print("🔌 初始化连接...")
    init_result = await driver.initialize()
    if not init_result['success']:
        print(f"❌ 连接失败: {init_result}")
        return
    
    print("✅ 连接成功")
    
    # 4. 发送配置请求
    building_id = "L1QinntdEOg"
    config_msg = {
        "type": "common-api",
        "callType": "config",
        "buildingId": f"building:{building_id}",
        "groupId": "1"
    }
    
    print(f"📤 发送配置请求...")
    print(f"请求: {json.dumps(config_msg, indent=2)}")
    
    # 5. 发送请求
    response = await driver._send_message(config_msg, timeout=10)
    print(f"📥 初始响应: {json.dumps(response, indent=2)}")
    
    # 6. 等待额外消息（可能包含配置数据）
    print(f"⏳ 等待额外消息 30 秒...")
    
    received_messages = []
    start_time = asyncio.get_event_loop().time()
    timeout = 30
    
    try:
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                # 检查消息队列
                if hasattr(driver, 'message_queue') and driver.message_queue:
                    try:
                        message = await asyncio.wait_for(driver.message_queue.get(), timeout=2)
                        received_messages.append(message)
                        print(f"📨 收到消息 #{len(received_messages)}: {json.dumps(message, indent=2, ensure_ascii=False)}")
                        
                        # 检查是否包含配置数据
                        if 'data' in message:
                            data = message['data']
                            if any(key in data for key in ['floors', 'areas', 'config', 'groups', 'elevators']):
                                print(f"🎉 发现配置数据!")
                                return message
                                
                    except asyncio.TimeoutError:
                        continue
                else:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"⚠️  等待消息时出错: {e}")
                break
                
    except KeyboardInterrupt:
        print("⏹️  用户中断")
    
    # 7. 总结
    print(f"\n📊 总结:")
    print(f"   - 初始响应: ✅ 成功 (状态码: {response.get('statusCode')})")
    print(f"   - 额外消息数量: {len(received_messages)}")
    
    if received_messages:
        print(f"   - 收到的消息类型: {[msg.get('type', 'unknown') for msg in received_messages]}")
    else:
        print(f"   - 🤔 没有收到额外的配置消息")
        print(f"   - 💡 可能需要检查其他获取配置的方法")

async def main():
    await test_config_with_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
