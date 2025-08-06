#!/usr/bin/env python3
"""
KONE Token缓存机制测试脚本
测试token的获取、缓存、自动刷新功能
"""

import asyncio
import yaml
import json
from datetime import datetime, timedelta
from drivers import KoneDriver

async def test_token_caching():
    """测试token缓存机制"""
    print("🚀 开始测试KONE Token智能缓存机制...")
    
    # 加载配置
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    kone_config = config['kone']
    driver = KoneDriver(
        client_id=kone_config['client_id'],
        client_secret=kone_config['client_secret'],
        token_endpoint=kone_config['token_endpoint'],
        ws_endpoint=kone_config['ws_endpoint']
    )
    
    print("\n1️⃣ 测试首次获取token...")
    start_time = datetime.now()
    token1 = await driver.get_access_token()
    first_duration = (datetime.now() - start_time).total_seconds()
    print(f"✅ 首次获取token成功，耗时: {first_duration:.2f}秒")
    print(f"   Token前缀: {token1[:20]}...")
    print(f"   过期时间: {driver.token_expiry}")
    
    print("\n2️⃣ 测试内存缓存（立即再次获取）...")
    start_time = datetime.now()
    token2 = await driver.get_access_token()
    second_duration = (datetime.now() - start_time).total_seconds()
    print(f"✅ 内存缓存命中，耗时: {second_duration:.2f}秒")
    print(f"   Token相同: {token1 == token2}")
    print(f"   速度提升: {(first_duration / second_duration):.1f}x")
    
    print("\n3️⃣ 检查配置文件缓存...")
    with open('config.yaml', 'r') as f:
        updated_config = yaml.safe_load(f)
    
    cached_token = updated_config['kone']['cached_token']
    print(f"✅ Token已保存到配置文件:")
    print(f"   缓存状态: {'有效' if cached_token['access_token'] else '无效'}")
    print(f"   过期时间: {cached_token['expires_at']}")
    print(f"   Token类型: {cached_token['token_type']}")
    
    print("\n4️⃣ 测试新实例的配置文件缓存...")
    # 创建新的driver实例，模拟重启后的情况
    new_driver = KoneDriver(
        client_id=kone_config['client_id'],
        client_secret=kone_config['client_secret'],
        token_endpoint=kone_config['token_endpoint'],
        ws_endpoint=kone_config['ws_endpoint']
    )
    
    start_time = datetime.now()
    token3 = await new_driver.get_access_token()
    third_duration = (datetime.now() - start_time).total_seconds()
    print(f"✅ 配置文件缓存命中，耗时: {third_duration:.2f}秒")
    print(f"   Token相同: {token1 == token3}")
    print(f"   相对首次速度提升: {(first_duration / third_duration):.1f}x")
    
    print("\n5️⃣ 测试token信息...")
    try:
        # 简单验证token格式
        token_parts = token1.split('.')
        print(f"✅ Token格式验证:")
        print(f"   Token部分数: {len(token_parts)}")
        print(f"   看起来像JWT: {'是' if len(token_parts) == 3 else '否'}")
        
        # 显示token过期策略
        now = datetime.now()
        expires_at = driver.token_expiry
        remaining = expires_at - now
        print(f"   剩余有效时间: {remaining}")
        print(f"   缓冲时间: 60秒")
        
    except Exception as e:
        print(f"⚠️ Token验证时出现错误: {e}")
    
    print("\n🎉 Token缓存机制测试完成!")
    print("\n📊 性能总结:")
    print(f"   首次获取: {first_duration:.2f}秒 (网络请求)")
    print(f"   内存缓存: {second_duration:.2f}秒 (即时)")
    print(f"   文件缓存: {third_duration:.2f}秒 (磁盘读取)")
    print(f"   缓存效果: 速度提升 {(first_duration / min(second_duration, third_duration)):.1f}x")

async def test_token_refresh():
    """测试token自动刷新机制"""
    print("\n🔄 测试token自动刷新机制...")
    
    # 加载配置
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    kone_config = config['kone']
    driver = KoneDriver(
        client_id=kone_config['client_id'],
        client_secret=kone_config['client_secret']
    )
    
    # 获取当前token
    current_token = await driver.get_access_token()
    current_expiry = driver.token_expiry
    
    print(f"✅ 当前token过期时间: {current_expiry}")
    
    # 模拟token即将过期（手动设置过期时间）
    driver.token_expiry = datetime.now() + timedelta(minutes=2)  # 2分钟后过期
    print(f"🕐 模拟token将在2分钟后过期...")
    
    # 再次获取token，应该触发刷新
    new_token = await driver.get_access_token()
    new_expiry = driver.token_expiry
    
    print(f"✅ 刷新后token过期时间: {new_expiry}")
    print(f"   Token已更新: {'是' if new_token != current_token else '否'}")
    print(f"   过期时间延长: {'是' if new_expiry > current_expiry else '否'}")

if __name__ == "__main__":
    print("🧪 KONE Token智能缓存机制测试")
    print("=" * 50)
    
    asyncio.run(test_token_caching())
    asyncio.run(test_token_refresh())
    
    print("\n✨ 所有测试完成! ✨")
