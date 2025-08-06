# HCM API接口和MQTT消息实现规范

**文档版本**: v1.4.0  
**创建日期**: 2025-08-02  
**更新日期**: 2025-08-05  
**适用系统**: 硬件控制模块(HCM) - 配送机器人硬件接口层  
**规范依据**: robot_comm_spec_zh.md v3.1

**v1.4.0 更新内容**:
- 统一坐标系统为local坐标，去除geodetic坐标引用
- 修正所有API示例中的coordinateType为"local"
- 更新文档版本说明，与最新CM实现保持一致
- 完善室内定位系统说明和本地坐标系统规范
- 新增地图配置规范(map.yaml)，确保HCM和CM坐标系统对齐

**v1.3.0 更新内容**:
- 新增Vision系统API接口定义(多摄像头支持)
- 添加RGB/深度/全景摄像头流接口
- 完善图像抓拍和摄像头状态监控
- 增加摄像头错误检测和配置管理

**v1.2.0 更新内容**:
- 新增QR扫描器API接口定义(scan/status/config)
- 添加QR扫描相关错误码和检测机制
- 完善QR扫描器配置参数和端点定义
- 增加QR扫描功能实施检查清单

**v1.1.0 更新内容**:
- 调整响应格式为统一的 `{"success": true, "data": {...}}` 结构，与CM系统兼容
- 修正位置数据结构，将 `coordinateType` 移至根级别，符合robot_comm_spec规范
- 更新配置示例，使用与CM系统一致的配置路径结构
- 完善所有API接口的伪代码实现指导

---

## 📋 **概述**

本文档定义了硬件控制模块(HCM)需要实现的API接口和MQTT消息发布规范，以支持通讯模块(CM)的硬件状态获取、控制命令转发和错误监控功能。

### **架构关系**
```
CM (通讯模块) ←--REST API--> HCM (硬件控制模块)
     │                         │
     ↓ MQTT发布                ↓ MQTT发布  
  外部MQTT Broker ←--MQTT--→ 外部MQTT Broker
  (完整状态消息)              (错误/货仓状态)
```

### **职责分工**
- **HCM**: 硬件控制、状态感知、错误检测、货仓监控、QR码扫描
- **CM**: 业务逻辑、任务管理、状态合成、对外通讯、QR码认证验证

### **QR扫描认证流程**
```
1. CM生成认证码和有效期，等待用户扫描
2. CM调用HCM的QR扫描接口，启动硬件扫描
3. HCM扫描到QR码后，返回扫描内容给CM
4. CM验证扫描内容是否为有效认证码
5. CM根据验证结果执行相应的业务逻辑
```

**说明**: HCM不负责认证码的生成和验证，只负责扫描硬件操作和返回扫描结果

### **坐标系统规范**

HCM系统统一使用**本地坐标系统(local coordinate system)**进行位置定位和导航：

**坐标系统特征**:
- **坐标类型**: `coordinateType: "local"`
- **原点设定**: 建筑物或工作区域的固定参考点
- **单位**: 米(meter)，精度到小数点后2位
- **坐标轴**: X轴(东西方向)、Y轴(南北方向)、Z轴(垂直高度)

**定位技术栈**:
- **主要技术**: SLAM(同步定位与地图构建)
- **传感器**: 激光雷达、IMU、视觉传感器
- **精度**: ±0.5米(accuracy字段表示当前精度)
- **更新频率**: 10Hz或更高

**与GPS的区别**:
- 不依赖GPS卫星信号，适用于室内环境
- 坐标值为相对于本地原点的偏移量
- 稳定性更高，不受天气和建筑物遮挡影响

### **地图配置规范**

HCM和CM系统需要使用统一的地图配置来确保坐标系统对齐。标准地图配置文件(`map.yaml`)格式如下：

```yaml
# map.yaml - 地图配置规范
image: map.png                    # 地图图像文件路径
resolution: 0.05                  # 地图分辨率 (米/像素)
origin: [-102.4, -102.4, 0.0]   # 地图原点坐标 [x, y, yaw]
occupied_thresh: 0.5             # 占用空间阈值 (0.0-1.0)
free_thresh: 0.2                # 自由空间阈值 (0.0-1.0)
negate: 0                       # 颜色反转标志 (0/1)
```

**配置参数说明**:
- **image**: 对应地图的栅格图像文件
- **resolution**: 地图分辨率，0.05表示每像素代表5厘米
- **origin**: 地图坐标系原点在世界坐标系中的位置，格式为[x, y, yaw]
- **occupied_thresh**: 像素值高于此阈值视为占用空间
- **free_thresh**: 像素值低于此阈值视为自由空间
- **negate**: 是否反转黑白像素的含义

**HCM实现要求**:
- HCM的本地坐标系统必须与map.yaml中定义的原点对齐
- 位置数据输出应基于地图原点计算相对坐标
- 支持标准ROS地图格式，便于与SLAM系统集成
- 确保厘米级精度，满足室内导航要求

---

## 🔧 **HCM需要实现的REST API接口**

### **API响应格式规范**

所有HCM API接口必须使用统一的响应格式，以确保与CM系统的兼容性：

**成功响应格式**:
```json
{
  "success": true,
  "data": {
    // 实际数据内容
  }
}
```

**错误响应格式**:
```json
{
  "success": false,
  "data": {
    "status": "error",
    "message": "错误描述",
    "error_code": "ERROR_CODE",
    "timestamp": "2025-08-02T12:00:00Z"
  }
}
```

### 1. **核心状态接口**

#### A. **获取完整硬件状态**
```http
GET /api/hcm/status
```

**接口说明**: 获取机器人完整硬件状态信息，供CM定期轮询使用

**响应格式**:
```json
{
  "success": true,
  "data": {
    "position": {
      "x": 12.34,
      "y": 5.67,
      "z": 0.00,
      "accuracy": 0.5
    },
    "coordinateType": "local",
    "battery": {
      "level": 87,
      "voltage": 24.2,
      "current": 1.5,
      "temperature": 35.0,
      "charging": false,
      "estimated_runtime": 180
    },
    "connection": "online",
    "fault": false,
  "sensors": {
    "lidar": {
      "status": "active",
      "range": 10.5,
      "last_update": "2025-08-02T12:00:00Z"
    },
    "camera": {
      "status": "active",
      "resolution": "1080p",
      "last_update": "2025-08-02T12:00:00Z"
    },
    "imu": {
      "status": "active",
      "orientation": {"roll": 0.1, "pitch": 0.2, "yaw": 45.0},
      "last_update": "2025-08-02T12:00:00Z"
    }
  },
  "motion": {
    "moving": false,
    "speed": 0.0,
    "direction": 0.0,
    "target_position": null
  },
  "timestamp": "2025-08-02T12:00:00Z"
  }
}
```

**实现伪码**:
```pseudocode
function getHardwareStatus():
    position = getCurrentPosition()
    battery = getBatteryStatus()
    sensors = getAllSensorStatus()
    motion = getMotionStatus()
    
    data = {
        "position": position,
        "coordinateType": "local",
        "battery": battery,
        "connection": "online",
        "fault": checkSystemFault(),
        "sensors": sensors,
        "motion": motion,
        "timestamp": getCurrentTimestamp()
    }
    
    return {
        "success": true,
        "data": data
    }
```

#### B. **获取位置信息（专用接口）**
```http
GET /api/hcm/position
```

**接口说明**: 高频位置查询专用接口，优化响应速度

**响应格式**:
```json
{
  "success": true,
  "data": {
    "position": {
      "x": 12.34,
      "y": 5.67,
      "z": 0.00,
      "accuracy": 0.5
    },
    "coordinateType": "local",
    "timestamp": "2025-08-02T12:00:00Z"
  }
}
```

**实现伪码**:
```pseudocode
function getPosition():
    // 优化的位置获取，减少数据处理开销
    position = readPositionSensors()
    
    data = {
        "position": {
            "x": position.x,
            "y": position.y,
            "z": position.z,
            "accuracy": position.accuracy
        },
        "coordinateType": "local",
        "timestamp": getCurrentTimestamp()
    }
    
    return {
        "success": true,
        "data": data
    }
```

#### C. **获取电池状态**
```http
GET /api/hcm/battery
```

