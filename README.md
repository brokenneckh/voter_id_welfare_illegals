# Voter ID Laws & Welfare Benefits for Illegal Immigrants

Analysis of the relationship between state voter ID requirements and state-funded welfare benefits available to illegal immigrants.

## Key Finding

States without effective voter ID requirements are **16x more likely** to offer welfare benefits to illegal immigrants (67% vs 4%, p<0.0001).

| Benefit Category | No Effective ID (24 states) | ID Required (27 states) | p-value |
|------------------|:---------------------------:|:-----------------------:|:-------:|
| **ANY Benefit** | **67%** | **4%** | <0.0001 |
| Healthcare (children) | 54% | 4% | 0.0001 |
| EITC (ITIN filers) | 46% | 0% | 0.0001 |
| Healthcare (adults) | 25% | 0% | 0.008 |
| Food assistance | 21% | 0% | 0.02 |
| Healthcare (seniors) | 8% | 0% | 0.22 |

**Note:** Not a single state requiring ID verification offers healthcare for illegal immigrant adults, food assistance, or EITC to illegal immigrants. The only overlap is children's healthcare (Rhode Island).

## State Classifications

### Voter ID Groups

**ID Required (Tiers 1-3):** 27 states
> AL, AR, AZ, FL, GA, ID, IN, KS, KY, LA, MI, MO, MS, MT, NC, ND, NE, NH, OH, RI, SC, SD, TN, TX, WI, WV, WY

**No Effective ID (Tiers 4-5):** 24 states
> AK, CA, CO, CT, DC, DE, HI, IA, IL, MA, MD, ME, MN, NJ, NM, NV, NY, OK, OR, PA, UT, VA, VT, WA

### States Offering Benefits to Illegal Immigrants

| Benefit | States |
|---------|--------|
| Health (Children) | CA, CT, DC, IL, MA, ME, MN, NJ, NY, OR, RI, UT, VT, WA |
| Health (Adults) | CA, CO, DC, MN, OR, WA |
| Health (Seniors) | IL, NY |
| Food Assistance | CA, IL, ME, MN, WA |
| State EITC (ITIN) | CA, CO, DC, IL, MD, ME, MN, NM, OR, VT, WA |

## Five-Tier Breakdown

| Tier | Voter ID Policy | N | Health (Adults) | Health (Children) | Health (Seniors) | Food | EITC | ANY |
|:----:|-----------------|:-:|:---------------:|:-----------------:|:----------------:|:----:|:----:|:---:|
| 1 | Strict Photo ID | 11 | 0% | 0% | 0% | 0% | 0% | 0% |
| 2 | Strict Non-Photo | 2 | 0% | 0% | 0% | 0% | 0% | 0% |
| 3 | Non-Strict Photo | 14 | 0% | 7% | 0% | 0% | 0% | 7% |
| 4 | Non-Strict Non-Photo | 9 | 33% | 33% | 0% | 11% | 33% | 56% |
| 5 | No Document Req | 15 | 20% | 67% | 13% | 27% | 53% | 73% |

Logistic regression trend test (tier as continuous predictor):
- ANY Benefit: p=0.0001
- Health (Children): p=0.0002
- EITC: p=0.0009
- Health (Adults): p=0.02
- Food: p=0.02

## What the Benefits Represent

| Column | Description |
|--------|-------------|
| `health_children` | State-funded health coverage for illegal immigrant children |
| `health_adults` | State-funded health coverage for ALL illegal immigrant adults |
| `health_seniors` | State-funded health coverage for illegal immigrant seniors 65+ |
| `food` | State food assistance available to illegal immigrants |
| `eitc` | State EITC available to ITIN filers |

**Why no cash benefits?** Research shows virtually no states provide direct cash assistance to illegal immigrants. Programs like California's CAPI explicitly exclude undocumented immigrants and serve only legal immigrants ineligible for federal SSI.

