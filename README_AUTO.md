# KONE 测试报告自动化系统 v2.0

**Author: IBC-AI CO.**

## 🏢 项目概述

这是一个完整的自动化系统，用于执行KONE电梯系统验证测试并生成符合指南格式的测试报告。系统基于FastAPI服务和虚拟建筑配置，实现了37项KONE SR-API v2.0验证测试的自动化执行。

## ✨ 功能特性

- **🔄 三阶段自动化执行**：系统预检查 → 核心测试 → 报告生成
- **📊 多格式报告生成**：Markdown、JSON、HTML、Excel四种格式
- **🧪 完整测试覆盖**：涵盖37项KONE验证测试用例
- **🏗️ 模块化架构**：测试协调器、用例映射器、数据管理器、报告生成器
- **🔍 详细日志记录**：完整的执行过程跟踪和错误处理
- **⚡ 一键运行支持**：简单命令行接口，支持多种执行模式

## 📁 项目结构

```
elevator/
├── main.py                          # 主执行脚本
├── test_coordinator.py              # 测试协调器
├── test_case_mapper.py              # 测试用例映射器
├── building_data_manager.py         # 虚拟建筑数据管理器
├── report_generator.py              # 报告生成器
├── test_execution_phases.py         # 三阶段执行逻辑
├── virtual_building_config.yml      # 虚拟建筑配置
├── config.yaml                      # 系统配置
├── app.py                          # FastAPI服务
├── drivers.py                      # 电梯驱动程序
└── verification_scripts/           # 验证脚本
    ├── test_coordinator_verify.py
    ├── test_mapper_verify.py
    ├── building_manager_verify.py
    ├── report_generator_verify.py
    └── test_phases_verify.py
```

## 🚀 快速开始

### 1. 环境准备

确保安装了必要的Python依赖：

```bash
pip install fastapi uvicorn httpx pyyaml
pip install openpyxl jinja2  # 可选：Excel和高级模板支持
```

### 2. 启动FastAPI服务

```bash
python app.py
```

服务将在 `http://localhost:8000` 启动。

### 3. 运行测试系统

#### 基础使用
```bash
python main.py
```

#### 高级选项
```bash
# 指定API地址
python main.py --api-url http://localhost:8080

# 指定配置文件
python main.py --config custom_config.yml

# 启用详细日志
python main.py --verbose

# 使用直接执行模式
python main.py --mode direct

# 模拟运行（不执行实际测试）
python main.py --dry-run
```

## 🔧 系统架构

### 核心组件

#### 1. 测试协调器 (TestCoordinator)
- **文件**: `test_coordinator.py`
- **功能**: 协调整个测试流程，管理API连接和会话
- **特性**: 异步上下文管理、错误处理、状态跟踪

#### 2. 测试用例映射器 (TestCaseMapper)
- **文件**: `test_case_mapper.py`
- **功能**: 管理37项测试用例的配置和映射
- **特性**: 分类管理、参数配置、验证逻辑

#### 3. 虚拟建筑数据管理器 (BuildingDataManager)
- **文件**: `building_data_manager.py`
- **功能**: 管理建筑配置、楼层映射、随机数据生成
- **特性**: 楼层转换、随机楼层对生成、数据验证

#### 4. 报告生成器 (ReportGenerator)
- **文件**: `report_generator.py`
- **功能**: 生成多格式测试报告
- **特性**: Markdown、JSON、HTML、Excel输出

### 执行流程

#### 阶段1：系统预检查 (`phase_1_setup`)
```python
✅ API连通性检查
✅ 建筑数据管理器初始化
✅ 测试用例映射器初始化
✅ 报告生成器初始化
✅ 服务状态检查
```

#### 阶段2：核心测试执行 (`phase_2_core_tests`)
```python
🧪 执行37项KONE验证测试
📊 实时进度跟踪
📈 统计计算和结果汇总
🔍 响应验证和错误处理
```

#### 阶段3：报告生成 (`phase_3_report_generation`)
```python
📝 多格式报告生成
💾 自动文件保存
📊 统计摘要输出
📁 文件路径反馈
```

## 📋 测试用例分类

### 初始化测试 (Tests 1-5)
- Test_1: Solution initialization
- Test_2: API connectivity verification
- Test_3: Service status check
- Test_4: Building configuration retrieval
- Test_5: Network connectivity test

