from fastapi import FastAPI, Query
from drivers import ElevatorDriver, KoneDriver, ElevatorCallRequest
import logging

app = FastAPI(title="Elevator Control API")
logging.basicConfig(filename='elevator.log', level=logging.INFO)

drivers = {
    'kone': KoneDriver(client_id='your_client_id', client_secret='your_client_secret')
}

@app.post("/api/elevator/call")
async def elevator_call(request: ElevatorCallRequest, elevator_type: str = Query('kone')):
    driver: ElevatorDriver = drivers.get(elevator_type.lower())
    if not driver:
        logging.error(f"Unsupported elevator type: {elevator_type}")
        return {'success': False, 'error': 'Unsupported elevator type'}
    result = await driver.call(request)
    logging.info(f"Call: {request.dict()} -> {result}")
    return result

@app.post("/api/elevator/cancel")
async def elevator_cancel(building_id: str, session_id: str, elevator_type: str = Query('kone')):
    driver = drivers.get(elevator_type.lower())
    if not driver:
        logging.error(f"Unsupported elevator type: {elevator_type}")
        return {'success': False, 'error': 'Unsupported elevator type'}
    result = await driver.cancel(building_id, session_id)
    logging.info(f"Cancel: {building_id}, {session_id} -> {result}")
    return result

@app.get("/api/elevator/mode")
async def elevator_mode(building_id: str, elevator_id: str, elevator_type: str = Query('kone')):
    driver = drivers.get(elevator_type.lower())
    if not driver:
        logging.error(f"Unsupported elevator type: {elevator_type}")
        return {'success': False, 'error': 'Unsupported elevator type'}
    result = await driver.get_mode(building_id, elevator_id)
    logging.info(f"Mode: {building_id}, {elevator_id} -> {result}")
    return result

@app.get("/api/elevator/initialize")
async def elevator_initialize(elevator_type: str = Query('kone')):
    driver: ElevatorDriver = drivers.get(elevator_type.lower())
    if not driver:
        logging.error(f"Unsupported elevator type: {elevator_type}")
        return {'success': False, 'error': 'Unsupported elevator type'}
    result = await driver.initialize()
    logging.info(f"Initialize: {result}")
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)