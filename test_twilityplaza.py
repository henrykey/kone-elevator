#!/usr/bin/env python
"""
TwilityPlaza虚拟建筑测试
使用真实的虚拟建筑数据进行完整功能测试
"""

import asyncio
import json
import yaml
from datetime import datetime
from drivers import KoneDriver, ElevatorCallRequest

# TwilityPlaza建筑配置
BUILDING_ID = "building:TwilityPlaza"
GROUP_ID = "1"

# 楼层到区域ID的映射（基于图片数据）
FLOOR_TO_AREA = {
    1: 1000,   # 1层
    2: 2000,   # 2层  
    3: 3000,   # 3层
    5: 5000,   # 5层
    10: 10000, # 10层
    15: 15000, # 15层
    20: 20000, # 20层
    25: 25000, # 25层
    30: 30000, # 30层
    35: 35000, # 35层
    40: 40000, # 40层 (顶层)
    -1: 1010   # 地下1层
}

# 电梯ID映射
LIFT_IDS = {
    "A": 1001010,  # Lift 1-A
    "B": 1001020,  # Lift 2-B  
    "C": 1001030,  # Lift 3-C
    "D": 1001040,  # Lift 4-D
    "E": 1001050,  # Lift 5-E
    "F": 1001060,  # Lift 6-F
    "G": 1001070,  # Lift 7-G
    "H": 1001080   # Lift 8-H
}

async def test_twilityplaza_complete():
    """使用TwilityPlaza进行完整功能测试"""
    
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
    
    try:
        print("🏢 TwilityPlaza虚拟建筑测试")
        print("=" * 60)
        print(f"建筑ID: {BUILDING_ID}")
        print(f"电梯组: {GROUP_ID}")
        print(f"楼层范围: 地下1层 - 40层")
        print(f"电梯数量: {len(LIFT_IDS)}部")
        
        # 1. 初始化连接
        print(f"\n1. 初始化连接...")
        init_result = await driver.initialize()
        if init_result.get('success'):
            print(f"✅ 连接初始化成功")
            print(f"   会话ID: {init_result.get('session_id')}")
        else:
            print(f"❌ 连接初始化失败: {init_result}")
            return False
        
        # 2. 测试ping
        print(f"\n2. 测试建筑连通性...")
        ping_result = await driver.ping(BUILDING_ID)
        print(f"Ping结果: {json.dumps(ping_result, indent=2)}")
        
        # 3. 获取建筑配置
        print(f"\n3. 获取建筑配置...")
        config_result = await driver.get_config(BUILDING_ID)
        print(f"配置结果: {json.dumps(config_result, indent=2)}")
        
        # 4. 获取支持的操作
        print(f"\n4. 获取支持的操作...")
        actions_result = await driver.get_actions(BUILDING_ID, GROUP_ID)
        print(f"操作结果: {json.dumps(actions_result, indent=2)}")
        
        # 5. 监控电梯状态
        print(f"\n5. 监控电梯状态...")
        mode_result = await driver.get_mode(BUILDING_ID, GROUP_ID)
        print(f"状态监控: {json.dumps(mode_result, indent=2)}")
        
        # 6. 电梯呼叫测试（多个场景）
        print(f"\n6. 电梯呼叫测试...")
        
        test_scenarios = [
            {
                "name": "1层到10层",
                "from_floor": 1,
                "to_floor": 10,
                "from_area": FLOOR_TO_AREA[1],
                "to_area": FLOOR_TO_AREA[10]
            },
            {
                "name": "地下1层到5层", 
                "from_floor": -1,
                "to_floor": 5,
                "from_area": FLOOR_TO_AREA[-1],
                "to_area": FLOOR_TO_AREA[5]
            },
            {
                "name": "20层到30层",
                "from_floor": 20,
                "to_floor": 30,
                "from_area": FLOOR_TO_AREA[20],
                "to_area": FLOOR_TO_AREA[30]
            }
        ]
        
        successful_calls = 0
        call_ids = []
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n  测试场景 {i}: {scenario['name']}")
            
            try:
                # 创建电梯呼叫请求
                call_request = ElevatorCallRequest(
                    building_id=BUILDING_ID,
                    group_id=GROUP_ID,
                    from_floor=scenario['from_floor'],
                    to_floor=scenario['to_floor'],
                    user_id=f"test-user-{i}",
                    source=scenario['from_area'],
                    destination=scenario['to_area'],
                    action_id=2,  # 标准目的地呼叫
                    terminal=1
                )
                
                call_result = await driver.call(call_request)
                print(f"    呼叫结果: {json.dumps(call_result, indent=6)}")
                
                if call_result.get('success'):
                    successful_calls += 1
                    if call_result.get('request_id'):
                        call_ids.append(call_result['request_id'])
                    print(f"    ✅ 场景 {i} 呼叫成功")
                else:
                    print(f"    ❌ 场景 {i} 呼叫失败")
                    
            except Exception as e:
                print(f"    ❌ 场景 {i} 异常: {e}")
        
        # 7. 测试取消呼叫
        if call_ids:
            print(f"\n7. 测试取消呼叫...")
            for call_id in call_ids[:2]:  # 只取消前两个
                try:
                    cancel_result = await driver.cancel(BUILDING_ID, call_id)
                    print(f"    取消 {call_id}: {json.dumps(cancel_result, indent=6)}")
                except Exception as e:
                    print(f"    取消 {call_id} 异常: {e}")
        
        # 8. 测试结果总结
        print(f"\n8. 测试总结")
        print("=" * 60)
        print(f"✅ 成功呼叫: {successful_calls}/{len(test_scenarios)}")
        print(f"✅ 建筑访问: {'可用' if ping_result.get('success') else '不可用'}")
        print(f"✅ 配置获取: {'成功' if config_result.get('success') else '失败'}")
        print(f"✅ 状态监控: {'成功' if mode_result.get('success') else '失败'}")
        
        return successful_calls > 0
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await driver.close()
        print(f"\n🔌 连接已关闭")

async def test_lift_specific_calls():
    """测试指定电梯呼叫"""
    
    print(f"\n" + "=" * 60)
    print("指定电梯呼叫测试")
    print("=" * 60)
    
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
    
    try:
        await driver.initialize()
        
        # 测试指定电梯A和电梯H
        for lift_name, lift_id in [("A", LIFT_IDS["A"]), ("H", LIFT_IDS["H"])]:
            print(f"\n测试指定电梯 {lift_name} (ID: {lift_id})")
            
            call_request = ElevatorCallRequest(
                building_id=BUILDING_ID,
                group_id=GROUP_ID,
                from_floor=1,
                to_floor=25,
                user_id=f"test-lift-{lift_name}",
                source=FLOOR_TO_AREA[1],
                destination=FLOOR_TO_AREA[25],
                action_id=2,
                terminal=1,
                allowed_lifts=[lift_id]
            )
            
            result = await driver.call(call_request)
            print(f"  结果: {json.dumps(result, indent=4)}")
            
    except Exception as e:
        print(f"❌ 指定电梯测试失败: {e}")
    finally:
        await driver.close()

if __name__ == "__main__":
    print("🚀 开始TwilityPlaza虚拟建筑完整测试...")
    
    # 运行完整测试
    result = asyncio.run(test_twilityplaza_complete())
    
    # 运行指定电梯测试
    asyncio.run(test_lift_specific_calls())
    
    print(f"\n🏁 TwilityPlaza测试完成!")
    print(f"测试结果: {'✅ 成功' if result else '❌ 失败'}")
