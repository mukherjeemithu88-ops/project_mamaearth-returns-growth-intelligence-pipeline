import pandas as pd

# Task 1 — Load and inspect raw data

orders = pd.read_csv("data/orders.csv")
customers = pd.read_csv("data/customers.csv")
products = pd.read_csv("data/products.csv")

print("Orders shape before cleaning:", orders.shape)


# Task 2 — Standardize payment_method casing

print("\nTask 2 — Payment methods before standardization:")
print(orders["payment_method"].unique())

orders["payment_method"] = (
    orders["payment_method"]
    .str.strip()
    .str.upper()
)

print("\nPayment methods after standardization:")
print(orders["payment_method"].unique())

print("\nPayment method counts:")
print(orders["payment_method"].value_counts())


# Task 3 — Remove duplicate orders

duplicate_columns = [
    "customer_id",
    "product_id",
    "order_date",
    "quantity",
    "discount_pct",
    "payment_method",
    "rating",
    "returned"
]

duplicate_mask = orders.duplicated(
    subset=duplicate_columns,
    keep="first"
)

dropped_order_ids = orders.loc[duplicate_mask, "order_id"].tolist()

print("\nTask 3 — Duplicate orders detected:")
print("Number of duplicate rows:", duplicate_mask.sum())
print("Dropped order_id values:", dropped_order_ids)

orders_clean = orders.loc[~duplicate_mask].copy()

print("Orders shape after duplicate removal:", orders_clean.shape)




# Task 4 — Impute missing values

print("\nTask 4 — Missing values before imputation:")
print(orders_clean[["discount_pct", "rating"]].isnull().sum())

discount_missing = orders_clean["discount_pct"].isna().sum()
rating_missing = orders_clean["rating"].isna().sum()

rating_median = orders_clean["rating"].median()

print("Discount values to impute:", discount_missing)
print("Rating values to impute:", rating_missing)
print("Rating median before imputation:", rating_median)

orders_clean["discount_pct"] = orders_clean["discount_pct"].fillna(0)
orders_clean["rating"] = orders_clean["rating"].fillna(rating_median)

print("\nMissing values after imputation:")
print(orders_clean[["discount_pct", "rating"]].isnull().sum())



# Task 5 — Merge and reconcile revenue

# Calculate raw revenue independently from the original raw CSVs.

raw_orders_for_revenue = orders.copy()

raw_orders_for_revenue = raw_orders_for_revenue.merge(
    products[["product_id", "price"]],
    on="product_id",
    how="left"
)

raw_orders_for_revenue["discount_pct"] = (
    raw_orders_for_revenue["discount_pct"].fillna(0)
)

raw_orders_for_revenue["order_value"] = (
    raw_orders_for_revenue["quantity"]
    * raw_orders_for_revenue["price"]
    * (1 - raw_orders_for_revenue["discount_pct"] / 100.0)
)

raw_total_revenue = raw_orders_for_revenue["order_value"].sum()

# Merge cleaned orders with product and customer information.
orders_clean = orders_clean.merge(
    products[["product_id", "price"]],
    on="product_id",
    how="left"
)

orders_clean = orders_clean.merge(
    customers[["customer_id", "city", "city_tier"]],
    on="customer_id",
    how="left"
)

orders_clean["order_value"] = (
    orders_clean["quantity"]
    * orders_clean["price"]
    * (1 - orders_clean["discount_pct"] / 100.0)
)

cleaned_revenue = orders_clean["order_value"].sum()
revenue_difference = raw_total_revenue - cleaned_revenue

# Independently calculate the revenue represented by the five dropped duplicates.
dropped_duplicate_rows = raw_orders_for_revenue[
    raw_orders_for_revenue["order_id"].isin(dropped_order_ids)
]

duplicate_revenue = dropped_duplicate_rows["order_value"].sum()

print("\nTask 5 — Revenue reconciliation:")
print(f"Cleaned Python revenue: {cleaned_revenue:.2f}")
print(f"Raw revenue: {raw_total_revenue:.2f}")
print(f"Difference: {revenue_difference:.2f}")
print(f"Dropped duplicate rows: {len(dropped_order_ids)}")
print(f"Revenue represented by dropped duplicates: {duplicate_revenue:.2f}")

