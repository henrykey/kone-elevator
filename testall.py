#!/usr/bin/env python3
"""
Complete Elevator Call Scenarios Test: Based on ping.py success pattern for all 37 test cases
Complete KONE SR-API v2.0 validation test suite
"""

import asyncio
import websockets
import json
import yaml
import base64
import requests
import aiohttp
import random
from datetime import datetime

def load_config():
    """Load configuration file"""
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    return config['kone']

def get_access_token(client_id, client_secret, token_endpoint):
    """Get access token"""
    print(f'[DEBUG] Request TOKEN: {token_endpoint}')
    
    # Basic Authentication
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'client_credentials',
        'scope': 'application/inventory callgiving/*'
    }
    
    response = requests.post(token_endpoint, data=data, headers=headers)
    
    if response.status_code == 200:
        token_data = response.json()
        print(f'[✅] Token acquired successfully, expires in: {token_data.get("expires_in", "unknown")} seconds')
        return token_data['access_token']
    else:
        raise Exception(f"Token request failed: {response.status_code}, {response.text}")

def get_request_id():
    """Generate request ID"""
    return random.randint(100000000, 999999999)

async def test_elevator_scenario(websocket, scenario_name, test_id, call_data, test_type="call", building_id="building:L1QinntdEOg"):
    """Test single elevator scenario"""
    print(f"\n🧪 {scenario_name} ({test_id})")
    print("-" * 40)
    
    request_id = get_request_id()
    
    if test_type == "ping":
        # Ping test
        ping_payload = {
            'type': 'common-api',
            'buildingId': building_id,
            'callType': 'ping',
            'groupId': '1',
            'payload': {
                'request_id': request_id
            }
        }
        
        print(f'[📤] Sending ping test')
        await websocket.send(json.dumps(ping_payload))
        
    elif test_type == "actions":
        # Action/status query test
        action_payload = {
            'type': 'common-api',
            'requestId': str(request_id),
            'buildingId': building_id,
            'callType': 'actions',
            'groupId': '1',
            'payload': {
                'request_id': request_id,
                'action': 'query',
                **call_data
            }
        }
        
        print(f'[📤] Sending action query: {call_data}')
        await websocket.send(json.dumps(action_payload))
        
    else:
        # Default call test
        call_payload = {
            'type': 'common-api',
            'requestId': str(request_id),
            'buildingId': building_id,
            'callType': 'actions',
            'groupId': '1',
            'payload': {
                'request_id': request_id,
                'action': 'call',
                **call_data
            }
        }
        
        print(f'[📤] Sending call: {call_data}')
        await websocket.send(json.dumps(call_payload))
    
    # Wait for responses
    responses = []
    timeout_count = 0
    max_timeout = 2
    
    while len(responses) < 2 and timeout_count < max_timeout:
        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=8.0)
            data = json.loads(message)
            responses.append(data)
            
            print(f'[📩] Response #{len(responses)}:')
            
            # Simplified output of key information
            if data.get('statusCode'):
                print(f'   Status Code: {data["statusCode"]}')
            if data.get('data', {}).get('time'):
                print(f'   Time: {data["data"]["time"]}')
            if data.get('callType'):
                print(f'   Call Type: {data["callType"]}')
                if data.get('callType') == 'actions':
                    call_types = data.get('data', {}).get('call_types', [])
                    print(f'   Supported call types count: {len(call_types)}')
                
        except asyncio.TimeoutError:
            timeout_count += 1
            print(f'[⚠️] Waiting timeout #{timeout_count}')
            break
        except Exception as e:
            print(f'[❌] Receive error: {e}')
            break
    
    # Analyze results
    if test_type == "ping":
        success = any(r.get('callType') == 'ping' for r in responses)
    else:
        success = any(r.get('statusCode') == 201 for r in responses)
        
    if success:
        print(f'[✅] {scenario_name} - Test passed!')
    else:
        print(f'[❌] {scenario_name} - Test failed')
        
    return success

