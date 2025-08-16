#!/usr/bin/env python3
import argparse
import asyncio
import jwt
from some_module import get_access_token, build_action_call

def build_action_call(bid: str, gid: str, action_id: int, deck: str, served_area: str, area: int) -> dict:
    payload = {
        "building_id": bid,
        "group_id": gid,
        "action_id": action_id,
        "deck": deck,
        "served_area": served_area,
        "area": area,
    }
    return payload

async def run(args):
    # Other code omitted for brevity

    # Token acquisition loop
    last_error = None
    for scope in possible_scopes:
        try:
            token = get_access_token(scope=scope)
            if not token:
                continue
            try:
                decoded = jwt.decode(token, options={"verify_signature": False})
                token_scopes = decoded.get("scope") or ""
                print("🔎 Token scopes:", token_scopes)
                match = scope in token_scopes
                validation_info = {
                    "requested_scope": scope,
                    "token_scopes": token_scopes,
                    "match": match,
                    "error": None if match else f"Token missing required scope {scope}"
                }
                if not match:
                    print(f"⚠️ Got token but scope mismatch (requested {scope}) – trying next")
                    continue
                print(f"✅ Using scope: {scope}")
                break
            except Exception as e:
                # If we cannot decode the token, proceed with this token but flag unknown scope
                print("⚠️ Could not decode token:", e)
                validation_info = {
                    "requested_scope": scope,
                    "token_scopes": "<unknown>",
                    "match": False,
                    "error": "Could not decode token to verify scopes"
                }
                # proceed with this token
                break
        except Exception as e:
            last_error = e

    # Other code omitted for brevity

    # Build messages for test cases 6-8
    for aid in [6,7,8]:
        msg = build_action_call(args.building, args.group, aid, args.deck, args.served_area, args.area)
        # send or process msg

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--building", required=True)
    p.add_argument("--group", required=True)
    p.add_argument("--deck", required=True)
    p.add_argument("--served-area", required=True)
    p.add_argument("--area", type=int, default=1000, help="Area ID for action calls (required for tests 6–8)")
    args = p.parse_args()

    asyncio.run(run(args))
