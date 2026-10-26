"""Download the US Census source data used to enrich the Iowa liquor sales data.

Source (no API key required):
  American Community Survey (ACS) 5-year estimates, 2020-2024, table-based summary files
  https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/

The national files are streamed and only Iowa county rows (GEO_ID 0500000US19xxx,
state FIPS 19) are kept. Columns and values are saved exactly as published.

Output (data/raw/census/):
  census_acs5y2024_<table>_iowa_counties.dat   pipe-delimited, one per ACS table

Usage:  python scripts/fetch_census.py
"""
import io
import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSUS_DIR = os.path.join(ROOT, "data", "raw", "census")

ACS_BASE = "https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/"
ACS_TABLES = {
    "b01001": "Sex by age",
    "b01002": "Median age",
    "b01003": "Total population",
    "b02001": "Race",
    "b03003": "Hispanic or Latino origin",
    "b11001": "Household type (households)",
    "b15003": "Educational attainment, population 25+",
    "b17001": "Poverty status in past 12 months",
    "b19013": "Median household income",
    "b19083": "Gini index of income inequality",
    "b19301": "Per capita income",
    "b23025": "Employment status, population 16+",
    "b25003": "Tenure (owner/renter occupied)",
    "b25010": "Average household size",
    "b25064": "Median gross rent",
    "b25077": "Median home value",
}
IOWA_COUNTY_PREFIX = "0500000US19"


def fetch_acs_table(table):
    url = f"{ACS_BASE}acsdt5y2024-{table}.dat"
    out = os.path.join(CENSUS_DIR, f"census_acs5y2024_{table}_iowa_counties.dat")
    kept = 0
    with urllib.request.urlopen(url, timeout=300) as resp, open(out, "w", encoding="utf-8", newline="\n") as fh:
        lines = io.TextIOWrapper(resp, encoding="utf-8")
        fh.write(next(lines))  # header
        for line in lines:
            if line.startswith(IOWA_COUNTY_PREFIX):
                fh.write(line)
                kept += 1
    print(f"  {table} ({ACS_TABLES[table]}): {kept} counties -> {os.path.basename(out)}")
    if kept != 99:
        raise SystemExit(f"Expected 99 Iowa counties in {table}, got {kept}")


if __name__ == "__main__":
    os.makedirs(CENSUS_DIR, exist_ok=True)
    print("Downloading ACS 5-year 2020-2024 tables (Iowa counties only)...")
    for t in ACS_TABLES:
        fetch_acs_table(t)
    print("Done.")
