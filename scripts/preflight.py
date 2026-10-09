from __future__ import annotations

import argparse

from common.preflight import preflight_succeeded, run_preflight


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the local prototype environment.")
    parser.add_argument(
        "--skip-port-check",
        action="store_true",
        help="Do not require ports 8000-8003 to be free.",
    )
    args = parser.parse_args()

    checks = run_preflight(check_ports=not args.skip_port_check)
    print("Repairer Orchestrator prototype preflight")
    print("=" * 41)
    for check in checks:
        marker = "PASS" if check.status == "pass" else "FAIL"
        print(f"[{marker}] {check.name}: {check.message}")

    if preflight_succeeded(checks):
        print("\nPreflight passed.")
        return 0
    print("\nPreflight failed. Resolve the failed checks before starting.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
