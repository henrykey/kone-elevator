# Author: IBC-AI CO.
"""
虚拟建筑数据管理器
负责从配置文件中读取建筑数据，提供楼层映射和随机数据生成功能
"""

import yaml
import random
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class BuildingDataManager:
    """
    虚拟建筑数据管理器
    负责管理建筑配置、楼层映射、电梯组信息等
    """
    
    def __init__(self, config_path: str = "virtual_building_config.yml"):
        """
        初始化建筑数据管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.building_config = None
        self.floor_mappings = {}
        self.area_id_mappings = {}
        self.available_floors = []
        self.elevator_groups = {}
        
        # 加载配置
        self.load_config()
        self._process_floor_mappings()
        
        logger.info(f"BuildingDataManager initialized with {len(self.available_floors)} available floors")
    
    def load_config(self) -> bool:
        """
        加载建筑配置文件
        
        Returns:
            bool: 加载成功返回True，失败返回False
        """
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.error(f"Building config file not found: {self.config_path}")
                return False
            
            with open(config_file, 'r', encoding='utf-8') as f:
                self.building_config = yaml.safe_load(f)
            
            logger.info(f"Successfully loaded building config: {self.get_building_id()}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load building config: {e}")
            return False
    
    def _process_floor_mappings(self):
        """
        处理楼层映射数据，建立楼层ID到area_id的映射关系
        """
        if not self.building_config or 'floors' not in self.building_config:
            logger.warning("No floor data found in building config")
            return
        
        floors_data = self.building_config['floors']
        
        for floor_name, floor_info in floors_data.items():
            if isinstance(floor_info, dict) and 'level' in floor_info:
                floor_level = floor_info['level']
                
                # 楼层ID转area_id的基本规则：楼层 * 1000
                base_area_id = floor_level * 1000
                
                # 存储楼层映射
                self.floor_mappings[floor_name] = {
                    'level': floor_level,
                    'base_area_id': base_area_id,
                    'lifts': floor_info.get('lifts', {})
                }
                
                # 如果有具体的电梯区域ID，使用实际值
                if 'lifts' in floor_info:
                    for lift_name, lift_areas in floor_info['lifts'].items():
                        if isinstance(lift_areas, dict):
                            front_id = lift_areas.get('front')
                            rear_id = lift_areas.get('rear')
                            
                            if front_id:
                                area_key = f"{floor_name}_{lift_name}_front"
                                self.area_id_mappings[area_key] = front_id
                                
                                # 添加到可用楼层列表
                                if front_id not in self.available_floors:
                                    self.available_floors.append(front_id)
                            
                            if rear_id:
                                area_key = f"{floor_name}_{lift_name}_rear"
                                self.area_id_mappings[area_key] = rear_id
                                
                                if rear_id not in self.available_floors:
                                    self.available_floors.append(rear_id)
                
                # 如果没有具体的电梯ID，使用基础area_id
                if not self.area_id_mappings:
                    self.available_floors.append(base_area_id)
        
        # 排序可用楼层
        self.available_floors.sort()
        
        # 处理电梯组信息
        if 'elevator_groups' in self.building_config:
            self.elevator_groups = self.building_config['elevator_groups']
        
        logger.info(f"Processed {len(self.floor_mappings)} floors, {len(self.available_floors)} area IDs available")
    
    def get_building_id(self) -> str:
        """
        获取建筑ID
        
        Returns:
            str: 建筑ID
        """
        if self.building_config and 'building' in self.building_config:
            return self.building_config['building'].get('id', 'Unknown')
        return 'Unknown'
    
    def floor_to_area_id(self, floor_level: int) -> int:
        """
        楼层ID转area_id
        
        Args:
            floor_level: 楼层编号
            
        Returns:
            int: 对应的area_id (楼层 * 1000)
        """
        return floor_level * 1000
    
    def area_id_to_floor(self, area_id: int) -> int:
        """
        area_id转楼层ID
        
        Args:
            area_id: 区域ID
            
        Returns:
            int: 楼层编号
        """
        return area_id // 1000
    
    def get_random_floor_pair(self) -> Tuple[int, int]:
        """
        获取随机起止楼层对（起止不同）
        
        Returns:
            tuple: (source_area_id, dest_area_id)
        """
        if len(self.available_floors) < 2:
            # 如果可用楼层少于2个，使用默认值
            logger.warning("Insufficient floors available, using default values")
            return (1000, 2000)
        
        # 随机选择两个不同的楼层
        source = random.choice(self.available_floors)
        dest = random.choice([f for f in self.available_floors if f != source])
        
        logger.debug(f"Generated random floor pair: {source} -> {dest}")
        return (source, dest)
    
    def get_random_floor_sequence(self, count: int = 3) -> List[int]:
        """
        获取随机楼层序列
        
        Args:
            count: 楼层数量
            
        Returns:
            list: 楼层area_id列表
        """
        if len(self.available_floors) < count:
            # 如果楼层不够，重复使用
            sequence = random.choices(self.available_floors, k=count)
        else:
            sequence = random.sample(self.available_floors, count)
        
        return sequence
    
    def get_valid_floors(self) -> List[int]:
        """
        获取所有有效的楼层area_id
        
        Returns:
            list: 有效楼层列表
        """
        return self.available_floors.copy()
    
    def get_invalid_floor_id(self) -> int:
        """
        获取一个无效的楼层ID（用于错误测试）
        
        Returns:
            int: 无效的area_id
        """
        if not self.available_floors:
            return 9999
        
        # 找一个不在有效范围内的ID
        max_floor = max(self.available_floors)
        return max_floor + 1000
    
    def get_elevator_groups(self) -> Dict[str, Any]:
        """
        获取电梯组配置
        
        Returns:
            dict: 电梯组信息
        """
        return self.elevator_groups.copy()
    
    def get_lifts_in_group(self, group_id: str = "group_1") -> List[str]:
        """
        获取指定组中的电梯列表
        
        Args:
            group_id: 电梯组ID
            
        Returns:
            list: 电梯ID列表
        """
        if group_id in self.elevator_groups:
            lifts = self.elevator_groups[group_id].get('lifts', [])
            return [lift.get('id', '') for lift in lifts if 'id' in lift]
        return []
    
    def get_floor_for_lift(self, floor_name: str, lift_name: str, side: str = "front") -> Optional[int]:
        """
        获取特定电梯在特定楼层的area_id
        
        Args:
            floor_name: 楼层名称
            lift_name: 电梯名称
            side: 侧面（front/rear）
            
        Returns:
            int: area_id，如果不存在返回None
        """
        if floor_name not in self.floor_mappings:
            return None
        
        floor_info = self.floor_mappings[floor_name]
        lifts = floor_info.get('lifts', {})
        
        if lift_name in lifts:
            lift_areas = lifts[lift_name]
            return lift_areas.get(side)
        
        return None
    
    def get_building_summary(self) -> Dict[str, Any]:
        """
        获取建筑概要信息
        
        Returns:
            dict: 建筑概要
        """
        return {
            "building_id": self.get_building_id(),
            "total_floors": len(self.floor_mappings),
            "total_area_ids": len(self.available_floors),
            "elevator_groups": len(self.elevator_groups),
            "floor_range": {
                "min_area_id": min(self.available_floors) if self.available_floors else None,
                "max_area_id": max(self.available_floors) if self.available_floors else None
            },
            "available_floors": self.available_floors[:10]  # 只显示前10个
        }
    
    def validate_area_id(self, area_id: int) -> bool:
        """
        验证area_id是否有效
        
        Args:
            area_id: 要验证的area_id
            
        Returns:
            bool: 有效返回True，无效返回False
        """
        return area_id in self.available_floors
    
    def get_test_data_set(self) -> Dict[str, Any]:
        """
        获取测试数据集（用于自动化测试）
        
        Returns:
            dict: 测试数据集
        """
        test_data = {
            "building_id": self.get_building_id(),
            "valid_floors": self.get_valid_floors()[:5],  # 前5个有效楼层
            "invalid_floor": self.get_invalid_floor_id(),
            "random_pairs": [self.get_random_floor_pair() for _ in range(3)],
            "floor_sequence": self.get_random_floor_sequence(4),
            "elevator_groups": list(self.elevator_groups.keys()),
            "sample_lifts": self.get_lifts_in_group()[:3]  # 前3个电梯
        }
        
        return test_data
