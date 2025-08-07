#!/usr/bin/env python3
"""
从零开始测试 KONE API 虚拟建筑发现和配置获取
目标：
1. 获取可用的虚拟建筑列表
2. 逐一测试每个建筑的配置获取
3. 分析返回的配置数据结构
"""

import asyncio
import json
import yaml
import websockets
import requests
import base64
from datetime import datetime
import uuid

class VirtualBuildingTester:
    def __init__(self):
        # 加载配置
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        self.kone_config = config['kone']
        
        self.client_id = self.kone_config['client_id']
        self.client_secret = self.kone_config['client_secret']
        self.token_endpoint = "https://dev.kone.com/api/v2/oauth2/token"
        self.ws_endpoint = "wss://dev.kone.com/stream-v2"
        self.api_base = "https://dev.kone.com/api/v2"
        
        self.access_token = None
        self.websocket = None

    async def get_access_token(self):
        """获取访问令牌"""
        print("🔑 正在获取访问令牌...")
        
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        response = requests.post(
            self.token_endpoint,
            data={
                'grant_type': 'client_credentials', 
                'scope': 'application/inventory callgiving/*'
            },
            headers={
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            print(f"✅ 令牌获取成功，有效期: {token_data.get('expires_in', 'N/A')}秒")
            return True
        else:
            print(f"❌ 令牌获取失败: {response.status_code}, {response.text}")
            return False

    async def get_available_resources(self):
        """获取可用资源列表（建筑ID）"""
        print("\n🏢 正在获取可用建筑资源...")
        
        if not self.access_token:
            if not await self.get_access_token():
                return []
        
        url = f"{self.api_base}/application/self/resources"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                resources = response.json()
                print(f"✅ 成功获取资源列表")
                print(f"📋 原始响应: {json.dumps(resources, indent=2, ensure_ascii=False)}")
                
                # 提取建筑ID
                building_ids = []
                if isinstance(resources, dict):
                    # 检查不同可能的数据结构
                    for key in ['buildings', 'resources', 'data', 'items']:
                        if key in resources:
                            items = resources[key]
                            if isinstance(items, list):
                                for item in items:
                                    if isinstance(item, dict):
                                        # 尝试提取建筑ID
                                        bid = item.get('buildingId') or item.get('id') or item.get('building_id')
                                        if bid:
                                            building_ids.append(bid)
                                    elif isinstance(item, str):
                                        building_ids.append(item)
                            break
                    
                    # 如果没有找到嵌套结构，检查顶层是否有建筑ID
                    if not building_ids:
                        bid = resources.get('buildingId') or resources.get('id') or resources.get('building_id')
                        if bid:
                            building_ids.append(bid)
                
                elif isinstance(resources, list):
                    for item in resources:
                        if isinstance(item, dict):
                            bid = item.get('buildingId') or item.get('id') or item.get('building_id')
                            if bid:
                                building_ids.append(bid)
                        elif isinstance(item, str):
                            building_ids.append(item)
                
                print(f"🏗️  提取到的建筑ID: {building_ids}")
                return building_ids
                
            else:
                print(f"❌ 获取资源失败: {response.status_code}, {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return []

    async def connect_websocket(self):
        """建立WebSocket连接"""
        if not self.access_token:
            if not await self.get_access_token():
                return False
        
        try:
            uri = f"{self.ws_endpoint}?accessToken={self.access_token}"
            print(f"🔌 正在连接WebSocket: {uri[:50]}...")
            
            self.websocket = await websockets.connect(
                uri,
                subprotocols=['koneapi'],
                ping_interval=30,
                ping_timeout=10
            )
            
            print("✅ WebSocket连接成功")
            return True
            
        except Exception as e:
            print(f"❌ WebSocket连接失败: {e}")
            return False

    async def test_building_config(self, building_id):
        """测试单个建筑的配置获取"""
        print(f"\n🏗️  测试建筑: {building_id}")
        print("-" * 50)
        
        if not self.websocket:
            if not await self.connect_websocket():
                return None
        
        # 确保建筑ID格式正确
        formatted_building_id = building_id if building_id.startswith("building:") else f"building:{building_id}"
        
        # 测试不同类型的配置请求
        test_requests = [
            {
                "name": "🔧 基础配置 (config)",
                "message": {
                    "type": "common-api",
                    "requestId": str(uuid.uuid4()),
                    "callType": "config",
                    "buildingId": formatted_building_id,
                    "groupId": "1"
                }
            },
            {
                "name": "🎯 操作列表 (actions)",
                "message": {
                    "type": "common-api",
                    "requestId": str(uuid.uuid4()),
                    "callType": "actions", 
                    "buildingId": formatted_building_id,
                    "groupId": "1"
                }
            },
            {
                "name": "📍 连通性测试 (ping)",
                "message": {
                    "type": "common-api",
                    "requestId": str(uuid.uuid4()),
                    "callType": "ping",
                    "buildingId": formatted_building_id,
                    "groupId": "1",
                    "payload": {
                        "request_id": int(datetime.now().timestamp() * 1000)
                    }
                }
            },
            {
                "name": "🗺️ 拓扑结构 (topology)",
                "message": {
                    "type": "common-api",
                    "requestId": str(uuid.uuid4()),
                    "callType": "topology",
                    "buildingId": formatted_building_id,
                    "groupId": "1"
                }
            },
            {
                "name": "📊 状态监控 (monitor)",
                "message": {
                    "type": "common-api",
                    "requestId": str(uuid.uuid4()),
                    "callType": "monitor",
                    "buildingId": formatted_building_id,
                    "groupId": "1"
                }
            }
        ]
        
        results = []
        
        for test in test_requests:
            print(f"\n{test['name']}")
            print(f"📤 请求: {json.dumps(test['message'], indent=2)}")
            
            try:
                # 发送请求
                await self.websocket.send(json.dumps(test['message']))
                
                # 等待响应
                try:
                    response_text = await asyncio.wait_for(self.websocket.recv(), timeout=15)
                    response = json.loads(response_text)
                    
                    print(f"📥 响应: {json.dumps(response, indent=2, ensure_ascii=False)}")
                    
                    # 分析响应
                    status_code = response.get('statusCode', 'N/A')
                    response_type = response.get('type', 'N/A')
                    
                    if status_code in [200, 201]:
                        print(f"✅ 成功: {status_code}")
                        data = response.get('data', {})
                        
                        # 检查是否包含有用的配置信息
                        useful_keys = []
                        for key in data.keys():
                            if key not in ['time', 'timestamp'] and data[key]:
                                useful_keys.append(key)
                        
                        if useful_keys:
                            print(f"📊 有用数据键: {useful_keys}")
                            results.append({
                                'test_name': test['name'],
                                'status': 'success',
                                'data': data,
                                'useful_keys': useful_keys
                            })
                        else:
                            print(f"⚠️ 只有基础响应数据")
                    else:
                        print(f"⚠️ 状态码: {status_code}")
                        if response_type == 'error':
                            print(f"❌ 错误: {response.get('message', '未知错误')}")
                        
                except asyncio.TimeoutError:
                    print(f"⏰ 请求超时")
                    
            except Exception as e:
                print(f"❌ 请求异常: {e}")
        
        return results

    async def discover_and_test_buildings(self):
        """发现并测试所有可用建筑"""
        print("🚀 KONE API 虚拟建筑发现和配置测试")
        print("=" * 60)
        
        # 1. 获取可用建筑列表
        building_ids = await self.get_available_resources()
        
        if not building_ids:
            print("⚠️ 未发现可用建筑，使用默认测试建筑ID")
            building_ids = ['L1QinntdEOg', 'fWlfHyPlaca']  # 已知的测试建筑ID
        
        # 2. 连接WebSocket
        if not await self.connect_websocket():
            print("❌ WebSocket连接失败，无法继续测试")
            return
        
        # 3. 测试每个建筑
        all_results = {}
        
        for building_id in building_ids:
            results = await self.test_building_config(building_id)
            if results:
                all_results[building_id] = results
        
        # 4. 总结分析
        print(f"\n📋 测试总结")
        print("=" * 60)
        
        if all_results:
            print(f"✅ 成功测试了 {len(all_results)} 个建筑:")
            
            for building_id, results in all_results.items():
                print(f"\n🏢 建筑 {building_id}:")
                success_count = len([r for r in results if r['status'] == 'success'])
                print(f"   - 成功请求: {success_count}/{len(results)}")
                
                for result in results:
                    if result['status'] == 'success' and result['useful_keys']:
                        print(f"   - {result['test_name']}: {result['useful_keys']}")
        else:
            print("❌ 未获取到任何有用的配置数据")
        
        # 5. 关闭连接
        if self.websocket:
            await self.websocket.close()
            print(f"\n🔌 WebSocket连接已关闭")

async def main():
    tester = VirtualBuildingTester()
    await tester.discover_and_test_buildings()

if __name__ == "__main__":
    asyncio.run(main())
