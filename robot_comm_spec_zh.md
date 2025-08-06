# 机器人通信接口规范 v3.1

**更新日期**: 2025-07-10  
**主要变更**: 
- 新增 autonomousMode 字段
- 完善字段说明表和术语统一
- 优化章节结构和示例格式

---

## 1. 概述

本文档描述了机器人与后台平台在配送原型系统中的通信结构。系统将遥测与控制通道进行分离，以提升效率与可靠性：

- **状态通道（MQTT）**：机器人通过 MQTT 实时上报位置、电量、任务状态、连接状态等。
- **控制与图像通道（REST API）**：后台通过 REST 接口发送控制命令，机器人通过 REST 上传图像。
- **所有通道**：均采用加密传输与身份认证机制，确保通信安全。

---

## 2. 通讯协议

### 2.1 MQTT（用于状态上报）

MQTT 适用于低带宽、高实时性的状态同步场景。建议使用如下命名规则的主题：

```
robots/{deviceId}/state
robots/{deviceId}/connection
```

- 状态上报建议使用 QoS 0（尽力而为）。
- 连接状态使用 QoS 1，确保送达。
- 所有机器人必须配置 **MQTT Last Will Message（遗嘱消息）**，以便在异常掉线时通知后台。

### 2.2 REST API（用于命令与图像）

- 后台通过 REST POST 命令控制机器人行为。
- 机器人通过 REST POST 上传图像（吐货照片、取货照片）。
- 所有接口建议使用 HTTPS，并携带有效身份认证 Token。内网环境（如 WireGuard 连接）可使用 HTTP。
- 缺省的Token是robotid的Base64编码。


---

## 3. MQTT 主题与消息结构

### 3.1 主题设计规范

采用分层结构，推荐如下：

```
robots/{deviceId}/state
robots/{deviceId}/connection
```

### 3.2 主题列表

| 主题                                | 发布方         | 订阅方     | 描述                        |
|-------------------------------------|----------------|------------|-----------------------------|
| robots/{deviceId}/state             | 机器人         | 后台       | 位置信息、电量、任务状态等 |
| robots/{deviceId}/connection        | Broker/机器人  | 后台       | 连接状态（在线/离线）      |
| robots/{deviceId}/network/ip        | 机器人         | 后台       | 网络IP地址信息             |
| robots/{deviceId}/error（可选）     | 机器人         | 后台       | 故障信息                    |
| robots/{deviceId}/cargo（可选）     | 机器人         | 后台       | 货仓状态                    |

### 3.3 消息示例

### 3.3.0 机器人状态上报（robots/{deviceId}/state）

**消息格式示例**：
```json
{
  "position": { "x": 12.34, "y": 5.67, "z": 0.00 },
  "coordinateType": "geodetic",
  "battery": 87,
  "taskStatus": "idle",
  "connection": "online",
  "autonomousMode": false,
  "fault": false,
  "binsNum": 6
}
```

**字段说明表**：

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `position` | Object | ✅ | 机器人当前位置坐标 |
| `coordinateType` | String | ✅ | 坐标类型，见3.6节说明 |
| `battery` | Number | ✅ | 电池电量百分比(0-100) |
| `taskStatus` | String | ✅ | 任务执行状态，见3.7节说明 |
| `taskId` | Number | ❌ | 当前任务ID（有任务时必需） |
| `connection` | String | ✅ | 连接状态：online/offline |
| `autonomousMode` | Boolean | ✅ | 是否启用自主模式 |
| `fault` | Boolean | ✅ | 是否有故障 |
| `binsNum` | Number | ✅ | 货仓总数量 |

当有激活任务时，必须包含 `taskId` 字段：

```json
{
  "position": { "x": 12.34, "y": 5.67, "z": 0.00 },
  "coordinateType": "geodetic", 
  "battery": 87,
  "taskStatus": "delivering",
  "taskId": 12345,
  "connection": "online",
  "autonomousMode": false,
  "fault": false,
  "binsNum": 6
}
```

### 3.3.1 机器人错误状态上报（robots/{deviceId}/error）

机器人检测到故障时，应通过 MQTT 主题 `robots/{deviceId}/error` 发布异常信息，用于后台展示与告警。

示例 Payload：

```json
{
  "timestamp": "2025-07-10T12:34:56Z",
  "errorCode": "ROBOT_TIPPED",
  "severity": "high",
  "message": "The robot has fallen sideways near Lobby A",
  "taskId": 12345,
  "position": { "x": 1.2921, "y": 103.7764, "z": 15.0 },
  "suggestion": "Check if robot needs manual recovery",
  "retryable": false
}
```