**响应格式**:
```json
{
  "success": true,
  "data": {
    "level": 87,
    "voltage": 24.2,
    "current": 1.5,
    "temperature": 35.0,
    "charging": false,
    "estimated_runtime": 180,
    "timestamp": "2025-08-02T12:00:00Z"
  }
}
```

### 2. **控制接口**

#### A. **移动控制**
```http
POST /api/hcm/move
```

**请求体**:
```json
{
  "x": 10.0,
  "y": 5.0,
  "z": 0.0,
  "coordinateType": "local",
  "speed": 1.0
}
```

**响应格式**:
```json
{
  "success": true,
  "data": {
    "status": "success",
    "message": "Moving to target position",
    "estimated_duration": 30.5,
    "timestamp": "2025-08-02T12:00:00Z"
  }
}
```

**实现伪码**:
```pseudocode
function moveToPosition(request):
    target = {
        "x": request.x,
        "y": request.y, 
        "z": request.z,
        "coordinateType": request.coordinateType,
        "speed": request.speed or defaultSpeed
    }
    
    // 路径规划和运动控制
    if (validateTarget(target)):
        result = startMovement(target)
        if (result.success):
            return {
                "success": true,
                "data": {
                    "status": "success",
                    "message": "Moving to target position",
                    "estimated_duration": calculateDuration(target),
                    "timestamp": getCurrentTimestamp()
                }
            }
        else:
            return {
                "success": false,
                "data": {
                    "status": "error",
                    "message": result.error_message,
                    "timestamp": getCurrentTimestamp()
                }
            }
    else:
        return {
            "success": false,
            "data": {
                "status": "error", 
                "message": "Invalid target position",
                "timestamp": getCurrentTimestamp()
            }
        }
```

#### B. **停止移动**
```http
POST /api/hcm/stop
```

**响应格式**:
```json
{
  "success": true,
  "data": {
    "status": "success",
    "message": "Motion stopped",
    "current_position": {
      "x": 8.5,
      "y": 4.2,
      "z": 0.0
    },
    "timestamp": "2025-08-02T12:00:00Z"
  }
}
```

### 3. **货仓控制接口**

#### A. **开启货仓**
```http
POST /api/hcm/cargo/open
```

**接口说明**: 控制指定货仓门开启，用于货物装载或客户取货

**请求体**:
```json
{
  "bin_id": 1,
  "reason": "customer_pickup",
  "task_id": 12345
}
```

**请求参数说明**:
- `bin_id`: 货仓ID (1-6)
- `reason`: 开启原因 ("customer_pickup", "loading", "maintenance", "emergency")
- `task_id`: 关联任务ID (可选)

**成功响应格式**:
```json
{
  "success": true,
  "data": {
    "status": "opened",
    "bin_id": 1,
    "message": "Cargo bin 1 opened successfully",
    "door_status": "open",
    "lock_status": "unlocked",
    "operation_duration": 2.3,
    "timestamp": "2025-08-02T12:00:00Z"
  }
}
```

**失败响应格式**:
```json
{
  "success": false,
  "data": {
    "status": "error",
    "bin_id": 1,
    "message": "Failed to open cargo bin 1: door mechanism jammed",
    "error_code": "DOOR_OPEN_FAIL",
    "timestamp": "2025-08-02T12:00:00Z"
  }
}
```

**实现伪码**:
```pseudocode
function openCargoBin(request):
    binId = request.bin_id
    reason = request.reason or "unknown"
    taskId = request.task_id or getCurrentTaskId()
    
    // 验证货仓ID
    if (binId < 1 or binId > 6):
        return {
            "success": false,
            "data": {
                "status": "error",
                "bin_id": binId,
                "message": "Invalid bin ID: " + binId + " (valid range: 1-6)",
                "error_code": "INVALID_BIN_ID",
                "timestamp": getCurrentTimestamp()
            }
        }
    
    // 检查货仓当前状态
    currentStatus = getCargoBinStatus(binId)
    if (currentStatus.door_status == "open"):
        return {
            "success": true,
            "data": {
                "status": "already_open",
                "bin_id": binId,
                "message": "Cargo bin " + binId + " is already open",
                "door_status": "open",
                "lock_status": "unlocked",
                "timestamp": getCurrentTimestamp()
            }
        }
    
    logInfo("Opening cargo bin " + binId + " for reason: " + reason + ", task: " + taskId)
    startTime = getCurrentTime()
    
    try:
        // 执行开仓操作
        result = performCargoBinOpen(binId)
        operationDuration = getCurrentTime() - startTime
        
        if (result.success):
            // 记录访问方法
            recordLastAccessMethod(binId, reason)
            
            // 立即发布货仓状态变化到MQTT
            publishCargoStatusChange(binId, "open", reason, taskId)
            
            logInfo("Cargo bin " + binId + " opened successfully")
            return {
                "success": true,
                "data": {
                    "status": "opened",
                    "bin_id": binId,
                    "message": "Cargo bin " + binId + " opened successfully",
                    "door_status": "open",
                    "lock_status": "unlocked",
                    "operation_duration": operationDuration,
                    "timestamp": getCurrentTimestamp()
                }
            }
        else:
            logError("Failed to open cargo bin " + binId + ": " + result.error)
            
            // 发布错误到MQTT
            publishErrorIfNeeded({
                "errorCode": "DOOR_OPEN_FAIL",
                "severity": "medium",
                "message": "Failed to open cargo bin " + binId + ": " + result.error,
                "suggestion": "Check door mechanism and retry operation",
                "retryable": true
            })
            
            return {
                "success": false,
                "data": {
                    "status": "error",
                    "bin_id": binId,
                    "message": "Failed to open cargo bin " + binId + ": " + result.error,
                    "error_code": "DOOR_OPEN_FAIL",
                    "timestamp": getCurrentTimestamp()
                }
            }
    catch (exception):
        logError("Cargo bin open exception: " + exception.message)
        return {
            "success": false,
            "data": {
                "status": "error",
                "bin_id": binId,
                "message": "Cargo bin operation exception: " + exception.message,
                "error_code": "CARGO_OPERATION_EXCEPTION",
                "timestamp": getCurrentTimestamp()
            }
        }
```

#### B. **关闭货仓**
```http
POST /api/hcm/cargo/close
```

**接口说明**: 控制指定货仓门关闭，完成货物操作后锁定货仓

**请求体**:
```json
{
  "bin_id": 1,
  "reason": "operation_complete",
  "task_id": 12345
}
```

**请求参数说明**:
- `bin_id`: 货仓ID (1-6)
- `reason`: 关闭原因 ("operation_complete", "timeout", "emergency", "manual")
- `task_id`: 关联任务ID (可选)

**成功响应格式**:
```json
{
  "success": true,
  "data": {
    "status": "closed",
    "bin_id": 1,
    "message": "Cargo bin 1 closed and locked successfully",
    "door_status": "closed",
    "lock_status": "locked",
    "operation_duration": 1.8,
    "timestamp": "2025-08-02T12:00:00Z"
  }
}
```

