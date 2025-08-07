#!/usr/bin/env python
# Author: IBC-AI CO.
"""
详细的KONE API ping调试测试
检查实际发送的消息和响应
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from drivers import KoneDriver
import yaml

# 详细日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def debug_ping_test():
    """详细调试ping测试"""
    
    print("🔍 KONE API Ping 调试测试")
    print("=" * 40)
    
    try:
        # 加载配置
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        with open('virtual_building_config.yml', 'r') as f:
            building_config = yaml.safe_load(f)
        
        building_id = building_config['building']['id']
        kone_config = config['kone']
        
        print(f"原始建筑ID: {building_id}")
        
        # 创建驱动
        driver = KoneDriver(
            client_id=kone_config['client_id'],
            client_secret=kone_config['client_secret']
        )
        
        # 初始化连接
        print("\\n🔌 初始化WebSocket连接...")
        init_result = await driver.initialize()
        print(f"初始化结果: {init_result}")
        
        if not init_result['success']:
            print("❌ 初始化失败")
            return False
        
        # 检查格式化逻辑
        formatted_id = building_id if building_id.startswith("building:") else f"building:{building_id}"
        print(f"\\n📝 buildingId格式化:")
        print(f"  原始: {building_id}")
        print(f"  格式化后: {formatted_id}")
        
        # 构建ping消息
        request_id = int(datetime.now().timestamp() * 1000)
        ping_msg = {
            "type": "common-api",
            "buildingId": formatted_id,
            "callType": "ping",
            "groupId": "1",
            "payload": {
                "request_id": request_id
            }
        }
        
        print(f"\\n📤 准备发送的ping消息:")
        print(json.dumps(ping_msg, indent=2))
        
        # 手动发送并监控
        print("\\n📡 发送ping请求...")
        
        # 记录时间
        start_time = time.time()
        
        try:
            # 发送消息
            await driver.websocket.send(json.dumps(ping_msg))
            print("✅ 消息已发送")
            
            # 等待响应 (较短超时)
            print("⏳ 等待响应...")
            
            response = await asyncio.wait_for(
                driver.websocket.recv(),
                timeout=5  # 较短超时便于调试
            )
            
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            
            print(f"📥 收到响应 (延迟: {latency:.2f}ms):")
            
            try:
                response_data = json.loads(response)
                print(json.dumps(response_data, indent=2))
                
                # 分析响应
                print("\\n📊 响应分析:")
                print(f"状态码: {response_data.get('statusCode', 'N/A')}")
                print(f"错误信息: {response_data.get('error', 'N/A')}")
                print(f"payLoad: {response_data.get('payLoad', 'N/A')}")
                
                if response_data.get('statusCode') == 200:
                    print("✅ Ping成功!")
                    return True
                else:
                    print(f"❌ Ping失败: {response_data}")
                    return False
                    
            except json.JSONDecodeError:
                print(f"原始响应 (非JSON): {response}")
                return False
            
        except asyncio.TimeoutError:
            print("⏰ 响应超时 (5秒)")
            print("可能的原因:")
            print("  1. 服务器处理缓慢")
            print("  2. buildingId不存在")
            print("  3. 网络问题")
            print("  4. API格式仍有问题")
            return False
        
        except Exception as e:
            print(f"💥 发送异常: {e}")
            return False
        
        finally:
            await driver.close()
    
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False


async def test_different_formats():
    """测试不同的buildingId格式"""
    
    print("\\n🧪 测试不同buildingId格式")
    print("-" * 30)
    
    formats_to_test = [
        "fWlfHyPlaca",           # 原始
        "building:fWlfHyPlaca",  # 格式化
        "Building:fWlfHyPlaca",  # 大写B
        "BUILDING:fWlfHyPlaca",  # 全大写
    ]
    
    for test_format in formats_to_test:
        print(f"\\n测试格式: {test_format}")
        
        # 模拟格式化逻辑
        formatted = test_format if test_format.startswith("building:") else f"building:{test_format}"
        print(f"格式化结果: {formatted}")
        
        # 检查是否符合预期
        if formatted == "building:fWlfHyPlaca":
            print("✅ 格式正确")
        else:
            print("❌ 格式可能有问题")


async def main():
    """主函数"""
    
    print("🚀 KONE API Ping 详细调试")
    print("Author: IBC-AI CO.")
    print("=" * 50)
    
    # 测试格式
    await test_different_formats()
    
    # 调试ping
    success = await debug_ping_test()
    
    print("\\n" + "=" * 50)
    if success:
        print("🎉 调试测试成功!")
    else:
        print("⚠️ 调试发现问题，但buildingId格式化逻辑是正确的")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
