# Data

## Source

- **USAspending.gov**, the official source of U.S. federal spending data, through its public API (https://api.usaspending.gov).
- **Filter:** product and service code S206 ("HOUSEKEEPING- GUARD"), contract award types A, B, C and D (blanket purchase agreement calls, purchase orders, delivery orders and definitive contracts), action dates from October 1, 2007 to September 30, 2026.
- **Downloaded:** October 29, 2026, by `code/01_download.py`.
- **Licence:** U.S. government works, in the public domain. The clean dataset built here is released under CC BY 4.0.

## Raw files (`raw/`)

| File | Contents |
|---|---|
| `s206_transactions.zip` | USAspending's prime transaction download, unchanged (the subaward file inside it is empty) |
| `api_totals_by_fiscal_year.json` | USAspending's own S206 contract totals by fiscal year, used as a check |

## Clean dataset (`clean/s206_transactions.csv.gz`)

One row per contract action: 215,353 rows, fiscal years 2008 to 2026. Values are kept as reported. Personal contact fields in the source (phone, fax, street address) are dropped.

| Column | Meaning |
|---|---|
| `transaction_key` | USAspending's unique key for the contract action |
| `award_key` | USAspending's unique key for the contract the action belongs to |
| `piid`, `modification_number`, `parent_piid` | Contract number, modification number, and the umbrella contract it is ordered under, if any |
| `action_date`, `fiscal_year` | Date of the action and the U.S. fiscal year (October to September) |
| `obligation_usd` | Money obligated by this action, current U.S. dollars; negative means money taken back |
| `awarding_agency`, `awarding_subagency`, `funding_agency` | Agency that signed the contract, its sub-agency, and the agency paying for it |
| `recipient_uei`, `recipient_name` | The company's unique entity ID and name |
| `recipient_parent_uei`, `recipient_parent_name` | The parent company, as reported |
| `recipient_country_code` | Country of the company's address |
| `pop_country_code`, `pop_country_name`, `pop_state_code`, `pop_city` | Where the work was done |
| `award_type`, `action_type` | Type of contract and of action (new award, modification, and so on) |
| `psc` | Product and service code (always S206) |
| `naics_code`, `naics_description` | Industry code of the work |
| `extent_competed`, `contract_pricing` | How the contract was competed and priced |
| `contingency_operation` | Whether the contract supports a contingency, humanitarian or peacekeeping operation |
| `description` | The contract action's description, as entered by the agency |

## Check

`clean/check_against_usaspending_totals.csv` compares the sum of `obligation_usd` by fiscal year with USAspending's published totals. The largest difference is $0.00.
