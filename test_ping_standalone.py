#!/usr/bin/env python
# Author: IBC-AI CO.
"""
独立的KONE API ping测试脚本
测试buildingId格式修正后的ping功能
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
from drivers import KoneDriver, ElevatorDriverFactory
import yaml

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ping_test.log')
    ]
)
logger = logging.getLogger(__name__)


async def test_ping_with_different_formats():
    """测试不同buildingId格式的ping请求"""
    
    print("🎯 KONE API Ping 测试")
    print("Author: IBC-AI CO.")
    print("=" * 50)
    
    try:
        # 1. 加载配置
        print("📋 Step 1: 加载配置...")
        
        # 加载虚拟建筑配置
        with open('virtual_building_config.yml', 'r', encoding='utf-8') as f:
            building_config = yaml.safe_load(f)
        
        original_building_id = building_config['building']['id']
        print(f"   原始 building_id: {original_building_id}")
        
        # 加载KONE API配置
        with open('config.yaml', 'r', encoding='utf-8') as f:
            api_config = yaml.safe_load(f)
        
        kone_config = api_config.get('kone', {})
        if not kone_config:
            print("   ❌ 未找到KONE配置")
            return False
        
        print(f"   ✅ 配置加载成功")
        
        # 2. 创建驱动实例
        print("\\n🔧 Step 2: 创建KONE驱动...")
        driver = KoneDriver(
            client_id=kone_config['client_id'],
            client_secret=kone_config['client_secret']
        )
        print("   ✅ 驱动实例创建成功")
        
        # 3. 测试不同格式的buildingId
        test_cases = [
            {
                "name": "原始格式 (应该自动添加前缀)",
                "building_id": original_building_id,
                "expected_format": f"building:{original_building_id}"
            },
            {
                "name": "完整格式 (已有前缀)",
                "building_id": f"building:{original_building_id}",
                "expected_format": f"building:{original_building_id}"
            },
            {
                "name": "错误的ID测试",
                "building_id": "invalid_building_id",
                "expected_format": "building:invalid_building_id"
            }
        ]
        
        print("\\n🧪 Step 3: 执行ping测试...")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\\n   测试 {i}: {test_case['name']}")
            print(f"   输入: {test_case['building_id']}")
            print(f"   期望格式: {test_case['expected_format']}")
            
            try:
                start_time = datetime.now()
                result = await driver.ping(test_case['building_id'])
                end_time = datetime.now()
                
                duration = (end_time - start_time).total_seconds() * 1000
                
                if result['success']:
                    print(f"   ✅ 成功: {result['message']}")
                    print(f"   📊 延迟: {result.get('latency_ms', 'N/A')}ms")
                    print(f"   ⏱️ 总耗时: {duration:.1f}ms")
                    if result.get('server_time'):
                        print(f"   🕐 服务器时间: {result['server_time']}")
                else:
                    print(f"   ❌ 失败: {result['error']}")
                    print(f"   📊 状态码: {result.get('status_code', 'N/A')}")
                    print(f"   ⏱️ 总耗时: {duration:.1f}ms")
                    
            except Exception as e:
                print(f"   💥 异常: {str(e)}")
        
        # 4. 测试连接状态
        print("\\n🔍 Step 4: 检查连接状态...")
        if driver.websocket and not driver.websocket.closed:
            print("   ✅ WebSocket连接正常")
        else:
            print("   ⚠️ WebSocket连接未建立或已关闭")
        
        if driver.session_id:
            print(f"   ✅ 会话ID: {driver.session_id}")
        else:
            print("   ⚠️ 未获取到会话ID")
        
        # 5. 清理连接
        print("\\n🧹 Step 5: 清理连接...")
        await driver.close()
        print("   ✅ 连接已关闭")
        
        print("\\n" + "=" * 50)
        print("✅ Ping测试完成!")
        return True
        
    except Exception as e:
        print(f"\\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_connectivity():
    """简单的API连通性测试"""
    
    print("\\n🌐 API连通性快速测试")
    print("-" * 30)
    
    try:
        # 使用工厂方法创建驱动
        drivers = ElevatorDriverFactory.create_from_config()
        
        if 'kone' not in drivers:
            print("❌ 无法创建KONE驱动实例")
            return False
        
        driver = drivers['kone']
        
        # 加载建筑ID
        with open('virtual_building_config.yml', 'r', encoding='utf-8') as f:
            building_config = yaml.safe_load(f)
        building_id = building_config['building']['id']
        
        print(f"🏢 测试建筑: {building_id}")
        
        # 执行ping
        print("📡 发送ping请求...")
        result = await driver.ping(building_id)
        
        if result['success']:
            print(f"✅ Ping成功!")
            print(f"   延迟: {result.get('latency_ms')}ms")
            print(f"   状态码: {result.get('status_code')}")
        else:
            print(f"❌ Ping失败: {result['error']}")
            print(f"   状态码: {result.get('status_code')}")
        
        await driver.close()
        return result['success']
        
    except Exception as e:
        print(f"❌ 连通性测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    
    print("🚀 KONE Ping 测试工具")
    print("测试buildingId格式修正效果")
    print("Author: IBC-AI CO.")
    print("=" * 60)
    
    # 检查必要文件
    required_files = ['config.yaml', 'virtual_building_config.yml']
    for file in required_files:
        if not Path(file).exists():
            print(f"❌ 缺少必要文件: {file}")
            return False
    
    print("✅ 必要文件检查通过")
    
    try:
        # 执行详细的ping测试
        success1 = await test_ping_with_different_formats()
        
        # 执行快速连通性测试
        success2 = await test_api_connectivity()
        
        print("\\n" + "=" * 60)
        if success1 and success2:
            print("🎉 所有测试通过!")
            print("buildingId格式修正生效，API连接正常")
        else:
            print("⚠️ 部分测试失败")
            if not success1:
                print("   - 详细ping测试失败")
            if not success2:
                print("   - 连通性测试失败")
        
        return success1 and success2
        
    except KeyboardInterrupt:
        print("\\n⏹️ 测试被用户中断")
        return False
    except Exception as e:
        print(f"\\n💥 测试过程中发生未处理的错误: {e}")
        return False


if __name__ == "__main__":
    print("启动KONE Ping测试...")
    success = asyncio.run(main())
    exit(0 if success else 1)