### 呼叫管理测试 (Tests 6-20)
- Test_6: Basic elevator call
- Test_7: Multi-floor call sequence
- Test_8: Call with delay parameter
- Test_9: Call cancellation
- Test_10: Concurrent call handling
- ...

### 状态监控测试 (Tests 11-15)
- Test_11: Elevator mode retrieval
- Test_12: Real-time status monitoring
- ...

### 错误处理测试 (Tests 16-25)
- Test_16: Invalid floor call
- Test_17: Same source and destination
- Test_18: Excessive delay parameter
- Test_19: Invalid building ID
- Test_20: Missing required parameters
- ...

### 性能测试 (Tests 21-37)
- Test_21: Response time measurement
- Test_22: Load testing simulation
- ...

## 📊 报告格式

### 1. Markdown报告
- 标准化文档格式
- 完整的测试结果和统计
- 建议和改进方案

### 2. JSON报告
- 结构化数据格式
- 便于系统集成和API交互
- 完整的元数据信息

### 3. HTML报告
- 交互式网页报告
- 支持折叠展开和样式美化
- 响应式设计

### 4. Excel报告
- 专业审计格式
- 多工作表结构
- 条件格式和图表

## 🔍 验证和测试

系统提供了完整的验证脚本：

```bash
# 验证各个组件
python test_coordinator_verify.py
python test_mapper_verify.py
python building_manager_verify.py
python report_generator_verify.py
python test_phases_verify.py
```

## ⚙️ 配置说明

### 虚拟建筑配置 (`virtual_building_config.yml`)
```yaml
building:
  id: "fWlfHyPlaca"

elevator_groups:
  group_1:
    lifts:
      - id: "Lift 1 - A"
        type: "passenger"

floors:
  deck_1:
    level: 41
    lifts:
      lift_1_a: {front: 1001010, rear: null}
```

### 系统配置 (`config.yaml`)
```yaml
default_elevator_type: kone
kone:
  client_id: "your-client-id"
  client_secret: "your-client-secret"
  token_endpoint: "https://dev.kone.com/api/v2/oauth2/token"
  ws_endpoint: "wss://dev.kone.com/stream-v2"
```

## 📈 输出示例

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    KONE 测试报告自动化系统 v2.0                                    ║
║                                                                              ║
║                            Author: IBC-AI CO.                               ║
║                                                                              ║
║  🏢 电梯系统验证测试 | 📊 多格式报告生成 | 🔄 三阶段自动化流程                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

📊 EXECUTION SUMMARY
Overall Status: COMPLETED
Completed Phases: 3/3
Total Duration: 45.67 seconds

Phase Status:
  phase_1: ✅ COMPLETED
  phase_2: ✅ COMPLETED
    → Tests: 37, Success Rate: 86.5%
  phase_3: ✅ COMPLETED

Generated Reports: ['markdown', 'json', 'html', 'excel']

Saved Files:
  📄 markdown: KONE_Validation_Report_20250806_143022.md
  📄 json: KONE_Validation_Report_20250806_143022.json
  📄 html: KONE_Validation_Report_20250806_143022.html
  📄 excel: KONE_Test_Report_20250806_143022.xlsx
```

## 🔧 扩展和定制

### 添加新测试用例
1. 在 `test_case_mapper.py` 中添加测试配置
2. 实现对应的验证逻辑
3. 更新测试统计

### 自定义报告格式
1. 在 `report_generator.py` 中添加新的生成方法
2. 修改模板或样式
3. 集成到主报告生成流程

### 扩展建筑配置
1. 修改 `virtual_building_config.yml`
2. 更新 `building_data_manager.py` 的解析逻辑
3. 验证数据映射关系

## 🐛 故障排除

### 常见问题

1. **API连接失败**
   - 检查FastAPI服务是否正常启动
   - 验证API地址和端口配置

2. **配置文件不存在**
   - 确保 `virtual_building_config.yml` 文件存在
   - 检查文件路径和权限

3. **Excel生成失败**
   - 安装openpyxl: `pip install openpyxl`
   - 检查文件写入权限

4. **测试执行超时**
   - 检查网络连接
   - 调整超时配置

## 📞 支持和联系

- **作者**: IBC-AI CO.
- **版本**: 2.0.0
- **框架**: KONE SR-API v2.0

---

*这个系统是为KONE电梯系统验证而专门设计的自动化测试解决方案。*