**实现伪码**:
```pseudocode
function closeCargoBin(request):
    binId = request.bin_id
    reason = request.reason or "manual"
    taskId = request.task_id or getCurrentTaskId()
    
    // 验证货仓ID
    if (binId < 1 or binId > 6):
        return {
            "success": false,
            "data": {
                "status": "error",
                "bin_id": binId,
                "message": "Invalid bin ID: " + binId + " (valid range: 1-6)",
                "error_code": "INVALID_BIN_ID",
                "timestamp": getCurrentTimestamp()
            }
        }
    
    // 检查货仓当前状态
    currentStatus = getCargoBinStatus(binId)
    if (currentStatus.door_status == "closed" and currentStatus.lock_status == "locked"):
        return {
            "success": true,
            "data": {
                "status": "already_closed",
                "bin_id": binId,
                "message": "Cargo bin " + binId + " is already closed and locked",
                "door_status": "closed",
                "lock_status": "locked",
                "timestamp": getCurrentTimestamp()
            }
        }
    
    logInfo("Closing cargo bin " + binId + " for reason: " + reason + ", task: " + taskId)
    startTime = getCurrentTime()
    
    try:
        // 执行关仓操作
        result = performCargoBinClose(binId)
        operationDuration = getCurrentTime() - startTime
        
        if (result.success):
            // 记录访问方法
            recordLastAccessMethod(binId, reason)
            
            // 立即发布货仓状态变化到MQTT
            publishCargoStatusChange(binId, "closed", reason, taskId)
            
            logInfo("Cargo bin " + binId + " closed and locked successfully")
            return {
                "success": true,
                "data": {
                    "status": "closed",
                    "bin_id": binId,
                    "message": "Cargo bin " + binId + " closed and locked successfully",
                    "door_status": "closed",
                    "lock_status": "locked",
                    "operation_duration": operationDuration,
                    "timestamp": getCurrentTimestamp()
                }
            }
        else:
            logError("Failed to close cargo bin " + binId + ": " + result.error)
            
            // 发布错误到MQTT
            publishErrorIfNeeded({
                "errorCode": "DOOR_CLOSE_FAIL",
                "severity": "medium",
                "message": "Failed to close cargo bin " + binId + ": " + result.error,
                "suggestion": "Check door mechanism and retry operation",
                "retryable": true
            })
            
            return {
                "success": false,
                "data": {
                    "status": "error",
                    "bin_id": binId,
                    "message": "Failed to close cargo bin " + binId + ": " + result.error,
                    "error_code": "DOOR_CLOSE_FAIL",
                    "timestamp": getCurrentTimestamp()
                }
            }
    catch (exception):
        logError("Cargo bin close exception: " + exception.message)
        return {
            "success": false,
            "data": {
                "status": "error",
                "bin_id": binId,
                "message": "Cargo bin operation exception: " + exception.message,
                "error_code": "CARGO_OPERATION_EXCEPTION",
                "timestamp": getCurrentTimestamp()
            }
        }
```

#### C. **查询货仓状态**
```http
GET /api/hcm/cargo/status
```

**接口说明**: 查询指定货仓或所有货仓的详细状态

**查询参数**:
- `bin_id`: 货仓ID (可选，不指定则返回所有货仓状态)

**单个货仓响应格式**:
```json
{
  "success": true,
  "data": {
    "bin_id": 1,
    "door_status": "closed",
    "lock_status": "locked",
    "cargo_present": true,
    "weight": 1.2,
    "temperature": 24.5,
    "humidity": 60,
    "last_access_time": "2025-08-02T11:30:00Z",
    "last_access_method": "customer_pickup",
    "sensor_status": {
      "door_sensor": "ok",
      "weight_sensor": "ok",
      "temperature_sensor": "ok",
      "lock_mechanism": "ok"
    },
    "timestamp": "2025-08-02T12:00:00Z"
  }
}
```

**所有货仓响应格式**:
```json
{
  "success": true,
  "data": {
    "bins": [
      {
        "bin_id": 1,
        "door_status": "closed",
        "lock_status": "locked",
        "cargo_present": true,
        "weight": 1.2
      },
      {
        "bin_id": 2,
        "door_status": "open",
        "lock_status": "unlocked",
        "cargo_present": false,
        "weight": 0.0
      }
    ],
    "total_bins": 6,
    "occupied_bins": 1,
    "overall_status": "normal",
    "timestamp": "2025-08-02T12:00:00Z"
  }
}
```

### 4. **QR扫描接口**

#### A. **系统健康状态**
```http
GET /api/hcm/health
```

**响应格式**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "uptime": 86400,
    "cpu_usage": 45.2,
    "memory_usage": 62.8,
    "disk_usage": 30.1,
    "components": {
      "motor_controller": "healthy",
      "sensor_array": "healthy", 
      "navigation": "healthy",
      "power_management": "healthy"
    },
    "timestamp": "2025-08-02T12:00:00Z"
  }
}
```

**实现伪码**:
```pseudocode
function getHealthStatus():
    components = checkAllComponents()
    system = getSystemMetrics()
    
    overallStatus = "healthy"
    for component in components:
        if (component.status != "healthy"):
            overallStatus = "degraded"
            break
    
    data = {
        "status": overallStatus,
        "uptime": system.uptime,
        "cpu_usage": system.cpu_percentage,
        "memory_usage": system.memory_percentage,
        "disk_usage": system.disk_percentage,
        "components": components,
        "timestamp": getCurrentTimestamp()
    }
    
    return {
        "success": true,
        "data": data
    }
```

### 5. **QR扫描接口**

#### A. **触发QR扫描**
```http
POST /api/hcm/qr/scan
```

**接口说明**: 触发硬件QR扫描器开始扫描，HCM扫描到QR码后返回扫描内容，由CM进行认证验证

**请求体**:
```json
{
  "timeout": 30,
  "taskId": 12345
}
```

**请求参数说明**:
- `timeout`: 扫描超时时间(秒)，默认30秒
- `taskId`: 任务ID，用于关联扫描请求(可选)

**成功扫描响应格式**:
```json
{
  "success": true,
  "data": {
    "status": "scanned",
    "qr_content": "AUTH_CODE_ABC123_TASK_12345",
    "scan_duration": 2.3,
    "quality_score": 0.95,
    "timestamp": "2025-08-02T12:00:00Z"
  }
}
```

**扫描超时响应格式**:
```json
{
  "success": true,
  "data": {
    "status": "timeout",
    "message": "No QR code detected within timeout period",
    "scan_duration": 30.0,
    "timestamp": "2025-08-02T12:00:00Z"
  }
}
```

**扫描失败响应格式**:
```json
{
  "success": false,
  "data": {
    "status": "error",
    "message": "QR scanner hardware error",
    "error_code": "SCANNER_HARDWARE_FAIL",
    "timestamp": "2025-08-02T12:00:00Z"
  }
}
```

**实现伪码**:
```pseudocode
function scanQRCode(request):
    taskId = request.taskId or getCurrentTaskId()
    timeout = request.timeout or 30
    
    if (!isQRScannerAvailable()):
        return {
            "success": false,
            "data": {
                "status": "error",
                "message": "QR scanner hardware not available",
                "error_code": "SCANNER_UNAVAILABLE",
                "timestamp": getCurrentTimestamp()
            }
        }
    
    logInfo("Starting QR scan for task: " + taskId)
    startTime = getCurrentTime()
    
    // 启动QR扫描硬件
    try:
        scanResult = performQRScan(timeout)
        scanDuration = getCurrentTime() - startTime
        
        if (scanResult.success):
            logInfo("QR scan successful: " + scanResult.content)
            return {
                "success": true,
                "data": {
                    "status": "scanned",
                    "qr_content": scanResult.content,
                    "scan_duration": scanDuration,
                    "quality_score": scanResult.qualityScore,
                    "timestamp": getCurrentTimestamp()
                }
            }
        else if (scanResult.timeout):
            logWarning("QR scan timeout after " + timeout + " seconds")
            return {
                "success": true,
                "data": {
                    "status": "timeout",
                    "message": "No QR code detected within timeout period",
                    "scan_duration": scanDuration,
                    "timestamp": getCurrentTimestamp()
                }
            }
        else:
            logError("QR scan failed: " + scanResult.error)
            return {
                "success": false,
                "data": {
                    "status": "error",
                    "message": "QR scanner hardware error: " + scanResult.error,
                    "error_code": "SCANNER_HARDWARE_FAIL",
                    "timestamp": getCurrentTimestamp()
                }
            }
    catch (exception):
        logError("QR scan exception: " + exception.message)
        return {
            "success": false,
            "data": {
                "status": "error",
                "message": "QR scanner exception: " + exception.message,
                "error_code": "SCANNER_EXCEPTION",
                "timestamp": getCurrentTimestamp()
            }
        }
