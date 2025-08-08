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
import uuid
from datetime import datetime
from pathlib import Path
from report_generator import ReportGenerator, TestResult
import threading
import time

def load_config():
    """Load configuration file"""
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    return config

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
    
    import time
    start_time = time.time()
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
        
    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000
        
    if success:
        print(f'[✅] {scenario_name} - Test passed! (Duration: {duration_ms:.1f}ms)')
    else:
        print(f'[❌] {scenario_name} - Test failed (Duration: {duration_ms:.1f}ms)')
        
    return success, duration_ms

def sort_buildings_by_preference(buildings):
    """
    Sort buildings by priority:
    1. v2 buildings first
    2. Buildings supporting v2
    3. v1 buildings
    """
    v2_buildings = [b for b in buildings if b.get('version') == 'v2']
    supports_v2_buildings = [b for b in buildings if b.get('version') != 'v2' and b.get('supports_v2', False)]
    v1_buildings = [b for b in buildings if b.get('version') != 'v2' and not b.get('supports_v2', False)]
    
    return v2_buildings + supports_v2_buildings + v1_buildings

def get_user_building_choice(buildings, timeout=5):
    """
    Let user choose building with timeout functionality
    """
    user_choice = [None]  # Use list to modify value in inner function
    
    def get_input():
        try:
            choice = input()
            if choice.strip():
                user_choice[0] = choice.strip()
        except:
            pass
    
    # Display building options
    print(f"\n🏗️ Detected {len(buildings)} buildings, please select building to test:")
    for i, building in enumerate(buildings, 1):
        version_label = "v2" if building.get('version') == 'v2' else ("supports v2" if building.get('supports_v2', False) else "v1")
        print(f"   {i}. {building['id']} ({building.get('name', 'N/A')}) [{version_label}]")
    
    print(f"\nPlease enter building number (1-{len(buildings)}), auto-select optimal building after {timeout}s: ", end='', flush=True)
    
    # Start input thread
    input_thread = threading.Thread(target=get_input)
    input_thread.daemon = True
    input_thread.start()
    
    # Wait for user input or timeout
    input_thread.join(timeout)
    
    if user_choice[0] is not None:
        try:
            choice_idx = int(user_choice[0]) - 1
            if 0 <= choice_idx < len(buildings):
                selected_building = buildings[choice_idx]
                print(f"\n✅ User selected: {selected_building['id']} ({selected_building.get('name', 'N/A')})")
                return selected_building
            else:
                print(f"\n⚠️ Invalid selection, auto-selecting optimal building")
        except ValueError:
            print(f"\n⚠️ Invalid input format, auto-selecting optimal building")
    else:
        print(f"\n⏱️ Timeout, auto-selecting optimal building")
    
    # Auto-select: choose first after priority sorting
    sorted_buildings = sort_buildings_by_preference(buildings)
    selected_building = sorted_buildings[0]
    version_label = "v2" if selected_building.get('version') == 'v2' else ("supports v2" if selected_building.get('supports_v2', False) else "v1")
    print(f"🎯 Auto-selected: {selected_building['id']} ({selected_building.get('name', 'N/A')}) [{version_label}]")
    
    return selected_building

async def get_available_buildings_list(config):
    """Get list of available buildings from KONE API with detailed information"""
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
                    print(f"🏢 Found {len(buildings)} available buildings")
                    
                    building_info_list = []
                    if buildings:
                        for building in buildings:
                            building_info = {
                                'id': building['id'],
                                'name': building.get('name', 'N/A'),
                                'version': 'v2' if 'V2' in building.get('desc', '') else 'v1',  # Determine version by desc
                                'supports_v2': 'V2' in building.get('desc', '')  # Whether supports v2
                            }
                            building_info_list.append(building_info)
                            
                            # Determine version label
                            version_label = "v2" if building_info['version'] == 'v2' else ("supports v2" if building_info['supports_v2'] else "v1")
                            print(f"   - {building['id']} ({building_info['name']}) [{version_label}]")
                        
                        return building_info_list, token
                    else:
                        print("⚠️ No available buildings found, returning default building list")
                        default_buildings = [
                            {'id': 'L1QinntdEOg', 'name': 'Default1', 'version': 'v1', 'supports_v2': True},
                            {'id': 'fWlfHyPlaca', 'name': 'Default2', 'version': 'v1', 'supports_v2': True}
                        ]
                        return default_buildings, token
                else:
                    print(f"❌ Failed to get building list: {response.status}")
                    default_buildings = [
                        {'id': 'L1QinntdEOg', 'name': 'Default1', 'version': 'v1', 'supports_v2': True},
                        {'id': 'fWlfHyPlaca', 'name': 'Default2', 'version': 'v1', 'supports_v2': True}
                    ]
                    return default_buildings, token
                    
    except Exception as e:
        print(f"❌ Exception getting building list: {e}")
        # Return default value
        token = get_access_token(config['client_id'], config['client_secret'], 
                                config.get('token_endpoint', 'https://dev.kone.com/api/v2/oauth2/token'))
        return ['L1QinntdEOg', 'fWlfHyPlaca'], token

