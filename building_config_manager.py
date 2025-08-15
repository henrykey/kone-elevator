#!/usr/bin/env python3
"""
建筑配置解析与校验管理器
Author: IBC-AI CO.

负责解析、验证和缓存建筑配置与动作配置
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class AreaInfo:
    """区域信息"""
    area_id: int
    floor_number: int
    area_type: str  # floor, lift_deck, etc.
    name: Optional[str] = None
    description: Optional[str] = None


@dataclass
class LiftInfo:
    """电梯信息"""
    lift_id: int
    name: Optional[str] = None
    deck_areas: List[int] = None  # 对应的 deck area IDs
    served_floors: List[int] = None  # 服务的楼层


@dataclass
class ActionInfo:
    """动作信息"""
    action_id: int
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = None


class BuildingConfigManager:
    """建筑配置管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.building_config: Optional[Dict[str, Any]] = None
        self.actions_config: Optional[Dict[str, Any]] = None
        self._area_mapping: Dict[int, AreaInfo] = {}
        self._floor_to_area: Dict[int, int] = {}
        self._lifts: Dict[int, LiftInfo] = {}
        self._actions: Dict[int, ActionInfo] = {}
    
    def load_building_config(self, config_response: Dict[str, Any]) -> bool:
        """
        加载建筑配置
        
        Args:
            config_response: 建筑配置响应数据
            
        Returns:
            bool: 是否加载成功
        """
        try:
            self.building_config = config_response
            self._parse_building_config()
            self.logger.info(f"Building config loaded successfully. Areas: {len(self._area_mapping)}, Lifts: {len(self._lifts)}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load building config: {e}")
            return False
    
    def load_actions_config(self, actions_response: Dict[str, Any]) -> bool:
        """
        加载动作配置
        
        Args:
            actions_response: 动作配置响应数据
            
        Returns:
            bool: 是否加载成功
        """
        try:
            self.actions_config = actions_response
            self._parse_actions_config()
            self.logger.info(f"Actions config loaded successfully. Actions: {len(self._actions)}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load actions config: {e}")
            return False
    
    def _parse_building_config(self) -> None:
        """解析建筑配置"""
        if not self.building_config:
            return
        
        try:
            payload = self.building_config.get("payload", {})
            
            # 解析区域信息
            areas = payload.get("areas", [])
            for area_data in areas:
                area_info = AreaInfo(
                    area_id=area_data.get("id"),
                    floor_number=area_data.get("floor", 0),
                    area_type=area_data.get("type", "unknown"),
                    name=area_data.get("name"),
                    description=area_data.get("description")
                )
                
                if area_info.area_id:
                    self._area_mapping[area_info.area_id] = area_info
                    
                    # 建立楼层到区域的映射 (只对 floor 类型的区域)
                    if area_info.area_type == "floor" and area_info.floor_number is not None:
                        self._floor_to_area[area_info.floor_number] = area_info.area_id
            
            # 解析电梯信息
            lifts = payload.get("lifts", [])
            for lift_data in lifts:
                deck_areas = []
                served_floors = []
                
                # 解析 deck areas
                if "deck_areas" in lift_data:
                    deck_areas = lift_data["deck_areas"]
                
                # 解析服务楼层
                if "served_floors" in lift_data:
                    served_floors = lift_data["served_floors"]
                
                lift_info = LiftInfo(
                    lift_id=lift_data.get("id"),
                    name=lift_data.get("name"),
                    deck_areas=deck_areas,
                    served_floors=served_floors
                )
                
                if lift_info.lift_id:
                    self._lifts[lift_info.lift_id] = lift_info
                    
        except Exception as e:
            self.logger.error(f"Error parsing building config: {e}")
            # TODO: 根据实际配置结构调整解析逻辑
            self._build_fallback_mapping()
    
    def _parse_actions_config(self) -> None:
        """解析动作配置"""
        if not self.actions_config:
            return
        
        try:
            payload = self.actions_config.get("data", {})
            
            # 检查是否包含 actions 或 supportedActions 字段
            actions = payload.get("actions", payload.get("supportedActions", []))
            
            if actions:
                for action_data in actions:
                    action_info = ActionInfo(
                        action_id=action_data.get("id"),
                        name=action_data.get("name", ""),
                        description=action_data.get("description"),
                        parameters=action_data.get("parameters", {})
                    )
                    
                    if action_info.action_id:
                        self._actions[action_info.action_id] = action_info
            else:
                # 如果没有 actions 字段，但有其他配置数据（如 destinations），
                # 说明 API 返回的是不同类型的配置，使用后备配置
                if "destinations" in payload or "version_major" in payload:
                    self.logger.info("Received building topology data instead of actions config, using fallback actions")
                    self._build_fallback_actions()
                    
        except Exception as e:
            self.logger.error(f"Error parsing actions config: {e}")
            # 提供默认动作配置
            self._build_fallback_actions()
    
    def _build_fallback_mapping(self) -> None:
        """
        构建后备映射 (当配置解析失败时使用)
        
        基于常见的电梯配置模式创建默认映射
        """
        self.logger.warning("Using fallback area mapping")
        
        # 创建默认的楼层到区域映射
        # TODO: 根据 KONE 实际规范调整
        for floor in range(-2, 21):  # -2 到 20 楼
            area_id = 1000 + floor * 1000 if floor >= 0 else 1000 + floor * 1000
            
            area_info = AreaInfo(
                area_id=area_id,
                floor_number=floor,
                area_type="floor",
                name=f"Floor {floor}",
                description=f"Fallback mapping for floor {floor}"
            )
            
            self._area_mapping[area_id] = area_info
            self._floor_to_area[floor] = area_id
    
    def _build_fallback_actions(self) -> None:
        """构建后备动作配置"""
        self.logger.warning("Using fallback actions config")
        
        # 根据常见的 KONE 动作 ID 创建默认配置
        default_actions = [
            {"id": 2, "name": "destination_call", "description": "Destination call"},
            {"id": 200, "name": "landing_call_up", "description": "Landing call up"},
            {"id": 2002, "name": "landing_call", "description": "Landing call"},
            {"id": 4, "name": "disabled_call", "description": "Disabled call"}
        ]
        
        for action_data in default_actions:
            action_info = ActionInfo(
                action_id=action_data["id"],
                name=action_data["name"],
                description=action_data["description"],
                parameters={}
            )
            self._actions[action_info.action_id] = action_info
    
    def get_area_id_by_floor(self, floor_number: int) -> Optional[int]:
        """
        根据楼层号获取区域ID
        
        Args:
            floor_number: 楼层号
            
        Returns:
            Optional[int]: 区域ID，如果找不到返回 None
        """
        return self._floor_to_area.get(floor_number)
    
    def get_area_info(self, area_id: int) -> Optional[AreaInfo]:
        """
        获取区域信息
        
        Args:
            area_id: 区域ID
            
        Returns:
            Optional[AreaInfo]: 区域信息，如果找不到返回 None
        """
        return self._area_mapping.get(area_id)
    
    def get_floor_by_area_id(self, area_id: int) -> Optional[int]:
        """
        根据区域ID获取楼层号
        
        Args:
            area_id: 区域ID
            
        Returns:
            Optional[int]: 楼层号，如果找不到返回 None
        """
        area_info = self._area_mapping.get(area_id)
        return area_info.floor_number if area_info else None
    
    def get_all_floor_areas(self) -> List[Tuple[int, int]]:
        """
        获取所有楼层区域映射
        
        Returns:
            List[Tuple[int, int]]: (floor_number, area_id) 列表
        """
        return [(floor, area_id) for floor, area_id in self._floor_to_area.items()]
    
    def get_lift_info(self, lift_id: int) -> Optional[LiftInfo]:
        """
        获取电梯信息
        
        Args:
            lift_id: 电梯ID
            
        Returns:
            Optional[LiftInfo]: 电梯信息
        """
        return self._lifts.get(lift_id)
    
    def get_all_lifts(self) -> List[LiftInfo]:
        """
        获取所有电梯信息
        
        Returns:
            List[LiftInfo]: 电梯信息列表
        """
        return list(self._lifts.values())
    
    def get_action_info(self, action_id: int) -> Optional[ActionInfo]:
        """
        获取动作信息
        
        Args:
            action_id: 动作ID
            
        Returns:
            Optional[ActionInfo]: 动作信息
        """
        return self._actions.get(action_id)
    
    def get_all_actions(self) -> List[ActionInfo]:
        """
        获取所有动作信息
        
        Returns:
            List[ActionInfo]: 动作信息列表
        """
        return list(self._actions.values())
    
    def validate_call_parameters(self, from_floor: int, to_floor: int, action_id: int) -> Tuple[bool, str]:
        """
        验证呼叫参数
        
        Args:
            from_floor: 起始楼层
            to_floor: 目标楼层  
            action_id: 动作ID
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        # 验证楼层是否存在
        from_area_id = self.get_area_id_by_floor(from_floor)
        if from_area_id is None:
            return False, f"Invalid from_floor: {from_floor} not found in building config"
        
        if to_floor is not None:
            to_area_id = self.get_area_id_by_floor(to_floor)
            if to_area_id is None:
                return False, f"Invalid to_floor: {to_floor} not found in building config"
            
            # 检查是否为同一楼层
            if from_floor == to_floor:
                return False, f"Source and destination floors cannot be the same: {from_floor}"
        
        # 验证动作ID
        action_info = self.get_action_info(action_id)
        if action_info is None:
            return False, f"Invalid action_id: {action_id} not found in actions config"
        
        return True, ""
    
    def get_monitoring_topics(self, building_id: str, group_id: str) -> List[str]:
        """
        获取可用的监控主题
        
        Args:
            building_id: 建筑ID
            group_id: 组ID
            
        Returns:
            List[str]: 监控主题列表
        """
        # TODO: 根据实际配置动态生成，或从配置中读取
        # 这里提供常见的监控主题
        base_topics = [
            f"lift_1/status",
            f"lift_1/position", 
            f"lift_1/direction",
            f"lift_1/load",
            f"group_{group_id}/status",
            f"calls/{building_id}/state"
        ]
        
        # 为所有电梯生成主题
        topics = []
        for lift_info in self.get_all_lifts():
            topics.extend([
                f"lift_{lift_info.lift_id}/status",
                f"lift_{lift_info.lift_id}/position",
                f"lift_{lift_info.lift_id}/direction",
                f"lift_{lift_info.lift_id}/load"
            ])
        
        # 如果没有电梯配置，使用默认主题
        if not topics:
            topics = base_topics
        
        return topics
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取配置摘要
        
        Returns:
            Dict[str, Any]: 配置摘要信息
        """
        return {
            "building_config_loaded": self.building_config is not None,
            "actions_config_loaded": self.actions_config is not None,
            "total_areas": len(self._area_mapping),
            "total_floor_areas": len(self._floor_to_area),
            "total_lifts": len(self._lifts),
            "total_actions": len(self._actions),
            "floor_range": {
                "min": min(self._floor_to_area.keys()) if self._floor_to_area else None,
                "max": max(self._floor_to_area.keys()) if self._floor_to_area else None
            },
            "available_actions": [action.action_id for action in self._actions.values()],
            "lift_ids": [lift.lift_id for lift in self._lifts.values()]
        }
