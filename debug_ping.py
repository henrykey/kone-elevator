#!/usr/bin/env python3

import asyncio
import json
from drivers import KoneDriverV2
import yaml

async def test_ping():
    """Debug ping functionality"""
    
    # 加载配置
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # 创建驱动
    driver = KoneDriverV2(
        client_id=config['client_id'],
        client_secret=config['client_secret']
    )
    
    building_id = "building:L1QinntdEOg"
    group_id = "1"
    
    try:
        print("🔧 Testing ping functionality...")
        
        # 测试1：直接ping调用
        print("\n1. Testing ping call...")
        ping_resp = await driver.ping(building_id, group_id)
        print(f"Ping Response: {json.dumps(ping_resp, indent=2)}")
        
        # 测试2：检查ping响应格式
        if ping_resp.get('callType') == 'ping':
            print("✅ Ping response has correct callType")
            if ping_resp.get('data'):
                print("✅ Ping response has data field")
                print(f"Data: {ping_resp.get('data')}")
            else:
                print("❌ Ping response missing data field")
        else:
            print(f"❌ Ping response has wrong callType: {ping_resp.get('callType')}")
        
    except Exception as e:
        print(f"❌ Ping failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await driver.close()

if __name__ == "__main__":
    asyncio.run(test_ping())
