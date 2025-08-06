
# 🧠 Copilot Prompt: KONE 测试报告自动化系统开发指南

## ✅ 项目背景

请你扮演一个资深 Python 开发者的助手，协助开发一个自动化系统，用于生成符合 KONE 指南格式的电梯系统验证测试报告。整个系统基于现有的 FastAPI 服务和虚拟建筑配置。

## 📁 结构要求

整个项目应按模块组织，包括：

- 测试协调器（TestCoordinator）
- 测试用例映射器（TestCaseMapper）
- 虚拟建筑管理器（BuildingDataManager）
- 报告生成器（ReportGenerator）
- 各阶段执行逻辑（phase_1_setup, phase_2_core_tests, phase_3_report_generation）

所有模块签名需统一为：  
`# Author: IBC-AI CO.`

---

## 🚧 阶段 1：构建测试协调器

目标：创建类 `KoneValidationTestCoordinator`，负责：

- 初始化 API 地址
- 加载虚拟建筑配置
- 加载测试指南模板
- 启动完整测试流程：运行预检查、执行测试、生成报告

类方法：

```python
async def run_full_validation(self) -> dict:
    \"\"\"
    执行完整的37项KONE验证测试：
    1. 系统预检查
    2. 执行测试套件
    3. 生成报告
    4. 返回多格式结果
    \"\"\"
```

完成后 **暂停生成**，等待继续指令。

---

## 🧩 阶段 2：构建测试用例映射器

目标：创建类 `TestCaseMapper`，用于将测试用例编号（如 `Test_1`、`Test_4`）映射为对应 API 请求配置，包括：

- 方法（GET/POST）
- 请求路径
- 参数
- 预期返回码
- 校验方法名

示例结构如下：

```python
TEST_CASES = {
  "Test_1": {
    "name": "Solution initialization",
    "api_call": "GET /api/elevator/initialize",
    "expected_status": 200,
    "validation": "check_session_creation"
  },
  ...
}
```

请使用 Python 类封装，完成后 **暂停生成**。

---

## 🏢 阶段 3：虚拟建筑数据管理器

目标：创建类 `BuildingDataManager`，负责从配置文件（YAML）中读取建筑数据，并能提供：

- 楼层 ID 转 area_id（如 3 -> 3000）
- 随机起止楼层对（起止不同）

类方法示意：

```python
def get_random_floor_pair(self) -> tuple:
    return source_area_id, dest_area_id
```

类中需读取默认配置文件 `virtual_building_config.yml`。完成后 **暂停生成**。

---

## 📝 阶段 4：报告生成器

目标：创建类 `ReportGenerator`，生成以下格式的测试报告：

- Markdown（用于标准化查看）
- JSON（用于系统集成）
- HTML（用于网页展示）
- Excel（用于审计归档）

生成方法签名：

```python
def generate_report(self, test_results: list, metadata: dict) -> dict:
    return {
        "markdown": ...,
        "json": ...,
        "html": ...,
        "excel": ...
    }
```

使用 Jinja2 或字符串模板实现。报告中公司名称固定为 `"IBC-AI CO."`。

完成后 **暂停生成**。

---

## 🧪 阶段 5：测试执行流程（分3阶段）

请实现以下函数：

```python
async def phase_1_setup(): ...
async def phase_2_core_tests(): ...
async def phase_3_report_generation(test_results): ...
```

流程要求：

- `phase_1_setup()`：检查 API、加载配置、连接验证
- `phase_2_core_tests()`：执行 37 项测试，组织结果
- `phase_3_report_generation()`：根据 metadata 和测试结果生成报告并返回

完成后 **暂停生成**。

---

## 🚀 阶段 6：自动化执行脚本

创建主执行入口 `main()`：

- 执行上述三阶段
- 打印测试结果与报告文件名
- 支持一键运行

文件头部加注释说明项目用途和作者。

完成后输出结束提示。

---

## 🧾 附加要求

- 所有 Python 文件头部添加：

```python
# Author: IBC-AI CO.
```

- 所有异步函数需包含 `async def`
- 所有 HTTP 请求使用 `httpx.AsyncClient` 或封装的 `api_call()` 工具
- 单元测试与模拟数据可在后续阶段加入

---
