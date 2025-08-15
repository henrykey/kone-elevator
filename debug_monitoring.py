#!/usr/bin/env python3
"""
调试监控订阅问题
"""
import asyncio
import logging
import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kone_api_client import CommonAPIClient, MonitoringAPIClient
from building_config_manager import BuildingConfigManager

async def debug_monitoring():
    """调试监控订阅"""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)
    
    building_id = "building:4TFxWRCv23D"
    group_id = "1"
    
    try:
        # 导入驱动程序
        from drivers import KoneDriver
        import yaml
        
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
        
        # 初始化连接
        init_result = await driver.initialize()
        if not init_result['success']:
            logger.error(f"初始化失败: {init_result}")
            return
        
        logger.info("WebSocket 连接已建立")
        
        # 创建监控客户端
        monitoring_client = MonitoringAPIClient(driver)
        
        logger.info("=== 测试不同的监控主题 ===")
        
        # 测试1: 单个电梯状态 (成功的)
        logger.info("测试1: lift_1/status")
        response1 = await monitoring_client.subscribe_monitoring(
            building_id=building_id,
            group_id=group_id,
            subtopics=["lift_1/status"],
            duration_sec=10,
            client_tag="debug_test_1"
        )
        logger.info(f"测试1结果: success={response1.success}, status={response1.status_code}, error={response1.error}")
        if response1.data:
            logger.info(f"测试1响应数据: {response1.data}")
        
        # 等待一下再进行下一个测试
        await asyncio.sleep(2)
        
        # 测试2: 多个电梯状态 (失败的)
        logger.info("测试2: lift_1/status, lift_2/status")
        response2 = await monitoring_client.subscribe_monitoring(
            building_id=building_id,
            group_id=group_id,
            subtopics=["lift_1/status", "lift_2/status"],
            duration_sec=10,
            client_tag="debug_test_2"
        )
        logger.info(f"测试2结果: success={response2.success}, status={response2.status_code}")
        
        # 测试3: 尝试不同的主题格式
        logger.info("测试3: call_state/+/+")
        response3 = await monitoring_client.subscribe_monitoring(
            building_id=building_id,
            group_id=group_id,
            subtopics=["call_state/+/+"],
            duration_sec=10,
            client_tag="debug_test_3"
        )
        logger.info(f"测试3结果: success={response3.success}, status={response3.status_code}")
        
        # 测试4: 尝试单个电梯多属性
        logger.info("测试4: lift_1/position")
        response4 = await monitoring_client.subscribe_monitoring(
            building_id=building_id,
            group_id=group_id,
            subtopics=["lift_1/position"],
            duration_sec=10,
            client_tag="debug_test_4"
        )
        logger.info(f"测试4结果: success={response4.success}, status={response4.status_code}")
        
        # 关闭连接
        if driver.websocket:
            await driver.websocket.close()
        
    except Exception as e:
        logger.error(f"调试测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_monitoring())
