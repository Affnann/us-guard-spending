"""Download every U.S. federal contract transaction coded PSC S206 (Housekeeping - Guard).

Source: USAspending.gov API (public domain U.S. government data).
Requests a prime-transaction download for fiscal years 2008-2026 (October 1, 2007 to
September 30, 2026), waits for the server to build it, and saves the zip to data/raw/.
Also saves USAspending's own yearly totals to data/raw/api_totals_by_fiscal_year.json,
used as a check in 02_clean.py.
"""
from pathlib import Path
import json
import time
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
API = "https://api.usaspending.gov/api/v2"
FILTERS = {
    "psc_codes": ["S206"],
    "award_type_codes": ["A", "B", "C", "D"],  # contracts: BPA calls, purchase orders, delivery orders, definitive contracts
    "time_period": [{"start_date": "2007-10-01", "end_date": "2026-09-30"}],
}

# 1. USAspending's own totals by fiscal year (for checking the download).
r = requests.post(f"{API}/search/spending_over_time/", json={"group": "fiscal_year", "filters": FILTERS}, timeout=120)
r.raise_for_status()
(RAW / "api_totals_by_fiscal_year.json").write_text(json.dumps(r.json()["results"], indent=1))

# 2. The transaction-level download.
r = requests.post(f"{API}/download/transactions/", json={"filters": FILTERS, "file_format": "csv"}, timeout=120)
r.raise_for_status()
job = r.json()
print("Requested", job["file_name"])
while True:
    s = requests.get(f"{API}/download/status", params={"file_name": job["file_name"]}, timeout=60).json()
    if s["status"] == "finished":
        break
    if s["status"] == "failed":
        raise SystemExit(f"Download failed: {s.get('message')}")
    time.sleep(30)

zip_path = RAW / "s206_transactions.zip"
with requests.get(job["file_url"], stream=True, timeout=600) as z:
    z.raise_for_status()
    with open(zip_path, "wb") as f:
        for chunk in z.iter_content(1 << 20):
            f.write(chunk)
print("Saved", zip_path, zip_path.stat().st_size // 1_000_000, "MB")