```

#### B. **获取QR扫描器状态**
```http
GET /api/hcm/qr/status
```

**接口说明**: 获取QR扫描器硬件状态和能力信息

**响应格式**:
```json
{
  "success": true,
  "data": {
    "scanner_status": "ready",
    "hardware_info": {
      "model": "Honeywell N6603",
      "firmware_version": "1.2.3",
      "serial_number": "SN123456789",
      "last_calibration": "2025-08-01T10:00:00Z"
    },
    "capabilities": {
      "supported_formats": ["QR_CODE", "DATA_MATRIX", "PDF417"],
      "max_resolution": "1920x1080",
      "focus_range": {"min": 5, "max": 300},
      "illumination": true,
      "autofocus": true
    },
    "current_settings": {
      "brightness": 75,
      "contrast": 80,
      "focus_mode": "auto",
      "illumination_enabled": true
    },
    "statistics": {
      "total_scans": 1247,
      "successful_scans": 1189,
      "success_rate": 95.3,
      "average_scan_time": 1.8,
      "last_scan_time": "2025-08-02T11:45:30Z"
    },
    "timestamp": "2025-08-02T12:00:00Z"
  }
}
```

**扫描器状态说明**:
- `ready`: 扫描器就绪，可以执行扫描
- `busy`: 正在执行扫描任务
- `error`: 扫描器故障
- `offline`: 扫描器离线或未连接
- `calibrating`: 正在校准中

**实现伪码**:
```pseudocode
function getQRScannerStatus():
    if (!isQRScannerConnected()):
        return {
            "success": true,
            "data": {
                "scanner_status": "offline",
                "error_message": "QR scanner hardware not connected",
                "timestamp": getCurrentTimestamp()
            }
        }
    
    hardwareInfo = getQRScannerHardwareInfo()
    capabilities = getQRScannerCapabilities()
    settings = getCurrentScannerSettings()
    stats = getScannerStatistics()
    status = getQRScannerCurrentStatus()
    
    data = {
        "scanner_status": status,
        "hardware_info": hardwareInfo,
        "capabilities": capabilities,
        "current_settings": settings,
        "statistics": stats,
        "timestamp": getCurrentTimestamp()
    }
    
    return {
        "success": true,
        "data": data
    }
```

#### C. **配置QR扫描器**
```http
PUT /api/hcm/qr/config
```

**接口说明**: 配置QR扫描器基本参数

**请求体**:
```json
{
  "brightness": 75,
  "contrast": 80,
  "illumination_enabled": true,
  "default_timeout": 30
}
```

**响应格式**:
```json
{
  "success": true,
  "data": {
    "status": "configured",
    "message": "QR scanner configuration updated successfully",
    "applied_settings": {
      "brightness": 75,
      "contrast": 80,
      "illumination_enabled": true,
      "default_timeout": 30
    },
    "timestamp": "2025-08-02T12:00:00Z"
  }
}
```

**实现伪码**:
```pseudocode
function configureQRScanner(configRequest):
    if (!isQRScannerAvailable()):
        return {
            "success": false,
            "data": {
                "status": "error",
                "message": "QR scanner not available for configuration",
                "error_code": "SCANNER_UNAVAILABLE",
                "timestamp": getCurrentTimestamp()
            }
        }
    
    // 验证配置参数
    if (configRequest.brightness < 0 or configRequest.brightness > 100):
        return {
            "success": false,
            "data": {
                "status": "error",
                "message": "Invalid brightness value (0-100)",
                "error_code": "INVALID_CONFIG",
                "timestamp": getCurrentTimestamp()
            }
        }
    
    if (configRequest.contrast < 0 or configRequest.contrast > 100):
        return {
            "success": false,
            "data": {
                "status": "error",
                "message": "Invalid contrast value (0-100)",
                "error_code": "INVALID_CONFIG",
                "timestamp": getCurrentTimestamp()
            }
        }
    
    // 应用配置
    try:
        applyQRScannerConfig(configRequest)
        logInfo("QR scanner configuration updated")
        
        return {
            "success": true,
            "data": {
                "status": "configured",
                "message": "QR scanner configuration updated successfully",
                "applied_settings": configRequest,
                "timestamp": getCurrentTimestamp()
            }
        }
    catch (exception):
        logError("Failed to apply QR scanner configuration: " + exception.message)
        return {
            "success": false,
            "data": {
                "status": "error",
                "message": "Failed to apply configuration: " + exception.message,
                "error_code": "CONFIG_APPLY_FAIL",
                "timestamp": getCurrentTimestamp()
            }
        }
```

### 6. **Vision系统接口**

#### A. **获取RGB视频流**
```http
GET /api/hcm/vision/rgb/stream
```

**接口说明**: 获取Intel RealSense D455 RGB摄像头实时视频流

**响应格式**: MJPEG视频流
```
Content-Type: multipart/x-mixed-replace; boundary=frame
```

**流数据格式**:
```
--frame
Content-Type: image/jpeg
Content-Length: [frame_size]

[JPEG frame data]
--frame
Content-Type: image/jpeg
Content-Length: [frame_size]

[JPEG frame data]
...
```

**错误响应**:
```json
{
  "success": false,
  "data": {
    "status": "error",
    "message": "RGB camera not available",
    "error_code": "CAMERA_RGB_UNAVAILABLE",
    "timestamp": "2025-08-04T12:00:00Z"
  }
}
```

**实现伪码**:
```pseudocode
function getRGBVideoStream():
    if (!isRGBCameraAvailable()):
        return {
            "success": false,
            "data": {
                "status": "error",
                "message": "RGB camera not available",
                "error_code": "CAMERA_RGB_UNAVAILABLE",
                "timestamp": getCurrentTimestamp()
            }
        }
    
    // 启动RealSense RGB流
    try:
        camera = RealSenseCamera()
        camera.enableRGBStream(1920, 1080, 30)  // 1080p@30fps
        
        // 返回MJPEG流生成器
        return generateMJPEGStream(camera.getRGBFrames())
        
    catch (exception):
        logError("RGB camera stream failed: " + exception.message)
        return {
            "success": false,
            "data": {
                "status": "error",
                "message": "Failed to start RGB stream: " + exception.message,
                "error_code": "CAMERA_RGB_START_FAIL",
                "timestamp": getCurrentTimestamp()
            }
        }
```

#### B. **获取深度视频流**
```http
GET /api/hcm/vision/depth/stream
```

**接口说明**: 获取Intel RealSense D455 深度摄像头实时视频流

**响应格式**: 深度数据流（可选格式：深度图像或原始深度数据）

**查询参数**:
- `format`: "image" (深度可视化图像) | "raw" (原始深度数据)，默认"image"
- `colormap`: "jet" | "hot" | "rainbow"，仅format=image时有效

**深度图像流响应**:
```
Content-Type: multipart/x-mixed-replace; boundary=frame
```

**原始深度数据响应**:
```
Content-Type: application/octet-stream
Content-Encoding: gzip
```

**实现伪码**:
```pseudocode
function getDepthVideoStream(format="image", colormap="jet"):
    if (!isDepthCameraAvailable()):
        return {
            "success": false,
            "data": {
                "status": "error",
                "message": "Depth camera not available",
                "error_code": "CAMERA_DEPTH_UNAVAILABLE",
                "timestamp": getCurrentTimestamp()
            }
        }
    
    try:
        camera = RealSenseCamera()
        camera.enableDepthStream(1280, 720, 30)  // 720p@30fps
        
        if (format == "image"):
            // 返回深度可视化图像流
            return generateDepthImageStream(camera.getDepthFrames(), colormap)
        else:
            // 返回原始深度数据流
            return generateRawDepthStream(camera.getDepthFrames())
            
    catch (exception):
        logError("Depth camera stream failed: " + exception.message)
        return {
            "success": false,
            "data": {
                "status": "error", 
                "message": "Failed to start depth stream: " + exception.message,
                "error_code": "CAMERA_DEPTH_START_FAIL",
                "timestamp": getCurrentTimestamp()
            }
        }
