"""Join Iowa liquor sales 2025 with US Census county data into one integrated CSV.

Inputs:
  data/raw/iowa_liquor_sales/iowa_liquor_sales_2025_*_part_*.csv  transaction-level liquor sales (5 parts)
  data/raw/census/census_acs5y2024_<table>_iowa_counties.dat      ACS 5-year 2020-2024, Iowa counties (run fetch_census.py)
  data/raw/census/census_gazetteer2024_iowa_counties.txt          Census Gazetteer 2024, Iowa counties

Outputs (data/processed/):
  census_iowa_counties.csv                     one row per county: the derived census variables
  iowa_liquor_sales_2025_census_integrated.csv all liquor rows + census variables (SSOT)

Join logic:
  - Join key: 5-digit county FIPS (liquor `county_fips_code` = last 5 chars of ACS GEO_ID
    0500000USsscccc = Gazetteer GEOID). Left join: every liquor row is kept.
  - Rows with a blank county are filled from the same `store_no` in other rows when the
    store maps to exactly one county; such rows get county_imputed_from_store = 1.
  - Exact duplicate rows (identical in every column) are kept but flagged:
    is_exact_duplicate = 1 on the 2nd and later occurrences.
  - ACS estimates are 5-year averages (2020-2024) used as a static county profile for 2025.
    Negative ACS sentinel values (e.g. -666666666) are written as blank.

Usage:  python scripts/join_datasets.py
"""
import csv
import glob
import hashlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSUS_DIR = os.path.join(ROOT, "data", "raw", "census")
PROCESSED_DIR = os.path.join(ROOT, "data", "processed")
LIQUOR_GLOB = os.path.join(ROOT, "data", "raw", "iowa_liquor_sales", "iowa_liquor_sales_2025_*_part_*.csv")
OUT_COUNTY = os.path.join(PROCESSED_DIR, "census_iowa_counties.csv")
OUT_JOINED = os.path.join(PROCESSED_DIR, "iowa_liquor_sales_2025_census_integrated.csv")


def load_acs(table):
    path = os.path.join(CENSUS_DIR, f"census_acs5y2024_{table}_iowa_counties.dat")
    out = {}
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="|"):
            vals = {}
            for k, v in row.items():
                if k == "GEO_ID" or "_E" not in k:
                    continue  # skip margins of error (_M)
                num = float(v) if v not in ("", None) else None
                vals[int(k.split("_E")[1])] = num if num is not None and num >= 0 else None
            out[row["GEO_ID"][-5:]] = vals
    return out


def load_gazetteer():
    path = os.path.join(CENSUS_DIR, "census_gazetteer2024_iowa_counties.txt")
    with open(path, encoding="utf-8") as fh:
        return {r["GEOID"]: r for r in csv.DictReader(fh, delimiter="\t")}


def pct(num, den):
    return round(100 * num / den, 2) if num is not None and den else None


