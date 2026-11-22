"""
AUDIT SCRIPT — Retail Insight Dashboard
Verifikasi independen dari Online Retail.xlsx
Dibandingkan dengan data.json dan angka referensi yang diberikan.
"""
import pandas as pd
import json
import sys, io

XLSX = r'c:\Users\ACER\OneDrive\Desktop\IBM DATA\LATIHAN_1\Online Retail.xlsx'
JSON = r'c:\Users\ACER\OneDrive\Desktop\IBM DATA\LATIHAN_1\data.json'

REF = {
    'raw_rows':       541909,
    'raw_columns':    8,
    'duplicates':     5268,
    'rows_after_dedup': 536641,
    'valid_sales_rows': 524878,
    'total_revenue':  10642110.80,
    'total_tx':       19960,
    'total_qty':      5572420,
    'aov':            533.17,
    'unique_customers': 4338,
    'unique_products':  3922,
}

results = []

def chk(name, ref, actual, group, note=''):
    status = 'PASS' if (ref is None or str(ref) == str(actual) or
              (isinstance(ref, float) and abs(ref - float(actual)) < 0.02) or
              (isinstance(ref, int)   and int(ref) == int(actual))) else 'FAIL'
    results.append({'group': group, 'name': name, 'ref': ref, 'actual': actual,
                    'status': status, 'note': note})

print("=" * 60)
print("RETAIL INSIGHT DASHBOARD — AUDIT REPORT")
print("=" * 60)

# ─────────────────────────────────────────
# GROUP 1: DATA QUALITY
# ─────────────────────────────────────────
print("\n[GROUP 1] Data Quality Verification from XLSX...")

df_raw = pd.read_excel(XLSX, engine='openpyxl')
raw_rows = len(df_raw)
raw_cols = len(df_raw.columns)
dup_count = int(df_raw.duplicated().sum())
rows_after_dedup = raw_rows - dup_count

chk('Raw Row Count',    REF['raw_rows'],    raw_rows,    'Data Quality')
chk('Raw Column Count', REF['raw_columns'], raw_cols,    'Data Quality')
chk('Exact Duplicates', REF['duplicates'],  dup_count,   'Data Quality')
chk('Rows After Dedup', REF['rows_after_dedup'], rows_after_dedup, 'Data Quality')

# Missing values
null_cid  = int(df_raw['CustomerID'].isnull().sum())
null_desc = int(df_raw['Description'].isnull().sum())
cancel_mask = df_raw['InvoiceNo'].astype(str).str.startswith('C')
cancel_rows = int(cancel_mask.sum())
cancel_inv  = int(df_raw[cancel_mask]['InvoiceNo'].nunique())
neg_qty_nc  = int(df_raw[(~cancel_mask) & (df_raw['Quantity'] < 0)].shape[0])
zero_price  = int((df_raw['UnitPrice'] <= 0).sum())

chk('Missing CustomerID',  135080, null_cid,   'Data Quality', '24.9% baris')
chk('Missing Description', 1454,   null_desc,  'Data Quality', 'Diisi StockCode')
chk('Cancellation Rows',   9288,   cancel_rows,'Data Quality', 'InvoiceNo prefix C')
chk('Cancellation Invoices', 3836, cancel_inv, 'Data Quality')
chk('Neg Qty (non-cancel)', 1336,  neg_qty_nc, 'Data Quality')
chk('Zero/Neg UnitPrice',  2517,   zero_price, 'Data Quality')

# ─────────────────────────────────────────
# GROUP 2: KPI ACCURACY
# ─────────────────────────────────────────
print("\n[GROUP 2] KPI Accuracy...")

df = df_raw.drop_duplicates().copy()
df['StockCode']   = df['StockCode'].astype(str)
df['Description'] = df['Description'].fillna(df['StockCode'])
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
df['Quantity']    = pd.to_numeric(df['Quantity'],  errors='coerce')
df['UnitPrice']   = pd.to_numeric(df['UnitPrice'], errors='coerce')
df = df.dropna(subset=['Quantity', 'UnitPrice', 'InvoiceDate'])

df['IsCancellation'] = df['InvoiceNo'].astype(str).str.startswith('C')
df_normal = df[~df['IsCancellation'] & (df['Quantity'] > 0) & (df['UnitPrice'] > 0)].copy()
df_normal['Revenue'] = df_normal['Quantity'] * df_normal['UnitPrice']