```

#### C. **获取全景视频流**
```http
GET /api/hcm/vision/360/stream
```

**接口说明**: 获取Seeker Mini 4-Way Camera 360°全景视频流

**响应格式**: MJPEG视频流
```
Content-Type: multipart/x-mixed-replace; boundary=frame
```

**查询参数**:
- `resolution`: "1080p" | "720p" | "480p"，默认"720p"
- `mode`: "stitched" (拼接全景) | "quad" (四路分屏)，默认"stitched"

**实现伪码**:
```pseudocode
function get360VideoStream(resolution="720p", mode="stitched"):
    if (!is360CameraAvailable()):
        return {
            "success": false,
            "data": {
                "status": "error",
                "message": "360° camera not available", 
                "error_code": "CAMERA_360_UNAVAILABLE",
                "timestamp": getCurrentTimestamp()
            }
        }
    
    try:
        panoramicCamera = SeekerMiniCamera()
        panoramicCamera.enableAllChannels()
        
        if (mode == "stitched"):
            // 返回拼接后的360°全景流
            return generatePanoramicStream(panoramicCamera.getStitchedFrames(), resolution)
        else:
            // 返回四路分屏流
            return generateQuadStream(panoramicCamera.getQuadFrames(), resolution)
            
    catch (exception):
        logError("360° camera stream failed: " + exception.message)
        return {
            "success": false,
            "data": {
                "status": "error",
                "message": "Failed to start 360° stream: " + exception.message,
                "error_code": "CAMERA_360_START_FAIL",
                "timestamp": getCurrentTimestamp()
            }
        }
```

#### D. **图像抓拍**
```http
POST /api/hcm/vision/capture
```

**接口说明**: 从指定摄像头抓拍单帧图像

**请求体**:
```json
{
  "camera_type": "rgb",
  "resolution": "1080p",
  "quality": "high",
  "format": "jpeg"
}
```

**请求参数说明**:
- `camera_type`: "rgb" | "depth" | "360" 
- `resolution`: "1080p" | "720p" | "480p"，可选
- `quality`: "low" | "medium" | "high"，可选
- `format`: "jpeg" | "png" | "base64"，可选

**成功响应格式**:
```json
{
  "success": true,
  "data": {
    "status": "captured",
    "image_data": "base64_encoded_image_data_here",
    "metadata": {
      "camera_type": "rgb",
      "resolution": "1920x1080",
      "format": "jpeg",
      "file_size": 245760,
      "capture_time": "2025-08-04T12:00:00Z",
      "camera_settings": {
        "exposure": "auto",
        "white_balance": "auto",
        "iso": 100
      }
    },
    "timestamp": "2025-08-04T12:00:00Z"
  }
}
```

**实现伪码**:
```pseudocode
function captureImage(request):
    cameraType = request.camera_type
    resolution = request.resolution or "720p"
    quality = request.quality or "medium"
    format = request.format or "jpeg"
    
    // 验证摄像头可用性
    if (!isCameraAvailable(cameraType)):
        return {
            "success": false,
            "data": {
                "status": "error",
                "message": cameraType + " camera not available",
                "error_code": "CAMERA_" + cameraType.toUpperCase() + "_UNAVAILABLE",
                "timestamp": getCurrentTimestamp()
            }
        }
    
    try:
        // 根据摄像头类型抓拍
        if (cameraType == "rgb"):
            camera = RealSenseCamera()
            frame = camera.captureRGBFrame(resolution)
        else if (cameraType == "depth"):
            camera = RealSenseCamera()
            frame = camera.captureDepthFrame(resolution)
        else if (cameraType == "360"):
            camera = SeekerMiniCamera()
            frame = camera.capture360Frame(resolution)
        
        // 编码图像
        encodedImage = encodeImage(frame, format, quality)
        metadata = generateImageMetadata(frame, cameraType, resolution, format)
        
        return {
            "success": true,
            "data": {
                "status": "captured",
                "image_data": encodedImage,
                "metadata": metadata,
                "timestamp": getCurrentTimestamp()
            }
        }
        
    catch (exception):
        logError("Image capture failed: " + exception.message)
        return {
            "success": false,
            "data": {
                "status": "error",
                "message": "Capture failed: " + exception.message,
                "error_code": "CAMERA_CAPTURE_FAIL",
                "timestamp": getCurrentTimestamp()
            }
        }
