
# -*- coding: utf-8 -*-
# Minimal SR-API Validation: Tests 1–3 (Token + Resources + Monitoring)
# Usage:
#   python3 test_t1_t3_runner.py --building 4TFxWRCv23D --group 1
# Requires: config.yaml with client_id/client_secret/token_endpoint/ws_endpoint

import argparse
import asyncio
import base64
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import aiohttp
import websockets
import yaml

CONFIG_PATH = Path("config.yaml")

def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError("config.yaml not found next to the runner.")
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    kone = cfg.get("kone", cfg)
    return {
        "client_id": kone["client_id"],
        "client_secret": kone["client_secret"],
        "token_endpoint": kone.get("token_endpoint", "https://dev.kone.com/api/v2/oauth2/token"),
        "ws_endpoint": kone.get("ws_endpoint", "wss://dev.kone.com/stream-v2"),
    }

def now_iso():
    return datetime.now(timezone.utc).isoformat()

class TokenError(Exception):
    pass

class TokenManager:
    def __init__(self, client_id: str, client_secret: str, token_endpoint: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_endpoint = token_endpoint
        self.cache: Dict[str, Dict[str, Any]] = {}

    def _valid(self, tok: Dict[str, Any]) -> bool:
        if not tok: return False
        exp = tok.get("expires_at")
        if not exp: return False
        try:
            dt = datetime.fromisoformat(exp)
        except Exception:
            return False
        return (dt - datetime.utcnow()) > timedelta(seconds=60)

    async def _fetch(self, scope: str) -> Dict[str, Any]:
        basic = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        headers = {"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "client_credentials", "scope": scope}
        async with aiohttp.ClientSession() as s:
            async with s.post(self.token_endpoint, headers=headers, data=data) as r:
                txt = await r.text()
                if r.status != 200:
                    raise TokenError(f"Token fetch failed {r.status}: {txt}")
                j = json.loads(txt)
                ttl = int(j.get("expires_in", 1800))
                j["expires_at"] = (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()
                j["scope_requested"] = scope
                return j

    async def get(self, scope_list: List[str]) -> Tuple[str, str]:
        errors = []
        for sc in scope_list:
            tok = self.cache.get(sc)
            if self._valid(tok):
                return tok["access_token"], sc
            try:
                nt = await self._fetch(sc)
                self.cache[sc] = nt
                return nt["access_token"], sc
            except Exception as e:
                errors.append(f"{sc} -> {e}")
        raise TokenError("All scope attempts failed:\n" + "\n".join(errors))

class KoneClient:
    def __init__(self, cfg: dict, building: str, group: str):
        self.cfg = cfg
        self.building_raw = building.replace("building:", "")
        self.building_id = "building:" + self.building_raw
        self.group = group
        self.tman = TokenManager(cfg["client_id"], cfg["client_secret"], cfg["token_endpoint"])
        self.traces: List[Dict[str, Any]] = []

    def call_scopes(self) -> List[str]:
        b = self.building_raw
        g = self.group
        return [
            f"callv2/group:{b}:{g}",
            f"callgiving/group:{b}:{g}",
            f"topology/group:{b}:{g} application/inventory",
            f"callgiving/{b}",
            f"robotcall/{b}",
        ]

    async def get_inventory_token(self) -> Tuple[str, str]:
        return await self.tman.get(["application/inventory"])

    async def list_resources(self, inv_token: str) -> Dict[str, Any]:
        url = "https://dev.kone.com/api/v2/application/self/resources"
        headers = {"Authorization": f"Bearer {inv_token}"}
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers=headers) as r:
                data = await r.json(content_type=None)
                self.traces.append({"when": now_iso(), "req": {"GET": url}, "status": r.status, "resp": data})
                return {"status": r.status, "json": data}

    async def ws_once(self, msg: dict, scope_hint: Optional[List[str]] = None, timeout: float = 8.0) -> Tuple[str, List[dict]]:
        scopes = scope_hint or self.call_scopes()
        token, used_scope = await self.tman.get(scopes)
        uri = f"{self.cfg['ws_endpoint']}?accessToken={token}"
        async with websockets.connect(uri, subprotocols=["koneapi"]) as ws:
            await ws.send(json.dumps(msg))
            out = []
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
                try:
                    out.append(json.loads(raw))
                except Exception:
                    out.append({"_raw": raw})
            except asyncio.TimeoutError:
                pass
        self.traces.append({"when": now_iso(), "ws_send": msg, "scope": used_scope, "ws_recv_first": out[0] if out else None})
        return used_scope, out

def build_common_config(bid: str, gid: str) -> dict:
    return {"type": "common-api", "requestId": str(int(time.time()*1000)), "callType": "config", "buildingId": bid, "groupId": gid}

def build_common_actions(bid: str, gid: str) -> dict:
    return {"type": "common-api", "requestId": str(int(time.time()*1000)), "callType": "actions", "buildingId": bid, "groupId": gid}

def build_common_ping(bid: str, gid: str) -> dict:
    return {"type": "common-api", "callType": "ping", "buildingId": bid, "groupId": gid, "payload": {"request_id": int(time.time())}}

def build_monitor(bid: str, gid: str) -> dict:
    return {"type": "site-monitoring", "callType": "monitor", "buildingId": bid, "groupId": gid,
            "requestId": str(int(time.time()*1000)),  # 添加缺失的requestId
            "payload": {"sub": f"sr-validator-{int(time.time())}", "duration": 30, "subtopics": ["lift_+/status"]}}

def ok(resp: dict, codes=(200, 201, 202)) -> bool:
    return resp.get("statusCode") in codes

async def run(building: str, group: str):
    cfg = load_config()
    cli = KoneClient(cfg, building, group)

    results = []

    # Test 1: inventory + resources + common-api (config/actions/ping)
    try:
        inv_tok, inv_sc = await cli.get_inventory_token()
        res = await cli.list_resources(inv_tok)
        if res["status"] != 200:
            results.append((1, "FAIL", f"/resources status {res['status']}"))
        else:
            used1, r1 = await cli.ws_once(build_common_config(cli.building_id, cli.group))
            used2, r2 = await cli.ws_once(build_common_actions(cli.building_id, cli.group))
            used3, r3 = await cli.ws_once(build_common_ping(cli.building_id, cli.group))
            ok_all = (r1 and ok(r1[0])) and (r2 and ok(r2[0])) and (r3 and ok(r3[0]))
            results.append((1, "PASS" if ok_all else "FAIL",
                            f"inventory scope={inv_sc}; ws scopes={used1}|{used2}|{used3}"))
    except Exception as e:
        results.append((1, "FAIL", f"exception: {e}"))

    # Test 2: monitoring -> 至少收到一条
    try:
        used, mon = await cli.ws_once(build_monitor(cli.building_id, cli.group), timeout=12.0)
        results.append((2, "PASS" if mon else "FAIL", f"monitor scope={used}; events={len(mon)}"))
    except Exception as e:
        results.append((2, "FAIL", f"monitor exception: {e}"))

    # Test 3: monitoring -> INFO（事件收到即可；是否 operational 看字段）
    try:
        used, mon = await cli.ws_once(build_monitor(cli.building_id, cli.group), timeout=12.0)
        results.append((3, "INFO" if mon else "FAIL", f"monitor scope={used}; events={len(mon)}"))
    except Exception as e:
        results.append((3, "FAIL", f"monitor exception: {e}"))

    # write report
    reports = Path("reports"); reports.mkdir(exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    md = [f"# SR-API Validation – Tests 1–3", f"Time: {datetime.utcnow().isoformat()}",
          f"Building: `{cli.building_id}`  ", f"Group: `{cli.group}`", "---", ""]
    names = {1:"Solution initialization",2:"Elevator mode – non-operational",3:"Elevator mode – operational"}
    expected = {
        1:"Auth OK; /resources OK; common-api {config,actions,ping} returns 200/201.",
        2:"Subscribe lift_+/status; receive events; if FRD/OSS/ATS/PRC -> do not call.",
        3:"Subscribe lift_+/status; receive events; if all false -> call allowed."
    }
    for tid, status, note in results:
        md += [f"## Test {tid} – {names[tid]}", f"**Expected**\n\n{expected[tid]}", f"**Result**: {status}", f"**Notes**: {note}", ""]
    md += ["---", "First responses (truncated):", ""]
    for t in cli.traces[-5:]:
        try:
            s = json.dumps(t, ensure_ascii=False)
        except Exception:
            s = str(t)
        md += ["```json", s[:1200] + ("..." if len(s)>1200 else ""), "```", ""]

    md_path = reports / f"t13_report_{ts}.md"
    md_path.write_text("\n".join(md), encoding="utf-8")
    traces_path = reports / f"t13_traces_{ts}.json"
    traces_path.write_text(json.dumps(cli.traces, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Report: {md_path}")
    print(f"Traces: {traces_path}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--building", required=True)
    ap.add_argument("--group", default="1")
    args = ap.parse_args()
    asyncio.run(run(args.building, args.group))