valid_rows   = len(df_normal)
total_rev    = round(float(df_normal['Revenue'].sum()), 2)
total_tx     = int(df_normal['InvoiceNo'].nunique())
total_qty    = int(df_normal['Quantity'].sum())
aov          = round(total_rev / total_tx, 2) if total_tx else 0
uniq_cust    = int(df_normal['CustomerID'].dropna().nunique())
uniq_prod    = int(df_normal['StockCode'].nunique())

chk('Valid Sales Rows',     REF['valid_sales_rows'],  valid_rows,  'KPI Accuracy')
chk('Total Revenue (£)',    REF['total_revenue'],     total_rev,   'KPI Accuracy')
chk('Total Transactions',   REF['total_tx'],          total_tx,    'KPI Accuracy')
chk('Total Quantity Sold',  REF['total_qty'],         total_qty,   'KPI Accuracy')
chk('AOV (£)',              REF['aov'],               aov,         'KPI Accuracy')
chk('Unique Customers',     REF['unique_customers'],  uniq_cust,   'KPI Accuracy', 'ID-known only')
chk('Unique Products',      REF['unique_products'],   uniq_prod,   'KPI Accuracy')

# ─────────────────────────────────────────
# GROUP 3: VISUALIZATION ACCURACY
# ─────────────────────────────────────────
print("\n[GROUP 3] Visualization Accuracy from data.json...")

with open(JSON, encoding='utf-8') as f:
    jd = json.load(f)

# 3a. Monthly trend sum == Total Revenue
monthly_sum = round(sum(r['Revenue'] for r in jd['monthly_trend']), 2)
chk('Monthly Trend Sum == Total Revenue', round(total_rev, 2), monthly_sum,
    'Visualization', f'Diff: {abs(total_rev - monthly_sum):.2f}')

# 3b. Country revenue sum == Total Revenue (may differ if country slice excludes some)
country_sum = round(sum(r['Revenue'] for r in jd['country_revenue']), 2)
chk('Country Revenue Sum == Total Revenue', round(total_rev, 2), country_sum,
    'Visualization', f'Diff: {abs(total_rev - country_sum):.2f}')

# 3c. Top 10 by Revenue — verify ordering
top10_rev = jd['top_products_by_revenue']
rev_values = [r['Revenue'] for r in top10_rev]
is_sorted_desc = all(rev_values[i] >= rev_values[i+1] for i in range(len(rev_values)-1))
chk('Top10 Revenue — Correctly Sorted Descending', True, is_sorted_desc,
    'Visualization', f'Top: {top10_rev[0]["Description"]} £{top10_rev[0]["Revenue"]:,.2f}')

# 3d. Top 10 by Qty — verify ordering
top10_qty = jd['top_products_by_qty']
qty_values = [r['Qty'] for r in top10_qty]
is_sorted_qty = all(qty_values[i] >= qty_values[i+1] for i in range(len(qty_values)-1))
chk('Top10 Qty — Correctly Sorted Descending', True, is_sorted_qty,
    'Visualization', f'Top: {top10_qty[0]["Description"]} {top10_qty[0]["Qty"]:,}')

# 3e. RFM customer count sum
rfm_total_cust = sum(s['Count'] for s in jd['rfm_segments'])
chk('RFM Total Customer Count', REF['unique_customers'], rfm_total_cust,
    'Visualization', 'Must match unique CustomerID count')

# 3f. RFM revenue sum
rfm_rev_sum = round(sum(s['Total_Revenue'] for s in jd['rfm_segments']), 2)
# RFM only covers ID-known customers — expect slightly less than total
df_rfm_check = df_normal.dropna(subset=['CustomerID'])
rfm_rev_expected = round(float(df_rfm_check['Revenue'].sum()), 2)
chk('RFM Revenue Sum == ID-Known Revenue', rfm_rev_expected, rfm_rev_sum,
    'Visualization', f'Expected £{rfm_rev_expected:,.2f}')

# 3g. Cancel invoices not double-counted (not in normal sales)
cancel_inv_nos = set(df[df['IsCancellation']]['InvoiceNo'].astype(str))
normal_inv_nos = set(df_normal['InvoiceNo'].astype(str))
overlap = cancel_inv_nos & normal_inv_nos
chk('No Invoice Overlap: Cancel vs Normal', 0, len(overlap),
    'Visualization', 'Cancel invoices fully isolated from sales')