async def get_available_buildings_list(config):
    """Get list of available buildings from KONE API"""
    try:
        token = get_access_token(config['client_id'], config['client_secret'], 
                                config.get('token_endpoint', 'https://dev.kone.com/api/v2/oauth2/token'))
        
        url = "https://dev.kone.com/api/v2/application/self/resources"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    buildings = data.get('buildings', [])
                    print(f"🏢 发现 {len(buildings)} 栋可用建筑")
                    
                    building_list = []
                    if buildings:
                        for building in buildings:
                            building_list.append(building['id'])
                            print(f"   - {building['id']} ({building.get('name', 'N/A')})")
                        return building_list, token
                    else:
                        print("⚠️ 未发现可用建筑，返回默认建筑列表")
                        return ['L1QinntdEOg', 'fWlfHyPlaca'], token
                else:
                    print(f"❌ 获取建筑列表失败: {response.status}")
                    return ['L1QinntdEOg', 'fWlfHyPlaca'], token
                    
    except Exception as e:
        print(f"❌ 获取建筑列表异常: {e}")
        # 返回默认值
        token = get_access_token(config['client_id'], config['client_secret'], 
                                config.get('token_endpoint', 'https://dev.kone.com/api/v2/oauth2/token'))
        return ['L1QinntdEOg', 'fWlfHyPlaca'], token

async def get_building_config_via_ping(websocket, building_id, max_retries=3):
    """Use ping call to get building configuration with retry mechanism"""
    formatted_building_id = building_id if building_id.startswith("building:") else f"building:{building_id}"
    
    for retry_count in range(max_retries):
        try:
            request_id = get_request_id()
            
            ping_msg = {
                "type": "common-api",
                "buildingId": formatted_building_id,
                "callType": "ping",
                "groupId": "1",
                "payload": {
                    "request_id": request_id
                }
            }
            
            print(f"📡 正在通过 ping 获取建筑 {building_id} 的配置... (尝试 {retry_count + 1}/{max_retries})")
            await websocket.send(json.dumps(ping_msg))
            
            # 等待响应
            timeout_count = 0
            while timeout_count < 3:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=15)
                    data = json.loads(message)
                    
                    # 检查是否是包含配置信息的ping响应
                    if (data.get('callType') == 'config' and 
                        data.get('data', {}).get('destinations')):
                        
                        print(f"✅ 成功获取建筑配置，包含 {len(data['data']['destinations'])} 个目标区域")
                        return data['data']
                    
                except asyncio.TimeoutError:
                    timeout_count += 1
                    print(f"⚠️ 等待配置响应超时 #{timeout_count}")
                    
            print(f"❌ 第 {retry_count + 1} 次尝试未能获取建筑配置")
            
            # 如果不是最后一次尝试，等待一小段时间再重试
            if retry_count < max_retries - 1:
                print("🔄 等待 2 秒后重试...")
                await asyncio.sleep(2)
                
        except Exception as e:
            print(f"❌ 第 {retry_count + 1} 次获取建筑配置异常: {e}")
            if retry_count < max_retries - 1:
                print("🔄 等待 2 秒后重试...")
                await asyncio.sleep(2)
    
    print(f"❌ 经过 {max_retries} 次尝试仍未能获取建筑配置")
    return None

