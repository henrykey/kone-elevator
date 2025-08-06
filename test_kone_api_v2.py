import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from drivers import KoneDriver, ElevatorCallRequest, ElevatorDriverFactory
from app import app
from fastapi.testclient import TestClient

# 测试客户端
client = TestClient(app)

class TestKoneDriver:
    """KONE驱动测试类"""
    
    @pytest.fixture
    def kone_driver(self):
        """创建KONE驱动实例"""
        return KoneDriver(
            client_id="test_client_id",
            client_secret="test_client_secret"
        )
    
    @pytest.mark.asyncio
    async def test_token_acquisition(self, kone_driver):
        """测试OAuth token获取"""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "access_token": "test_token_123",
                "expires_in": 3600,
                "token_type": "Bearer"
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            token = await kone_driver.get_access_token()
            
            assert token == "test_token_123"
            assert kone_driver.access_token == "test_token_123"
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, kone_driver):
        """测试WebSocket连接"""
        with patch('websockets.connect') as mock_connect:
            mock_ws = AsyncMock()
            mock_connect.return_value = mock_ws
            mock_ws.closed = False
            
            with patch.object(kone_driver, 'get_access_token', return_value="test_token"):
                result = await kone_driver._connect_websocket()
                
                assert result is True
                assert kone_driver.websocket == mock_ws
                mock_connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_session_creation(self, kone_driver):
        """测试会话创建"""
        with patch.object(kone_driver, '_connect_websocket', return_value=True):
            with patch.object(kone_driver, '_send_message') as mock_send:
                mock_send.return_value = {
                    "status": 201,
                    "sessionId": "test_session_123",
                    "message": "Session created"
                }
                
                result = await kone_driver.initialize()
                
                assert result['success'] is True
                assert result['status_code'] == 201
                assert result['session_id'] == "test_session_123"
                assert kone_driver.session_id == "test_session_123"

class TestElevatorAPI:
    """电梯API测试类"""
    
    def test_root_endpoint(self):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == "Elevator Control API v2.0"
        assert 'endpoints' in data
    
    def test_status_endpoint(self):
        """测试状态端点"""
        response = client.get("/api/elevator/status")
        assert response.status_code == 200
        data = response.json()
        assert 'available_types' in data
    
    def test_call_validation_same_floor(self):
        """测试同楼层呼叫验证"""
        call_data = {
            "building_id": "building:9990000951",
            "source": 3000,
            "destination": 3000,  # 相同楼层
            "action_id": 2,
            "group_id": "1"
        }
        
        response = client.post("/api/elevator/call?elevator_type=kone", json=call_data)
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'SAME_SOURCE_AND_DEST_FLOOR' in data['error']
    
    def test_call_validation_invalid_delay(self):
        """测试无效延迟验证"""
        call_data = {
            "building_id": "building:9990000951",
            "source": 3000,
            "destination": 5000,
            "delay": 60,  # 超过30秒限制
            "action_id": 2,
            "group_id": "1"
        }
        
        response = client.post("/api/elevator/call?elevator_type=kone", json=call_data)
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'Invalid delay' in data['error']

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