错误码建议使用大写英文缩写（如 `ROBOT_TIPPED`），如下为常见错误码：

| 错误码 | 中文含义 | 描述 |
|--------|----------|------|
| `LOW_BATTERY` | 电量过低 | Battery level is below safe threshold |
| `NETWORK_LOST` | 网络丢失 | Robot lost network connection |
| `MOTOR_FAIL` | 电机故障 | Motor malfunction or unable to move |
| `WHEEL_BLOCKED` | 轮子卡住 | Something is blocking the wheel |
| `ROBOT_TIPPED` | 机器人倾倒 | Robot has tilted or fallen over |
| `GPS_LOST` | 无法定位 | Lost GPS / indoor positioning signal |
| `DELIVERY_TIMEOUT` | 配送超时 | Took too long to deliver |
| `ELEVATOR_FAIL` | 电梯失败 | Failed to interact with elevator |
| `TAMPER_DETECTED` | 撬动警报 | Unauthorized access or tampering detected |
| `DOOR_OPEN_FAIL` | 仓门无法打开 | Cargo door failed to open |

---

### 3.3.2 货仓状态上报（robots/{deviceId}/cargo）

用于报告当前货仓状态，例如门的开闭、是否有货物、仓位使用情况等。

示例 Payload：

```json
{
  "timestamp": "2025-07-10T12:35:10Z",
  "doorStatus": "closed",
  "cargoPresent": true,
  "slots": [
    { "slotId": 1, "occupied": true, "itemId": "SKU12345" },
    { "slotId": 2, "occupied": false }
  ],
  "temperature": 24.5,
  "humidity": 60,
  "tamperAlert": false,
  "lastAccessMethod": "user_pickup",
  "taskId": 12345
}
```

字段说明：

- `doorStatus`：仓门状态，可取值 `open` / `closed` / `locked`
- `cargoPresent`：是否检测到货物
- `slots`：各仓位的使用状态（可选）
- `temperature` / `humidity`：仓内环境参数（可选）
- `tamperAlert`：是否有非法开启/撬动
- `lastAccessMethod`：最后开启方式（如 `robot_init` / `user_pickup` / `admin_override`）

---



---

### 3.4 遗嘱消息（Will Message）设计

每个机器人在连接 MQTT Broker 前必须配置 Last Will Message：

- **主题**：robots/{deviceId}/connection
- **消息内容**：
```json
{
  "status": "offline",
  "reason": "disconnect"
}
```
- **QoS**：1
- **Retain**：true

机器人上线后应主动发布上线消息：

```json
{
  "status": "online",
  "reason": "startup"
}
```

### 3.5 网络IP地址发布

机器人在连接到MQTT Broker后应立即发布网络IP地址信息，用于后台系统识别和管理机器人的网络连接状态。

- **主题**：robots/{deviceId}/network/ip
- **消息内容**：
```json
{
  "interface": "wireguard",
  "ip": "192.168.123.101",
  "timestamp": "2025-07-05T10:30:00Z"
}
```

当使用其他网络接口时：
```json
{
  "interface": "ethernet",
  "ip": "192.168.1.100",
  "timestamp": "2025-07-05T10:30:00Z"
}
```

- **QoS**：1（确保送达）
- **Retain**：false
- **发布时机**：连接MQTT Broker成功后立即发布一次

---

### 3.6 坐标类型字段说明

为确保后台系统能正确识别并转换位置数据，建议在每条状态消息中添加字段 `coordinateType`，用于标识 position 中的坐标类型。

支持类型如下：

- **geodetic**：大地坐标（默认），x/y/z 分别为 纬度（lat）、经度（lng）、高程（h），单位为度/米。
- **geocentric**：地心直角坐标系，x/y/z 为以地球中心为原点的三维坐标，单位为米。
- **local**：本地坐标系，x/y/z 为地图/图像坐标（结合 origin 与 resolution 解释），单位为米或像素。

### 3.7 任务状态说明
#### 示例：
当有激活任务时，必须有 `taskId` 字段。

```json
{
  "position": { "x": 1.2921, "y": 103.7764, "z": 15.2 },
  "coordinateType": "geodetic",
  "battery": 85,
  "taskStatus": "delivering",
  "taskId": 12345,
  "connection": "online",
  "autonomousMode": false,
  "fault": false,
  "binsNum": 6,
  "timestamp": "2025-07-10T12:34:56Z"
}
```