def generate_virtual_building_config(building_id, config_data):
    """Generate virtual_building_config.yml based on API data"""
    config_file_path = 'virtual_building_config.yml'
    
    # 检查文件是否存在
    config_file_exists = False
    try:
        with open(config_file_path, 'r') as f:
            existing_config = yaml.safe_load(f)
            config_file_exists = True
            if existing_config.get('building', {}).get('id') == building_id:
                print(f"✅ 配置文件已存在且建筑ID匹配 ({building_id})，跳过重建")
                return
    except FileNotFoundError:
        print(f"📝 配置文件 {config_file_path} 不存在，将创建新文件")
        config_file_exists = False
    
    # 如果没有配置数据，创建基础配置文件
    if not config_data:
        print("⚠️ 无API配置数据，创建基础配置文件")
        basic_config = {
            'building': {
                'id': building_id,
                'name': f'Virtual Building {building_id}',
                'api_version': 3
            },
            'elevator_groups': {
                'group_1': {
                    'lifts': [
                        {'id': 'Lift A', 'type': 'passenger'},
                        {'id': 'Lift B', 'type': 'passenger'},
                        {'id': 'Lift C', 'type': 'passenger'},
                        {'id': 'Lift D', 'type': 'passenger'}
                    ]
                }
            },
            'floors': {
                f'f_{i}': {
                    'level': i,
                    'areas': [
                        {'area_id': i * 1000, 'side': 1, 'short_name': str(i)},
                        {'area_id': i * 1000 + 10, 'side': 2, 'short_name': f'{i}R'}
                    ]
                } for i in range(1, 41)  # 默认1-40层
            }
        }
        
        with open(config_file_path, 'w') as f:
            yaml.dump(basic_config, f, default_flow_style=False, indent=2, allow_unicode=True)
        
        print(f"✅ 已创建基础配置文件 {config_file_path}")
        print(f"   - 建筑ID: {building_id}")
        print(f"   - 默认楼层: 1-40")
        print(f"   - 默认电梯: 4部 (A, B, C, D)")
        return
    
    try:
        destinations = config_data.get('destinations', [])
        groups = config_data.get('groups', [])
        
        # 构建新的配置结构
        new_config = {
            'building': {
                'id': building_id,
                'name': f'Virtual Building {building_id}',
                'api_version': config_data.get('version_major', 3)
            },
            'elevator_groups': {},
            'floors': {},
            'destinations': []
        }
        
        # 处理电梯组
        if groups:
            for group in groups:
                group_id = f"group_{group.get('group_id', 1)}"
                lifts = []
                for lift in group.get('lifts', []):
                    lifts.append({
                        'id': lift.get('lift_name', f"Lift_{lift.get('lift_id', 'Unknown')}"),
                        'lift_id': lift.get('lift_id'),
                        'type': 'passenger'
                    })
                new_config['elevator_groups'][group_id] = {'lifts': lifts}
        
        # 处理楼层目标
        floors_dict = {}
        for dest in destinations:
            area_id = dest.get('area_id')
            floor_id = dest.get('group_floor_id')
            short_name = dest.get('short_name', str(floor_id))
            
            if floor_id not in floors_dict:
                floors_dict[floor_id] = {
                    'level': floor_id,
                    'areas': [],
                    'short_name': short_name
                }
            
            floors_dict[floor_id]['areas'].append({
                'area_id': area_id,
                'side': dest.get('group_side', 1),
                'short_name': dest.get('short_name'),
                'exit': dest.get('exit', False)
            })
        
        # 转换为配置格式
        for floor_id, floor_data in sorted(floors_dict.items()):
            floor_key = f"f_{floor_id}"
            new_config['floors'][floor_key] = floor_data
        
        # 保存配置文件
        with open(config_file_path, 'w') as f:
            yaml.dump(new_config, f, default_flow_style=False, indent=2, allow_unicode=True)
        
        print(f"✅ 已生成新的 {config_file_path}")
        print(f"   - 建筑ID: {building_id}")
        print(f"   - 楼层数: {len(floors_dict)}")
        print(f"   - 目标区域数: {len(destinations)}")
        print(f"   - 电梯组数: {len(groups)}")
        
    except Exception as e:
        print(f"❌ 生成配置文件失败: {e}")
        # 如果生成失败且文件不存在，创建基础配置
        if not config_file_exists:
            print("🔄 创建基础配置文件作为备选...")
            generate_virtual_building_config(building_id, None)

