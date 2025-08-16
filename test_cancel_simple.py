#!/usr/bin/env python3
"""
Simple test for cancel call functionality
"""

import asyncio
import json
import yaml
from drivers import KoneDriverV2

async def test_cancel_call():
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    client_id = config['kone']['client_id']
    client_secret = config['kone']['client_secret']
    
    driver = KoneDriverV2(client_id, client_secret)
    
    try:
        # Test cancel with a dummy session_id (should return 404)
        print("❌ Testing cancel call with dummy session_id...")
        session_id = 123  # dummy session ID
        cancel_resp = await driver.delete_call(
            "building:4TFxWRCv23D", str(session_id), "1"
        )
        print(f"🚫 Cancel response: {json.dumps(cancel_resp, indent=2)}")
        
        if cancel_resp.get('statusCode') == 404:
            print("✅ Cancel API working correctly (404 for non-existent session)")
        elif cancel_resp.get('statusCode') in [200, 201, 202]:
            print("✅ Cancel API accepts the request")
        elif cancel_resp.get('statusCode') == 400:
            print("⚠️ Cancel API payload validation error (400)")
        else:
            print(f"❌ Cancel API response unexpected: {cancel_resp.get('statusCode')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            await driver.close()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_cancel_call())
