# Viva Prep — Matching Liquor Supply to Demand: What Drives Spirits Buying in Iowa?

Group 1 — Darshita Yadav (240981), Raghav Yadav (240598), Rayna Manchanda (240601), Prerit Shrivastava (240593)

---

## 1. Dataset — "what"

Two raw sources, joined into one table:

- **Iowa Liquor Sales, 2025** (Iowa Data Hub, dataset 1262) — every spirits order placed by every licensed store in Iowa, Jan–Dec 2025. 2.49 million rows after dedup, 5 CSV parts as downloaded, CC BY licence, published by the state's Alcohol Operations Bureau. Line-item grain: one row = one order line (store, date, product, quantity, price).
- **American Community Survey 5-year, 2020–2024** (US Census Bureau) — 16 demographic tables, Iowa's 99 counties only. Population, age, income, race/ethnicity, education, housing, employment.

**Integrated dataset** (the single source of truth used for analysis):
- 2,920,609 rows × 46 columns → 23 sales columns + 2 QA flag columns + 21 census columns (prefixed `cty_*`).
- After filtering out exact duplicates: 2,490,613 unique sales rows.
- ~1.1 GB — too large for Excel, loaded with Python/pandas.

**Why this dataset / why it matters:** liquor demand is a real operational problem for the state wholesaler, and Iowa publishes both the full transaction log *and* county-level census data, which is what makes a credible county-level join possible without needing a third-party crosswalk.

