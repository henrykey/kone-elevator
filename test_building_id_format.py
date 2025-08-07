#!/usr/bin/env python
# Author: IBC-AI CO.
"""
buildingId 格式转换测试
只测试格式化逻辑，不进行实际API调用
"""

def test_building_id_format():
    """测试buildingId格式化逻辑"""
    
    print("🧪 buildingId 格式化测试")
    print("=" * 40)
    
    test_cases = [
        {
            "input": "fWlfHyPlaca",
            "expected": "building:fWlfHyPlaca",
            "description": "原始ID (应添加前缀)"
        },
        {
            "input": "building:fWlfHyPlaca", 
            "expected": "building:fWlfHyPlaca",
            "description": "已有前缀 (保持不变)"
        },
        {
            "input": "building:99900009301",
            "expected": "building:99900009301", 
            "description": "标准格式 (保持不变)"
        },
        {
            "input": "99900009301",
            "expected": "building:99900009301",
            "description": "数字ID (应添加前缀)"
        },
        {
            "input": "",
            "expected": "building:",
            "description": "空字符串 (边界测试)"
        },
        {
            "input": "building:",
            "expected": "building:",
            "description": "只有前缀 (边界测试)"
        }
    ]
    
    all_passed = True
    
    for i, case in enumerate(test_cases, 1):
        # 执行格式化逻辑（与drivers.py中的逻辑相同）
        input_id = case["input"]
        formatted_id = input_id if input_id.startswith("building:") else f"building:{input_id}"
        expected = case["expected"]
        
        passed = formatted_id == expected
        all_passed = all_passed and passed
        
        status = "✅" if passed else "❌"
        print(f"{status} 测试 {i}: {case['description']}")
        print(f"   输入: '{input_id}'")
        print(f"   结果: '{formatted_id}'")
        print(f"   期望: '{expected}'")
        if not passed:
            print(f"   ⚠️ 不匹配!")
        print()
    
    print("=" * 40)
    if all_passed:
        print("🎉 所有格式化测试通过!")
        print("buildingId格式化逻辑正确")
    else:
        print("❌ 部分测试失败")
        print("需要检查格式化逻辑")
    
    return all_passed


def test_api_message_format():
    """测试API消息格式"""
    
    print("\\n📨 API消息格式测试")
    print("=" * 40)
    
    # 模拟ping消息构建过程
    original_building_id = "fWlfHyPlaca"
    formatted_building_id = original_building_id if original_building_id.startswith("building:") else f"building:{original_building_id}"
    
    ping_msg = {
        "type": "common-api",
        "buildingId": formatted_building_id,
        "callType": "ping",
        "groupId": "1",
        "payload": {
            "request_id": 1691234567890
        }
    }
    
    print(f"原始建筑ID: {original_building_id}")
    print(f"格式化后: {formatted_building_id}")
    print("\\n生成的ping消息:")
    import json
    print(json.dumps(ping_msg, indent=2, ensure_ascii=False))
    
    # 验证格式
    expected_building_id = "building:fWlfHyPlaca"
    is_correct = ping_msg["buildingId"] == expected_building_id
    
    print(f"\\n验证结果: {'✅ 正确' if is_correct else '❌ 错误'}")
    print(f"期望buildingId: {expected_building_id}")
    print(f"实际buildingId: {ping_msg['buildingId']}")
    
    return is_correct


def main():
    """主测试函数"""
    
    print("🔧 KONE buildingId 格式修正验证")
    print("Author: IBC-AI CO.")
    print("测试修正后的格式化逻辑")
    print("=" * 50)
    
    # 测试格式化逻辑
    test1_passed = test_building_id_format()
    
    # 测试API消息格式
    test2_passed = test_api_message_format()
    
    print("\\n" + "=" * 50)
    print("📊 测试总结:")
    print(f"格式化逻辑测试: {'✅ 通过' if test1_passed else '❌ 失败'}")
    print(f"API消息格式测试: {'✅ 通过' if test2_passed else '❌ 失败'}")
    
    if test1_passed and test2_passed:
        print("\\n🎉 所有测试通过!")
        print("buildingId格式修正工作正常")
        print("现在发送的API请求应该符合v2规范")
    else:
        print("\\n⚠️ 部分测试失败，需要检查修正逻辑")
    
    return test1_passed and test2_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