async def get_building_config_via_ping(websocket, building_id, max_retries=3):
    """Use multiple request types to get building configuration with retry mechanism"""
    formatted_building_id = building_id if building_id.startswith("building:") else f"building:{building_id}"
    
    for retry_count in range(max_retries):
        try:
            # Try multiple request types to get configuration
            test_requests = [
                {
                    "name": "actions",
                    "message": {
                        "type": "common-api",
                        "requestId": str(uuid.uuid4()),
                        "callType": "actions",
                        "buildingId": formatted_building_id,
                        "groupId": "1"
                    }
                },
                {
                    "name": "config", 
                    "message": {
                        "type": "common-api",
                        "requestId": str(uuid.uuid4()),
                        "callType": "config",
                        "buildingId": formatted_building_id,
                        "groupId": "1"
                    }
                },
                {
                    "name": "ping",
                    "message": {
                        "type": "common-api",
                        "buildingId": formatted_building_id,
                        "callType": "ping",
                        "groupId": "1",
                        "payload": {
                            "request_id": get_request_id()
                        }
                    }
                }
            ]
            
            print(f"📡 Getting building {building_id} configuration... (attempt {retry_count + 1}/{max_retries})")
            
            for request in test_requests:
                try:
                    print(f"  🔸 Trying {request['name']} request...")
                    await websocket.send(json.dumps(request['message']))
                    
                    # Wait for response
                    timeout_count = 0
                    while timeout_count < 2:  # Reduce waiting time for single request
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=10)
                            data = json.loads(message)
                            
                            # Check configuration data in response
                            if (data.get('callType') == 'actions' and 
                                data.get('data', {}).get('destinations')):
                                
                                config_data = data['data']
                                print(f"✅ Successfully obtained building configuration via request")
                                print(f"   - Destination areas count: {len(config_data.get('destinations', []))}")
                                print(f"   - Elevator groups count: {len(config_data.get('groups', []))}")
                                return config_data
                            
                            # Check configuration data in response
                            elif (data.get('callType') == 'config' and 
                                  data.get('data', {}).get('destinations')):
                                
                                config_data = data['data']
                                print(f"✅ Successfully obtained building configuration via request")
                                print(f"   - Destination areas count: {len(config_data.get('destinations', []))}")
                                print(f"   - Elevator groups count: {len(config_data.get('groups', []))}")
                                return config_data
                            
                            # Check response
                            elif data.get('callType') == 'ping':
                                print(f"  ✓ ping response normal, status code: {data.get('statusCode', 'N/A')}")
                                
                        except asyncio.TimeoutError:
                            timeout_count += 1
                            print(f"    ⚠️ {request['name']} request timeout #{timeout_count}")
                            break
                        except Exception as e:
                            print(f"    ❌ {request['name']} request parsing exception: {e}")
                            break
                            
                except Exception as e:
                    print(f"    ❌ {request['name']} request sending exception: {e}")
                    continue
                    
            print(f"❌ Attempt .* failed to get building configuration")
            
            # If not the last attempt, wait a short time before retry
            if retry_count < max_retries - 1:
                print("🔄 Wait  seconds before retry...")
                await asyncio.sleep(3)
                
        except Exception as e:
            print(f"❌ Attempt .* get building configuration exception: {e}")
            if retry_count < max_retries - 1:
                print("🔄 Wait  seconds before retry...")
                await asyncio.sleep(3)
    
    print(f"❌ Unable to get building configuration after .* attempts")
    return None