If asked "why spirits and not beer/wine": Iowa is a control state for spirits only — ABD is the sole wholesaler for spirits, which is exactly why this stakeholder can act on the findings (they don't control beer/wine distribution).

---

## 2. Problem statement — "what"

**Stakeholder:** Iowa Alcoholic Beverages Division (ABD) — the state's only spirits wholesaler; it licenses and supplies every one of Iowa's ~2,240 retail liquor stores.

**Problem:** Per-adult spirits demand varies enormously by county — from **1.4 to 22.7 liters per adult in 2025**, a ~16x spread. ABD currently has no systematic way to know *which county characteristics* predict (a) how much a county buys and (b) what kind of spirits it buys.

**Why it matters / business impact:** Without demand-driven stocking, ABD either overstocks (tied-up capital, waste, warehousing cost) or understocks (stock-outs, lost sales, retailer complaints) across its ~2,240 stores. Getting the stocking *profile* and the *category mix* right per county is a direct cost/revenue lever.

**Framing as a decision problem, not just a descriptive one:** the goal isn't "describe the variation" — it's to find predictive county traits robust enough that ABD can set differentiated stocking policy by county (or county cluster).

---

## 3. Stakeholders

- **Primary: Iowa ABD** — owns distribution decisions, wants per-county stocking and mix recommendations. This is who the recommendations in section 6 of the summary are written for.
- **Secondary / downstream stakeholders worth naming if asked:**
  - **Retailers** (the ~2,240 licensed stores) — experience the stock-outs/overstock directly; benefit from better-matched inventory.
  - **Public health bodies** — Recommendation 3 flags high-volume counties for public-health review, since demand concentration can also be a consumption/risk signal, not just a logistics one.
  - **State policymakers / legislature** — interested in both revenue (ABD is a state revenue source) and public-health externalities.
- Only ABD is treated as the acting decision-maker in this project; the others are why Recommendation 3 exists and why the limitations section flags that store-level sales ≠ where the buyer actually lives (so public-health inference needs care).

---

## 4. Hypotheses — on what basis, and what things

**Research question:** Which county characteristics explain how much spirits each county buys per adult, and which kinds it buys?

The hypotheses were chosen because they each map to an **actionable, ABD-controllable decision** (how much stock, and which category mix) and because the needed variable exists in the ACS census tables already joined in. Each pairs a county **demographic/economic trait** (independent variable) with a **demand outcome** (dependent variable):

| | County trait (X) | Outcome (Y) | Basis for hypothesizing a relationship |
|---|---|---|---|
| H1 | Population size | Liters per adult + orders per person | Larger, denser populations → more retail density, more urban drinking occasions, more disposable retail infrastructure |
| H2 | % Hispanic population | Share of tequila/mezcal sales (controlling for size & income) | Culturally-linked product preference; tests whether demographic composition shapes *category mix*, not just volume |
| H3 | Median household income | Share of premium-priced spirits (price per liter) | Standard economic expectation — higher income affords premium/luxury substitution |
| H4 | % young adults (21–34) | Share of RTD (ready-to-drink) and flavored spirits | Younger drinkers are the core market for RTD/flavored categories per industry trends |

**Outcome in the actual notebook run (12 hypotheses tested total: the 4 above + 9 new candidates):**
- **Supported:** H1 (population → liters per adult and orders per capita) and H2 (% Hispanic → tequila/mezcal share).
- **Rejected:** income- and unemployment-based hypotheses (H3 did not survive — be ready to explain this honestly rather than hide it).

**Validation discipline (be ready to explain *how* hypotheses were tested, this is a common viva question):**
- Split-sample test: screen candidates on Jan–Jun data, confirm survivors on Jul–Dec data — a hypothesis only "counts" if it holds in *both* halves.
- p < 0.05 **after correcting for multiple testing** (since 12 hypotheses were tested simultaneously — plain p<0.05 without correction would inflate false positives).
- Robustness checks: results re-checked after removing extreme/outlier counties, and after population-weighting counties (so one huge county like Polk doesn't dominate the conclusion).
- Rejected hypotheses are reported, not dropped silently — this is a deliberate methodological choice to avoid p-hacking / cherry-picking.

**Statistical tools used:** Spearman correlation (rank-based, robust to non-linearity/outliers — appropriate since liquor demand distributions are skewed), a regression model with controls (to isolate each trait's effect net of others, e.g. H2 controls for county size and income), and K-means clustering (to group counties into stocking-profile segments for Recommendation 1).

---

## 5. Integration — how done, how datasets merged

**Grain decision:** keep sales at line-item grain (one row per order line) for the master table, then **aggregate to one row per county** only when actually running the hypothesis tests — this preserves flexibility (can re-aggregate by time period, category, etc.) while still answering county-level questions.

**Join mechanics:**
- **Join key:** 5-digit county FIPS code (`county_fips_code`), present on both sides — sales rows carry it per store, census rows are already one-per-county.
- **Join type:** left join (sales as the base table), since the goal is to enrich every sale with its county's demographic profile.
- **Match rate:** 99.96% of rows matched successfully.

**Data cleaning before/around the join (be ready to narrate this — it's the most "engineering" part of the project):**
1. **Duplicates:** 429,996 repeated rows (Aug–Oct) were flagged (`is_exact_duplicate`) and removed. Root cause traced: one of the 5 download CSV parts (`part_0005.csv`) was almost entirely a re-export of rows already present in parts 3–4, caused by how the download zip was packaged — not a data-entry error. Verified against the publisher's own stated row count (2,490,620), which matches parts 1–4 exactly.
2. **Missing county:** 621 rows had a blank county, imputed from the store's other known rows (`county_imputed_from_store` flag); 1,308 rows with no recoverable county were dropped.
3. **Unit/measurement fix:** Nov–Dec `sales_liters` values were truncated (floored) to whole numbers at the source, understating Nov–Dec liters by 3.4% (every sub-1L item showing as 0). Fixed by recomputing liters from `sales_bottles × bottle_volume_ml / 1000` rather than trusting the published liters column.
4. **Known but accepted gaps:** `state_bottle_cost`/`state_bottle_retail` are blank for all of Jan–Jun 2025 — price per liter is instead derived as `sales_dollars ÷ liters`. `invoice_id` changes grain (line-level → invoice-level) in September 2025, so it's explicitly *not* used as a unique key anywhere.

**Validation after integration:**
- All 99 Iowa counties present in every source (no county silently dropped).
- Half-year totals reconcile to full-year totals (internal consistency check).
- Everything is rebuilt from raw files by two scripts (`fetch_census.py`, `join_datasets.py`) — the pipeline is reproducible end-to-end, not a one-off manual join. This matters for the "single source of truth" claim: anyone can regenerate the exact same integrated file from the raw inputs.

**Why FIPS code and not county name:** county names have spelling/casing inconsistencies and some duplicate names across states; FIPS is a standardized numeric key, which is why it was chosen as the join key over a text match on county name.

---

## 6. Other things likely to come up in viva

**Why K-means for clustering, not something else?**
K-means was chosen to create interpretable, mutually exclusive county groups for Recommendation 1 (stocking profiles) — it's simple to explain to a non-technical stakeholder (ABD) compared to hierarchical or density-based alternatives, and the number of county "types" needed is small and roughly known in advance.

**Why BADIR framework?**
Business question → Analysis plan/Data → Insights → Recommendation — used to keep the project anchored to a decision ABD can act on, rather than drifting into open-ended exploration. Walk through: Business question (who needs more/different stock) → Data (liters per adult, category shares, county factors) → Insights (correlation + regression + clustering) → 3 concrete Recommendations.

**Causality vs correlation (expect this question directly):**
Explicitly a correlational study — hypotheses describe *associations*, not causal mechanisms. No randomized/controlled element exists (can't randomly assign demographics to counties), so causal language is deliberately avoided throughout.

**Key limitations to state proactively:**
- Sales are recorded at the **store**, not where the buyer lives — tourism and cross-border/cross-county shopping inflate some counties (named examples: Dickinson, Clinton — likely lake/tourism and border counties). This is why the project is explicit that results describe *counties*, not *individuals* (ecological-inference caveat).
- 2020–2024 ACS averages are assumed to still describe 2025 counties — a timing-lag assumption, reasonable for a stable population but worth naming as an assumption, not a fact.
- ACS unemployment estimates are unreliable in small counties (median margin of error 39% of the estimate) — this is partly *why* unemployment-based hypotheses were rejected, not just random bad luck.

**Numbers worth memorizing cold:**
- 1.4–22.7 L/adult range across counties; ~2,240 stores; ~2.49M rows (sales); 16 census tables / 99 counties; 2.92M rows × 46 columns (pre-dedup integrated table); 2,490,613 unique rows post-dedup; 99.96% join match rate; 429,996 duplicate rows removed; 621 imputed + 1,308 dropped missing-county rows; 12 hypotheses tested total (4 original + 9 new), H1 & H2 supported, income/unemployment hypotheses rejected.

**If asked "what would you do differently / next steps":**
Data dictionary, full chart/model set, finalized county groupings, and translating the clusters into the actual per-county stocking recommendation — i.e., this pre-submission summary is the scoping/validation stage, not the final analysis.