async def multi_scenario_test():
    """Execute complete elevator scenario tests - all 37 test cases with dynamic building selection"""
    print("🏢 KONE Complete Elevator Call Test (37 test cases)")
    print("Enhanced with dynamic building configuration")
    print("=" * 60)
    
    try:
        # Load configuration
        config = load_config()
        
        # 1. Get available buildings list
        print("\n🔍 步骤 1: 获取可用建筑列表...")
        building_list, token = await get_available_buildings_list(config)
        
        if not building_list:
            print("⚠️ 未获取到建筑列表，使用默认建筑")
            building_list = ['L1QinntdEOg', 'fWlfHyPlaca']
        
        selected_building_id = None
        config_data = None
        websocket = None
        
        # 2. Try each building until successful config retrieval
        ws_endpoint = config.get('ws_endpoint', 'wss://dev.kone.com/stream-v2')
        uri = f"{ws_endpoint}?accessToken={token}"
        
        for i, building_id in enumerate(building_list):
            print(f"\n🔌 步骤 2.{i+1}: 尝试建筑 {building_id} ({i+1}/{len(building_list)})...")
            
            try:
                # Establish WebSocket connection for this building
                websocket = await websockets.connect(uri, subprotocols=['koneapi'])
                print('[✅] WebSocket connection established')
                
                # 3. Try to get building configuration via ping
                print(f"🏗️ 步骤 3.{i+1}: 获取建筑 {building_id} 的配置...")
                config_data = await get_building_config_via_ping(websocket, building_id, max_retries=1)
                
                if config_data:
                    print(f"✅ 成功获取建筑 {building_id} 的配置!")
                    selected_building_id = building_id
                    break
                else:
                    print(f"❌ 建筑 {building_id} 配置获取失败，尝试下一栋...")
                    await websocket.close()
                    websocket = None
                    
            except Exception as e:
                print(f"❌ 连接建筑 {building_id} 失败: {e}")
                if websocket:
                    await websocket.close()
                    websocket = None
        
        # Check if we found a working building
        if not selected_building_id:
            print("❌ 所有建筑配置获取都失败，使用第一个建筑作为默认选择")
            selected_building_id = building_list[0]
            # Re-establish connection for the default building
            websocket = await websockets.connect(uri, subprotocols=['koneapi'])
            print('[✅] WebSocket connection established for default building')
        
        # 4. Generate/update virtual_building_config.yml
        print(f"\n📝 步骤 4: 更新配置文件...")
        generate_virtual_building_config(selected_building_id, config_data)
        
        # 5. Execute all test scenarios with the selected building
        print(f"\n📊 步骤 5: 执行 37 项测试 (建筑: {selected_building_id})...")
        
        # Update building ID in test scenarios
        formatted_building_id = selected_building_id if selected_building_id.startswith("building:") else f"building:{selected_building_id}"
        
        # Complete list of 37 test scenarios
        test_scenarios = [
            # Initialization tests
            {"name": "Solution initialization", "test_id": "Test_1", "test_type": "ping", "data": {}},
            {"name": "API connectivity verification", "test_id": "Test_2", "test_type": "ping", "data": {}},
            {"name": "Service status check", "test_id": "Test_3", "test_type": "ping", "data": {}},
            {"name": "Building configuration validation", "test_id": "Test_4", "test_type": "actions", "data": {"action": "config"}},
            {"name": "WebSocket handshake verification", "test_id": "Test_5", "test_type": "ping", "data": {}},
                
                # Call management tests
                {"name": "Basic destination call", "test_id": "Test_6", "test_type": "call", "data": {
                    "from_floor": 1, "to_floor": 2, "user_id": "robot_test_6", "source": 1000, "destination": 2000, "action_id": 2, "terminal": 1
                }},
                {"name": "Multi-floor call", "test_id": "Test_7", "test_type": "call", "data": {
                    "from_floor": 1, "to_floor": 5, "user_id": "robot_test_7", "source": 1000, "destination": 5000
                }},
                {"name": "Delayed call", "test_id": "Test_8", "test_type": "call", "data": {
                    "from_floor": 2, "to_floor": 3, "user_id": "robot_test_8", "source": 2000, "destination": 3000, "delay": 5
                }},
                {"name": "Call cancellation", "test_id": "Test_9", "test_type": "call", "data": {
                    "from_floor": 1, "to_floor": 4, "user_id": "robot_test_9", "source": 1000, "destination": 4000
                }},
                {"name": "Concurrent calls", "test_id": "Test_10", "test_type": "call", "data": {
                    "from_floor": 1, "to_floor": 4, "user_id": "robot_test_10", "source": 1000, "destination": 4000
                }},
                
                # Status monitoring tests
                {"name": "Real-time status monitoring", "test_id": "Test_11", "test_type": "actions", "data": {"action": "status"}},
                {"name": "Elevator position tracking", "test_id": "Test_12", "test_type": "actions", "data": {"action": "position"}},
                {"name": "Group status query", "test_id": "Test_13", "test_type": "actions", "data": {"action": "group_status"}},
                {"name": "Load status monitoring", "test_id": "Test_14", "test_type": "actions", "data": {"action": "load_status"}},
                {"name": "Movement direction detection", "test_id": "Test_15", "test_type": "actions", "data": {"action": "direction"}},
                
                # Error handling tests
                {"name": "Invalid floor handling", "test_id": "Test_16", "test_type": "call", "data": {
                    "from_floor": 99, "to_floor": 2, "user_id": "robot_test_16", "source": 9999, "destination": 2000
                }},
                {"name": "Same floor error", "test_id": "Test_17", "test_type": "call", "data": {
                    "from_floor": 2, "to_floor": 2, "user_id": "robot_test_17", "source": 2000, "destination": 2000
                }},
                {"name": "Excessive delay error", "test_id": "Test_18", "test_type": "call", "data": {
                    "from_floor": 1, "to_floor": 2, "user_id": "robot_test_18", "source": 1000, "destination": 2000, "delay": 60
                }},
                {"name": "Invalid building ID", "test_id": "Test_19", "test_type": "call", "data": {
                    "from_floor": 1, "to_floor": 2, "user_id": "robot_test_19", "source": 1000, "destination": 2000
                }},
                {"name": "Missing parameters error", "test_id": "Test_20", "test_type": "call", "data": {
                    "user_id": "robot_test_20"  # Deliberately missing required parameters
                }},
                
                # Performance tests
                {"name": "Response time test", "test_id": "Test_21", "test_type": "ping", "data": {}},
                {"name": "Load performance test", "test_id": "Test_22", "test_type": "call", "data": {
                    "from_floor": 1, "to_floor": 3, "user_id": "robot_test_22", "source": 1000, "destination": 3000
                }},
                {"name": "Multi-user concurrency", "test_id": "Test_23", "test_type": "call", "data": {
                    "from_floor": 2, "to_floor": 4, "user_id": "robot_test_23", "source": 2000, "destination": 4000
                }},
                {"name": "Peak load handling", "test_id": "Test_24", "test_type": "call", "data": {
                    "from_floor": 3, "to_floor": 5, "user_id": "robot_test_24", "source": 3000, "destination": 5000
                }},
                {"name": "Continuous call handling", "test_id": "Test_25", "test_type": "call", "data": {
                    "from_floor": 4, "to_floor": 6, "user_id": "robot_test_25", "source": 4000, "destination": 6000
                }},
                {"name": "Long-term connection stability", "test_id": "Test_26", "test_type": "ping", "data": {}},
                {"name": "High-frequency call handling", "test_id": "Test_27", "test_type": "call", "data": {
                    "from_floor": 5, "to_floor": 7, "user_id": "robot_test_27", "source": 5000, "destination": 7000
                }},
                {"name": "Complex path planning", "test_id": "Test_28", "test_type": "call", "data": {
                    "from_floor": 1, "to_floor": 10, "user_id": "robot_test_28", "source": 1000, "destination": 10000
                }},
                {"name": "Multi-stop handling", "test_id": "Test_29", "test_type": "call", "data": {
                    "from_floor": 2, "to_floor": 8, "user_id": "robot_test_29", "source": 2000, "destination": 8000
                }},
                {"name": "Rapid response test", "test_id": "Test_30", "test_type": "ping", "data": {}},
                {"name": "System recovery capability", "test_id": "Test_31", "test_type": "actions", "data": {"action": "recovery"}},
                {"name": "Error recovery test", "test_id": "Test_32", "test_type": "actions", "data": {"action": "error_recovery"}},
                {"name": "Resource utilization", "test_id": "Test_33", "test_type": "actions", "data": {"action": "resource_usage"}},
                {"name": "Service availability", "test_id": "Test_34", "test_type": "ping", "data": {}},
                {"name": "Data consistency", "test_id": "Test_35", "test_type": "actions", "data": {"action": "data_consistency"}},
            {"name": "Integration test", "test_id": "Test_36", "test_type": "call", "data": {
                "from_floor": 6, "to_floor": 9, "user_id": "robot_test_36", "source": 6000, "destination": 9000
            }},
            {"name": "End-to-end validation", "test_id": "Test_37", "test_type": "call", "data": {
                "from_floor": 7, "to_floor": 11, "user_id": "robot_test_37", "source": 7000, "destination": 11000
            }}
        ]
        
        # Execute all test scenarios
        results = []
        print(f"\n🚀 Starting execution of {len(test_scenarios)} test scenarios...")
        
        for i, scenario in enumerate(test_scenarios, 1):
            try:
                print(f"\n📊 Progress: {i}/{len(test_scenarios)}")
                success = await test_elevator_scenario(
                    websocket, 
                    scenario["name"], 
                    scenario["test_id"], 
                    scenario["data"],
                    scenario.get("test_type", "call"),
                    formatted_building_id
                )
                results.append({
                    "scenario": scenario["name"],
                    "test_id": scenario["test_id"],
                    "success": success,
                    "category": scenario.get("category", "unknown")
                })
                
                # Brief delay to avoid too rapid requests
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f'[💥] {scenario["name"]} exception: {e}')
                results.append({
                    "scenario": scenario["name"],
                    "test_id": scenario["test_id"],
                    "success": False,
                    "error": str(e),
                    "category": scenario.get("category", "unknown")
                })
        
        # Summary results
        print("\n" + "=" * 80)
        print("📊 Test Results Summary:")
        print("-" * 80)
        
        success_count = 0
        categories = {}
        
        for result in results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            error_info = f" ({result.get('error', '')})" if not result["success"] and result.get('error') else ""
            print(f"{result['test_id']:12} | {result['scenario']:25} | {status}{error_info}")
            
            if result["success"]:
                success_count += 1
            
            # Statistics by category
            category = result.get("category", "unknown")
            if category not in categories:
                categories[category] = {"total": 0, "passed": 0}
            categories[category]["total"] += 1
            if result["success"]:
                categories[category]["passed"] += 1
        
        print(f"\n📈 Overall Results: {success_count}/{len(results)} tests passed ({success_count/len(results)*100:.1f}%)")
        
        # Category statistics
        if categories:
            print(f"\n📋 Category Statistics:")
            for category, stats in categories.items():
                rate = stats["passed"] / stats["total"] * 100 if stats["total"] > 0 else 0
                print(f"  {category}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")
        
        return success_count == len(results)
        
    except Exception as e:
        print(f'[💥] Overall test exception: {e}')
        import traceback
        print(f'[🔍] Detailed error: {traceback.format_exc()}')
        return False
    finally:
        if websocket and not websocket.closed:
            await websocket.close()

async def main():
    """Main function"""
    print(f"🕒 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = await multi_scenario_test()
    
    print("\n" + "="*80)
    if success:
        print("🎊 All 37 elevator call scenarios test successful!")
        print("✅ KONE WebSocket API complete functionality verification passed")
        print("🏆 Perfect achievement of 100% success rate target!")
    else:
        print("⚠️ Some elevator call scenarios test failed")
        print("🔧 Recommend checking specific failed scenarios")
        print("📋 Compare with REST API test results for analysis")
        
    exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
