"""
Retail Insight Dashboard — Data Preparation v3
PERBAIKAN:
- Tambah invoice_index: per-invoice aggregate {date,country,segment,revenue,qty}
  untuk KPI (unique transactions, unique customers) yang akurat saat filter aktif
- Tambah cancel_by_date_country untuk filter cancellation
- Tambah prod_by_date_country untuk ALL products (bukan top-200) per date+country
  disimpan sebagai {date, country, StockCode, description, revenue, qty}
  tapi hanya sampai top-500 produk untuk menjaga ukuran file
- Simpan rows_before_dedup dan rows_after_dedup terpisah di quality_report
"""

import pandas as pd
import json, os, sys, io
from datetime import datetime

FILE_IN  = r'c:\Users\ACER\OneDrive\Desktop\IBM DATA\LATIHAN_1\Online Retail.xlsx'
FILE_OUT = r'c:\Users\ACER\OneDrive\Desktop\IBM DATA\LATIHAN_1\data.json'

print("=" * 60)
print("Retail Insight Dashboard v3 - Data Preparation")
print("=" * 60)

# ─────────────────────────────────
# 1. LOAD
# ─────────────────────────────────
print("\n[1] Loading...")
df_raw = pd.read_excel(FILE_IN, engine='openpyxl')
raw_rows = len(df_raw)
raw_cols = len(df_raw.columns)
print(f"    Raw rows: {raw_rows:,}  cols: {raw_cols}")

# ─────────────────────────────────
# 2. QUALITY COUNTS (before dedup)
# ─────────────────────────────────
dup_count    = int(df_raw.duplicated().sum())
missing_cid  = int(df_raw['CustomerID'].isnull().sum())
missing_desc = int(df_raw['Description'].isnull().sum())
cancel_mask  = df_raw['InvoiceNo'].astype(str).str.startswith('C')
cancel_rows_raw = int(cancel_mask.sum())
cancel_inv_raw  = int(df_raw[cancel_mask]['InvoiceNo'].nunique())
neg_qty_nc   = int(df_raw[(~cancel_mask) & (df_raw['Quantity'] < 0)].shape[0])
zero_price   = int((df_raw['UnitPrice'] <= 0).sum())
rows_after_dedup = raw_rows - dup_count
print(f"    Duplicates: {dup_count:,}  After dedup: {rows_after_dedup:,}")

# ─────────────────────────────────
# 3. CLEAN
# ─────────────────────────────────
print("\n[2] Cleaning...")
df = df_raw.drop_duplicates().copy()
df['StockCode']   = df['StockCode'].astype(str)
df['Description'] = df['Description'].fillna(df['StockCode'])
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
df['Quantity']    = pd.to_numeric(df['Quantity'],  errors='coerce')
df['UnitPrice']   = pd.to_numeric(df['UnitPrice'], errors='coerce')
df = df.dropna(subset=['Quantity','UnitPrice','InvoiceDate'])

df['IsCancellation'] = df['InvoiceNo'].astype(str).str.startswith('C')
df_cancel = df[df['IsCancellation']].copy()
df_normal = df[~df['IsCancellation'] & (df['Quantity'] > 0) & (df['UnitPrice'] > 0)].copy()

df_normal['Revenue']   = (df_normal['Quantity'] * df_normal['UnitPrice']).round(2)
df_normal['YearMonth'] = df_normal['InvoiceDate'].dt.to_period('M').astype(str)
df_normal['DateStr']   = df_normal['InvoiceDate'].dt.strftime('%Y-%m-%d')
df_normal['Hour']      = df_normal['InvoiceDate'].dt.hour.astype(int)
df_normal['InvoiceNo'] = df_normal['InvoiceNo'].astype(str)
df_normal['CustomerID'] = df_normal['CustomerID'].apply(
    lambda x: str(int(x)) if pd.notna(x) else None
)

print(f"    Normal rows: {len(df_normal):,}  Cancel rows: {len(df_cancel):,}")