```

#### E. **获取摄像头状态**
```http
GET /api/hcm/vision/status
```

**接口说明**: 获取所有摄像头的状态和能力信息

**响应格式**:
```json
{
  "success": true,
  "data": {
    "cameras": {
      "rgb": {
        "status": "active",
        "hardware_info": {
          "model": "Intel RealSense D455",
          "serial_number": "936622073175",
          "firmware_version": "5.13.0.50"
        },
        "capabilities": {
          "max_resolution": "1920x1080",
          "supported_formats": ["RGB8", "BGR8", "RGBA8"],
          "frame_rates": [15, 30, 60],
          "auto_exposure": true,
          "auto_white_balance": true
        },
        "current_settings": {
          "resolution": "1920x1080",
          "frame_rate": 30,
          "exposure": "auto",
          "white_balance": "auto"
        },
        "statistics": {
          "frames_captured": 12847,
          "dropped_frames": 23,
          "average_fps": 29.7,
          "last_frame_time": "2025-08-04T11:59:58Z"
        }
      },
      "depth": {
        "status": "active",
        "hardware_info": {
          "model": "Intel RealSense D455",
          "serial_number": "936622073175",
          "firmware_version": "5.13.0.50"
        },
        "capabilities": {
          "max_resolution": "1280x720",
          "depth_range": {"min": 0.1, "max": 10.0},
          "accuracy": 0.02,
          "frame_rates": [15, 30, 60]
        },
        "current_settings": {
          "resolution": "1280x720",
          "frame_rate": 30,
          "depth_units": 0.001
        },
        "statistics": {
          "frames_captured": 12847,
          "dropped_frames": 15,
          "average_fps": 29.8,
          "last_frame_time": "2025-08-04T11:59:58Z"
        }
      },
      "360": {
        "status": "active",
        "hardware_info": {
          "model": "Seeker Mini 4-Way Camera",
          "serial_number": "SMC4W-2024-001",
          "firmware_version": "2.1.0"
        },
        "capabilities": {
          "channels": 4,
          "max_resolution_per_channel": "1920x1080",
          "panoramic_resolution": "3840x1920",
          "stitching_modes": ["auto", "manual"],
          "frame_rates": [15, 30]
        },
        "current_settings": {
          "mode": "panoramic",
          "resolution": "1920x960",
          "frame_rate": 30,
          "stitching": "auto"
        },
        "statistics": {
          "frames_captured": 8563,
          "stitching_errors": 2,
          "average_fps": 29.5,
          "last_frame_time": "2025-08-04T11:59:57Z"
        }
      }
    },
    "system_info": {
      "gpu_usage": 45.2,
      "memory_usage": 68.7,
      "processing_latency": 12.3,
      "total_bandwidth": "850 MB/s"
    },
    "timestamp": "2025-08-04T12:00:00Z"
  }
}
```

**摄像头状态说明**:
- `active`: 摄像头正常工作
- `inactive`: 摄像头已连接但未激活
- `error`: 摄像头故障
- `disconnected`: 摄像头未连接

#### F. **配置摄像头**
```http
PUT /api/hcm/vision/config
```

**接口说明**: 配置摄像头参数

**请求体**:
```json
{
  "camera_type": "rgb",
  "settings": {
    "resolution": "1920x1080",
    "frame_rate": 30,
    "exposure": "auto",
    "white_balance": "auto",
    "brightness": 0,
    "contrast": 0,
    "saturation": 0
  }
}
```

**响应格式**:
```json
{
  "success": true,
  "data": {
    "status": "configured",
    "message": "Camera configuration updated successfully",
    "camera_type": "rgb",
    "applied_settings": {
      "resolution": "1920x1080",
      "frame_rate": 30,
      "exposure": "auto",
      "white_balance": "auto",
      "brightness": 0,
      "contrast": 0,
      "saturation": 0
    },
    "timestamp": "2025-08-04T12:00:00Z"
  }
}
```

---

## 📡 **HCM需要发布的MQTT消息**

### 1. **错误状态上报（robots/{deviceId}/error）**

#### **消息格式（严格按照规范3.3.1）**:
```json
{
  "timestamp": "2025-08-02T12:34:56Z",
  "errorCode": "MOTOR_FAIL",
  "severity": "high",
  "message": "Left motor malfunction detected",
  "taskId": 12345,
  "position": { "x": 1.2921, "y": 103.7764, "z": 15.0 },
  "suggestion": "Check motor connections and restart system",
  "retryable": false
}
```

#### **HCM需要检测和发布的错误码**:

| 错误码 | 触发条件 | 严重级别 | retryable | 检测方法 |
|--------|----------|----------|-----------|----------|
| `LOW_BATTERY` | 电量 < 20% | medium | false | 电池管理系统 |
| `MOTOR_FAIL` | 电机故障 | high | false | 电机反馈信号 |
| `WHEEL_BLOCKED` | 轮子阻塞 | medium | true | 电流异常检测 |
| `ROBOT_TIPPED` | 机器人倾倒 | high | false | IMU传感器 |
| `NETWORK_LOST` | 网络断开 | medium | true | 网络连接监控 |
| `POSITION_LOST` | 定位丢失 | medium | true | 定位系统状态 |
| `ELEVATOR_FAIL` | 电梯交互失败 | medium | true | 电梯通信协议 |
| `DOOR_OPEN_FAIL` | 仓门开启失败 | medium | true | 门锁反馈信号 |
| `DOOR_CLOSE_FAIL` | 仓门关闭失败 | medium | true | 门锁反馈信号 |
| `CARGO_OPERATION_EXCEPTION` | 货仓操作异常 | medium | true | 货仓控制系统 |
| `TAMPER_DETECTED` | 撬动警报 | high | false | 震动/倾斜传感器 |
| `QR_SCANNER_FAIL` | QR扫描器故障 | medium | false | QR扫描器硬件检测 |
| `QR_SCAN_TIMEOUT` | QR扫描超时 | low | true | 扫描任务超时检测 |
| `CAMERA_RGB_FAIL` | RGB摄像头故障 | medium | false | RealSense RGB摄像头检测 |
| `CAMERA_DEPTH_FAIL` | 深度摄像头故障 | medium | false | RealSense深度摄像头检测 |
| `CAMERA_360_FAIL` | 全景摄像头故障 | medium | false | Seeker Mini摄像头检测 |
| `CAMERA_STREAM_FAIL` | 摄像头流中断 | low | true | 视频流状态监控 |

#### **错误检测实现伪码**:
```pseudocode
class ErrorMonitor:
    function __init__():
        this.errorHistory = {}
        this.errorCooldown = 60  // 60秒内同类错误不重复发布
        this.mqttClient = initializeMQTTClient()
    
    function checkBatteryLevel():
        batteryLevel = getBatteryLevel()
        if (batteryLevel < 20):
            this.publishErrorIfNeeded({
                "errorCode": "LOW_BATTERY",
                "severity": "medium",
                "message": "Battery level is " + batteryLevel + "%, below safe threshold",
                "suggestion": "Return to charging station immediately",
                "retryable": false
            })
    
    function checkMotorStatus():
        motorStatus = getMotorDiagnostics()
        if (motorStatus.leftMotorFault):
            this.publishErrorIfNeeded({
                "errorCode": "MOTOR_FAIL",
                "severity": "high",
                "message": "Left motor malfunction detected",
                "suggestion": "Check motor connections and restart system",
                "retryable": false
            })
        if (motorStatus.rightMotorFault):
            this.publishErrorIfNeeded({
                "errorCode": "MOTOR_FAIL",
                "severity": "high",
                "message": "Right motor malfunction detected",
                "suggestion": "Check motor connections and restart system",
                "retryable": false
            })
    
    function checkWheelBlockage():
        if (detectWheelBlockage()):
            this.publishErrorIfNeeded({
                "errorCode": "WHEEL_BLOCKED",
                "severity": "medium",
                "message": "Wheel obstruction detected, unable to move",
                "suggestion": "Clear obstruction and retry movement",
                "retryable": true
            })
    
    function checkRobotOrientation():
        imuData = getIMUData()
        tiltAngle = calculateTiltAngle(imuData)
        if (tiltAngle > 30):  // 倾斜超过30度
            this.publishErrorIfNeeded({
                "errorCode": "ROBOT_TIPPED",
                "severity": "high",
                "message": "Robot has tilted " + tiltAngle + " degrees",
                "suggestion": "Check if robot needs manual recovery",
                "retryable": false
            })
    
    function checkQRScannerStatus():
        if (!isQRScannerConnected()):
            this.publishErrorIfNeeded({
                "errorCode": "QR_SCANNER_FAIL",
                "severity": "medium",
                "message": "QR scanner hardware disconnected or not responding",
                "suggestion": "Check QR scanner hardware connections and restart if necessary",
                "retryable": false
            })
        else if (getQRScannerHealthStatus() == "error"):
            this.publishErrorIfNeeded({
                "errorCode": "QR_SCANNER_FAIL",
                "severity": "medium",
                "message": "QR scanner hardware error detected",
                "suggestion": "Restart QR scanner or check hardware status",
                "retryable": false
            })
    
    function checkQRScanTimeout(scanTaskId, timeoutSeconds):
        // 在扫描任务启动时调用，监控超时
        if (isScanTaskTimedOut(scanTaskId, timeoutSeconds)):
            this.publishErrorIfNeeded({
                "errorCode": "QR_SCAN_TIMEOUT",
                "severity": "low",
                "message": "QR scan operation timed out after " + timeoutSeconds + " seconds",
                "suggestion": "Ensure proper lighting and QR code visibility, then retry",
                "retryable": true
            })
    
    function checkCameraStatus():
        // 检查RGB摄像头状态
        if (!isRGBCameraConnected()):
            this.publishErrorIfNeeded({
                "errorCode": "CAMERA_RGB_FAIL",
                "severity": "medium",
                "message": "RGB camera (RealSense D455) disconnected or not responding",
                "suggestion": "Check RealSense D455 USB connection and restart camera service",
                "retryable": false
            })
        else if (getRGBCameraHealthStatus() == "error"):
            this.publishErrorIfNeeded({
                "errorCode": "CAMERA_RGB_FAIL",
                "severity": "medium", 
                "message": "RGB camera hardware error detected",
                "suggestion": "Restart RealSense service or check camera hardware",
                "retryable": false
            })
        
        // 检查深度摄像头状态
        if (!isDepthCameraConnected()):
            this.publishErrorIfNeeded({
                "errorCode": "CAMERA_DEPTH_FAIL",
                "severity": "medium",
                "message": "Depth camera (RealSense D455) disconnected or not responding", 
                "suggestion": "Check RealSense D455 depth sensor and restart camera service",
                "retryable": false
            })
        
        // 检查360°摄像头状态
        if (!is360CameraConnected()):
            this.publishErrorIfNeeded({
                "errorCode": "CAMERA_360_FAIL",
                "severity": "medium",
                "message": "360° camera (Seeker Mini) disconnected or not responding",
                "suggestion": "Check Seeker Mini 4-Way Camera USB/MIPI connection",
                "retryable": false
            })
    
    function checkCameraStreams():
        // 监控摄像头流状态
        for cameraType in ["rgb", "depth", "360"]:
            streamStatus = getCameraStreamStatus(cameraType)
            if (streamStatus.isActive and streamStatus.framesDropped > 100):
                this.publishErrorIfNeeded({
                    "errorCode": "CAMERA_STREAM_FAIL",
                    "severity": "low",
                    "message": cameraType + " camera stream unstable, dropped " + streamStatus.framesDropped + " frames",
                    "suggestion": "Check camera bandwidth and USB connection quality",
                    "retryable": true
                })
            else if (streamStatus.isActive and streamStatus.fps < expectedFps * 0.8):
                this.publishErrorIfNeeded({
                    "errorCode": "CAMERA_STREAM_FAIL", 
                    "severity": "low",
                    "message": cameraType + " camera FPS degraded to " + streamStatus.fps,
                    "suggestion": "Check system load and camera performance",
                    "retryable": true
                })
    
    function publishErrorIfNeeded(errorData):
        currentTime = getCurrentTimestamp()
        lastTime = this.errorHistory[errorData.errorCode] or 0
        
        if (currentTime - lastTime > this.errorCooldown):
            this.errorHistory[errorData.errorCode] = currentTime
            
            completeErrorData = {
                "timestamp": currentTime,
                "errorCode": errorData.errorCode,
                "severity": errorData.severity,
                "message": errorData.message,
                "taskId": getCurrentTaskId(),
                "position": getCurrentPosition(),
                "suggestion": errorData.suggestion,
                "retryable": errorData.retryable
            }
            
            this.mqttClient.publish(
                "robots/" + DEVICE_ID + "/error",
                JSON.stringify(completeErrorData),
                qos=1,  // 确保送达
                retain=false
            )