`taskStatus` 字段用于标识机器人当前的任务执行状态，支持以下状态值：

| 状态值 | 中文描述 | 说明 |
|--------|----------|------|
| `idle` | 闲置 | 机器人空闲，等待新任务 |
| `delivering` | 配送中 | 正在执行配送任务，前往目标位置 |
| `arrived` | 到达 | 已到达目标位置，准备执行吐货或其他操作 |
| `delivered` | 配送完成 | 货品已送达 |
| `restocking` | 返回补货 | 返回仓库或补给点进行货物补充 |
| `charging` | 返回充电 | 返回充电站进行电量补充 |

当任务状态不为 `idle` 时，建议附带 `taskId` 字段以标识当前任务。

```json
{
  "position": { "x": 1.2921, "y": 103.7764, "z": 15.2 },
  "coordinateType": "geodetic",
  "battery": 85,
  "taskStatus": "delivering",
  "taskId": 12345
}
```

后台收到状态消息时应结合 `coordinateType` 进行位置转换或显示处理。

### 3.8 自主模式说明

`autonomousMode` 字段用于标识机器人当前的运行模式：

- **true**：自主模式，机器人可自主决策和执行任务
- **false**：受控模式，机器人严格按照后台指令执行

#### 模式切换规则：
1. 机器人启动时默认为 `false`（受控模式）
2. 通过后台命令可切换模式
3. 发生故障时自动切换为 `false`
4. 模式变更时必须立即发布状态更新

#### 影响范围：
- **自主模式 (true)**：机器人可自动开始下一个任务、自主决策路径等
- **受控模式 (false)**：每个动作都需要后台明确指令

---

## 4. REST API 接口定义

### 4.1 后台下发命令

#### 4.1.0 送货任务命令

- `POST /api/robots/{robotId}/task`

```json
{
  "taskId": 1234,
  "binId": 2,
  "number": 1,
  "location":{
    "address":"1-2-101",
    "coordinateType": "geodetic",
    "position":{
      "x": 10.0,
      "y": 5.0,
      "z": 0.0
    }
  }  
}
```

#### 4.1.1 移动命令/激活任务

- `POST /api/robots/{robotId}/move`

```json
{
  "taskId": 1234,
  "coordinateType": "geodetic",
  "x": 10.0,
  "y": 5.0,
  "z": 0.0
}
```

#### 4.1.2 吐货命令

- `POST /api/robots/{robotId}/deliver`

```json
{
  "taskId": 1234,
  "binId": 2,
  "number": 1
}
```

#### 4.1.3 暂停任务
- `POST /api/robots/{robotId}/pause`

```json
{
  "taskId": 1234
}
```

#### 4.1.4 恢复任务
- `POST /api/robots/{robotId}/resume`

```json
{
  "taskId": 1234
}
```

#### 4.1.5 中止任务
- `POST /api/robots/{robotId}/abort`

```json
{
  "taskId": 1234
}
```
#### 4.1.6 返回补货命令
- `POST /api/robots/{robotId}/restock`

```json
{
  "taskId": 1234,
  "location":{
    "address":"仓库A-补货区",
    "coordinateType": "geodetic",
    "position":{
      "x": 1.2950,
      "y": 103.7800,
      "z": 0.0
    }
  }
}
```

#### 4.1.7 返回充电命令
- `POST /api/robots/{robotId}/charge`

```json
{
  "taskId": 1234,
  "location":{
    "address":"充电站B-3号位",
    "coordinateType": "geodetic",
    "position":{
      "x": 1.2930,
      "y": 103.7850,
      "z": 0.0
    }
  }
}
```

#### 4.1.8 任务队列管理接口（后台查询）

##### 获取任务队列状态
- `GET /api/JKROBOT/{robotId}/tasks`

返回机器人当前的任务队列状态：

```json
{
  "success": true,
  "robotId": "robot001",
  "queue": {
    "currentTask": {
      "taskId": "task_20250702_103000_robot001",
      "status": "delivering",
      "startTime": "2025-07-02T10:30:00Z"
    },
    "pendingTasks": [
      {
        "taskId": "task_20250702_103100_robot001",
        "binId": 3,
        "location": {...},
        "priority": 1
      }
    ],
    "completedTasks": [
      {
        "taskId": "task_20250702_102000_robot001",
        "completedTime": "2025-07-02T10:25:00Z"
      }
    ]
  },
  "config": {
    "multiTaskMode": true,
    "autonomousMode": false,
    "maxQueueSize": 6
  }
}
```

