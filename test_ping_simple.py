#!/usr/bin/env python
# Author: IBC-AI CO.
"""
简化的KONE API ping测试
验证修正后的buildingId格式是否解决500错误
"""

import asyncio
import logging
import sys
import json
from drivers import KoneDriver
import yaml

# 设置简单日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def simple_ping_test():
    """简化的ping测试"""
    
    print("🎯 简化KONE Ping测试")
    print("验证buildingId格式修正效果")
    print("=" * 40)
    
    try:
        # 加载配置
        print("📋 加载配置...")
        
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        with open('virtual_building_config.yml', 'r') as f:
            building_config = yaml.safe_load(f)
        
        building_id = building_config['building']['id']
        kone_config = config['kone']
        
        print(f"建筑ID: {building_id}")
        print(f"将格式化为: building:{building_id}")
        
        # 创建驱动
        print("\\n🔧 创建驱动...")
        driver = KoneDriver(
            client_id=kone_config['client_id'],
            client_secret=kone_config['client_secret']
        )
        
        # 测试ping
        print("\\n📡 发送ping请求...")
        print(f"使用buildingId: {building_id}")
        
        try:
            result = await driver.ping(building_id)
            
            print("\\n📊 结果:")
            print(f"成功: {result['success']}")
            print(f"状态码: {result.get('status_code', 'N/A')}")
            
            if result['success']:
                print(f"延迟: {result.get('latency_ms', 'N/A')}ms")
                print(f"消息: {result.get('message', 'N/A')}")
                print("✅ buildingId格式修正成功!")
            else:
                print(f"错误: {result.get('error', 'N/A')}")
                
                # 检查是否仍然是500错误
                if result.get('status_code') == 500:
                    print("❌ 仍然是500错误 - 可能还有其他问题")
                else:
                    print("⚠️ 不同的错误 - buildingId格式修正可能有效")
            
            return result['success']
            
        except Exception as e:
            print(f"💥 异常: {e}")
            return False
        
        finally:
            await driver.close()
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


async def check_websocket_connection():
    """检查WebSocket连接和会话创建"""
    
    print("\\n🔌 WebSocket连接测试")
    print("-" * 25)
    
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        kone_config = config['kone']
        driver = KoneDriver(
            client_id=kone_config['client_id'],
            client_secret=kone_config['client_secret']
        )
        
        print("初始化连接...")
        init_result = await driver.initialize()
        
        print(f"初始化结果: {init_result['success']}")
        if init_result['success']:
            print(f"会话ID: {init_result.get('session_id', 'N/A')}")
            print("✅ WebSocket连接和会话创建成功")
        else:
            print(f"❌ 初始化失败: {init_result.get('error')}")
        
        await driver.close()
        return init_result['success']
        
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False


async def main():
    """主函数"""
    
    print("🚀 KONE API buildingId 修正验证")
    print("Author: IBC-AI CO.")
    print("=" * 50)
    
    # 检查WebSocket连接
    ws_success = await check_websocket_connection()
    
    # 测试ping
    ping_success = await simple_ping_test()
    
    print("\\n" + "=" * 50)
    print("📊 测试总结:")
    print(f"WebSocket连接: {'✅ 成功' if ws_success else '❌ 失败'}")
    print(f"Ping测试: {'✅ 成功' if ping_success else '❌ 失败'}")
    
    if ws_success and ping_success:
        print("\\n🎉 所有测试通过!")
        print("buildingId格式修正有效，500错误已解决")
    elif ws_success and not ping_success:
        print("\\n⚠️ WebSocket连接成功但ping失败")
        print("可能是服务器端或网络问题，不是buildingId格式问题")
    else:
        print("\\n❌ 连接或配置问题")
    
    return ws_success and ping_success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