# ─────────────────────────────────
# 4. GLOBAL KPI
# ─────────────────────────────────
total_revenue      = round(float(df_normal['Revenue'].sum()), 2)
total_transactions = int(df_normal['InvoiceNo'].nunique())
total_qty          = int(df_normal['Quantity'].sum())
aov                = round(total_revenue / total_transactions, 2) if total_transactions else 0
unique_customers   = int(df_normal['CustomerID'].dropna().nunique())
date_min           = df_normal['InvoiceDate'].min().strftime('%Y-%m-%d')
date_max           = df_normal['InvoiceDate'].max().strftime('%Y-%m-%d')
print(f"\n[3] KPIs: Rev=£{total_revenue:,.2f} Tx={total_transactions:,} AOV=£{aov} Cust={unique_customers:,}")

# ─────────────────────────────────
# 5. RFM SEGMENTATION
# ─────────────────────────────────
print("\n[4] RFM...")
df_rfm   = df_normal.dropna(subset=['CustomerID'])
snapshot = df_rfm['InvoiceDate'].max() + pd.Timedelta(days=1)

rfm = df_rfm.groupby('CustomerID').agg(
    Recency   = ('InvoiceDate', lambda x: (snapshot - x.max()).days),
    Frequency = ('InvoiceNo',   'nunique'),
    Monetary  = ('Revenue',     'sum')
).reset_index()

rfm['R_Score'] = pd.qcut(rfm['Recency'],                        q=5, labels=[5,4,3,2,1]).astype(int)
rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), q=5, labels=[1,2,3,4,5]).astype(int)
rfm['M_Score'] = pd.qcut(rfm['Monetary'].rank(method='first'),  q=5, labels=[1,2,3,4,5]).astype(int)

def segment(row):
    r, f, m = row['R_Score'], row['F_Score'], row['M_Score']
    if r >= 4 and f >= 4 and m >= 4:    return 'Champions'
    if r >= 3 and f >= 3:                return 'Loyal Customers'
    if r >= 4 and f <= 2:                return 'New Customers'
    if r >= 3 and m >= 3:                return 'Potential Loyalists'
    if r <= 2 and f >= 3 and m >= 3:     return 'At Risk'
    if r <= 2 and f <= 2 and m <= 2:     return 'Lost / Churned'
    return 'Need Attention'

rfm['Segment']  = rfm.apply(segment, axis=1)
rfm['Monetary'] = rfm['Monetary'].round(2)

seg_summary = (
    rfm.groupby('Segment')
    .agg(Count=('CustomerID','count'), Avg_Recency=('Recency','mean'),
         Avg_Frequency=('Frequency','mean'), Avg_Monetary=('Monetary','mean'),
         Total_Revenue=('Monetary','sum'))
    .reset_index().sort_values('Total_Revenue', ascending=False).round(2)
)
seg_list    = seg_summary.to_dict('records')
seg_map     = dict(zip(rfm['CustomerID'], rfm['Segment']))

# Attach segment to normal transactions
df_normal['Segment'] = df_normal['CustomerID'].map(seg_map).fillna('Unknown')

# Per-customer record (with country and date range for filter)
cust_meta = (
    df_rfm.groupby('CustomerID').agg(
        Country   = ('Country',   lambda x: x.mode()[0]),
        FirstDate = ('DateStr',   'min'),
        LastDate  = ('DateStr',   'max')
    ).reset_index()
)
cust_meta_dict = cust_meta.set_index('CustomerID').to_dict('index')

rfm_records = []
for _, row in rfm.iterrows():
    meta = cust_meta_dict.get(row['CustomerID'], {})
    rfm_records.append({
        'CustomerID': row['CustomerID'],
        'Recency':    int(row['Recency']),
        'Frequency':  int(row['Frequency']),
        'Monetary':   float(row['Monetary']),
        'Segment':    row['Segment'],
        'Country':    meta.get('Country',''),
        'FirstDate':  meta.get('FirstDate',''),
        'LastDate':   meta.get('LastDate','')
    })

print(f"    RFM customers: {len(rfm_records):,}")

# ─────────────────────────────────
# 6. MONTHLY TREND
# ─────────────────────────────────
monthly = (
    df_normal.groupby('YearMonth')
    .agg(Revenue=('Revenue','sum'), Transactions=('InvoiceNo','nunique'), Qty=('Quantity','sum'))
    .reset_index().sort_values('YearMonth')
)
monthly['Revenue'] = monthly['Revenue'].round(2)
monthly_list = monthly.rename(columns={'YearMonth':'month'}).to_dict('records')

