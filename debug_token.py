#!/usr/bin/env python3
"""
测试KONE token获取的详细调试脚本
"""

import requests
import yaml
import json

def test_token_request():
    """测试token请求的详细信息"""
    print("🔍 调试KONE Token请求...")
    
    # 加载配置
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    kone_config = config['kone']
    client_id = kone_config['client_id']
    client_secret = kone_config['client_secret']
    token_endpoint = kone_config['token_endpoint']
    
    print(f"📋 请求信息:")
    print(f"   Endpoint: {token_endpoint}")
    print(f"   Client ID: {client_id}")
    print(f"   Client Secret: {client_secret[:10]}...")
    
    # 尝试不同的scope配置
    scopes_to_try = [
        None,  # 不使用scope
        f'callgiving/{client_id} robotcall/{client_id}',
        f'callgiving/{client_id}',
        f'robotcall/{client_id}',
        'callgiving robotcall',
        'https://api.kone.com/callgiving https://api.kone.com/robotcall'
    ]
    
    for i, scope in enumerate(scopes_to_try, 1):
        print(f"\n{i}️⃣ 尝试scope: {scope or '(无scope)'}")
        
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        if scope:
            data["scope"] = scope
        
        try:
            print(f"   请求数据: {json.dumps(data, indent=2)}")
            response = requests.post(token_endpoint, data=data, timeout=30)
            
            print(f"   状态码: {response.status_code}")
            print(f"   响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                token_data = response.json()
                print(f"✅ 成功获取token!")
                print(f"   Token类型: {token_data.get('token_type', 'N/A')}")
                print(f"   过期时间: {token_data.get('expires_in', 'N/A')}秒")
                print(f"   Scope: {token_data.get('scope', 'N/A')}")
                print(f"   Token前缀: {token_data.get('access_token', '')[:30]}...")
                return token_data
            else:
                try:
                    error_data = response.json()
                    print(f"❌ 错误响应: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"❌ 错误响应文本: {response.text}")
                    
        except Exception as e:
            print(f"❌ 请求异常: {e}")
    
    print("\n🚫 所有scope尝试均失败")
    return None

def test_different_methods():
    """尝试不同的认证方法"""
    print("\n🔧 尝试不同的认证方法...")
    
    # 加载配置
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    kone_config = config['kone']
    client_id = kone_config['client_id']
    client_secret = kone_config['client_secret']
    token_endpoint = kone_config['token_endpoint']
    
    # 方法1: Basic Auth
    print("\n1️⃣ 尝试Basic Authentication...")
    try:
        data = {"grant_type": "client_credentials"}
        response = requests.post(
            token_endpoint, 
            data=data,
            auth=(client_id, client_secret),
            timeout=30
        )
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ Basic Auth成功!")
            return response.json()
        else:
            print(f"❌ Basic Auth失败: {response.text}")
    except Exception as e:
        print(f"❌ Basic Auth异常: {e}")
    
    # 方法2: 在URL中使用参数
    print("\n2️⃣ 尝试URL参数方式...")
    try:
        params = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        }
        response = requests.get(token_endpoint, params=params, timeout=30)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ URL参数成功!")
            return response.json()
        else:
            print(f"❌ URL参数失败: {response.text}")
    except Exception as e:
        print(f"❌ URL参数异常: {e}")
    
    return None

if __name__ == "__main__":
    print("🧪 KONE Token请求调试工具")
    print("=" * 40)
    
    result = test_token_request()
    if not result:
        result = test_different_methods()
    
    if result:
        print(f"\n🎉 Token获取成功!")
        print(f"最终token: {result.get('access_token', '')[:50]}...")
    else:
        print(f"\n💥 所有方法均失败，请检查凭证或联系KONE支持")
