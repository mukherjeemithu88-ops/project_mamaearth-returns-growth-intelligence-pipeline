import pandas as pd
import matplotlib.pyplot as plt

# Load raw CSV files
orders = pd.read_csv("data/orders.csv")
customers = pd.read_csv("data/customers.csv")
products = pd.read_csv("data/products.csv")

# Standardize payment method
orders["payment_method"] = (
    orders["payment_method"]
    .str.strip()
    .str.upper()
)

# Remove duplicate orders using the same business columns as clean_and_eda.py
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

orders_clean = orders.loc[~duplicate_mask].copy()

# Impute missing values
orders_clean["discount_pct"] = (
    orders_clean["discount_pct"].fillna(0)
)

orders_clean["rating"] = (
    orders_clean["rating"].fillna(
        orders_clean["rating"].median()
    )
)

# Merge product information
orders_clean = orders_clean.merge(
    products[["product_id", "price"]],
    on="product_id",
    how="left"
)

# Merge customer information
orders_clean = orders_clean.merge(
    customers[["customer_id", "city_tier"]],
    on="customer_id",
    how="left"
)

# Calculate order value
orders_clean["order_value"] = (
    orders_clean["quantity"]
    * orders_clean["price"]
    * (1 - orders_clean["discount_pct"] / 100.0)
)

# Identify quantity outliers using IQR
q1 = orders_clean["quantity"].quantile(0.25)
q3 = orders_clean["quantity"].quantile(0.75)
iqr = q3 - q1

lower_fence = q1 - 1.5 * iqr
upper_fence = q3 + 1.5 * iqr

orders_clean["is_outlier"] = (
    (orders_clean["quantity"] < lower_fence)
    | (orders_clean["quantity"] > upper_fence)
)


# ---------------------------------------------------------
# Visualization 1 — Return rate by payment method
# ---------------------------------------------------------

return_rate_by_payment = (
    orders_clean
    .groupby("payment_method")["returned"]
    .mean()
    .mul(100)
    .sort_values(ascending=False)
)

fig, ax = plt.subplots(figsize=(8, 5))

bars = ax.bar(
    return_rate_by_payment.index,
    return_rate_by_payment.values
)

ax.set_title("COD Returns at 44.4% — 3x Card")
ax.set_xlabel("Payment Method")
ax.set_ylabel("Return Rate (%)")

for bar, value in zip(
    bars,
    return_rate_by_payment.values
):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height(),
        f"{value:.1f}%",
        ha="center",
        va="bottom"
    )

plt.tight_layout()

plt.savefig(
    "visualizations/return_rate_by_payment.png",
    dpi=150
)

plt.close()


# ---------------------------------------------------------
# Visualization 2 — Monthly revenue trend
# ---------------------------------------------------------

orders_clean["order_date"] = pd.to_datetime(
    orders_clean["order_date"]
)

orders_clean["year_month"] = (
    orders_clean["order_date"]
    .dt.to_period("M")
    .astype(str)
)

monthly_revenue = (
    orders_clean.loc[~orders_clean["is_outlier"]]
    .groupby("year_month")["order_value"]
    .sum()
    .round(2)
)

fig, ax = plt.subplots(figsize=(9, 5))

ax.plot(
    monthly_revenue.index,
    monthly_revenue.values,
    marker="o"
)

ax.set_title(
    "March 2026 Is the True Revenue Peak After Outlier Correction"
)

ax.set_xlabel("Month")
ax.set_ylabel("Revenue (INR)")

for month, revenue in monthly_revenue.items():
    ax.annotate(
        f"₹{revenue:,.0f}",
        (month, revenue),
        textcoords="offset points",
        xytext=(0, 8),
        ha="center"
    )

plt.xticks(rotation=45)

plt.tight_layout()

plt.savefig(
    "visualizations/monthly_revenue_trend.png",
    dpi=150
)

plt.close()

print("Visualization files created successfully.")