# ─────────────────────────────────
# 7. COUNTRY REVENUE
# ─────────────────────────────────
country = (
    df_normal.groupby('Country')
    .agg(Revenue=('Revenue','sum'), Transactions=('InvoiceNo','nunique'), Customers=('CustomerID','nunique'))
    .reset_index().sort_values('Revenue', ascending=False)
)
country['Revenue'] = country['Revenue'].round(2)
country_list = country.to_dict('records')

# ─────────────────────────────────
# 8. TOP PRODUCTS
# ─────────────────────────────────
prod = (
    df_normal.groupby(['StockCode','Description'])
    .agg(Revenue=('Revenue','sum'), Qty=('Quantity','sum'), Transactions=('InvoiceNo','nunique'))
    .reset_index()
)
prod['Revenue'] = prod['Revenue'].round(2)
top_prod_rev = prod.nlargest(10,'Revenue')[['StockCode','Description','Revenue','Qty','Transactions']].to_dict('records')
top_prod_qty = prod.nlargest(10,'Qty')[['StockCode','Description','Revenue','Qty','Transactions']].to_dict('records')

# ─────────────────────────────────
# 9. INVOICE INDEX
# PURPOSE: Exact KPI computation under any filter combination.
# Each row = one unique invoice: {InvoiceNo, DateStr, Country, Segment,
#                                  Revenue, Qty, CustomerID (or null)}
# JS will filter this array and compute exact unique-invoice count.
# Size estimate: ~20k invoices × small fields ≈ 2-3 MB
# ─────────────────────────────────
print("\n[5] Building invoice index...")
inv_df = (
    df_normal.groupby(['InvoiceNo','DateStr','Country','Segment'])
    .agg(
        Revenue    = ('Revenue',    'sum'),
        Qty        = ('Quantity',   'sum'),
        CustomerID = ('CustomerID', 'first')
    )
    .reset_index()
)
inv_df['Revenue'] = inv_df['Revenue'].round(2)
# Ensure CustomerID is proper null (None) not NaN float or the string 'None'
inv_df['CustomerID'] = inv_df['CustomerID'].apply(
    lambda x: x if (x is not None and str(x) not in ('nan','None','')) else None
)

invoice_index = inv_df.to_dict('records')
print(f"    Invoice records: {len(invoice_index):,}")

# ─────────────────────────────────────────────────────────────────
# 10. PRODUCT INDEXES — compact multi-dimensional approach
# Strategy: 3 small pre-aggregated tables that JS combines to get
# accurate top-10 for any filter combination.
#
# (a) prod_month  : YearMonth × StockCode  — date filter at month granularity
# (b) prod_country: Country × StockCode    — country filter
# (c) prod_segment: Segment × StockCode    — segment filter
#
# JS intersects these by StockCode when multiple filters are active.
# prod_month covers all 3,922 products × 13 months = max ~51k rows.
# prod_country covers ~20k rows. prod_segment covers ~23k rows.
# Total ~94k rows ≈ reasonable for a 3-5 MB JSON.
# ─────────────────────────────────────────────────────────────────
print("\n[6] Building product indexes...")

# (a) Product × YearMonth — date range filter (month granularity)
prod_month = (
    df_normal.groupby(['YearMonth','StockCode','Description'])
    .agg(Revenue=('Revenue','sum'), Qty=('Quantity','sum'))
    .reset_index()
)
prod_month['Revenue'] = prod_month['Revenue'].round(2)
prod_month_list = prod_month.to_dict('records')
print(f"    prod_month: {len(prod_month_list):,}")

# (b) Product × Country  — country filter
prod_country = (
    df_normal.groupby(['Country','StockCode','Description'])
    .agg(Revenue=('Revenue','sum'), Qty=('Quantity','sum'))
    .reset_index()
)
prod_country['Revenue'] = prod_country['Revenue'].round(2)
prod_country_list = prod_country.to_dict('records')
print(f"    prod_country: {len(prod_country_list):,}")

# (c) Product × Segment  — segment filter
prod_segment = (
    df_normal.groupby(['Segment','StockCode','Description'])
    .agg(Revenue=('Revenue','sum'), Qty=('Quantity','sum'))
    .reset_index()
)
prod_segment['Revenue'] = prod_segment['Revenue'].round(2)
prod_segment_list = prod_segment.to_dict('records')
print(f"    prod_segment: {len(prod_segment_list):,}")

