"""Clean the S206 (guard services) contract transactions and check them against USAspending's totals.

Reads data/raw/s206_transactions.zip. Writes data/clean/s206_transactions.csv.gz.
Each row is one contract action (a new award or a modification). Obligations are kept exactly as
reported, including negative amounts (money taken back from an earlier obligation).
"""
from pathlib import Path
import json
import zipfile
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, CLEAN = ROOT / "data" / "raw", ROOT / "data" / "clean"
CLEAN.mkdir(parents=True, exist_ok=True)

KEEP = {
    "contract_transaction_unique_key": "transaction_key",
    "contract_award_unique_key": "award_key",
    "award_id_piid": "piid",
    "modification_number": "modification_number",
    "parent_award_id_piid": "parent_piid",
    "action_date": "action_date",
    "action_date_fiscal_year": "fiscal_year",
    "federal_action_obligation": "obligation_usd",
    "awarding_agency_name": "awarding_agency",
    "awarding_sub_agency_name": "awarding_subagency",
    "funding_agency_name": "funding_agency",
    "recipient_uei": "recipient_uei",
    "recipient_name": "recipient_name",
    "recipient_parent_uei": "recipient_parent_uei",
    "recipient_parent_name": "recipient_parent_name",
    "recipient_country_code": "recipient_country_code",
    "primary_place_of_performance_country_code": "pop_country_code",
    "primary_place_of_performance_country_name": "pop_country_name",
    "primary_place_of_performance_state_code": "pop_state_code",
    "primary_place_of_performance_city_name": "pop_city",
    "award_type": "award_type",
    "action_type": "action_type",
    "product_or_service_code": "psc",
    "naics_code": "naics_code",
    "naics_description": "naics_description",
    "extent_competed": "extent_competed",
    "type_of_contract_pricing": "contract_pricing",
    "contingency_humanitarian_or_peacekeeping_operation": "contingency_operation",
    "transaction_description": "description",
}

z = zipfile.ZipFile(RAW / "s206_transactions.zip")
name = next(n for n in z.namelist() if "PrimeTransactions" in n)
df = pd.read_csv(z.open(name), usecols=list(KEEP), dtype=str, low_memory=False).rename(columns=KEEP)
df["obligation_usd"] = pd.to_numeric(df["obligation_usd"]).fillna(0.0)
df["fiscal_year"] = df["fiscal_year"].astype(int)
df = df.sort_values(["action_date", "transaction_key"]).reset_index(drop=True)

# Checks.
assert df["transaction_key"].is_unique, "duplicate transactions"
assert set(df["psc"]) == {"S206"}, set(df["psc"])
assert df["fiscal_year"].between(2008, 2026).all()
api = {int(r["time_period"]["fiscal_year"]): r["aggregated_amount"] for r in json.loads((RAW / "api_totals_by_fiscal_year.json").read_text())}
mine = df.groupby("fiscal_year")["obligation_usd"].sum()
check = pd.DataFrame({"this_dataset_usd": mine, "usaspending_total_usd": pd.Series(api)})
check["difference_usd"] = check["this_dataset_usd"] - check["usaspending_total_usd"]
check.index.name = "fiscal_year"
check.to_csv(CLEAN / "check_against_usaspending_totals.csv")
print(check.round(0).to_string())
print("largest absolute difference: $", round(check["difference_usd"].abs().max(), 2))

df.to_csv(CLEAN / "s206_transactions.csv.gz", index=False, compression="gzip")
print(len(df), "transactions,", df["award_key"].nunique(), "awards")
