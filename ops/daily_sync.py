"""Request a full synchronization from the Oracle service and report its result."""

import json
import time
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener

BASE = "http://127.0.0.1:8767"
opener = build_opener(ProxyHandler({}))


def request(path, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = Request(BASE + path, data=data, headers={"Content-Type": "application/json"})
    with opener.open(req, timeout=10) as response:
        return json.load(response)


def main():
    deadline = time.monotonic() + 4 * 60 * 60
    while True:
        try:
            run_id = request("/api/sync/start", {"mode": "full"})["run_id"]
            break
        except HTTPError as error:
            if error.code != 409 or time.monotonic() >= deadline:
                raise
            time.sleep(15)
    print(f"Started full synchronization {run_id}", flush=True)

    while time.monotonic() < deadline:
        status = request("/api/sync/status")
        if status.get("run_id") != run_id:
            raise SystemExit("Synchronization state was lost")
        if not status["running"]:
            if status.get("stop") or status.get("error"):
                raise SystemExit(status.get("error") or "Synchronization was stopped")
            result = status.get("result") or {}
            print(json.dumps(result, ensure_ascii=False), flush=True)
            publication = result.get("publication")
            if not publication or publication.get("skipped") or result.get("failed"):
                for line in status["log"]:
                    if "[실패]" in line or "[게시 보류]" in line:
                        print(line, flush=True)
                raise SystemExit("Synchronization or publication needs attention")
            return
        time.sleep(10)

    raise SystemExit("Synchronization did not finish within four hours")


if __name__ == "__main__":
    main()
