from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.responses import JSONResponse
from drivers import ElevatorDriver, ElevatorDriverFactory, ElevatorCallRequest
import logging
import yaml
from typing import Dict, Optional

# 配置日志
logging.basicConfig(
    filename='elevator.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载配置
def load_config():
    try:
        with open('config.yaml', 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}

config = load_config()
api_config = config.get('api', {})

app = FastAPI(
    title=api_config.get('title', 'Elevator Control API v2.0'),
    description=api_config.get('description', 'WebSocket-based elevator control service following KONE SR-API v2.0'),
    version="2.0.0"
)

# 初始化驱动
drivers: Dict[str, ElevatorDriver] = ElevatorDriverFactory.create_from_config()

def get_driver(elevator_type: str = Query('kone', description="Elevator type")) -> ElevatorDriver:
    """获取电梯驱动依赖"""
    driver = drivers.get(elevator_type.lower())
    if not driver:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported elevator type: {elevator_type}. Available types: {list(drivers.keys())}"
        )
    return driver

@app.get("/")
async def root():
    """根端点，返回API信息"""
    return {
        "name": "Elevator Control API v2.0",
        "version": "2.0.0",
        "description": "WebSocket-based elevator control service following KONE SR-API v2.0",
        "supported_types": list(drivers.keys()),
        "endpoints": {
            "initialize": "/api/elevator/initialize",
            "call": "/api/elevator/call",
            "cancel": "/api/elevator/cancel",
            "mode": "/api/elevator/mode",
            "config": "/api/elevator/config",
            "ping": "/api/elevator/ping"
        }
    }

@app.get("/api/elevator/initialize")
async def elevator_initialize(driver: ElevatorDriver = Depends(get_driver)):
    """初始化电梯连接和会话"""
    try:
        result = await driver.initialize()
        
        if result['success']:
            logger.info(f"Initialize successful: {result}")
            return JSONResponse(
                status_code=result.get('status_code', 200),
                content=result
            )
        else:
            logger.error(f"Initialize failed: {result}")
            return JSONResponse(
                status_code=result.get('status_code', 500),
                content=result
            )
            
    except Exception as e:
        error_result = {
            'success': False,
            'status_code': 500,
            'error': f'Initialize failed: {str(e)}'
        }
        logger.error(f"Initialize error: {error_result}")
        return JSONResponse(status_code=500, content=error_result)

@app.post("/api/elevator/call")
async def elevator_call(
    request: ElevatorCallRequest,
    driver: ElevatorDriver = Depends(get_driver)
):
    """发起电梯呼叫"""
    try:
        # 验证请求参数
        if request.source == request.destination:
            error_result = {
                'success': False,
                'status_code': 400,
                'error': 'SAME_SOURCE_AND_DEST_FLOOR'
            }
            logger.error(f"Call validation failed: {error_result}")
            return JSONResponse(status_code=400, content=error_result)
        
        if request.delay > 30:
            error_result = {
                'success': False,
                'status_code': 400,
                'error': 'Invalid delay: maximum 30 seconds allowed'
            }
            logger.error(f"Call validation failed: {error_result}")
            return JSONResponse(status_code=400, content=error_result)
        
        result = await driver.call(request)
        
        if result['success']:
            logger.info(f"Call successful: {request.dict()} -> {result}")
            return JSONResponse(
                status_code=result.get('status_code', 200),
                content=result
            )
        else:
            logger.error(f"Call failed: {result}")
            return JSONResponse(
                status_code=result.get('status_code', 500),
                content=result
            )
            
    except Exception as e:
        error_result = {
            'success': False,
            'status_code': 500,
            'error': f'Call failed: {str(e)}'
        }
        logger.error(f"Call error: {error_result}")
        return JSONResponse(status_code=500, content=error_result)

@app.post("/api/elevator/cancel")
async def elevator_cancel(
    building_id: str = Query(..., description="Building ID"),
    request_id: str = Query(..., description="Request ID to cancel"),
    driver: ElevatorDriver = Depends(get_driver)
):
    """取消电梯呼叫"""
    try:
        result = await driver.cancel(building_id, request_id)
        
        if result['success']:
            logger.info(f"Cancel successful: {building_id}, {request_id} -> {result}")
            return JSONResponse(
                status_code=result.get('status_code', 200),
                content=result
            )
        else:
            logger.error(f"Cancel failed: {result}")
            return JSONResponse(
                status_code=result.get('status_code', 500),
                content=result
            )
            
    except Exception as e:
        error_result = {
            'success': False,
            'status_code': 500,
            'error': f'Cancel failed: {str(e)}'
        }
        logger.error(f"Cancel error: {error_result}")
        return JSONResponse(status_code=500, content=error_result)