def build_county_table():
    t = {name: load_acs(name) for name in (
        "b01001", "b01002", "b01003", "b02001", "b03003", "b11001", "b15003", "b17001",
        "b19013", "b19083", "b19301", "b23025", "b25003", "b25010", "b25064", "b25077")}
    gaz = load_gazetteer()
    counties = {}
    for fips in sorted(gaz):
        sa = t["b01001"][fips]  # sex by age: 2 = male total, 3-25 male ages, 27-49 female ages
        pop = t["b01003"][fips][1]
        pop_21 = sum(sa[i] for i in list(range(9, 26)) + list(range(33, 50)))   # 21 years and over
        pop_65 = sum(sa[i] for i in list(range(20, 26)) + list(range(44, 50)))   # 65 years and over
        edu = t["b15003"][fips]
        emp = t["b23025"][fips]
        land = float(gaz[fips]["ALAND_SQMI"])
        counties[fips] = {
            "cty_name_census": gaz[fips]["NAME"],
            "cty_total_population": pop,
            "cty_population_21_plus": pop_21,
            "cty_pct_population_21_plus": pct(pop_21, pop),
            "cty_pct_population_65_plus": pct(pop_65, pop),
            "cty_pct_male": pct(sa[2], sa[1]),
            "cty_median_age": t["b01002"][fips][1],
            "cty_households": t["b11001"][fips][1],
            "cty_avg_household_size": t["b25010"][fips][1],
            "cty_owner_occupied_rate": pct(t["b25003"][fips][2], t["b25003"][fips][1]),
            "cty_median_household_income": t["b19013"][fips][1],
            "cty_per_capita_income": t["b19301"][fips][1],
            "cty_gini_index": t["b19083"][fips][1],
            "cty_poverty_rate": pct(t["b17001"][fips][2], t["b17001"][fips][1]),
            "cty_labor_force": emp[3],
            "cty_unemployment_rate": pct(emp[5], emp[3]),
            "cty_pct_bachelors_or_higher": pct(sum(edu[i] for i in (22, 23, 24, 25)), edu[1]),
            "cty_median_home_value": t["b25077"][fips][1],
            "cty_median_gross_rent": t["b25064"][fips][1],
            "cty_pct_white_alone": pct(t["b02001"][fips][2], t["b02001"][fips][1]),
            "cty_pct_black_alone": pct(t["b02001"][fips][3], t["b02001"][fips][1]),
            "cty_pct_hispanic": pct(t["b03003"][fips][3], t["b03003"][fips][1]),
            "cty_land_area_sqmi": land,
            "cty_population_density_per_sqmi": round(pop / land, 2),
            "cty_latitude": float(gaz[fips]["INTPTLAT"]),
            "cty_longitude": float(gaz[fips]["INTPTLONG"]),
        }
    return counties


def fmt(v):
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def liquor_rows():
    for path in sorted(glob.glob(LIQUOR_GLOB)):
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            header = next(reader)
            for row in reader:
                yield header, row


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    counties = build_county_table()
    census_cols = list(next(iter(counties.values())))
    with open(OUT_COUNTY, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["county_fips_code"] + census_cols)
        for fips, c in counties.items():
            w.writerow([fips] + [fmt(c[k]) for k in census_cols])
    print(f"Wrote {len(counties)} counties -> {os.path.basename(OUT_COUNTY)}")

    # Pass 1: map each store to its county, for rows where the county is blank.
    store_counties = {}
    for header, row in liquor_rows():
        r = dict(zip(header, row))
        if r["county_fips_code"]:
            store_counties.setdefault(r["store_no"], set()).add((r["county_fips_code"], r["county_name"]))
    store_county = {s: next(iter(c)) for s, c in store_counties.items() if len(c) == 1}

    # Pass 2: write the integrated file.
    seen = set()
    n = matched = imputed = dups = 0
    with open(OUT_JOINED, "w", newline="", encoding="utf-8") as fh:
        w = None
        for header, row in liquor_rows():
            if w is None:
                fips_i, name_i, store_i = (header.index(c) for c in ("county_fips_code", "county_name", "store_no"))
                w = csv.writer(fh)
                w.writerow(header + ["county_imputed_from_store", "is_exact_duplicate"] + census_cols)
            n += 1
            digest = hashlib.md5("\x1f".join(row).encode()).digest()
            is_dup = digest in seen
            seen.add(digest)
            dups += is_dup
            was_imputed = False
            if not row[fips_i] and row[store_i] in store_county:
                row[fips_i], row[name_i] = store_county[row[store_i]]
                was_imputed = True
                imputed += 1
            c = counties.get(row[fips_i])
            matched += c is not None
            w.writerow(row + [int(was_imputed), int(is_dup)]
                       + [fmt(c[k]) if c else "" for k in census_cols])

    print(f"Wrote {n:,} rows x {len(header) + 2 + len(census_cols)} columns -> {os.path.basename(OUT_JOINED)}")
    print(f"  matched to a census county: {matched:,} ({100 * matched / n:.2f}%)")
    print(f"  county imputed from store_no: {imputed:,}")
    print(f"  unmatched (no county): {n - matched:,}")
    print(f"  flagged exact duplicates: {dups:,}")


if __name__ == "__main__":
    main()
