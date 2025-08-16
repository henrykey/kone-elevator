# KONE虚拟建筑测试配置摘要

基于KONE提供的最新虚拟建筑测试指引

## 动作调用禁用测试建筑
- **Building ID**: ye4KrX2cei
- **用途**: 测试禁用的动作调用 (Disabled Action Calls)
- **描述**: 用于调用Action 4（false），测试禁用动作的处理
- **Group IDs**: 1
- **特殊功能**: disabled_action_4

## 直通型轿厢呼叫测试建筑
- **Building ID**: yEJ4j9Xetj
- **用途**: 测试直通型轿厢呼叫 (Through-Type Car Calls)
- **描述**: 用于呼叫1200-12010，测试直通型轿厢呼叫功能
- **Group IDs**: 1
- **Area IDs**: 1200-12010 (10811个)
- **特殊功能**: through_car_calls

## 转运呼叫测试建筑
- **Building ID**: ig8zimMyQf
- **用途**: 测试转运呼叫 (Transfer Calls)
- **描述**: 用于呼叫10000-40000，测试转运呼叫功能
- **Group IDs**: 1
- **Area IDs**: 10000-40000 (30001个)
- **特殊功能**: transfer_calls

## 门禁测试建筑
- **Building ID**: joykVHPoOW7
- **用途**: 测试门禁控制 (Access Control)
- **描述**: 用于测试RFID门禁系统，支持多种Media配置
- **Group IDs**: 1
- **Area IDs**: 40000-41000 (1001个)
- **Media配置**:
  - ID: 0009, Type: RFID
  - ID: 0007, Type: RFID
- **特殊功能**: access_control, rfid_media

## 多群组测试建筑
- **Building ID**: BPa9jEEo3lр
- **用途**: 测试多群组配置 (Multi-Group)
- **描述**: 支持多个群组和终端的复杂配置测试
- **Group IDs**: 1, 2
- **Area IDs**: 17020-56000 (7个)
- **Terminal IDs**: 10011, 11013
- **特殊功能**: multi_group, multiple_terminals

## 测试用例映射
- **test_1_initialization**: 多群组测试建筑 (BPa9jEEo3lр)
- **test_2_mode_non_operational**: 多群组测试建筑 (BPa9jEEo3lр)
- **test_3_mode_operational**: 多群组测试建筑 (BPa9jEEo3lр)
- **test_4_basic_call**: 多群组测试建筑 (BPa9jEEo3lр)
- **test_5_hold_open**: 多群组测试建筑 (BPa9jEEo3lр)
- **test_6_unknown_action**: 动作调用禁用测试建筑 (ye4KrX2cei)
- **test_7_delete_call**: 多群组测试建筑 (BPa9jEEo3lр)
- **test_8_transfer_calls**: 转运呼叫测试建筑 (ig8zimMyQf)
- **test_9_through_car_calls**: 直通型轿厢呼叫测试建筑 (yEJ4j9Xetj)
- **test_10_access_control**: 门禁测试建筑 (joykVHPoOW7)
- **test_11_rfid_media**: 门禁测试建筑 (joykVHPoOW7)
- **test_12_multi_group**: 多群组测试建筑 (BPa9jEEo3lр)
- **test_13_terminal_switching**: 多群组测试建筑 (BPa9jEEo3lр)

**默认建筑**: 多群组测试建筑

## 注意事项
- **排除测试章节**: 6.7 与 6.8 暂时排除
- **后续支持**: 将由KONE专家支持后续处理