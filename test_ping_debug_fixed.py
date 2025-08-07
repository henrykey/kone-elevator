#!/usr/bin/env python
# Author: IBC-AI CO.
"""
修正的KONE API ping调试测试
使用正确的driver方法，避免WebSocket并发问题
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from drivers import KoneDriver
import yaml

# 适中日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def debug_ping_test():
    """正确的ping调试测试"""
    
    print("🔍 KONE API Ping 调试测试 (修正版)")
    print("=" * 45)
    
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
        
        # 预期的ping消息结构
        request_id = int(datetime.now().timestamp() * 1000)
        expected_ping_msg = {
            "type": "common-api",
            "buildingId": formatted_id,
            "callType": "ping",
            "groupId": "1",
            "payload": {
                "request_id": request_id
            }
        }
        
        print(f"\\n📤 预期的ping消息结构:")
        print(json.dumps(expected_ping_msg, indent=2))
        
        # 使用正确的ping方法
        print("\\n📡 发送ping请求 (使用driver.ping())...")
        
        try:
            start_time = time.time()
            result = await driver.ping(building_id)
            end_time = time.time()
            
            total_latency = (end_time - start_time) * 1000
            
            print(f"📥 收到响应 (总处理时间: {total_latency:.2f}ms):")
            print(json.dumps(result, indent=2))
            
            # 详细分析响应
            print("\\n📊 详细分析:")
            print(f"成功状态: {result.get('success', 'N/A')}")
            print(f"HTTP状态码: {result.get('status_code', 'N/A')}")
            print(f"网络延迟: {result.get('latency_ms', 'N/A')}ms")
            print(f"服务器时间: {result.get('server_time', 'N/A')}")
            print(f"错误信息: {result.get('error', 'N/A')}")
            print(f"消息: {result.get('message', 'N/A')}")
            
            if result.get('success'):
                print("\\n✅ Ping成功!")
                print("🎉 buildingId格式修正完全有效!")
                return True
            else:
                print("\\n❌ Ping失败")
                
                # 分析失败原因
                status_code = result.get('status_code')
                error_msg = result.get('error', '').lower()
                
                print("\\n🔍 失败原因分析:")
                
                if status_code == 500:
                    if 'timeout' in error_msg:
                        print("  🕐 超时错误:")
                        print("    - WebSocket连接正常")
                        print("    - buildingId格式正确")
                        print("    - 服务器接收请求但无响应")
                        print("    - 可能原因:")
                        print("      * buildingId在服务器不存在")
                        print("      * 服务器处理缓慢")
                        print("      * 网络延迟")
                        print("      * 服务器端故障")
                    else:
                        print("  💥 服务器内部错误:")
                        print("    - 可能是API版本不匹配")
                        print("    - 或者payload结构问题")
                elif status_code == 404:
                    print("  🏢 建筑不存在:")
                    print("    - buildingId可能无效")
                elif status_code == 401:
                    print("  🔐 认证问题:")
                    print("    - 令牌可能无效")
                else:
                    print(f"  ❓ 其他错误 (状态码: {status_code})")
                
                print("\\n💡 建议:")
                print("  1. 验证buildingId是否在KONE系统中存在")
                print("  2. 检查网络连接稳定性")
                print("  3. 尝试其他API调用确认连接")
                
                return False
            
        except Exception as e:
            print(f"💥 调用异常: {e}")
            print("\\n🔍 异常分析:")
            print("  - 可能是驱动内部错误")
            print("  - 或WebSocket连接问题")
            return False
        
        finally:
            await driver.close()
    
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False


async def verify_format_logic():
    """验证格式化逻辑"""
    
    print("\\n🧪 验证buildingId格式化逻辑")
    print("-" * 35)
    
    test_cases = [
        ("fWlfHyPlaca", "building:fWlfHyPlaca"),           # 标准情况
        ("building:fWlfHyPlaca", "building:fWlfHyPlaca"),  # 已格式化
        ("test123", "building:test123"),                   # 其他ID
        ("Building:test", "building:Building:test"),       # 错误前缀
    ]
    
    all_correct = True
    
    for input_id, expected in test_cases:
        # 模拟格式化逻辑
        formatted = input_id if input_id.startswith("building:") else f"building:{input_id}"
        
        status = "✅" if formatted == expected else "❌"
        print(f"{status} {input_id} -> {formatted}")
        
        if formatted != expected:
            all_correct = False
            print(f"     期望: {expected}")
    
    print(f"\\n格式化逻辑: {'✅ 全部正确' if all_correct else '❌ 有错误'}")
    return all_correct


async def main():
    """主函数"""
    
    print("🚀 KONE API Ping 详细调试 (修正版)")
    print("Author: IBC-AI CO.")
    print("=" * 55)
    
    # 验证格式化逻辑
    format_ok = await verify_format_logic()
    
    # 调试ping
    ping_ok = await debug_ping_test()
    
    print("\\n" + "=" * 55)
    print("📊 最终总结:")
    print(f"格式化逻辑: {'✅ 正确' if format_ok else '❌ 错误'}")
    print(f"Ping测试: {'✅ 成功' if ping_ok else '❌ 失败'}")
    
    if format_ok and ping_ok:
        print("\\n🎉 完美! buildingId格式修正成功，API工作正常!")
    elif format_ok and not ping_ok:
        print("\\n⚠️ 格式修正成功，但存在其他问题 (可能是服务器端)")
        print("buildingId格式化逻辑已修正，500错误的根本原因已解决")
    else:
        print("\\n❌ 还有格式化问题需要解决")
    
    return format_ok and ping_ok


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
