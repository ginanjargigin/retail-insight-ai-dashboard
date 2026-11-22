import pandas as pd
import json
from datetime import datetime

FILE = r'c:\Users\ACER\OneDrive\Desktop\IBM DATA\LATIHAN_1\Online Retail.xlsx'

print("Loading dataset...")
df = pd.read_excel(FILE, engine='openpyxl')

print("=== BASIC INFO ===")
print("Shape:", df.shape)
print("Columns:", list(df.columns))
print("Dtypes:\n", df.dtypes)
print("\nNull counts:\n", df.isnull().sum())
print("\nSample rows:\n", df.head(5).to_string())

# --- Cleaning ---
df_clean = df.dropna(subset=['CustomerID'])
df_clean = df_clean[df_clean['Quantity'] > 0]
df_clean = df_clean[df_clean['UnitPrice'] > 0]
df_clean['Revenue'] = df_clean['Quantity'] * df_clean['UnitPrice']
df_clean['InvoiceDate'] = pd.to_datetime(df_clean['InvoiceDate'])
df_clean['YearMonth'] = df_clean['InvoiceDate'].dt.to_period('M').astype(str)
df_clean['Month'] = df_clean['InvoiceDate'].dt.month
df_clean['Year'] = df_clean['InvoiceDate'].dt.year

print("\n=== AFTER CLEANING ===")
print("Cleaned shape:", df_clean.shape)
print("Date range:", df_clean['InvoiceDate'].min(), "to", df_clean['InvoiceDate'].max())
print("Total Revenue: £{:,.2f}".format(df_clean['Revenue'].sum()))
print("Unique Customers:", df_clean['CustomerID'].nunique())
print("Unique Products:", df_clean['StockCode'].nunique())
print("Unique Countries:", df_clean['Country'].nunique())
print("Total Transactions:", df_clean['InvoiceNo'].nunique())

# --- Revenue by Country (Top 10) ---
print("\n=== TOP 10 COUNTRIES BY REVENUE ===")
country_rev = df_clean.groupby('Country')['Revenue'].sum().sort_values(ascending=False).head(10)
for c, v in country_rev.items():
    print(f"  {c}: £{v:,.2f}")

# --- Monthly Revenue Trend ---
print("\n=== MONTHLY REVENUE TREND ===")
monthly = df_clean.groupby('YearMonth')['Revenue'].sum().sort_index()
for m, v in monthly.items():
    print(f"  {m}: £{v:,.2f}")

# --- Top 10 Products by Revenue ---
print("\n=== TOP 10 PRODUCTS BY REVENUE ===")
prod_rev = df_clean.groupby(['StockCode','Description'])['Revenue'].sum().sort_values(ascending=False).head(10)
for (sc, desc), v in prod_rev.items():
    print(f"  {desc} ({sc}): £{v:,.2f}")

# --- Top 10 Products by Quantity ---
print("\n=== TOP 10 PRODUCTS BY QUANTITY SOLD ===")
prod_qty = df_clean.groupby(['StockCode','Description'])['Quantity'].sum().sort_values(ascending=False).head(10)
for (sc, desc), v in prod_qty.items():
    print(f"  {desc} ({sc}): {v:,}")

# --- Customer Orders Distribution ---
print("\n=== CUSTOMER ORDER FREQUENCY ===")
cust_orders = df_clean.groupby('CustomerID')['InvoiceNo'].nunique()
print("  Mean orders per customer:", round(cust_orders.mean(), 2))
print("  Median:", cust_orders.median())
print("  Max:", cust_orders.max())
print("  Distribution:")
bins = [0,1,2,5,10,20,50,999]
labels = ['1','2','3-5','6-10','11-20','21-50','50+']
dist = pd.cut(cust_orders, bins=bins, labels=labels).value_counts().sort_index()
for k, v in dist.items():
    print(f"    {k} orders: {v} customers ({v/len(cust_orders)*100:.1f}%)")

# --- RFM Analysis ---
print("\n=== RFM SEGMENTATION ===")
snapshot_date = df_clean['InvoiceDate'].max() + pd.Timedelta(days=1)
rfm = df_clean.groupby('CustomerID').agg(
    Recency=('InvoiceDate', lambda x: (snapshot_date - x.max()).days),
    Frequency=('InvoiceNo', 'nunique'),
    Monetary=('Revenue', 'sum')
).reset_index()

# Score 1-5 (5=best for F and M, 5=best=lowest recency so invert)
rfm['R_Score'] = pd.qcut(rfm['Recency'], q=5, labels=[5,4,3,2,1]).astype(int)
rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), q=5, labels=[1,2,3,4,5]).astype(int)
rfm['M_Score'] = pd.qcut(rfm['Monetary'].rank(method='first'), q=5, labels=[1,2,3,4,5]).astype(int)
rfm['RFM_Score'] = rfm['R_Score'] + rfm['F_Score'] + rfm['M_Score']

def segment(row):
    r, f, m = row['R_Score'], row['F_Score'], row['M_Score']
    if r >= 4 and f >= 4 and m >= 4:
        return 'Champions'
    elif r >= 3 and f >= 3:
        return 'Loyal Customers'
    elif r >= 4 and f <= 2:
        return 'New Customers'
    elif r >= 3 and f >= 1 and m >= 3:
        return 'Potential Loyalists'
    elif r <= 2 and f >= 3 and m >= 3:
        return 'At Risk'
    elif r <= 2 and f <= 2 and m <= 2:
        return 'Lost/Churned'
    else:
        return 'Need Attention'

rfm['Segment'] = rfm.apply(segment, axis=1)
seg_summary = rfm.groupby('Segment').agg(
    Count=('CustomerID','count'),
    Avg_Recency=('Recency','mean'),
    Avg_Frequency=('Frequency','mean'),
    Avg_Monetary=('Monetary','mean'),
    Total_Revenue=('Monetary','sum')
).round(2).sort_values('Total_Revenue', ascending=False)

print(seg_summary.to_string())

print("\n=== RFM STATS ===")
print(rfm[['Recency','Frequency','Monetary']].describe().round(2).to_string())

# --- Average Order Value by Country (Top 10) ---
print("\n=== AVG ORDER VALUE BY COUNTRY (TOP 10) ===")
aov = df_clean.groupby('Country').agg(
    Total_Revenue=('Revenue','sum'),
    Num_Orders=('InvoiceNo','nunique')
)
aov['AOV'] = aov['Total_Revenue'] / aov['Num_Orders']
aov_top = aov.sort_values('AOV', ascending=False).head(10)
for c, row in aov_top.iterrows():
    print(f"  {c}: AOV=£{row['AOV']:.2f} (Orders={int(row['Num_Orders'])})")

# --- Hourly sales pattern ---
print("\n=== SALES BY HOUR ===")
df_clean['Hour'] = df_clean['InvoiceDate'].dt.hour
hourly = df_clean.groupby('Hour')['Revenue'].sum().sort_index()
for h, v in hourly.items():
    print(f"  {h:02d}:00 - £{v:,.2f}")

# --- Cancellations ---
cancelled = df[df['InvoiceNo'].astype(str).str.startswith('C')]
print(f"\n=== CANCELLATIONS ===")
print(f"  Total cancelled rows: {len(cancelled)}")
print(f"  Cancellation rate (rows): {len(cancelled)/len(df)*100:.1f}%")
print(f"  Cancelled invoices: {cancelled['InvoiceNo'].nunique()}")

print("\n=== DONE ===")
