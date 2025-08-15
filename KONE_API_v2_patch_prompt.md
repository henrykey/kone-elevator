# 📋 KONE API v2.0 测试提示词 – 修正版布丁版
**Signature:** IBC-AI CO.

## 目的
在已完成的 Category A–G 实现基础上，仅对与《Service Robot API solution validation test guide v2》不完全一致的部分进行补充或加强测试。
**不要重复执行已完成且已符合指南的部分**。

---

## 执行规则
- 对照下表的 **状态** 执行：
  - **[保留]**：保持原实现，不做变动；
  - **[加强]**：在原实现基础上补充新的测试逻辑、断言、报告字段；
  - **[新增]**：增加新的测试用例或功能说明。
- 新增或加强的测试逻辑，应直接补充到现有对应 Category 的实现文件与报告生成逻辑中。
- 所有补丁完成后，更新报告，标记“补丁版完成”。

---

## Category 修正表

### Category A – Configuration & Basic API
状态：[保留]  
说明：Test 1、4 已覆盖，符合指南。

---

### Category B – Monitoring & Events
状态：[加强]  
补充：
- **Test 2 / Test 3**
  - 模拟 **非运营模式**（FRD、OSS、ATS、PRC 任一），验证呼叫被拒绝。
  - 模拟 **运营模式**，验证呼叫成功（201 + session_id）。

```python
async def test_elevator_mode(websocket, building_id):
    # 非运营模式
    set_mode_non_operational(building_id)
    resp = await call_lift(...)
    assert resp.get("statusCode") != 201

    # 运营模式
    set_mode_operational(building_id)
    resp = await call_lift(...)
    assert resp.get("statusCode") == 201
    assert "session_id" in resp
```

---

### Category C – Basic Elevator Calls
状态：[加强]  
补充：
1. **Test 5（Door hold open）**
   - payload 增加 `soft_time` 字段，验证开门时间 ≥ 硬时间 + 软时间。
2. **Test 14（Specific lift call）**
   - 请求中加入 `allowed-lifts` 参数，并验证呼叫的电梯 ID 符合要求。
3. **Test 6–10**
   - 增加 **Option 1 / Option 2 分支验证**（阻止 vs 立即取消）。

```python
# Door hold soft time
payload["payload"]["soft_time"] = 5

# Specific lift call
payload["payload"]["allowed-lifts"] = [lift_id]

# Option 分支
if resp.get("statusCode") == 201 and "cancel Reason" in resp:
    record_cancel_reason(resp)
else:
    assert resp.get("statusCode") != 201
```

---

### Category D – Error Handling & Validation
状态：[加强]  
补充：
- 为 Test 16–20 的错误响应增加 **cancel reason 精确匹配**（与指南一致，区分大小写和空格）。

---

### Category E – Performance & Load Testing
状态：[加强]  
补充：
- 对应 Test 21–30，在报告附录中增加 **功能声明 1–7 实现说明**
  （Multiple groups、Access control、Geolocation、Barrier control、Barrier side location、Driving direction、Multiple call prevention）。

---

### Category F – System-Level Testing
状态：[新增]  
补充：
- **Test 38（Custom case）**
- **功能声明 8**：日志记录与访问权限调用日志处理方法；
- **功能声明 9**：安全性自评表完成情况；
- **功能声明 10**：电梯内外的连接性处理方法。

```python
# 功能声明输出示例
{
  "log_handling": "...",
  "cybersecurity_self_assessment": "...",
  "connectivity_management": "..."
}
```

---

### Category G – Integration & E2E
状态：[加强]（替换原描述）  
补充：
- **Test 36**：通信中断 → ping 失败 → 等待恢复 → ping 成功。
- **Test 37**：恢复后发起呼叫并验证响应（201 + session_id + 正确楼层）。
- 报告增加：中断持续时间、ping 次数、恢复时间戳、恢复后呼叫详情。

```python
async def test_comm_recovery(websocket, building_id, group_id):
    simulate_comm_down()
    assert not await ping_until_success(websocket, building_id, group_id, max_attempts=3)

    restore_comm()
    assert await ping_until_success(websocket, building_id, group_id)

    resp = await call_lift_after_recovery(...)
    assert resp.get("statusCode") == 201
    assert "session_id" in resp
```

---

## Test–Category 映射确认

| Test | Category | 状态 |
|------|----------|------|
| 1,4  | A | 保留 |
| 2,3  | B | 加强 |
| 5–10 | C | 加强 |
| 14   | C | 加强 |
| 6–10 Option 分支 | C | 加强 |
| 16–20 | D | 加强 |
| 21–30 | E | 加强 |
| 31–35 | F | 保留 |
| 36,37 | G | 加强 |
| 38, 功能声明 8–10 | F | 新增 |

---

**执行指令**：  
> 按上表逐个 Category 补充实现，修改后运行相关新增/加强的测试用例并更新报告。不需变动的部分保持原实现。补丁完成后，报告文件需标注为“补丁版完成”，并在附录中列出所有新增/加强的测试结果与功能声明说明。

**Signature:** IBC-AI CO.