```

### 2. **货仓状态上报（robots/{deviceId}/cargo）**

#### **消息格式（严格按照规范3.3.2）**:
```json
{
  "timestamp": "2025-08-02T12:35:10Z",
  "doorStatus": "closed",
  "cargoPresent": true,
  "slots": [
    { "slotId": 1, "occupied": true, "itemId": "SKU12345" },
    { "slotId": 2, "occupied": false },
    { "slotId": 3, "occupied": true, "itemId": "SKU67890" },
    { "slotId": 4, "occupied": false },
    { "slotId": 5, "occupied": false },
    { "slotId": 6, "occupied": false }
  ],
  "temperature": 24.5,
  "humidity": 60,
  "tamperAlert": false,
  "lastAccessMethod": "robot_init",
  "taskId": 12345
}
```

#### **货仓状态字段实现说明**:

| 字段 | 数据来源 | 实现方式 | 伪码示例 |
|------|----------|----------|----------|
| `doorStatus` | 门锁传感器 | 磁性传感器/编码器 | `getDoorStatus()` |
| `cargoPresent` | 重量传感器 | 总重量变化检测 | `getTotalWeight() > emptyWeight` |
| `slots` | 仓位传感器 | 每仓位重量/光电传感器 | `getSlotStatus(slotId)` |
| `temperature` | 温度传感器 | DS18B20等 | `readTemperatureSensor()` |
| `humidity` | 湿度传感器 | DHT22等 | `readHumiditySensor()` |
| `tamperAlert` | 震动传感器 | 异常震动检测 | `detectTamperAlert()` |

#### **货仓状态监控实现伪码**:
```pseudocode
class CargoMonitor:
    function __init__():
        this.mqttClient = initializeMQTTClient()
        this.emptyWeightThreshold = 50  // 50g以上认为有货物
        this.slotCount = 6
        this.publishInterval = 30  // 30秒定期发布
        
    function getCargoStatus():
        return {
            "timestamp": getCurrentTimestamp(),
            "doorStatus": this.getDoorStatus(),
            "cargoPresent": this.detectCargoPresence(),
            "slots": this.getAllSlotStatus(),
            "temperature": this.readTemperatureSensor(),
            "humidity": this.readHumiditySensor(),
            "tamperAlert": this.checkTamperDetection(),
            "lastAccessMethod": this.getLastAccessMethod(),
            "taskId": getCurrentTaskId()
        }
    
    function getDoorStatus():
        // 读取门锁传感器状态
        doorSensor = readDoorSensor()
        if (doorSensor.isLocked):
            return "locked"
        else if (doorSensor.isOpen):
            return "open"
        else:
            return "closed"
    
    function detectCargoPresence():
        totalWeight = 0
        for (i = 1; i <= this.slotCount; i++):
            slotWeight = readSlotWeight(i)
            totalWeight += slotWeight
        
        return totalWeight > this.emptyWeightThreshold
    
    function getAllSlotStatus():
        slots = []
        for (i = 1; i <= this.slotCount; i++):
            slotWeight = readSlotWeight(i)
            occupied = slotWeight > this.emptyWeightThreshold
            
            slotData = {
                "slotId": i,
                "occupied": occupied
            }
            
            if (occupied):
                slotData["itemId"] = getItemIdForSlot(i)
            
            slots.append(slotData)
        
        return slots
    
    function readTemperatureSensor():
        // 读取温度传感器
        return readSensorValue("temperature")
    
    function readHumiditySensor():
        // 读取湿度传感器  
        return readSensorValue("humidity")
    
    function checkTamperDetection():
        // 检测异常震动或撬动
        vibrationLevel = readVibrationSensor()
        return vibrationLevel > tamperThreshold
    
    function getLastAccessMethod():
        // 从日志或状态中获取最后访问方式
        return getStoredLastAccessMethod()
    
    function publishCargoStatus():
        cargoStatus = this.getCargoStatus()
        this.mqttClient.publish(
            "robots/" + DEVICE_ID + "/cargo",
            JSON.stringify(cargoStatus),
            qos=0,  // 尽力而为
            retain=false
        )
    
    function startPeriodicPublishing():
        // 定期发布货仓状态
        while (true):
            this.publishCargoStatus()
            sleep(this.publishInterval)
    
    function publishOnStateChange():
        // 状态变化时立即发布
        previousState = this.lastCargoState
        currentState = this.getCargoStatus()
        
        if (hasSignificantChange(previousState, currentState)):
            this.publishCargoStatus()
            this.lastCargoState = currentState
```

---

## ⚙️ **HCM实现配置规范**

### 1. **API服务配置**
```yaml
# HCM配置示例 - 与CM系统兼容的配置结构
hardware:
  hcm_api:
    base_url: "http://localhost:8080"  # HCM API基础URL
    timeout: 30                       # 请求超时(秒)
    retry_attempts: 3                 # 重试次数
    retry_interval: 1                 # 重试间隔(秒)
    endpoints:                        # API端点配置
      status: "/api/hcm/status"
      position: "/api/hcm/position"
      battery: "/api/hcm/battery"
      move: "/api/hcm/move"
      stop: "/api/hcm/stop"
      health: "/api/hcm/health"
      cargo_open: "/api/hcm/cargo/open"
      cargo_close: "/api/hcm/cargo/close"
      cargo_status: "/api/hcm/cargo/status"
      qr_scan: "/api/hcm/qr/scan"
      qr_status: "/api/hcm/qr/status"
      qr_config: "/api/hcm/qr/config"
      vision_rgb_stream: "/api/hcm/vision/rgb/stream"
      vision_depth_stream: "/api/hcm/vision/depth/stream"
      vision_360_stream: "/api/hcm/vision/360/stream"
      vision_capture: "/api/hcm/vision/capture"
      vision_status: "/api/hcm/vision/status"
      vision_config: "/api/hcm/vision/config"

# HCM内部服务配置
hcm:
  api:
    host: "0.0.0.0"           # 监听所有接口
    port: 8080                # 标准端口
    timeout: 30               # 请求超时(秒)
    max_connections: 10       # 最大并发连接数
    
  sensors:
    position:
      update_interval: 0.5    # 位置更新间隔(秒)
      accuracy_threshold: 1.0 # 精度阈值(米)
    battery:
      update_interval: 5.0    # 电池状态更新间隔(秒)
      low_threshold: 20       # 低电量阈值(%)
      critical_threshold: 10  # 严重低电量阈值(%)
    cargo:
      update_interval: 1.0    # 货仓状态更新间隔(秒)
      weight_threshold: 50    # 货物检测阈值(g)
      tamper_threshold: 5.0   # 撬动检测阈值
    qr_scanner:
      health_check_interval: 10.0  # QR扫描器健康检查间隔(秒)
      default_timeout: 30          # 默认扫描超时时间(秒)
      default_brightness: 75       # 默认亮度(0-100)
      default_contrast: 80         # 默认对比度(0-100)
      illumination_enabled: true   # 自动照明开关
      retry_attempts: 3            # 连接重试次数
      retry_interval: 2            # 重试间隔(秒)
    vision:
      health_check_interval: 5.0   # 摄像头健康检查间隔(秒)
      stream_quality_monitor: true # 流质量监控开关
      frame_drop_threshold: 100    # 丢帧报警阈值
      fps_degradation_threshold: 0.8  # FPS下降报警阈值(相对于期望FPS)
      auto_restart_on_fail: true   # 摄像头故障时自动重启
      cameras:
        rgb:
          default_resolution: "1920x1080"  # 默认分辨率
          default_fps: 30                  # 默认帧率
          auto_exposure: true              # 自动曝光
          auto_white_balance: true         # 自动白平衡
        depth:
          default_resolution: "1280x720"   # 默认分辨率
          default_fps: 30                  # 默认帧率
          depth_units: 0.001               # 深度单位(米)
        panoramic:
          default_resolution: "1920x960"   # 默认分辨率
          default_fps: 30                  # 默认帧率
          stitching_mode: "auto"           # 拼接模式
      
  mqtt:
    broker:
      host: "mqtt.example.com"
      port: 1883
      username: "${DEVICE_ID}"
      password: "${DEVICE_TOKEN}"
      keep_alive: 60
    publishing:
      error_qos: 1            # 错误消息QoS
      cargo_qos: 0            # 货仓状态QoS  
      error_retain: false     # 错误消息不保留
      cargo_retain: false     # 货仓状态不保留
    topics:
      error: "robots/${DEVICE_ID}/error"
      cargo: "robots/${DEVICE_ID}/cargo"
      connection: "robots/${DEVICE_ID}/connection"
