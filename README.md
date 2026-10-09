# Mamaearth Returns & Growth Intelligence Pipeline

This is the README for my capstone project. I have kept it practical and step-by-step so that someone opening the repository for the first time can understand what I built and reproduce the results from beginning to end.

## 1. Project Overview

The Mamaearth Returns & Growth Intelligence Pipeline is an end-to-end data analytics project built as part of the Data Analytics with AI & Gen AI programme from E&ICT Academy IIT Roorkee.

The project takes the supplied customer, product and order data through three connected layers: a SQL relational/reporting layer, a Python/Pandas cleaning and analysis layer, and a GenAI-powered narrative layer. The key principle is that each layer uses verified information from the layer before it and does not manually introduce analytical numbers.

## 2. Repository Structure

```text
<repo>/
├── README.md
├── requirements.txt
├── sql/
│   ├── schema.sql
│   ├── seed_data.sql
│   └── reports.sql
├── data/
│   ├── customers.csv
│   ├── products.csv
│   └── orders.csv
├── analysis/
│   ├── clean_and_eda.py
│   └── visualize.py
├── visualizations/
│   ├── return_rate_by_payment.png
│   └── monthly_revenue_trend.png
└── narrator/
    ├── findings.json
    ├── generate_narrative.py
    └── sample_output.txt
```

## 3. How the Pipeline Works

```text
RAW CSV DATA
│
├── Part 1: SQLite relational layer
│   ├── schema.sql
│   ├── seed_data.sql
│   └── reports.sql
│
└── Part 2: Python / Pandas analysis
    ├── clean_and_eda.py
    ├── findings.json
    └── visualize.py
            │
            ▼
    Part 3: Insight Narrator
    └── generate_narrative.py
            │
            ├── Gemini online mode
            └── deterministic offline mode
```

Part 1 and Part 2 intentionally work independently from the same raw CSV inputs. The verified Part 2 findings are then handed to Part 3 through `findings.json`.

## 4. Prerequisites

- Python 3.x
- SQLite 3.x / `sqlite3` command-line tool
- Python packages: pandas, matplotlib and google-genai
- A Gemini API key is optional; the narrator has an offline fallback
- Run commands from the repository root

Install the Python dependencies with:

```bash
pip install pandas matplotlib google-genai
```

## 5. Part 1 — SQL Relational Layer & Reporting

I used SQLite to create the relational store, load the supplied CSV data and run the required reports.

### 5.1 Create a fresh SQLite database

For a clean reproducible run, use a fresh database because `reports.sql` adds the `loyalty_tier` column.

From the repository root:

```bash
sqlite3 mamaearth_run.db
```

At the SQLite prompt:

```text
.read sql/schema.sql
.read sql/seed_data.sql
.read sql/reports.sql
```

The seed script loads the three CSV files and converts blank `discount_pct` and `rating` values to SQL NULL. Expected counts are 45 customers, 16 products and 180 orders.

### 5.2 What the SQL layer produces

- Order count, total revenue and average order value
- `COUNT(*)` versus `COUNT(rating)`
- Customers with no orders
- City-level return counts and return rates
- Customer spending rankings using `ORDER BY`, `LIMIT` and `OFFSET`
- Revenue and order counts by product category
- Customer name matching and distinct acquisition sources
- A `loyalty_tier` column derived from `city_tier`

Key Part 1 validation figures:

- Customers: 45
- Products: 16
- Orders: 180
- Raw total revenue: ₹99,860.20
- Average order value: ₹554.78
- Rated orders: 165
- Unrated orders: 15
- Loyalty tiers: Gold 28, Silver 17

## 6. Part 2 — Python / Pandas Cleaning and EDA

The Python layer reads the original CSV files directly rather than using the SQLite database.

From the repository root:

```bash
python analysis/clean_and_eda.py
```

The script performs the following sequence:

1. Loads the CSV files and confirms `orders.shape` is (180, 9)
2. Standardizes `payment_method`
3. Detects and removes the five duplicate orders
4. Imputes missing `discount_pct` and `rating` values
5. Merges products and customers and calculates `order_value`
6. Performs quantity IQR outlier detection
7. Calculates return rates by payment method
8. Calculates return rates by payment method and city tier
9. Runs the correlation analysis
10. Calculates monthly revenue before and after removing quantity outliers
11. Writes the verified findings to `narrator/findings.json`

### 6.1 Important cleaning results

- Raw orders: 180
- Duplicate rows removed: 5 — O0176 to O0180
- Cleaned orders: 175
- Missing `discount_pct` values: 12
- Missing `rating` values: 15
- Rating median used for imputation: 3.0
- Cleaned revenue: ₹97,358.30
- Revenue difference from the raw SQL total: ₹2,501.90
- The reconciliation difference is represented by the five duplicate rows removed during cleaning

### 6.2 Return-rate findings

- CARD: 14.7%
- COD: 44.4%
- UPI: 18.9%
- Highest-risk segment: COD + Tier-2 cities at 54.5%

### 6.3 Outlier-corrected revenue

Two quantity outliers were identified: O0011 with quantity 25 and O0098 with quantity 30. These orders materially inflate January's apparent revenue.

- January 2026 apparent revenue: ₹29,582.10
- January 2026 corrected revenue: ₹11,637.10
- March 2026 corrected revenue: ₹20,318.90
- March 2026 is the true peak month after the quantity outliers are excluded

## 7. Part 2 — Visualizations

After `clean_and_eda.py` completes, run:

```bash
python analysis/visualize.py
```

- `visualizations/return_rate_by_payment.png` — return rate by cleaned payment method, with exact percentages
- `visualizations/monthly_revenue_trend.png` — outlier-corrected monthly revenue trend, showing the actual peak month

## 8. Part 3 — GenAI-Powered Insight Narrator