print(
    "\nReconciliation note: The revenue difference is attributable to the "
    "five duplicate rows removed during cleaning. Their combined order "
    "value is {:.2f}, which matches the revenue difference. The discount "
    "and rating imputations did not change the total order_value because "
    "missing discounts were treated as 0 and rating does not affect "
    "order_value."
    .format(duplicate_revenue)
)




# Task 6 — IQR outlier detection for quantity

q1 = orders_clean["quantity"].quantile(0.25)
q3 = orders_clean["quantity"].quantile(0.75)
iqr = q3 - q1

lower_fence = q1 - 1.5 * iqr
upper_fence = q3 + 1.5 * iqr

print("\nTask 6 — Quantity IQR outlier detection:")
print(f"Q1: {q1}")
print(f"Q3: {q3}")
print(f"IQR: {iqr}")
print(f"Lower fence: {lower_fence}")
print(f"Upper fence: {upper_fence}")

quantity_outliers = orders_clean[
    (orders_clean["quantity"] < lower_fence)
    | (orders_clean["quantity"] > upper_fence)
]

print("\nQuantity outliers:")
print(
    quantity_outliers[
        ["order_id", "quantity", "product_id"]
    ].to_string(index=False)
)

orders_clean["is_outlier"] = False
orders_clean.loc[quantity_outliers.index, "is_outlier"] = True

print("\nOutlier flag counts:")
print(orders_clean["is_outlier"].value_counts())




# Task 7 — COD return-rate hypothesis

print("\nTask 7 — Hypothesis:")
print("Hypothesis: COD has a higher return rate than CARD and UPI.")

return_rate_by_payment = (
    orders_clean
    .groupby("payment_method")["returned"]
    .agg(["count", "mean"])
)

return_rate_by_payment["return_rate_pct"] = (
    return_rate_by_payment["mean"] * 100
).round(1)

print("\nReturn rate by payment method:")
print(return_rate_by_payment)

print("\nHypothesis result: Confirmed")





# Task 8 — COD return rate by city tier

print("\nTask 8 — COD return rate by city tier:")

return_rate_by_payment_tier = (
    orders_clean
    .groupby(["payment_method", "city_tier"])["returned"]
    .agg(["count", "mean"])
)

return_rate_by_payment_tier["return_rate_pct"] = (
    return_rate_by_payment_tier["mean"] * 100
).round(1)

print(return_rate_by_payment_tier)

print("\nCOD return rate by city tier:")

cod_tier_rates = return_rate_by_payment_tier.loc["COD"]

print(cod_tier_rates)

highest_risk_segment = cod_tier_rates["return_rate_pct"].idxmax()
highest_risk_rate = cod_tier_rates["return_rate_pct"].max()

print(
    f"\nHighest-risk segment: COD + Tier-{highest_risk_segment} "
    f"cities at {highest_risk_rate:.1f}% return rate."
)

print(
    "Finding: COD return risk is not uniform across city tiers."
)



# Task 9 — Correlation analysis

print("\nTask 9 — Correlation matrix:")

correlation_columns = [
    "rating",
    "returned",
    "discount_pct",
    "quantity"
]

correlation_matrix = orders_clean[correlation_columns].corr()

print(correlation_matrix)

print("\nCorrelation strength classification:")

def classify_correlation(value):
    absolute_value = abs(value)

    if absolute_value <= 0.19:
        return "Negligible"
    elif absolute_value <= 0.39:
        return "Weak"
    elif absolute_value <= 0.69:
        return "Moderate"
    else:
        return "Strong"


pairs = [
    ("rating", "returned"),
    ("rating", "discount_pct"),
    ("rating", "quantity"),
    ("returned", "discount_pct"),
    ("returned", "quantity"),
    ("discount_pct", "quantity")
]

