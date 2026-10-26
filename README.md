# ADS End-Term Project: Iowa Liquor Sales 2025 + US Census

Transaction-level Iowa liquor sales for 2025, enriched with US Census county demographics
(ACS 5-year 2020-2024) into a single integrated dataset.

## Structure

```
ads/
├── README.md
├── docs/                          course guidelines (project + pre-submission)
├── data/
│   ├── links.txt                  source links for every dataset
│   ├── raw/
│   │   ├── iowa_liquor_sales/     5 CSV parts, Jan-Dec 2025 (as downloaded)
│   │   └── census/                16 ACS tables, Iowa counties only (as published)
│   └── processed/
│       ├── census_iowa_counties.csv                       99 counties x 21 derived census variables
│       ├── iowa_liquor_sales_2025_census_integrated.csv   integrated dataset (SSOT)
│       └── county_features_2025.csv                       county x period aggregates (built by the notebook)
├── notebooks/
│   └── hypothesis_testing.ipynb   screens candidate hypotheses (Jan-Jun) and confirms them (Jul-Dec)
├── requirements.txt               packages for the notebook
└── scripts/
    ├── fetch_census.py            downloads the census files into data/raw/census/
    └── join_datasets.py           builds the SSOT in data/processed/
```

## Rebuild

The scripts need Python 3 (standard library only). Run from the project root:

```
python scripts/fetch_census.py
python scripts/join_datasets.py
```

The notebook needs the packages in `requirements.txt` (a local `.venv` is set up with Python 3.11):

```
uv venv --python 3.11 .venv
uv pip install --python .venv -r requirements.txt
.venv\Scripts\python -m jupyter lab notebooks/hypothesis_testing.ipynb
```

## Hypotheses

`notebooks/hypothesis_testing.ipynb` fixes 12 candidate hypotheses in advance (3 of the 4 from
the pre-submission draft plus 9 new ones), screens them on Jan-Jun, confirms survivors on Jul-Dec and
checks robustness on the full year. Supported: county population size -> liters per adult and
order lines per capita (H1), % Hispanic -> tequila/mezcal share (H2). Income- and
unemployment-based hypotheses were rejected. Add new candidates to the `CANDIDATES` table and re-run all cells.

## Integrated dataset

- 2,920,609 rows x 46 columns: 23 liquor sales columns, 2 flags, 21 county census columns (`cty_*`).
- Join key: 5-digit county FIPS code (`county_fips_code`); left join, 99.96% of rows matched.
- `county_imputed_from_store = 1`: blank county filled from the same `store_no` (621 rows).
- `is_exact_duplicate = 1`: row identical to an earlier one (429,996 rows, Aug-Oct).
  **Filter these out before analysis**; 2,490,613 unique rows remain. 429,989 of the flagged rows are
  `part_0005.csv`, a copy of rows already in parts 3-4 created by the download zip (the publisher
  lists 2,490,620 rows, which parts 1-4 match exactly).

## Known data issues

- `state_bottle_cost` and `state_bottle_retail` are blank for all of Jan-Jun 2025.
- Nov-Dec 2025: `sales_liters`, `sales_gallons`, prices and `sales_dollars` are truncated to whole numbers
  (every 50 ml mini shows 0 liters; Nov-Dec liters understated by 3.4%). Recompute liters as
  `sales_bottles * bottle_volume_ml / 1000` (the notebook does this). Ignore `sales_gallons`.
- `invoice_id` changes from line-level to invoice-level IDs in September 2025; it is not a unique key.
- Census values are 2020-2024 averages applied to 2025 sales, and vary only across 99 counties:
  aggregate to county level before testing demographic hypotheses. ACS unemployment is unreliable
  in small counties (median margin of error 39% of the estimate).
- The integrated CSV is ~1.1 GB (too many rows for Excel); load it with Python or R.