##### 取消特定任务
- `DELETE /api/JKROBOT/{robotId}/tasks/{taskId}`

取消队列中的特定任务（不能取消正在执行的任务）。
---

### 4.2 机器人上传/查询接口

#### 4.2.1 上传图像

- `POST /api/JKROBOT/{robotId}/images`

```json
{
  "taskId": 1234,
  "type": "deliver",
  "timestamp": "2025-05-19T12:34:56Z",
  "image": "<Base64编码JPEG>"
}
```

#### 4.2.2 货物信息查询接口（机器人主动查询）

##### 查询特定货仓货物信息
- `GET /api/JKROBOT/{robotId}/cargo?binId={binId}`

机器人向后台查询指定货仓的货物信息：

```json
{
  "success": true,
  "robotId": "robot001",
  "binId": 2,
  "cargo": {
    "items": [
      {
        "name": "商品A",
        "quantity": 5,
        "weight": 1.2,
        "category": "food"
      }
    ],
    "totalWeight": 6.0,
    "capacity": 10,
    "utilization": 0.5
  },
  "timestamp": "2025-07-03T10:30:00Z"
}
```

##### 查询全部货仓清单
- `GET /api/JKROBOT/{robotId}/cargo/inventory`

机器人向后台查询所有货仓的货物清单：

```json
{
  "success": true,
  "robotId": "robot001",
  "inventory": {
    "bins": [
      {
        "binId": 1,
        "items": [],
        "totalWeight": 0,
        "capacity": 10,
        "utilization": 0
      },
      {
        "binId": 2,
        "items": [
          {
            "name": "商品A",
            "quantity": 5,
            "weight": 1.2
          }
        ],
        "totalWeight": 6.0,
        "capacity": 10,
        "utilization": 0.5
      }
    ],
    "totalCapacity": 60,
    "totalUtilization": 0.1
  },
  "timestamp": "2025-07-03T10:30:00Z"
}
```

**注意**：货物查询接口采用多层查询策略：
1. 优先使用缓存数据（默认5分钟有效期）
2. 缓存失效时向后台API查询：`GET {backend_url}/api/JKROBOT/{robotId}/cargo?binId={binId}`
3. 后台查询失败时返回备用数据

---

#### 4.2.3 任务恢复接口（机器人自动恢复任务）

- `GET /api/JKROBOT/orders?robotId={robotId}&status=assigned`

机器人启动时自动调用，拉取分配给自己的未完成任务。

**请求参数：**
- `robotId`：机器人ID
- `status`：任务状态（如 assigned、pending, active 等，通常为 assigned）

**返回示例：**
```json
{
  "success": true,
  "orders": [
    {
      "order_id": "ORD20250707123001",
      "cargo_bind_id": "COKE_001",
      "customer_name": "张三",
      "delivery_address": "1-2-101",
      "delivery_lat": 1.2966,
      "delivery_lng": 103.7764,
      "quantity": 2,
      "status": "assigned",
      "assigned_robot_id": "robot001",
      "created_at": "2025-07-07T12:30:01Z"
    }
  ]
}
```

#### 4.2.4 通知客户取货接口（任务通知）

- `POST /api/JKROBOT/{robotId}/notify-pickup`

机器人在到达目标点、需要客户取货时调用，后台可推送通知（如短信、App等），并返回本次任务的提货验证码。

**请求体：**
```json
{
  "taskId": "ORD20250707123001"
}
```

**返回示例：**
```json
{
  "success": true,
  "order_id": "ORD20250707123001",
  "auth_code": "A1B2C3",
  "expires_at": "2025-07-07T13:30:00Z",
  "message": "通知已发送，验证码有效"
}
```

#### 4.2.5 获取/刷新验证码接口

- `GET /api/JKROBOT/{robotId}/auth-code`

**请求体：**
```json
{
  "taskId": "ORD20250707123001"
}
```

机器人或前端在验证码过期或需要新验证码时调用，获取当前订单最新有效的提货验证码。

**返回示例：**
```json
{
  "success": true,
  "order_id": "ORD20250707123001",
  "auth_code": "Z9Y8X7",
  "expires_at": "2025-07-07T13:30:00Z"
}
```
#### 4.2.6 当前任务完成通知接口

- POST /api/JKROBOT/{robotId}/task-complete

请求体：
```json
{
  "taskId": "ORD20250707123001"
}
```
- 描述：机器人在完成当前任务后调用，通知后台任务已完成。
---

## 5. 鉴权机制

### 5.1 MQTT 鉴权

