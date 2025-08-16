import asyncio

async def run(args):
    # ... other code ...
    print("🔎 Token scopes:", decoded.get("scope"))
    
    validation_info = {
        "requested_scope": scope,
        "token_scopes": decoded.get("scope"),
        "match": scope in (decoded.get("scope") or ""),
        "error": None if scope in (decoded.get("scope") or "") else f"Token missing required scope {scope}"
    }
    print("🔐 Scope validation:", validation_info)
    
    # ... other code ...
    raw = await asyncio.wait_for(ws.recv(), timeout=12)
    print("📋 Scope validation summary:", validation_info)
    print("✅ first response:", raw)
    # ... other code ...