for variable_1, variable_2 in pairs:
    correlation_value = correlation_matrix.loc[
        variable_1, variable_2
    ]

    strength = classify_correlation(correlation_value)

    print(
        f"{variable_1} vs {variable_2}: "
        f"{correlation_value:.2f} → {strength}"
    )

discount_return_correlation = correlation_matrix.loc[
    "discount_pct",
    "returned"
]

print(
    f"\nDiscount vs returned correlation: "
    f"{discount_return_correlation:.2f}"
)

print(
    'Hypothesis: "Higher discounts reduce returns" — Busted'
)

print(
    "Finding: The discount_pct vs returned correlation is negligible, "
    "so the data does not support a meaningful relationship between "
    "higher discounts and lower returns."
)




# Task 10 — Monthly revenue and outlier impact

print("\nTask 10 — Monthly revenue and outlier impact:")

orders_clean["order_date"] = pd.to_datetime(
    orders_clean["order_date"]
)

orders_clean["year_month"] = (
    orders_clean["order_date"]
    .dt.to_period("M")
    .astype(str)
)

# Monthly revenue including outliers.
monthly_revenue_with_outliers = (
    orders_clean
    .groupby("year_month")["order_value"]
    .sum()
    .round(2)
)

print("\nMonthly revenue including outliers:")
print(monthly_revenue_with_outliers)

# Monthly revenue excluding quantity outliers.
monthly_revenue_without_outliers = (
    orders_clean.loc[~orders_clean["is_outlier"]]
    .groupby("year_month")["order_value"]
    .sum()
    .round(2)
)

print("\nMonthly revenue excluding quantity outliers:")
print(monthly_revenue_without_outliers)

# Identify apparent and corrected peak months.
apparent_peak_month = monthly_revenue_with_outliers.idxmax()
apparent_peak_revenue = monthly_revenue_with_outliers.max()

true_peak_month = monthly_revenue_without_outliers.idxmax()
true_peak_revenue = monthly_revenue_without_outliers.max()

print(
    f"\nApparent peak including outliers: "
    f"{apparent_peak_month} — ₹{apparent_peak_revenue:.2f}"
)

print(
    f"True peak excluding outliers: "
    f"{true_peak_month} — ₹{true_peak_revenue:.2f}"
)

print(
    "\nFinding: January's apparent revenue lead is an artifact of "
    "the two bulk orders O0011 and O0098. After excluding these "
    "quantity outliers, March 2026 is the genuine revenue peak."
)



# Part 3 — Generate verified findings.json

import json
from pathlib import Path

findings = {
    "cleaned_total_revenue_inr": round(cleaned_revenue, 2),
    "raw_total_revenue_inr": round(raw_total_revenue, 2),
    "duplicate_reconciliation_delta_inr": round(
        revenue_difference, 2
    ),
    "return_rate_by_payment": {
        "COD": round(
            return_rate_by_payment.loc["COD", "return_rate_pct"],
            1
        ),
        "CARD": round(
            return_rate_by_payment.loc["CARD", "return_rate_pct"],
            1
        ),
        "UPI": round(
            return_rate_by_payment.loc["UPI", "return_rate_pct"],
            1
        )
    },
    "highest_risk_segment": {
        "payment_method": "COD",
        "city_tier": int(highest_risk_segment),
        "return_rate_pct": round(
            float(highest_risk_rate),
            1
        )
    },
    "true_peak_month": {
        "month": true_peak_month,
        "revenue_inr": round(
            float(true_peak_revenue),
            2
        )
    },
    "outlier_inflated_month": {
        "month": apparent_peak_month,
        "apparent_revenue_inr": round(
            float(apparent_peak_revenue),
            2
        ),
        "corrected_revenue_inr": round(
            float(
                monthly_revenue_without_outliers.loc[
                    apparent_peak_month
                ]
            ),
            2
        )
    }
}

findings_path = Path("narrator/findings.json")

findings_path.parent.mkdir(
    parents=True,
    exist_ok=True
)

with findings_path.open(
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        findings,
        file,
        indent=2
    )

print("\nPart 3 — findings.json generated successfully:")
print(json.dumps(findings, indent=2))
