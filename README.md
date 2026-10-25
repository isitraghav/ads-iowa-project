# ADS End-Term Project: Iowa Liquor Sales 2025 + US Census

Transaction-level Iowa liquor sales for 2025, enriched with US Census county demographics
(ACS 5-year 2020-2024 and Census Gazetteer 2024) into a single integrated dataset.

## Structure

```
ads/
├── README.md
├── docs/                          course guidelines (project + pre-submission)
├── data/
│   ├── links.txt                  source links for every dataset
│   ├── raw/
│   │   ├── iowa_liquor_sales/     5 CSV parts, Jan-Dec 2025 (as downloaded)
│   │   └── census/                ACS tables + Gazetteer, Iowa counties only (as published)
│   └── processed/
│       ├── census_iowa_counties.csv                       99 counties x 26 derived census variables
│       └── iowa_liquor_sales_2025_census_integrated.csv   integrated dataset (SSOT)
└── scripts/
    ├── fetch_census.py            downloads the census files into data/raw/census/
    └── join_datasets.py           builds everything in data/processed/
```

## Rebuild

Requires Python 3 (standard library only). Run from the project root:

```
python scripts/fetch_census.py
python scripts/join_datasets.py
```

## Integrated dataset

- 2,920,609 rows x 51 columns: 23 liquor sales columns, 2 flags, 26 county census columns (`cty_*`).
- Join key: 5-digit county FIPS code (`county_fips_code`); left join, 99.96% of rows matched.
- `county_imputed_from_store = 1`: blank county filled from the same `store_no` (621 rows).
- `is_exact_duplicate = 1`: row identical to an earlier one (429,996 rows, Aug-Oct).
  **Filter these out before analysis**; about 2.49M unique rows remain.

## Known data issues

- `state_bottle_cost` and `state_bottle_retail` are blank for all of Jan-Jun 2025.
- `invoice_id` changes from line-level to invoice-level IDs in September 2025; it is not a unique key.
- Census values are 2020-2024 averages applied to 2025 sales, and vary only across 99 counties:
  aggregate to county level before testing demographic hypotheses.
- The integrated CSV is ~1.1 GB (too many rows for Excel); load it with Python or R.