```

### 2. **发布频率和策略**

| 消息类型 | 发布频率 | 触发条件 | QoS | 实现伪码 |
|---------|----------|----------|-----|----------|
| Error消息 | 即时 | 检测到错误时立即发布 | 1 | `publishErrorIfNeeded()` |
| Cargo状态 | 30秒定期 + 状态变化时 | 定期或状态改变 | 0 | `publishCargoStatus()` |
| Connection | 启动时 + 异常时 | 连接状态变化 | 1 | `publishConnectionStatus()` |

### 3. **错误处理和重试机制**

```pseudocode
class HCMErrorHandler:
    function handleAPIError(request, error):
        logError("API Error", request, error)
        
        response = {
            "success": false,
            "data": {
                "status": "error",
                "message": error.message,
                "error_code": error.code,
                "timestamp": getCurrentTimestamp()
            }
        }
        
        // 发布系统错误到MQTT
        if (error.isCritical):
            this.publishSystemError(error)
            
        return response
    
    function handleMQTTPublishFailure(topic, message, error):
        logError("MQTT Publish Failed", topic, error)
        
        // 重试机制
        retryCount = 0
        maxRetries = 3
        
        while (retryCount < maxRetries):
            sleep(2^retryCount)  // 指数退避
            try:
                this.mqttClient.publish(topic, message)
                break
            catch (retryError):
                retryCount++
                if (retryCount >= maxRetries):
                    // 存储到本地队列，待网络恢复后重发
                    this.storeFailedMessage(topic, message)
```

---

## 🔄 **HCM与CM交互流程**

### 1. **系统启动流程**
```pseudocode
function startHCMSystem():
    // 1. 初始化硬件组件
    initializeHardware()
    
    // 2. 启动API服务
    startAPIServer("0.0.0.0", 8080)
    
    // 3. 连接MQTT Broker
    connectMQTTBroker()
    
    // 4. 发布上线消息
    publishConnectionStatus("online", "startup")
    
    // 5. 启动监控线程
    startErrorMonitoring()
    startCargoMonitoring()
    
    // 6. 系统就绪
    logInfo("HCM System Ready")
```

### 2. **正常运行流程**
```
1. HCM启动API服务监听端口8080
2. CM定期调用GET /api/hcm/status获取硬件状态  
3. HCM后台监控线程检测错误并发布到MQTT
4. HCM后台线程定期发布货仓状态到MQTT
5. CM调用POST /api/hcm/move发送移动命令
6. HCM执行移动并更新状态
```

### 3. **错误处理流程**
```
1. HCM检测到硬件错误
2. HCM立即发布错误消息到robots/{deviceId}/error
3. HCM在/api/hcm/status响应中设置fault=true
4. CM轮询获取状态，发现fault=true
5. CM在状态合成时包含fault状态并发布到MQTT
6. 后台系统收到故障信息并触发告警
```

---

## 📋 **实施检查清单**

### **REST API接口实现**
- [ ] `GET /api/hcm/status` - 完整硬件状态
- [ ] `GET /api/hcm/position` - 位置信息
- [ ] `GET /api/hcm/battery` - 电池状态  
- [ ] `POST /api/hcm/move` - 移动控制
- [ ] `POST /api/hcm/stop` - 停止移动
- [ ] `GET /api/hcm/health` - 健康检查
- [ ] `POST /api/hcm/cargo/open` - 开启货仓
- [ ] `POST /api/hcm/cargo/close` - 关闭货仓
- [ ] `GET /api/hcm/cargo/status` - 查询货仓状态
- [ ] `POST /api/hcm/qr/scan` - QR扫描触发
- [ ] `GET /api/hcm/qr/status` - QR扫描器状态
- [ ] `PUT /api/hcm/qr/config` - QR扫描器配置
- [ ] `GET /api/hcm/vision/rgb/stream` - RGB视频流
- [ ] `GET /api/hcm/vision/depth/stream` - 深度视频流  
- [ ] `GET /api/hcm/vision/360/stream` - 360°全景视频流
- [ ] `POST /api/hcm/vision/capture` - 图像抓拍
- [ ] `GET /api/hcm/vision/status` - 摄像头状态查询
- [ ] `PUT /api/hcm/vision/config` - 摄像头配置

### **MQTT消息发布**
- [ ] `robots/{deviceId}/error` - 错误状态上报
- [ ] `robots/{deviceId}/cargo` - 货仓状态上报
- [ ] `robots/{deviceId}/connection` - 连接状态上报

### **错误检测实现**
- [ ] `LOW_BATTERY` - 电池电量监控
- [ ] `MOTOR_FAIL` - 电机故障检测
- [ ] `WHEEL_BLOCKED` - 轮子阻塞检测
- [ ] `ROBOT_TIPPED` - 倾倒检测
- [ ] `NETWORK_LOST` - 网络连接监控
- [ ] `POSITION_LOST` - 定位信号监控
- [ ] `ELEVATOR_FAIL` - 电梯交互监控
- [ ] `DOOR_OPEN_FAIL` - 仓门开启操作监控
- [ ] `DOOR_CLOSE_FAIL` - 仓门关闭操作监控
- [ ] `CARGO_OPERATION_EXCEPTION` - 货仓操作异常监控
- [ ] `TAMPER_DETECTED` - 撬动检测
- [ ] `QR_SCANNER_FAIL` - QR扫描器故障检测
- [ ] `QR_SCAN_TIMEOUT` - QR扫描超时检测
- [ ] `CAMERA_RGB_FAIL` - RGB摄像头故障检测
- [ ] `CAMERA_DEPTH_FAIL` - 深度摄像头故障检测
- [ ] `CAMERA_360_FAIL` - 全景摄像头故障检测
- [ ] `CAMERA_STREAM_FAIL` - 摄像头流状态监控

### **QR扫描功能实现**
- [ ] QR扫描器硬件连接和初始化
- [ ] QR码内容扫描和读取功能
- [ ] 扫描超时处理机制
- [ ] 扫描器状态监控和错误检测
- [ ] 扫描器基本配置参数管理(亮度、对比度等)
- [ ] 扫描结果质量评估
- [ ] 与CM的扫描请求/响应接口对接

### **Vision系统功能实现**
- [ ] Intel RealSense D455 RGB摄像头驱动集成
- [ ] Intel RealSense D455 深度摄像头驱动集成
- [ ] Seeker Mini 4-Way Camera 360°摄像头驱动集成
- [ ] MJPEG视频流编码和传输
- [ ] 深度数据可视化和原始数据传输
- [ ] 360°全景图像拼接和四路分屏模式
- [ ] 多摄像头同步和时间戳管理
- [ ] 图像抓拍和格式转换(JPEG/PNG/Base64)
- [ ] 摄像头参数配置(分辨率、帧率、曝光等)
- [ ] 视频流质量监控和性能统计
- [ ] GPU加速的图像处理和AI推理集成
- [ ] 摄像头故障检测和自动恢复机制

### **货仓状态监控**
- [ ] 门锁状态检测
- [ ] 货物存在检测
- [ ] 各仓位占用状态
- [ ] 温湿度监控
- [ ] 撬动警报检测

### **系统集成测试**
- [ ] CM-HCM REST API通信测试
- [ ] MQTT消息发布测试
- [ ] 错误检测和上报测试
- [ ] 货仓状态监控测试
- [ ] 故障恢复和重试测试

---

## 📞 **技术支持**

**文档作者**: IBC-AI Co.  
**文档维护**: 通讯模块CM开发团队  
**集成支持**: robot_comm_spec_zh.md规范  
**版本管理**: 与CM v2.0.0兼容

本规范为HCM开发提供完整的接口定义和实现指导，确保与CM的无缝集成和robot_comm_spec_zh.md规范的严格遵循。