@app.get("/api/elevator/mode")
async def elevator_mode(
    building_id: str = Query(..., description="Building ID"),
    group_id: str = Query("1", description="Group ID"),
    driver: ElevatorDriver = Depends(get_driver)
):
    """获取电梯模式/状态"""
    try:
        result = await driver.get_mode(building_id, group_id)
        
        if result['success']:
            logger.info(f"Mode check successful: {building_id}, {group_id} -> {result}")
            return JSONResponse(
                status_code=result.get('status_code', 200),
                content=result
            )
        else:
            logger.error(f"Mode check failed: {result}")
            return JSONResponse(
                status_code=result.get('status_code', 500),
                content=result
            )
            
    except Exception as e:
        error_result = {
            'success': False,
            'status_code': 500,
            'error': f'Mode check failed: {str(e)}'
        }
        logger.error(f"Mode check error: {error_result}")
        return JSONResponse(status_code=500, content=error_result)

@app.get("/api/elevator/config")
async def elevator_config(
    building_id: str = Query(..., description="Building ID"),
    driver: ElevatorDriver = Depends(get_driver)
):
    """获取建筑配置"""
    try:
        result = await driver.get_config(building_id)
        
        if result['success']:
            logger.info(f"Config retrieval successful: {building_id}")
            return JSONResponse(
                status_code=result.get('status_code', 200),
                content=result
            )
        else:
            logger.error(f"Config retrieval failed: {result}")
            return JSONResponse(
                status_code=result.get('status_code', 500),
                content=result
            )
            
    except Exception as e:
        error_result = {
            'success': False,
            'status_code': 500,
            'error': f'Config retrieval failed: {str(e)}'
        }
        logger.error(f"Config error: {error_result}")
        return JSONResponse(status_code=500, content=error_result)

@app.get("/api/elevator/ping")
async def elevator_ping(
    building_id: str = Query(..., description="Building ID"),
    driver: ElevatorDriver = Depends(get_driver)
):
    """Ping建筑以检查连接性"""
    try:
        result = await driver.ping(building_id)
        
        if result['success']:
            logger.info(f"Ping successful: {building_id}, latency: {result.get('latency_ms')}ms")
            return JSONResponse(
                status_code=result.get('status_code', 200),
                content=result
            )
        else:
            logger.error(f"Ping failed: {result}")
            return JSONResponse(
                status_code=result.get('status_code', 500),
                content=result
            )
            
    except Exception as e:
        error_result = {
            'success': False,
            'status_code': 500,
            'error': f'Ping failed: {str(e)}'
        }
        logger.error(f"Ping error: {error_result}")
        return JSONResponse(status_code=500, content=error_result)

@app.get("/api/elevator/status")
async def get_available_types():
    """获取可用的电梯类型和状态"""
    status = {}
    for elevator_type, driver in drivers.items():
        try:
            # 尝试检查连接状态
            status[elevator_type] = {
                "available": True,
                "type": type(driver).__name__
            }
        except Exception as e:
            status[elevator_type] = {
                "available": False,
                "error": str(e)
            }
    
    return {
        "available_types": status,
        "default_type": config.get('default_elevator_type', 'kone')
    }

# 优雅关闭处理
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    logger.info("Shutting down elevator control service...")
    for elevator_type, driver in drivers.items():
        try:
            if hasattr(driver, 'close'):
                await driver.close()
            logger.info(f"Closed {elevator_type} driver")
        except Exception as e:
            logger.error(f"Error closing {elevator_type} driver: {e}")

if __name__ == "__main__":
    import uvicorn
    
    host = api_config.get('host', '0.0.0.0')
    port = api_config.get('port', 8000)
    
    logger.info(f"Starting Elevator Control API v2.0 on {host}:{port}")
    uvicorn.run(app, host=host, port=port)