The third layer converts the verified findings into a business-oriented Situation–Complication–Resolution (SCR) narrative. The narrator reads `findings.json` rather than recalculating the analytical results.

The solution supports both Gemini online generation and a deterministic offline fallback so the project can still be graded without network access or an API key.

### 8.1 findings.json

The end of `clean_and_eda.py` writes `narrator/findings.json` automatically.

```json
{
  "cleaned_total_revenue_inr": 97358.3,
  "raw_total_revenue_inr": 99860.2,
  "duplicate_reconciliation_delta_inr": 2501.9,
  "return_rate_by_payment": {
    "COD": 44.4,
    "CARD": 14.7,
    "UPI": 18.9
  },
  "highest_risk_segment": {
    "payment_method": "COD",
    "city_tier": 2,
    "return_rate_pct": 54.5
  },
  "true_peak_month": {
    "month": "2026-03",
    "revenue_inr": 20318.9
  },
  "outlier_inflated_month": {
    "month": "2026-01",
    "apparent_revenue_inr": 29582.1,
    "corrected_revenue_inr": 11637.1
  }
}
```

### 8.2 Gemini online mode

If I want to run the online path, I set the Gemini key as `GEMINI_API_KEY`. The key must never be hard-coded or committed to GitHub.

Windows Command Prompt:

```bat
set GEMINI_API_KEY=YOUR_GEMINI_API_KEY
python narrator/generate_narrative.py
```

Windows PowerShell:

```powershell
$env:GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
python narrator/generate_narrative.py
```

The project uses the free Gemini usage path; a paid-only API dependency is not required.

#### Running the online mode in Google Colab

The online path can also be run in Google Colab. These three setup cells are run in the Colab notebook before the script. They are Colab-only and are not part of `generate_narrative.py`.

Before starting, save the Gemini key as a Colab secret (key icon in the left sidebar). In my notebook the secret is named `MM_API_KEY`.

**Step 1 — Create the `narrator` folder and upload the files.** When the upload button appears, choose `generate_narrative.py` and `findings.json`.

```python
import os
from google.colab import files

os.makedirs("narrator", exist_ok=True)
os.chdir("narrator")
files.upload()
os.chdir("/content")
```

**Step 2 — Confirm the files are in place.**

```python
print(os.listdir("narrator"))
```

**Step 3 — Install the Gemini library and load the key from Colab secrets.**

```python
!pip install -q google-genai

from google.colab import userdata
os.environ["GEMINI_API_KEY"] = userdata.get("MM_API_KEY")
```

After these three steps, run the narrator:

```python
!python narrator/generate_narrative.py
```

### 8.3 Offline mode — no API key required

If `GEMINI_API_KEY` is not configured, `generate_narrative.py` uses the deterministic offline function.

```bash
python narrator/generate_narrative.py
```

This path requires no network access and produces the same SCR structure from the verified findings.

## 9. Numeric Accuracy Check

The narrator includes a checker for the five figures required by the capstone brief. It normalizes commas and prints a pass/fail result for each figure.

- ₹97,358.30 — cleaned total revenue
- 44.4% — COD return rate
- 54.5% — COD + Tier-2 highest-risk segment return rate
- ₹2,501.90 — duplicate-driven revenue reconciliation delta
- March with ₹20,318.90 — true peak month

## 10. Online Sample Output

For the online Gemini path, the actual generated narrative is saved as `narrator/sample_output.txt`. This gives the grader a fixed sample to verify rather than depending on a live API call.

```bash
python narrator/generate_narrative.py
# Save the actual online narrative as:
# narrator/sample_output.txt
```

## 11. Complete End-to-End Execution Order

1. Create a fresh SQLite database
2. Run `sql/schema.sql`
3. Run `sql/seed_data.sql`
4. Run `sql/reports.sql` and verify Part 1 outputs
5. Run `python analysis/clean_and_eda.py`
6. Confirm `narrator/findings.json` is generated
7. Run `python analysis/visualize.py` and confirm both PNGs are generated
8. Run `python narrator/generate_narrative.py` with `GEMINI_API_KEY` for online mode, or without it for offline mode
9. For the online path, save the actual narrative in `narrator/sample_output.txt`
10. Run the numeric checker and confirm all five figures pass

## 12. Reproducibility and Data Integrity

- The supplied CSV files are not manually edited
- `seed_data.sql` makes database loading reproducible
- Part 2 cleans the CSV data programmatically
- `findings.json` is generated from calculated Python variables
- The narrator receives analytical values from `findings.json`
- The offline narrator requires no API key or network access
- The SQLite database is a local working artifact and should not be committed
- The scripts are designed to be re-runnable from the raw CSVs

## 13. Key Takeaway

The main outcome is not just a collection of SQL queries, Python calculations or an AI-generated paragraph. The project demonstrates a connected and reproducible analytics pipeline.

The SQL layer establishes the relational view. The Python layer cleans the raw orders and validates the findings. `findings.json` provides the controlled hand-off to GenAI. The narrator then converts those verified findings into an SCR-style business narrative while retaining a deterministic offline path.

## 14. Technology Used

- SQLite
- Python
- Pandas
- Matplotlib
- Google GenAI / Gemini API
- JSON
- GitHub

## 15. Final Repository Checklist

- `README.md`
- `requirements.txt`
- `sql/schema.sql`
- `sql/seed_data.sql`
- `sql/reports.sql`
- `data/customers.csv`
- `data/products.csv`
- `data/orders.csv`
- `analysis/clean_and_eda.py`
- `analysis/visualize.py`
- `visualizations/return_rate_by_payment.png`
- `visualizations/monthly_revenue_trend.png`
- `narrator/findings.json`
- `narrator/generate_narrative.py`
- `narrator/sample_output.txt`