# ─────────────────────────────────
# 11. CANCELLATION (global + by date+country for filter)
# ─────────────────────────────────
print("\n[7] Cancellation analysis...")
df_cancel['InvoiceDate'] = pd.to_datetime(df_cancel['InvoiceDate'])
df_cancel['YearMonth']   = df_cancel['InvoiceDate'].dt.to_period('M').astype(str)
df_cancel['DateStr']     = df_cancel['InvoiceDate'].dt.strftime('%Y-%m-%d')
df_cancel['Quantity']    = pd.to_numeric(df_cancel['Quantity'],  errors='coerce').fillna(0)
df_cancel['UnitPrice']   = pd.to_numeric(df_cancel['UnitPrice'], errors='coerce').fillna(0)
df_cancel['ReturnValue'] = (df_cancel['Quantity'].abs() * df_cancel['UnitPrice']).round(2)

cancel_monthly = (
    df_cancel.groupby('YearMonth')
    .agg(CancelInvoices=('InvoiceNo','nunique'), ReturnValue=('ReturnValue','sum'))
    .reset_index().sort_values('YearMonth')
)
cancel_monthly['ReturnValue'] = cancel_monthly['ReturnValue'].round(2)

# Cancel by date+country for filter support
cancel_dc = (
    df_cancel.groupby(['DateStr','Country'])
    .agg(CancelInvoices=('InvoiceNo','nunique'), ReturnValue=('ReturnValue','sum'))
    .reset_index()
)
cancel_dc['ReturnValue'] = cancel_dc['ReturnValue'].round(2)
cancel_dc_list = cancel_dc.to_dict('records')

total_cancel_invoices = int(df_cancel['InvoiceNo'].nunique())
total_return_value    = round(float(df_cancel['ReturnValue'].sum()), 2)
cancel_rate_inv       = round(total_cancel_invoices / (total_transactions + total_cancel_invoices) * 100, 2)
cancel_rate_rows      = round(cancel_rows_raw / raw_rows * 100, 2)
print(f"    Cancel invoices: {total_cancel_invoices:,}  Return: £{total_return_value:,.2f}")
print(f"    cancel_dc slices: {len(cancel_dc_list):,}")

# ─────────────────────────────────
# 12. FILTER OPTIONS
# ─────────────────────────────────
all_countries  = sorted(df_normal['Country'].dropna().unique().tolist())
all_segments   = sorted(rfm['Segment'].unique().tolist())
all_months     = sorted(df_normal['YearMonth'].unique().tolist())
top50_df = prod.nlargest(50, 'Revenue')
top50_products = (
    top50_df[['StockCode','Description']]
    .apply(lambda r: {'code': str(r['StockCode']), 'name': str(r['Description'])}, axis=1)
    .tolist()
)
top50_codes = set(top50_df['StockCode'].tolist())

# ─────────────────────────────────
# 12b. PRODUCT → INVOICE MAPPING (prod_inv_map)
# PURPOSE: Exact KPI when product filter is active.
# For each top-50 product, store the list of InvoiceNos that contain it.
# JS will intersect this with invoice_index (already filtered by date/country/segment)
# to get exact unique-invoice count without double-counting.
# ─────────────────────────────────
print("\n[9] Building prod_inv_map for top-50 products...")
prod_inv_map = {}
for sc in top50_codes:
    invs = df_normal[df_normal['StockCode'] == sc]['InvoiceNo'].unique().tolist()
    prod_inv_map[str(sc)] = invs

prod_inv_size = len(json.dumps(prod_inv_map, separators=(',',':')))
print(f"    prod_inv_map: {len(prod_inv_map)} products, {prod_inv_size/1024:.0f} KB")

# ─────────────────────────────────
# 12c. CANCELLATION DEDUP STATS
# Store both before-dedup and after-dedup cancel row counts explicitly
# ─────────────────────────────────
cancel_rows_after_dedup = int(len(df_cancel))