# 3h. JSON KPI matches computed values
json_kpi = jd['kpi']
chk('JSON KPI: Total Revenue',      round(total_rev, 2), json_kpi['total_revenue'],    'Visualization')
chk('JSON KPI: Total Transactions', total_tx,            json_kpi['total_transactions'],'Visualization')
chk('JSON KPI: Total Qty',          total_qty,           json_kpi['total_qty_sold'],    'Visualization')
chk('JSON KPI: AOV',                aov,                 json_kpi['aov'],               'Visualization')
chk('JSON KPI: Unique Customers',   uniq_cust,           json_kpi['unique_customers'],  'Visualization')

# ─────────────────────────────────────────
# GROUP 4: FILTER FUNCTIONALITY (code-level)
# ─────────────────────────────────────────
print("\n[GROUP 4] Filter Logic Validation (data-level)...")

# 4a. Date filter — check UK revenue for 2011-01 only
uk_jan = sum(
    r['Revenue'] for r in jd['date_country_slices']
    if r['Country'] == 'United Kingdom' and r['DateStr'].startswith('2011-01')
)
# Compute from scratch
df_uk_jan = df_normal[
    (df_normal['Country'] == 'United Kingdom') &
    (df_normal['InvoiceDate'].dt.to_period('M').astype(str) == '2011-01')
]
uk_jan_expected = round(float(df_uk_jan['Revenue'].sum()), 2)
chk('Date+Country Filter (UK, Jan-2011)', uk_jan_expected, round(uk_jan, 2),
    'Filter Functionality', f'Expected £{uk_jan_expected:,.2f}')

# 4b. Country filter — Germany revenue
de_rev_json = round(sum(r['Revenue'] for r in jd['date_country_slices'] if r['Country'] == 'Germany'), 2)
de_rev_xlsx = round(float(df_normal[df_normal['Country'] == 'Germany']['Revenue'].sum()), 2)
chk('Country Filter: Germany Revenue', de_rev_xlsx, de_rev_json,
    'Filter Functionality', f'From XLSX: £{de_rev_xlsx:,.2f}')

# 4c. Segment filter — Champions revenue
champ_json = round(sum(r['Revenue'] for r in jd['date_country_slices'] if r['Segment'] == 'Champions'), 2)
champ_seg  = next((s for s in jd['rfm_segments'] if s['Segment'] == 'Champions'), {})
champ_rfm  = champ_seg.get('Total_Revenue', 0)
chk('Segment Filter: Champions Revenue (slice vs rfm_segments)',
    round(champ_rfm, 2), champ_json, 'Filter Functionality',
    f'rfm_segments: £{champ_rfm:,.2f} | date_country_slice: £{champ_json:,.2f}')

# 4d. Product filter — top product in prod_month_country
top_prod_code = top10_rev[0]['StockCode']
prod_json_sum = round(sum(r['Revenue'] for r in jd['prod_month_country'] if r['StockCode'] == top_prod_code), 2)
prod_xlsx_sum = round(float(df_normal[df_normal['StockCode'] == top_prod_code]['Revenue'].sum()), 2)
chk(f'Product Filter: Top Product Revenue ({top_prod_code})', prod_xlsx_sum, prod_json_sum,
    'Filter Functionality', f'From XLSX: £{prod_xlsx_sum:,.2f}')

# 4e. Reset filter — unfiltered KPI matches global
chk('Reset Filter: KPI matches global KPI', True,
    (json_kpi['total_revenue'] == round(total_rev, 2)), 'Filter Functionality')

# 4f. Empty filter result handling
# Check: if we filter a country with 0 revenue in prod_month_country for a non-top-200 product
# This is a known limitation — test it
non_top200_codes = set(df_normal['StockCode'].unique()) - set(r['StockCode'] for r in jd['prod_month_country'])
chk('Non-Top-200 Products Excluded from prod_month_country',
    True, len(non_top200_codes) > 0,
    'Filter Functionality',
    f'{len(non_top200_codes)} products excluded (known limitation, fallback to global top-10 in JS)')

# ─────────────────────────────────────────
# GROUP 5: OVERALL QUALITY
# ─────────────────────────────────────────

