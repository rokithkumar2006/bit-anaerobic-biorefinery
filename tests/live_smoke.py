"""Read-only live smoke tests for the deployed BIT biorefinery site."""
import json
import math
import os
import sys
import time
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("LIVE_BASE_URL", "https://bit-anaerobic-biorefinery.vercel.app").rstrip("/")
REQUIRED_PAGES = ["overview", "waste", "data", "stpdata", "workflow", "opensource",
                  "digester", "prediction", "optimization", "scenarios", "circular", "quality"]

def require(condition, message):
    if not condition:
        raise AssertionError(message)

def main():
    failures = []
    started = time.time()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page_errors = []
        console_errors = []
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
        try:
            response = page.goto(BASE_URL, wait_until="domcontentloaded", timeout=45000)
            require(response is not None and response.status < 400,
                    f"Homepage failed: HTTP {response.status if response else 'no response'}")
            page.locator("#nav button[data-page]").first.wait_for(timeout=15000)

            for target in REQUIRED_PAGES:
                try:
                    button = page.locator(f'#nav button[data-page="{target}"]')
                    require(button.count() == 1, f"Navigation target '{target}' is missing or duplicated")
                    button.click(timeout=10000)
                    page.locator(f'.page#{target}.active').wait_for(timeout=8000)
                except Exception as exc:
                    failures.append(f"Navigation '{target}': {exc}")

            health = page.request.get(urljoin(BASE_URL + "/", "api/health"), timeout=30000)
            require(health.status == 200, f"/api/health returned HTTP {health.status}")
            health_json = health.json()
            require(health_json.get("status") == "ok", f"/api/health did not report status=ok: {health_json}")
            print("PASS /api/health:", json.dumps(health_json, sort_keys=True))

            stp_response = page.request.get(urljoin(BASE_URL + "/", "data/stp_exploratory_dataset.json"), timeout=30000)
            require(stp_response.status == 200, f"STP dataset returned HTTP {stp_response.status}")
            stp = stp_response.json()
            tank_count = len(stp.get("tankReadings", []))
            flow_count = len(stp.get("flowGasReadings", []))
            require(tank_count == 27 and flow_count == 12,
                    f"Unexpected STP record counts: tank={tank_count}, flow/gas={flow_count}")
            require(bool(stp.get("sourceNote")), "STP dataset is missing its provenance/limitation note")
            print(f"PASS STP data: {tank_count} tank readings; {flow_count} flow/gas records")

            payload = {"feed_rate_kg_day": 600, "food_share_pct": 55, "garden_share_pct": 15,
                       "temperature_c": 37, "hrt_days": 25, "duration_days": 1, "timestep_hours": 24}
            simulation = page.request.post(urljoin(BASE_URL + "/", "api/simulate"),
                                           data=payload, timeout=120000)
            try:
                result = simulation.json()
            except Exception:
                result = {"response_text": simulation.text()[:1000]}
            require(simulation.status == 200, f"/api/simulate returned HTTP {simulation.status}: {result}")
            gas = result.get("tail_period_mean", {}).get("biogas_m3_day")
            methane = result.get("tail_period_mean", {}).get("methane_m3_day")
            ph = result.get("final", {}).get("pH_model_output")
            require(isinstance(gas, (int, float)) and math.isfinite(gas), f"Invalid biogas output: {gas!r}")
            require(isinstance(methane, (int, float)) and math.isfinite(methane), f"Invalid methane output: {methane!r}")
            require(isinstance(ph, (int, float)) and math.isfinite(ph), f"Invalid model pH output: {ph!r}")
            require("not validated" in result.get("model_status", "").lower(),
                    "Simulation response must disclose its unvalidated/proxy status")
            print("PASS simulation smoke test:", json.dumps(
                {"biogas_m3_day": gas, "methane_m3_day": methane, "model_pH": ph,
                 "model_status": result.get("model_status")}, sort_keys=True))

            if page_errors:
                failures.append("Browser JavaScript exceptions: " + " | ".join(page_errors[:10]))
            if console_errors:
                print("Browser console errors observed (reported, not fatal if uncaught JS errors are absent):")
                for error in console_errors[:10]:
                    print("  -", error)
            if failures:
                raise AssertionError("\n".join(failures))
            print(f"ALL LIVE SMOKE TESTS PASSED in {time.time() - started:.1f}s")
        finally:
            browser.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"LIVE SMOKE TEST FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