# ─────────────────────────────────
# 13. monthly_country_seg
# Legacy slices (kept for monthly trend chart under date+country+segment filter)
monthly_country_seg = (
    df_normal.groupby(['YearMonth','Country','Segment'])
    .agg(Revenue=('Revenue','sum'), Transactions=('InvoiceNo','nunique'), Qty=('Quantity','sum'))
    .reset_index()
)
monthly_country_seg['Revenue'] = monthly_country_seg['Revenue'].round(2)
mcs_list = monthly_country_seg.to_dict('records')
print(f"\n[8] monthly_country_seg: {len(mcs_list):,}")

# ─────────────────────────────────
# 13. ASSEMBLE & WRITE
# ─────────────────────────────────
print("\n[9] Assembling data.json...")

output = {
    "meta": {
        "generated_at": datetime.now().isoformat(),
        "source_file":  "Online Retail.xlsx",
        "raw_rows":     raw_rows,
        "rows_after_dedup": rows_after_dedup,
        "duplicates_removed": dup_count,
        "normal_rows":  int(len(df_normal)),
        "cancellation_rows": int(len(df_cancel)),
        "date_min": date_min,
        "date_max": date_max
    },
    "quality_report": {
        "raw_rows":                raw_rows,
        "rows_after_dedup":        rows_after_dedup,
        "duplicates_removed":      dup_count,
        "missing_customer_id":     missing_cid,
        "missing_customer_id_pct": round(missing_cid / rows_after_dedup * 100, 1),
        "missing_description":     missing_desc,
        "cancellation_rows_raw":   cancel_rows_raw,
        "cancellation_rows_dedup": cancel_rows_after_dedup,
        "cancellation_rows_removed_by_dedup": cancel_rows_raw - cancel_rows_after_dedup,
        "cancellation_invoices":   cancel_inv_raw,
        "negative_qty_non_cancel": neg_qty_nc,
        "zero_price_rows":         zero_price,
        "valid_sales_rows":        int(len(df_normal))
    },
    "kpi": {
        "total_revenue":      total_revenue,
        "total_transactions": total_transactions,
        "total_qty_sold":     total_qty,
        "aov":                aov,
        "unique_customers":   unique_customers
    },
    "cancellation": {
        "total_cancel_invoices": total_cancel_invoices,
        "total_return_value":    total_return_value,
        "cancel_rate_rows_pct":  cancel_rate_rows,
        "cancel_rate_inv_pct":   cancel_rate_inv,
        "monthly":               cancel_monthly.to_dict('records'),
        "by_date_country":       cancel_dc_list
    },
    "filters": {
        "date_min":     date_min,
        "date_max":     date_max,
        "countries":    all_countries,
        "segments":     all_segments,
        "top_products": top50_products,
        "months":       all_months
    },
    "monthly_trend":          monthly_list,
    "country_revenue":        country_list,
    "top_products_by_revenue": top_prod_rev,
    "top_products_by_qty":    top_prod_qty,
    "rfm_segments":           seg_list,
    "rfm_customers":          rfm_records,
    "invoice_index":          invoice_index,
    "prod_inv_map":           prod_inv_map,
    "prod_month":             prod_month_list,
    "prod_country":           prod_country_list,
    "prod_segment":           prod_segment_list,
    "monthly_country_seg":    mcs_list
}

# Custom JSON encoder: convert NaN/Inf floats to null
class SafeEncoder(json.JSONEncoder):
    def iterencode(self, o, _one_shot=False):
        # Replace NaN/Inf with None before encoding
        return super().iterencode(self._sanitize(o), _one_shot)
    def _sanitize(self, obj):
        if isinstance(obj, float):
            import math
            return None if (math.isnan(obj) or math.isinf(obj)) else obj
        if isinstance(obj, dict):
            return {k: self._sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._sanitize(v) for v in obj]
        return obj

with open(FILE_OUT, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, separators=(',',':'), cls=SafeEncoder)

size_mb = os.path.getsize(FILE_OUT) / (1024*1024)
print(f"\ndata.json written: {size_mb:.1f} MB")
print(f"Keys: {list(output.keys())}")
print("\nInvoice index items:   ", len(invoice_index))
print("prod_inv_map products: ", len(prod_inv_map))
print("prod_month items:      ", len(prod_month_list))
print("prod_country items:    ", len(prod_country_list))
print("prod_segment items:    ", len(prod_segment_list))
print("cancel_rows_raw:       ", cancel_rows_raw)
print("cancel_rows_after_dedup:", cancel_rows_after_dedup)
print("\n[DONE]")