# 5a. All required JSON keys present
required_keys = ['meta','quality_report','kpi','cancellation','filters',
                 'monthly_trend','country_revenue','top_products_by_revenue',
                 'top_products_by_qty','rfm_segments','rfm_customers',
                 'date_country_slices','prod_month_country','monthly_country_seg']
missing_keys = [k for k in required_keys if k not in jd]
chk('All Required JSON Keys Present', 0, len(missing_keys),
    'Overall Quality', f'Missing: {missing_keys if missing_keys else "None"}')

# 5b. JSON file size reasonable (< 5 MB)
import os
json_size_mb = os.path.getsize(JSON) / (1024*1024)
chk('JSON File Size < 5 MB', True, json_size_mb < 5,
    'Overall Quality', f'Actual: {json_size_mb:.2f} MB')

# 5c. StockCode types all string
sc_types = set(type(r['StockCode']).__name__ for r in jd['prod_month_country'])
chk('StockCode Type is String (no int/float)', {'str'}, sc_types,
    'Overall Quality', f'Types found: {sc_types}')

# 5d. date_country_slices completeness
dcs_rev_sum = round(sum(r['Revenue'] for r in jd['date_country_slices']), 2)
chk('date_country_slices Revenue == Total Revenue',
    round(total_rev, 2), dcs_rev_sum,
    'Overall Quality', f'Diff: {abs(total_rev - dcs_rev_sum):.2f}')

# 5e. monthly_country_seg completeness
mcs_rev_sum = round(sum(r['Revenue'] for r in jd['monthly_country_seg']), 2)
chk('monthly_country_seg Revenue == Total Revenue',
    round(total_rev, 2), mcs_rev_sum,
    'Overall Quality', f'Diff: {abs(total_rev - mcs_rev_sum):.2f}')

# 5f. Unique products in data.json
json_uniq_prod = len(set(r['StockCode'] for r in jd['top_products_by_revenue'] + jd['top_products_by_qty']))
# Just verify top lists exist and have 10 items
chk('Top Products List Has 10 Items', 10, len(jd['top_products_by_revenue']),
    'Overall Quality')
chk('Top Qty List Has 10 Items', 10, len(jd['top_products_by_qty']),
    'Overall Quality')

# 5g. HTML files exist
html_exists = os.path.exists(r'c:\Users\ACER\OneDrive\Desktop\IBM DATA\LATIHAN_1\index.html')
css_exists  = os.path.exists(r'c:\Users\ACER\OneDrive\Desktop\IBM DATA\LATIHAN_1\style.css')
js_exists   = os.path.exists(r'c:\Users\ACER\OneDrive\Desktop\IBM DATA\LATIHAN_1\script.js')
chk('index.html Exists',  True, html_exists, 'Overall Quality')
chk('style.css Exists',   True, css_exists,  'Overall Quality')
chk('script.js Exists',   True, js_exists,   'Overall Quality')

# ─────────────────────────────────────────
# PRINT SUMMARY
# ─────────────────────────────────────────
print("\n" + "=" * 60)
print("AUDIT RESULTS SUMMARY")
print("=" * 60)

groups = {}
for r in results:
    groups.setdefault(r['group'], []).append(r)

total_pass = sum(1 for r in results if r['status'] == 'PASS')
total_fail = sum(1 for r in results if r['status'] == 'FAIL')

for grp, items in groups.items():
    p = sum(1 for i in items if i['status'] == 'PASS')
    f = sum(1 for i in items if i['status'] == 'FAIL')
    print(f"\n--- {grp} ({p} PASS / {f} FAIL) ---")
    for i in items:
        icon = 'OK' if i['status'] == 'PASS' else 'XX'
        print(f"  [{icon}] {i['name']}")
        if i['status'] == 'FAIL' or i['note']:
            print(f"       REF={i['ref']}  |  ACTUAL={i['actual']}  |  NOTE: {i['note']}")

print(f"\n{'='*60}")
print(f"TOTAL: {total_pass} PASS | {total_fail} FAIL out of {len(results)} checks")
print(f"{'='*60}")

# Output JSON for structured use
import json as _json
print("\n[JSON_RESULTS_START]")
print(_json.dumps(results, default=str))
print("[JSON_RESULTS_END]")
