from __future__ import annotations

import argparse

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke-test a running synthetic Repairer Portal stack."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    with httpx.Client(base_url=args.base_url, timeout=5.0) as client:
        index = client.get("/")
        index.raise_for_status()
        if "Repairer Desk" not in index.text:
            raise RuntimeError("The portal landing page was not recognized.")

        login = client.post(
            "/api/login",
            json={
                "username": "demo.repairer",
                "password": "Synthetic123!",
            },
        )
        login.raise_for_status()

        health = client.get("/api/services/health")
        health.raise_for_status()
        services = health.json()["services"]
        unavailable = [
            service["display_name"] for service in services if service["status"] != "available"
        ]
        if unavailable:
            raise RuntimeError(f"Services not ready: {', '.join(unavailable)}")

        reset = client.post("/api/session/new")
        reset.raise_for_status()
        logout = client.post("/api/logout")
        logout.raise_for_status()

    print(
        f"Portal smoke test passed: login, {len(services)} service health checks, "
        "session reset, and logout."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