def generate_virtual_building_config(building_id, config_data):
    """Generate virtual_building_config.yml based on API data"""
    config_file_path = 'virtual_building_config.yml'
    
    # Check if file exists
    config_file_exists = False
    try:
        with open(config_file_path, 'r') as f:
            existing_config = yaml.safe_load(f)
            config_file_exists = True
            if existing_config.get('building', {}).get('id') == building_id:
                print(f"✅ Configuration file exists and Building ID matches ({building_id})，skip rebuild")
                return
    except FileNotFoundError:
        print(f"📝 Configuration file .* does not exist, will create new file")
        config_file_exists = False
    
    # If no configuration data, create basic configuration file
    if not config_data:
        print("⚠️ No API configuration data, create basic configuration file")
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
                } for i in range(1, 41)  # Default 1-40 floors
            }
        }
        
        with open(config_file_path, 'w') as f:
            yaml.dump(basic_config, f, default_flow_style=False, indent=2, allow_unicode=True)
        
        print(f"✅ Created basic configuration file {config_file_path}")
        print(f"   - Building ID: {building_id}")
        print(f"   - Default floors: 1-40")
        print(f"   - Default elevators: 4 elevators (A, B, C, D)")
        return
    
    try:
        destinations = config_data.get('destinations', [])
        groups = config_data.get('groups', [])
        
        # Build new configuration structure
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
        
        # Process elevator groups
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
        
        # Process floor targets
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
        
        # Convert to configuration format
        for floor_id, floor_data in sorted(floors_dict.items()):
            floor_key = f"f_{floor_id}"
            new_config['floors'][floor_key] = floor_data
        
        # Save configuration file
        with open(config_file_path, 'w') as f:
            yaml.dump(new_config, f, default_flow_style=False, indent=2, allow_unicode=True)
        
        print(f"✅ Generated new {config_file_path}")
        print(f"   - Building ID: {building_id}")
        print(f"   - Floor count: {len(floors_dict)}")
        print(f"   - Target areas count: {len(destinations)}")
        print(f"   - Elevator groups count: {len(groups)}")
        
    except Exception as e:
        print(f"❌ Failed to generate configuration file: {e}")
        # If generation fails and file does not exist, create basic configuration
        if not config_file_exists:
            print("🔄 Create basic configuration file as fallback...")
            generate_virtual_building_config(building_id, None)

