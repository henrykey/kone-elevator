# Author: IBC-AI CO.
"""
测试协调器验证脚本
用于验证KoneValidationTestCoordinator的基础功能
"""

import asyncio
import sys
from test_coordinator import KoneValidationTestCoordinator


async def test_coordinator_basic():
    """测试协调器基础功能"""
    print("🚀 Starting KONE Validation Test Coordinator verification...")
    
    async with KoneValidationTestCoordinator() as coordinator:
        # 运行完整验证流程
        result = await coordinator.run_full_validation()
        
        print("\n📊 Test Coordination Results:")
        print(f"Overall Status: {result['summary'].get('overall_status')}")
        print(f"Completed Phases: {result['summary'].get('completed_phases', 0)}/3")
        
        if result['summary'].get('overall_status') == 'PARTIALLY_COMPLETED':
            print(f"✅ Phase 1 completed successfully")
            print(f"📋 Next Step: {result['summary'].get('next_step')}")
        
        return result


if __name__ == "__main__":
    result = asyncio.run(test_coordinator_basic())
    
    if result['summary'].get('overall_status') in ['COMPLETED', 'PARTIALLY_COMPLETED']:
        print("\n✅ Test Coordinator verification successful!")
        sys.exit(0)
    else:
        print(f"\n❌ Test Coordinator verification failed: {result['summary'].get('error')}")
        sys.exit(1)
