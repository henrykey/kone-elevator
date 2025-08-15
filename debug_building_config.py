#!/usr/bin/env python3
"""
调试建筑配置获取问题
"""

import asyncio
import json
import logging
from test_scenarios_v2 import TestScenariosV2
from kone_api_client import CommonAPIClient

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')

async def debug_building_config():
    test_runner = TestScenariosV2()
    
    try:
        print("🔍 开始调试建筑配置获取...")
        
        # 获取访问令牌
        access_token = test_runner._get_access_token()
        print("✅ Token获取成功")
        
        # 建立 WebSocket 连接
        websocket = await test_runner._create_websocket_connection(access_token)
        print("✅ WebSocket连接成功")
        
        # 创建API客户端
        common_client = CommonAPIClient(websocket)
        
        # 尝试获取建筑配置
        config_response = await common_client.get_building_config(
            building_id="building:L1QinntdEOg",
            group_id="1"
        )
        
        print(f"📊 配置响应: success={config_response.success}")
        print(f"📊 错误信息: {config_response.error}")
        print(f"📊 响应数据类型: {type(config_response.data)}")
        
        if config_response.data:
            print(f"📊 响应数据（前200字符）: {str(config_response.data)[:200]}...")
        
        # 尝试关闭WebSocket
        await websocket.close()
        print("✅ WebSocket已关闭")
        
    except Exception as e:
        print(f"❌ 调试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_building_config())