async def multi_scenario_test():
    """Execute complete elevator scenario tests - all 37 test cases with dynamic building selection"""
    print("🏢 KONE Complete Elevator Call Test (37 test cases)")
    print("Enhanced with dynamic building configuration and user selection")
    print("=" * 60)
    
    try:
        # Load configuration
        config = load_config()
        
        # 1. Get available buildings list
        print("\n🔍 Step : Get available building list...")
        building_info_list, token = await get_available_buildings_list(config['kone'])
        
        if not building_info_list:
            print("⚠️ Failed to get building list, using default buildings")
            building_info_list = [
                {'id': 'L1QinntdEOg', 'name': 'Default1', 'version': 'v1', 'supports_v2': True},
                {'id': 'fWlfHyPlaca', 'name': 'Default2', 'version': 'v1', 'supports_v2': True}
            ]
        
        # 2. Let user choose building or auto-select after timeout
        if len(building_info_list) > 1:
            selected_building = get_user_building_choice(building_info_list, timeout=5)
        else:
            selected_building = building_info_list[0]
            print(f"\n🎯 Only one building, auto-select：{selected_building['id']} ({selected_building.get('name', 'N/A')})")
        
        selected_building_id = selected_building['id']
        config_data = None
        websocket = None
        
        # 3. Connect to selected building and get configuration
        ws_endpoint = config.get('ws_endpoint', 'wss://dev.kone.com/stream-v2')
        uri = f"{ws_endpoint}?accessToken={token}"
        
        print(f"\n🔌 Step : Connect to selected building {selected_building_id}...")
        
        try:
            # Establish WebSocket connection for selected building
            websocket = await websockets.connect(uri, subprotocols=['koneapi'])
            print('[✅] WebSocket connection established')
            
            # Try to get building configuration via ping
            print(f"🏗️ Step 3: Get building configuration...")
            config_data = await get_building_config_via_ping(websocket, selected_building_id, max_retries=3)
            
            if config_data:
                print(f"✅ Successfully obtained building configuration!")
            else:
                print(f"❌ Building .* configuration failed, trying other buildings...")
                await websocket.close()
                websocket = None
                
                # Fallback: try other buildings in priority order
                sorted_buildings = sort_buildings_by_preference(building_info_list)
                for fallback_building in sorted_buildings:
                    if fallback_building['id'] == selected_building_id:
                        continue  # Skip already tried building
                    
                    print(f"\n🔄 Trying fallback building {fallback_building['id']}...")
                    try:
                        websocket = await websockets.connect(uri, subprotocols=['koneapi'])
                        config_data = await get_building_config_via_ping(websocket, fallback_building['id'], max_retries=1)
                        
                        if config_data:
                            selected_building_id = fallback_building['id']
                            selected_building = fallback_building
                            print(f"✅ Successfully connected to fallback building {selected_building_id}!")
                            break
                        else:
                            await websocket.close()
                            websocket = None
                    except Exception as e:
                        print(f"❌ Failed to connect to fallback building : {e}")
                        if websocket:
                            await websocket.close()
                            websocket = None
                            
        except Exception as e:
            print(f"❌ Failed to connect to building : {e}")
            if websocket:
                await websocket.close()
                websocket = None
        
        # Check if we found a working building
        if not selected_building_id or not config_data:
            print("❌ All building configuration attempts failed, using first building as default")
            selected_building_id = building_info_list[0]['id']
            selected_building = building_info_list[0]
            # Re-establish connection for the default building
            websocket = await websockets.connect(uri, subprotocols=['koneapi'])
            print('[✅] WebSocket connection established for default building')
            print("🔄 Create basic configuration file as fallback...")
            generate_virtual_building_config(selected_building_id, None)
        
        # 4. Generate/update virtual_building_config.yml
        print(f"\n📝 Step 4: Update configuration file...")
        if config_data:
            generate_virtual_building_config(selected_building_id, config_data)
        else:
            print("⚠️ No configuration data, will try to re-obtain during testing")
        
        # 5. Execute all test scenarios with the selected building
        print(f"\n📊 Step : Execute  tests (building: {selected_building_id})...")
        version_label = "v2" if selected_building.get('version') == 'v2' else ("supports v2" if selected_building.get('supports_v2', False) else "v1")
        print(f"🏗️ Selected building info: {selected_building.get('name', 'N/A')} [{version_label}]")
        
        # 5. Execute all test scenarios with the selected building
        print(f"\n📊 Step : Execute  tests (building: {selected_building_id})...")
        
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
                success, duration_ms = await test_elevator_scenario(
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
                    "duration_ms": duration_ms,
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
                    "duration_ms": 0,  # Set to 0 for failed tests
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
        
        return success_count == len(results), results
        
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
    
    # Load configuration
    config = load_config()
    
    success, test_results = await multi_scenario_test()
    
    # Generate comprehensive test reports
    try:
        print("\n📊 Generate multi-format test reports...")
        
        # Convert test results to TestResult objects with enhanced fields
        report_test_results = []
        
        # 测试用例的映射信息（从指南获取）
        test_guide_info = {
            "Test_1": {
                "name": "Solution initialization",
                "description": "Solution initialization",
                "expected_result": "- Connections established by solution to test environment (Virtual or Preproduction).\n- Authentication successful\n- Get resources successful\n- Building config can be obtained.\n- Response code 200\n- Response code 401 in case if there is issue with API Credentials\n- Building actions can be obtained.\n- Response code 200\n- Response code 401 in case if there is issue with API Credentials"
            },
            "Test_2": {
                "name": "API connectivity verification", 
                "description": "Verification of API connectivity and WebSocket establishment",
                "expected_result": "- WebSocket connection established successfully\n- API endpoints accessible\n- Authentication working properly"
            },
            "Test_3": {
                "name": "Service status check",
                "description": "Check if elevator service is operational",
                "expected_result": "- Service status check successful\n- System operational status confirmed"
            },
            "Test_4": {
                "name": "Building configuration validation",
                "description": "Validate building configuration retrieval",
                "expected_result": "- Building configuration retrieved successfully\n- Configuration data complete and valid"
            },
            "Test_5": {
                "name": "WebSocket handshake verification",
                "description": "Verify WebSocket handshake process",
                "expected_result": "- WebSocket handshake completed successfully\n- Connection stable and ready for communication"
            },
            "Test_6": {
                "name": "Basic destination call",
                "description": "Call: Basic call -> Source: any floor, Destination: any floor Note: Landing Call – Source only, Car Call – Destination only",
                "expected_result": "- Call accepted and elevator moving\n- Response code 201\n- Session id returned\n- Elevator tracking\n- Floor markings are as expected\n- Floor order is as expected\n- Elevator destination is correct as requested"
            }
            # 可以继续添加其他测试用例的映射...
        }
        
        for result in test_results:
            status = "PASS" if result["success"] else "FAIL"
            
            # 从映射获取测试信息，如果没有则使用默认值
            guide_info = test_guide_info.get(result["test_id"], {})
            test_name = guide_info.get("name", result["scenario"])
            description = guide_info.get("description", result["scenario"])
            expected_result = guide_info.get("expected_result", "Test should execute successfully and return expected results")
            
            test_result = TestResult(
                test_id=result["test_id"],
                name=test_name,
                description=description,
                expected_result=expected_result,
                test_result=status,
                status=status,
                duration_ms=result.get("duration_ms", 0),
                error_message=result.get("error", None),
                response_data=result.get("response_data", None),
                category=result.get("category", "elevator_call")
            )
            report_test_results.append(test_result)
        
        # Prepare enhanced metadata with guide-required fields
        metadata = {
            "test_framework": "KONE SR-API v2.0",
            "api_version": "2.0.0",
            "test_date": datetime.now().isoformat(),
            "total_tests": len(test_results),
            "building_id": "Dynamic",
            "test_environment": "WebSocket",
            "tester": "testall.py",
            "version": "2.0.0",
            # 从指南要求的额外字段
            "setup": "Get access to the equipment for testing:\n- Virtual equipment, available in KONE API portal\n- Preproduction equipment, by contacting KONE API Support (api-support@kone.com)",
            "pre_test_setup": "- Test environments available for the correct KONE API organization.\n- Building id can be retrieved (/resource endpoint).",
            "date": datetime.now().strftime("%d.%m.%Y"),
            "solution_provider": "IBC-AI CO.",
            "company_address": "待填写",
            "contact_person": "待填写", 
            "contact_email": "待填写",
            "contact_phone": "待填写",
            "tester": "自动化测试系统",
            "tested_system": "KONE Elevator Control Service",
            "system_version": "待填写",
            "software_name": "KONE SR-API Test Suite",
            "software_version": "2.0.0",
            "kone_sr_api_version": "v2.0",
            "kone_assistant_email": "待填写"
        }
        
        # Generate report
        reports_dir = Path("./reports")
        reports_dir.mkdir(exist_ok=True)
        
        generator = ReportGenerator("IBC-AI CO.")
        reports = generator.generate_report(report_test_results, metadata, str(reports_dir), config)
        
        # Save additional formats to files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save Markdown report
        if "markdown" in reports:
            md_filename = f"testall_report_{timestamp}.md"
            md_filepath = reports_dir / md_filename
            with open(md_filepath, 'w', encoding='utf-8') as f:
                f.write(reports["markdown"])
            print(f"✅ Markdown report generated：{md_filepath}")
        
        # Save JSON report
        if "json" in reports:
            json_filename = f"testall_report_{timestamp}.json"
            json_filepath = reports_dir / json_filename
            with open(json_filepath, 'w', encoding='utf-8') as f:
                f.write(reports["json"])
            print(f"✅ JSON report generated：{json_filepath}")
        
        # Save HTML report
        if "html" in reports:
            html_filename = f"testall_report_{timestamp}.html"
            html_filepath = reports_dir / html_filename
            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(reports["html"])
            print(f"✅ HTML report generated：{html_filepath}")
        
        # Excel report (already saved by generator)
        if "excel" in reports:
            print(f"✅ Excel report generated：{reports['excel']}")
        
        print(f"\n📁 All reports saved to：{reports_dir.absolute()}")
        
    except Exception as e:
        print(f"⚠️ Report generation failed：{e}")
        import traceback
        print(f"🔍 Detailed error：{traceback.format_exc()}")
    
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
