import pytest
import requests
import asyncio

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_initialization():
    response = requests.get(f"{BASE_URL}/api/elevator/initialize?elevator_type=kone")
    assert response.status_code == 200
    assert response.json()['success'] is True
    assert 'session_id' in response.json()

@pytest.mark.asyncio
async def test_basic_call():
    payload = {"building_id": "building:9990000951", "source": 3000, "destination": 5000}
    response = requests.post(f"{BASE_URL}/api/elevator/call?elevator_type=kone", json=payload)
    assert response.status_code == 200
    assert response.json()['success'] is True
    assert 'session_id' in response.json()

@pytest.mark.asyncio
async def test_invalid_delay():
    payload = {"building_id": "building:9990000951", "source": 3000, "destination": 5000, "delay": 40}
    response = requests.post(f"{BASE_URL}/api/elevator/call?elevator_type=kone", json=payload)
    assert response.status_code == 200
    assert response.json()['success'] is False
    assert 'Invalid json payload' in response.json()['error']

@pytest.mark.asyncio
async def test_cancel():
    response = requests.post(f"{BASE_URL}/api/elevator/cancel?building_id=building:9990000951&session_id=sim_ses_12345&elevator_type=kone")
    assert response.status_code == 200
    assert response.json()['success'] is True
    assert 'Call cancelled' in response.json()['message']