**Note on EITC for ITIN Filers:** State EITC programs that extend eligibility to ITIN filers primarily benefit illegal immigrants. According to the [Immigration Research Initiative](https://immresearch.org/publications/people-who-are-undocumented-occupations-taxes-paid-and-long-term-economic-benefits/), "the overwhelming majority of people filing taxes using ITINs are people who are undocumented."

## Program Enrollment Data

California publishes the most transparent enrollment data:

| Program | Enrollment | Annual Cost | Source |
|---------|------------|-------------|--------|
| Healthcare (Medi-Cal) | 1.7 million | $8.5 billion | [CalMatters](https://calmatters.org/health/2025/03/medi-cal-budget-shortfall/) |
| EITC (CalEITC) | ~315,000 ITIN filers | — | [PPIC](https://www.ppic.org/blog/are-eligible-undocumented-immigrants-claiming-the-caleitc-and-young-child-tax-credit/) |

**Other states:**
- Washington: ~24,000 enrolled/applying for Medicaid expansion
- Colorado: 11,000 (hit enrollment cap in first 2 days)
- New York: 480,000 in emergency Medicaid (seniors 65+ only for full coverage)

Most states do not publish immigration-status breakdowns for program enrollment.

## Methodology

### Voter ID Classification

Voter ID laws are categorized into five tiers per NCSL:

1. **Strict Photo ID** – Must show government-issued photo ID; no alternatives
2. **Strict Non-Photo ID** – Must show ID (photo not required); no alternatives
3. **Non-Strict Photo ID** – Photo ID requested, but alternatives allowed (affidavit, vouching)
4. **Non-Strict Non-Photo ID** – ID requested, non-photo accepted, can sign affidavit
5. **No Document Required** – No ID needed; identity verified via signature match or poll book

For the primary analysis, these collapse into two groups based on **functional outcome**:
- **ID Required (Tiers 1-3):** Voter must present an identification document
- **No Effective ID (Tiers 4-5):** Voter can cast ballot without presenting ID

### Statistical Methods

- **Primary comparison:** Fisher's exact test (appropriate for small cell counts)
- **Trend analysis:** Logistic regression with tier (1-5) as continuous predictor
- **Significance threshold:** Two-tailed p<0.05

### Welfare Scores

Two composite scores are calculated:

1. **Adults Score (0-3):** `health_adults + food + eitc`
   - Focused on working-age illegal immigrant adults

2. **Any Coverage Score (0-3):** `(any health) + food + eitc`
   - Includes children and seniors

## Limitations

1. **Ecological design:** State-level analysis shows association between policies but cannot establish that the same individuals are affected by both.

2. **Omitted variables:** States may differ on unobserved characteristics (political culture, demographics, fiscal capacity) influencing both policies. Association is correlational, not causal.

3. **Policy heterogeneity:** Binary coding obscures variation in program generosity and eligibility thresholds.

4. **Small sample:** With N=51 jurisdictions and sparse cells, statistical power is limited for rare benefits (e.g., senior health coverage).

## Visualizations

### Maps
- `state_map.png` – 5-tier NCSL classification with benefit symbols
- `state_map_2tier.png` – ID Required vs No Effective ID (primary analysis)

### Tables
- `table_granular_pvalues.png` – 5-tier breakdown with logistic regression p-values
- `table_2tier_stats.png` – Fisher exact test comparison (No ID vs ID Required)
- `map_with_table.png` – Combined map and summary table

### Map Legend
- **Ha** = Healthcare for adults
- **Hc** = Healthcare for children
- **Hs** = Healthcare for seniors (65+)
- **F** = Food assistance
- **E** = EITC for ITIN filers

## Data Sources

- **Voter ID Requirements:** [National Conference of State Legislatures (NCSL)](https://www.ncsl.org/elections-and-campaigns/voter-id)
- **Health Coverage:** [KFF State Health Coverage for Immigrants](https://www.kff.org/), [NILC Health Coverage Maps](https://www.nilc.org/)
- **Food Assistance:** [NILC State Food Programs](https://www.nilc.org/resources/state_food/)
- **EITC for ITIN Filers:** [ITEP State EITC Analysis](https://itep.org/)

## Usage

### Requirements

```bash
pip install -r requirements.txt
```

### Generate Visualizations

```bash
python src/main.py           # Maps and charts
python src/create_tables.py  # Summary tables
python src/create_tables2.py # Statistical tables with p-values
```

Output files are created in the `output/` directory.

### Project Structure

```
├── data/
│   └── state_policies.csv      # State-level policy data
├── src/
│   ├── prepare_data.py         # Data loading and preparation
│   ├── stats.py                # Statistical analysis
│   ├── visualize.py            # Map and chart generation
│   ├── create_tables.py        # Summary table generation
│   ├── create_tables2.py       # Statistical tables with p-values
│   └── main.py                 # Main pipeline
├── output/
│   ├── state_map*.png          # Static maps
│   ├── table_*.png             # Summary tables
│   ├── comparison_chart.png    # Bar chart comparison
│   ├── strip_plot.html         # Interactive strip plot
│   └── choropleth_map.html     # Interactive choropleth
└── requirements.txt
```

## License

MIT