- 用户名 = 设备 ID
- 密码 = Token
- ClientID 示例：`d:orgId:robot:R1234`

### 5.2 REST API 鉴权

- 使用 `Authorization: Bearer <token>` 头部
- 可启用 HTTPS, wireguard或其他VPN时用HTTP

---

## 6. 图像内容

### 6.1 机器人视频流接口

```http
GET /camera/stream
```

- 描述：返回实时 MJPEG 视频流（multipart JPEG 格式）
- 请求头：
  - `Authorization: Bearer <token>`（可选）
- 响应：
  - 状态码：`200 OK`
  - Content-Type: `multipart/x-mixed-replace; boundary=frame`
- 用途：后台或客户端页面中展示机器人当前视野

---

### 6.2 获取当前图像帧

```http
GET /camera/snapshot
```

- 描述：获取当前摄像头图像（单帧 JPEG）
- 查询参数：
  - `base64`（布尔，可选）：若为 true，返回 Base64 编码 JPEG JSON 对象
- 响应：
  - `Content-Type: image/jpeg`（默认）
  - 或 `application/json`，当 `base64=true` 时：
    ```json
    {
      "image": "<Base64 编码 JPEG>"
    }
    ```
- 用途：用于后台抓拍、存证或图像识别等场景

---

### 6.3 上传机器人图像（后台代理）

```http
POST /api/robots/{robotId}/images
```

- 描述：上传机器人图像（抓拍照片）作为任务执行记录
- 请求体：
  ```json
  {
    "taskId": 1234,
    "type": "deliver",  // 可选：pickup, deliver, verify 等
    "timestamp": "2025-05-19T12:34:56Z",
    "image": "<Base64 编码 JPEG>"
  }
  ```
- 响应：
  - `200 OK` 表示上传成功
- 用途：用于上传任务执行图像证据，如包裹投放现场图等

### 6.4 平台视频流代理接口

```http
GET /api/JKROBOT/{robotId}/video-stream
```

- 描述：平台代理接口，用于访问机器人的视频流
- 参数：
  - `robotId`：机器人唯一标识符（用于解析对应的 WG 内网 IP）
- 请求头：
  - `Authorization: Bearer <token>`（如启用认证）
- 响应：
  - 状态码：`200 OK`
  - Content-Type: `multipart/x-mixed-replace; boundary=frame`（与 MJPEG 视频流一致）
- 用途：
  - 提供给前端统一的视频访问入口
  - 由平台后端转发请求至对应机器人的 `/camera/stream` 接口
  - 屏蔽机器人真实 IP，便于权限控制、日志审计和跨域管理
---

## 7. 取货验证工作流说明

1. 机器人到达目标配送地点；
2. 机器人通过 MQTT 更新状态为 "arrived"；
3. 机器人调用通知接口，后台通知用户（push消息、短信、 打电话等），必要时更新发送取货验证码；
4. 用户使用收到的有效验证码生成QR码或直接提供验证码；
5. 机器人扫描用户提供的QR验证码或接受手动输入；
6. 验证码校验通过后，机器人开仓允许用户取货；
7. 用户取货完成，机器人关仓；
8. 机器人拍照记录取货完成状态并上传照片（pickup）；
9. 机器人更新任务状态为 "delivered"，任务结束。

### 7.1 验证码工作流详细说明

#### 步骤1-3：到达和通知
- 机器人到达目标位置后，状态变为 `arrived`
- 调用 `POST /api/JKROBOT/{robotId}/notify-pickup` 接口
- 后台返回验证码并向用户发送通知

#### 步骤4-6：验证和开仓  
- 用户通过短信/App收到6位验证码（如 `A1B2C3`）
- 用户可将验证码生成QR码，或直接告知机器人
- 机器人扫描QR码或接受语音/手动输入
- 验证通过后自动开启对应货仓

#### 步骤7-9：取货和完成
- 用户取出货物，机器人检测并关闭货仓
- 机器人拍照上传取货完成照片（type: "pickup"）
- 调用 `POST /api/JKROBOT/{robotId}/task-complete` 通知任务完成
- 任务状态更新为 `delivered`

### 7.2 验证码相关接口

配合此工作流，相关接口包括：

- **通知取货**：`POST /api/JKROBOT/{robotId}/notify-pickup`
- **获取验证码**：`GET /api/JKROBOT/{robotId}/auth-code`  
- **任务完成**：`POST /api/JKROBOT/{robotId}/task-complete`
- **上传照片**：`POST /api/JKROBOT/{robotId}/images`（type: "pickup"）

---

## 接口规范结束
