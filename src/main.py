"""WASH module: usage stats collector."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone

API_BASE = os.environ.get("API_BASE_URL", "http://dynamic-api:3001").rstrip("/")
DATA_DIR = os.environ.get("MODULE_DATA_DIR", "/data")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "120"))
LOOKBACK_HOURS = int(os.environ.get("LOOKBACK_HOURS", "24"))


def fetch_usage_stats() -> list[dict]:
    url = f"{API_BASE}/api/crm/usage-stats?limit=1000"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"] if isinstance(payload["data"], list) else []
    if isinstance(payload, list):
        return payload
    return []


def aggregate(stats: list[dict]) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max(1, LOOKBACK_HOURS))
    by_wash: dict[str, dict] = defaultdict(lambda: {"usageTime": 0, "launchCount": 0, "posts": set()})

    total_usage = 0
    total_launches = 0
    considered = 0

    for row in stats:
        recorded = row.get("recordedAt") or row.get("createdAt")
        if recorded:
            try:
                dt = datetime.fromisoformat(str(recorded).replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if dt < cutoff:
                    continue
            except ValueError:
                pass
        considered += 1
        usage = int(row.get("usageTime") or 0)
        launches = int(row.get("launchCount") or 0)
        wash_id = str(row.get("washId") or "unknown")
        post_id = str(row.get("postId") or "")
        total_usage += usage
        total_launches += launches
        bucket = by_wash[wash_id]
        bucket["usageTime"] += usage
        bucket["launchCount"] += launches
        if post_id:
            bucket["posts"].add(post_id)

    washes = {
        wid: {
            "usageTime": data["usageTime"],
            "launchCount": data["launchCount"],
            "postCount": len(data["posts"]),
        }
        for wid, data in by_wash.items()
    }

    return {
        "recordedAt": datetime.now(timezone.utc).isoformat(),
        "lookbackHours": LOOKBACK_HOURS,
        "rowsConsidered": considered,
        "totalUsageTimeSec": total_usage,
        "totalLaunchCount": total_launches,
        "washCount": len(washes),
        "byWash": washes,
    }


def save_snapshot(snapshot: dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, "last_snapshot.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)


def main() -> None:
    while True:
        try:
            stats = fetch_usage_stats()
            snapshot = aggregate(stats)
            save_snapshot(snapshot)
            print(
                f"[usage-stats] washes={snapshot['washCount']} "
                f"usage={snapshot['totalUsageTimeSec']}s launches={snapshot['totalLaunchCount']}"
            )
        except urllib.error.URLError as err:
            print(f"[usage-stats] API error: {err}")
        except Exception as err:  # noqa: BLE001
            print(f"[usage-stats] error: {err}")
        time.sleep(max(30, POLL_INTERVAL))


if __name__ == "__main__":
    main()
