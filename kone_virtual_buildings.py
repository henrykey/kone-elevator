"""
KONE虚拟建筑测试配置管理器
基于KONE提供的最新虚拟建筑测试指引
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import yaml

@dataclass
class VirtualBuilding:
    """虚拟建筑配置"""
    building_id: str
    name: str
    purpose: str
    description: str
    group_ids: List[str] = None
    area_ids: List[int] = None
    terminal_ids: List[int] = None
    media_configs: List[Dict] = None
    special_features: List[str] = None

@dataclass
class MediaConfig:
    """门禁媒体配置"""
    media_id: str
    media_cc: str = None
    media_type: str = "RFID"
    floors: List[int] = None

class KoneVirtualBuildingManager:
    """KONE虚拟建筑配置管理器"""
    
    def __init__(self):
        self.buildings = self._load_kone_virtual_buildings()
    
    def _load_kone_virtual_buildings(self) -> Dict[str, VirtualBuilding]:
        """加载KONE提供的虚拟建筑配置"""
        
        buildings = {}
        
        # 1. 动作调用禁用测试
        buildings["disabled_actions"] = VirtualBuilding(
            building_id="ye4KrX2cei",
            name="动作调用禁用测试建筑",
            purpose="测试禁用的动作调用 (Disabled Action Calls)",
            description="用于调用Action 4（false），测试禁用动作的处理",
            group_ids=["1"],
            special_features=["disabled_action_4"]
        )
        
        # 2. 直通型轿厢呼叫测试
        buildings["through_car_calls"] = VirtualBuilding(
            building_id="yEJ4j9Xetj", 
            name="直通型轿厢呼叫测试建筑",
            purpose="测试直通型轿厢呼叫 (Through-Type Car Calls)",
            description="用于呼叫1200-12010，测试直通型轿厢呼叫功能",
            group_ids=["1"],
            area_ids=list(range(1200, 12011)),
            special_features=["through_car_calls"]
        )
        
        # 3. 转运呼叫测试
        buildings["transfer_calls"] = VirtualBuilding(
            building_id="ig8zimMyQf",
            name="转运呼叫测试建筑", 
            purpose="测试转运呼叫 (Transfer Calls)",
            description="用于呼叫10000-40000，测试转运呼叫功能",
            group_ids=["1"],
            area_ids=list(range(10000, 40001)),
            special_features=["transfer_calls"]
        )
        
        # 4. 门禁测试 (Access Control)
        buildings["access_control"] = VirtualBuilding(
            building_id="joykVHPoOW7",
            name="门禁测试建筑",
            purpose="测试门禁控制 (Access Control)",
            description="用于测试RFID门禁系统，支持多种Media配置",
            group_ids=["1"],
            area_ids=list(range(40000, 41001)),
            media_configs=[
                {
                    "media_id": "0009",
                    "media_cc": "2b", 
                    "media_type": "RFID",
                    "floors": list(range(40000, 41001))
                },
                {
                    "media_id": "0007",
                    "media_type": "RFID",
                    "floors": list(range(40000, 41001))
                }
            ],
            special_features=["access_control", "rfid_media"]
        )
        
        # 5. 多群组测试 (Multi-Group)
        buildings["multi_group"] = VirtualBuilding(
            building_id="BPa9jEEo3lр",
            name="多群组测试建筑",
            purpose="测试多群组配置 (Multi-Group)",
            description="支持多个群组和终端的复杂配置测试",
            group_ids=["1", "2"],
            terminal_ids=[10011, 11013],
            area_ids=[53000, 54000, 55000, 56000, 17020, 18020, 19020],
            special_features=["multi_group", "multiple_terminals"]
        )
        
        return buildings
    
    def get_building(self, test_type: str) -> Optional[VirtualBuilding]:
        """根据测试类型获取对应的虚拟建筑"""
        return self.buildings.get(test_type)
    
    def get_building_by_id(self, building_id: str) -> Optional[VirtualBuilding]:
        """根据建筑ID获取虚拟建筑"""
        for building in self.buildings.values():
            if building.building_id == building_id:
                return building
        return None
    
    def list_available_buildings(self) -> List[Dict]:
        """列出所有可用的虚拟建筑"""
        result = []
        for key, building in self.buildings.items():
            result.append({
                "key": key,
                "building_id": building.building_id,
                "name": building.name,
                "purpose": building.purpose,
                "features": building.special_features or []
            })
        return result
    
    def get_test_mapping(self) -> Dict[str, str]:
        """获取测试用例到虚拟建筑的映射"""
        return {
            # 基础功能测试 - 使用多群组建筑 (最全面)
            "test_1_initialization": "multi_group",
            "test_2_mode_non_operational": "multi_group", 
            "test_3_mode_operational": "multi_group",
            
            # 呼叫功能测试
            "test_4_basic_call": "multi_group",
            "test_5_hold_open": "multi_group",
            "test_6_unknown_action": "disabled_actions",  # 测试禁用动作
            "test_7_delete_call": "multi_group",
            
            # 转运和直通呼叫测试
            "test_8_transfer_calls": "transfer_calls",
            "test_9_through_car_calls": "through_car_calls",
            
            # 门禁测试
            "test_10_access_control": "access_control",
            "test_11_rfid_media": "access_control",
            
            # 多群组和高级功能测试
            "test_12_multi_group": "multi_group",
            "test_13_terminal_switching": "multi_group",
            
            # 其他测试默认使用多群组建筑
            "default": "multi_group"
        }
    
    def get_building_for_test(self, test_name: str) -> VirtualBuilding:
        """根据测试名称获取推荐的虚拟建筑"""
        mapping = self.get_test_mapping()
        building_key = mapping.get(test_name, mapping["default"])
        return self.buildings[building_key]
    
    def generate_config_summary(self) -> str:
        """生成配置摘要报告"""
        summary = []
        summary.append("# KONE虚拟建筑测试配置摘要\n")
        summary.append("基于KONE提供的最新虚拟建筑测试指引\n")
        
        for key, building in self.buildings.items():
            summary.append(f"## {building.name}")
            summary.append(f"- **Building ID**: {building.building_id}")
            summary.append(f"- **用途**: {building.purpose}")
            summary.append(f"- **描述**: {building.description}")
            
            if building.group_ids:
                summary.append(f"- **Group IDs**: {', '.join(building.group_ids)}")
            
            if building.area_ids:
                area_range = f"{min(building.area_ids)}-{max(building.area_ids)}"
                summary.append(f"- **Area IDs**: {area_range} ({len(building.area_ids)}个)")
            
            if building.terminal_ids:
                summary.append(f"- **Terminal IDs**: {', '.join(map(str, building.terminal_ids))}")
            
            if building.media_configs:
                summary.append("- **Media配置**:")
                for media in building.media_configs:
                    summary.append(f"  - ID: {media['media_id']}, Type: {media['media_type']}")
            
            if building.special_features:
                summary.append(f"- **特殊功能**: {', '.join(building.special_features)}")
            
            summary.append("")
        
        # 添加测试映射信息
        summary.append("## 测试用例映射")
        mapping = self.get_test_mapping()
        for test_name, building_key in mapping.items():
            if test_name != "default":
                building = self.buildings[building_key]
                summary.append(f"- **{test_name}**: {building.name} ({building.building_id})")
        
        summary.append(f"\n**默认建筑**: {self.buildings[mapping['default']].name}")
        
        # 添加排除信息
        summary.append("\n## 注意事项")
        summary.append("- **排除测试章节**: 6.7 与 6.8 暂时排除")
        summary.append("- **后续支持**: 将由KONE专家支持后续处理")
        
        return "\n".join(summary)

# 全局实例
KONE_VIRTUAL_BUILDINGS = KoneVirtualBuildingManager()

if __name__ == "__main__":
    # 生成配置摘要
    manager = KoneVirtualBuildingManager()
    print(manager.generate_config_summary())
