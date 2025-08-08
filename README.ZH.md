# KONE电梯控制服务与测试套件

一个面向KONE服务机器人的电梯控制系统，包含REST API服务和WebSocket测试程序，支持KONE SR-API v2.0的完整集成与验证。

## 🏢 项目简介

本项目包含两个核心模块：
1. **REST API服务**（`acesslifts.py`）：基于FastAPI的电梯控制服务
2. **WebSocket测试套件**（`testall.py`）：KONE电梯API自动化测试程序

---

## ✨ 主要功能

### REST API服务
- 多品牌电梯驱动架构，易于扩展
- 完全兼容KONE SR-API v2.0
- 动态建筑ID与配置自动检测
- 完善的日志记录与错误处理
- 参数校验（延迟、楼层等）
- 高性能异步响应

### WebSocket测试套件（testall.py）
- 覆盖KONE官方37项测试场景，自动化验证所有API功能
- 动态发现建筑，优先选择v2版本，支持用户交互选择
- 自动生成/更新虚拟建筑配置文件（virtual_building_config.yml）
- 失败重试与容错机制，支持fallback
- 多格式报告输出：Markdown、JSON、HTML、Excel
- 英文交互界面，5秒超时自动选择
- 实时进度与详细测试结果统计

---

## 🚀 快速开始

### 环境要求
- Python 3.9+
- pip
- KONE API账号（生产环境）

### 安装与运行
```bash
git clone <仓库地址>
cd elevator
pip install -r requirements.txt
```

#### 配置KONE API（编辑`config.yaml`）
```yaml
kone:
  client_id: "你的client-id"
  client_secret: "你的client-secret"
  token_endpoint: "https://dev.kone.com/api/v2/oauth2/token"
  ws_endpoint: "wss://dev.kone.com/stream-v2"
```

#### 启动REST API服务
```bash
python acesslifts.py
# 访问 http://localhost:8000
```

#### 运行WebSocket测试套件
```bash
python testall.py
# 交互式选择建筑，自动执行全部测试
```

---

## 📋 API接口说明

### REST API服务（acesslifts.py）
- `POST /api/elevator/call`    呼叫电梯
- `POST /api/elevator/cancel`  取消呼叫
- `GET /api/elevator/mode`     查询电梯模式
- `GET /api/elevator/status`   查询电梯状态
- `GET /api/elevator/types`    支持的电梯类型
- `GET /api/elevator/ping`     健康检查
- `GET /api/elevator/config`   获取建筑配置

### WebSocket测试套件（testall.py）
- 自动发现建筑，优先v2，支持用户选择
- 37项测试场景自动执行
- 生成多格式报告，保存至`./reports/`

---

## 🏗️ 架构与模块

- `acesslifts.py`：主服务入口，FastAPI实现
- `testall.py`：KONE电梯API自动化测试主程序
- `drivers.py`：电梯驱动抽象与KONE实现
- `report_generator.py`：多格式报告生成
- `config.yaml`：KONE API配置
- `virtual_building_config.yml`：自动生成的建筑配置
- `reports/`：测试报告输出目录

---

## 🧪 测试与验证

- 运行`python testall.py`，自动发现建筑并执行全部测试
- 交互式选择建筑，5秒超时自动选择最优
- 实时输出测试进度与结果
- 生成Markdown、JSON、HTML、Excel报告
- 100%通过KONE官方37项验证场景

---

## ⚙️ 配置说明

- `config.yaml`：KONE API账号与端点配置
- `virtual_building_config.yml`：自动生成，保存建筑结构与电梯分组
- 环境变量支持生产部署

---

## 📊 日志与监控

- 所有操作均有详细日志，支持JSON结构化输出
- 错误与性能指标实时记录
- 测试报告自动归档

---

## 🛡️ 错误处理与安全

- 完善的HTTP状态码与错误信息
- 参数校验与输入过滤
- 支持OAuth2与API Key认证
- 自动重试与容错机制

---

## 📁 项目结构
```
elevator/
├── acesslifts.py              # REST API服务主入口
├── testall.py                 # KONE电梯测试主程序
├── drivers.py                 # 驱动抽象与KONE实现
├── report_generator.py        # 报告生成
├── config.yaml                # KONE API配置
├── requirements.txt           # 依赖
├── run.sh                     # 启动脚本
├── virtual_building_config.yml # 自动生成的建筑配置
├── reports/                   # 测试报告目录
└── ...
```

---

## 配置 Solution Provider 信息

在 `config.yaml` 文件中，您可以通过 `solution_provider` 字段配置报告中的“Solution Provider”信息。例如：

```yaml
solution_provider:
  company_name: IBC-AI CO.
  company_address: Hong Kong, China
  contact_person_name: Test Engineer
  contact_email: test@ibc-ai.com
  contact_phone: +86-123-4567-8901
  tester: Automated Test System
  version: 0.2.1
```

这些信息会自动出现在生成的测试报告的“Solution Provider”表格中。

---

## 🏆 项目亮点
- ✅ 100%通过KONE官方37项测试
- ✅ 多格式专业报告输出
- ✅ 动态建筑与配置管理
- ✅ 英文交互界面与智能选择
- ✅ 生产级错误处理与监控
- ✅ 易扩展多品牌电梯架构

---

**版本**：v0.2.0  
**最后更新**：2025年8月8日  
**兼容性**：KONE SR-API v2.0

**技术支持**：dev@ibc-ai.com

---

🎊 完美通过全部测试场景，KONE电梯API验证100%成功！
