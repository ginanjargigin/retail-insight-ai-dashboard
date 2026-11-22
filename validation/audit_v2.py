"""
POST-FIX AUDIT SCRIPT — Retail Insight Dashboard v3
Memverifikasi semua 8 perbaikan yang diminta.
"""
import pandas as pd
import json, os, sys, io

XLSX = r'c:\Users\ACER\OneDrive\Desktop\IBM DATA\LATIHAN_1\Online Retail.xlsx'
JSON = r'c:\Users\ACER\OneDrive\Desktop\IBM DATA\LATIHAN_1\data.json'

results = []
def chk(group, name, ref, actual, note=''):
    if ref is None:
        status = 'PASS'
    elif isinstance(ref, bool):
        status = 'PASS' if bool(actual) == ref else 'FAIL'
    elif isinstance(ref, (int, float)):
        status = 'PASS' if abs(float(ref) - float(actual)) < 0.05 else 'FAIL'
    else:
        status = 'PASS' if str(ref) == str(actual) else 'FAIL'
    results.append({'group':group,'name':name,'ref':ref,'actual':actual,'status':status,'note':note})

print("Loading XLSX...")
df_raw = pd.read_excel(XLSX, engine='openpyxl')
raw_rows = len(df_raw)
dup_count = int(df_raw.duplicated().sum())
rows_after_dedup = raw_rows - dup_count
df = df_raw.drop_duplicates().copy()
df['StockCode'] = df['StockCode'].astype(str)
df['Description'] = df['Description'].fillna(df['StockCode'])
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
df['UnitPrice'] = pd.to_numeric(df['UnitPrice'], errors='coerce')
df = df.dropna(subset=['Quantity','UnitPrice','InvoiceDate'])
df['IsCancellation'] = df['InvoiceNo'].astype(str).str.startswith('C')
df_cancel = df[df['IsCancellation']].copy()
df_normal = df[~df['IsCancellation'] & (df['Quantity']>0) & (df['UnitPrice']>0)].copy()
df_normal['Revenue'] = (df_normal['Quantity'] * df_normal['UnitPrice']).round(2)
df_normal['DateStr'] = df_normal['InvoiceDate'].dt.strftime('%Y-%m-%d')
df_normal['YearMonth'] = df_normal['InvoiceDate'].dt.to_period('M').astype(str)
df_normal['InvoiceNo'] = df_normal['InvoiceNo'].astype(str)
df_normal['CustomerID'] = df_normal['CustomerID'].apply(lambda x: str(int(x)) if pd.notna(x) else None)

# RFM
df_rfm = df_normal.dropna(subset=['CustomerID'])
snapshot = df_rfm['InvoiceDate'].max() + pd.Timedelta(days=1)
rfm = df_rfm.groupby('CustomerID').agg(
    Recency=('InvoiceDate', lambda x:(snapshot-x.max()).days),
    Frequency=('InvoiceNo','nunique'),
    Monetary=('Revenue','sum')
).reset_index()
rfm['R_Score'] = pd.qcut(rfm['Recency'], q=5, labels=[5,4,3,2,1]).astype(int)
rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), q=5, labels=[1,2,3,4,5]).astype(int)
rfm['M_Score'] = pd.qcut(rfm['Monetary'].rank(method='first'), q=5, labels=[1,2,3,4,5]).astype(int)
def seg(r):
    r2,f,m = r['R_Score'],r['F_Score'],r['M_Score']
    if r2>=4 and f>=4 and m>=4: return 'Champions'
    if r2>=3 and f>=3: return 'Loyal Customers'
    if r2>=4 and f<=2: return 'New Customers'
    if r2>=3 and m>=3: return 'Potential Loyalists'
    if r2<=2 and f>=3 and m>=3: return 'At Risk'
    if r2<=2 and f<=2 and m<=2: return 'Lost / Churned'
    return 'Need Attention'
rfm['Segment'] = rfm.apply(seg, axis=1)
seg_map = dict(zip(rfm['CustomerID'], rfm['Segment']))
df_normal['Segment'] = df_normal['CustomerID'].map(seg_map).fillna('Unknown')

print("Loading JSON...")
with open(JSON, encoding='utf-8') as f:
    jd = json.load(f)

print("\n--- FIX 1: Filter engine on invoice_index ---")
# Check invoice_index has correct structure
inv = jd['invoice_index']
chk('FIX1','invoice_index exists in JSON', True, 'invoice_index' in jd)
chk('FIX1','invoice_index count == unique invoices', 19960, len(inv))
# Spot check UK Jan-2011
uk_jan_inv = [r for r in inv if r['DateStr'].startswith('2011-01') and r['Country']=='United Kingdom']
uk_jan_rev_expected = round(float(df_normal[
    (df_normal['DateStr'].str.startswith('2011-01')) &
    (df_normal['Country']=='United Kingdom')]['Revenue'].sum()), 2)
uk_jan_rev_actual = round(sum(r['Revenue'] for r in uk_jan_inv), 2)
chk('FIX1','Filter UK Jan-2011 Revenue from invoice_index', uk_jan_rev_expected, uk_jan_rev_actual,
    f'Exp=£{uk_jan_rev_expected:,.2f} Act=£{uk_jan_rev_actual:,.2f}')

print("\n--- FIX 2: Exact KPI — no double-count ---")
# Simulate JS computeKPIsFromInvoices for UK
uk_inv = [r for r in inv if r['Country']=='United Kingdom']
uk_rev_exact = round(sum(r['Revenue'] for r in uk_inv), 2)
uk_tx_exact  = len(uk_inv)  # 1 row per invoice
uk_cust_exact = len(set(r['CustomerID'] for r in uk_inv if r['CustomerID']))
uk_rev_xlsx  = round(float(df_normal[df_normal['Country']=='United Kingdom']['Revenue'].sum()), 2)
uk_tx_xlsx   = int(df_normal[df_normal['Country']=='United Kingdom']['InvoiceNo'].nunique())
uk_cust_xlsx = int(df_normal[df_normal['Country']=='United Kingdom']['CustomerID'].dropna().nunique())
chk('FIX2','UK Revenue: invoice_index vs XLSX', uk_rev_xlsx, uk_rev_exact)
chk('FIX2','UK Transactions: invoice_index vs XLSX (exact)', uk_tx_xlsx, uk_tx_exact,
    f'No double-count: each invoice appears once')
chk('FIX2','UK Unique Customers: invoice_index vs XLSX', uk_cust_xlsx, uk_cust_exact)

print("\n--- FIX 3: Date filter day-level accuracy ---")
# Filter 2011-03-15 to 2011-03-31 — should not include 2011-03-01 to 2011-03-14
mid_march_inv = [r for r in inv if '2011-03-15' <= r['DateStr'] <= '2011-03-31']
mid_march_rev_expected = round(float(df_normal[
    (df_normal['DateStr']>='2011-03-15') & (df_normal['DateStr']<='2011-03-31')
]['Revenue'].sum()), 2)
mid_march_rev_actual = round(sum(r['Revenue'] for r in mid_march_inv), 2)
chk('FIX3','Mid-March filter (2011-03-15 to 2011-03-31) day-level', mid_march_rev_expected, mid_march_rev_actual,
    f'Exp=£{mid_march_rev_expected:,.2f} Act=£{mid_march_rev_actual:,.2f}')
# Verify 2011-03-01 NOT included
early_march_inv = [r for r in inv if r['DateStr']=='2011-03-01']
early_march_in_mid = any(r['DateStr']=='2011-03-01' for r in mid_march_inv)
chk('FIX3','Early March (2011-03-01) excluded from mid-march filter', False, early_march_in_mid)

print("\n--- FIX 4: Product charts cover ALL products ---")
pm = jd.get('prod_month', [])
chk('FIX4','prod_month exists in JSON', True, 'prod_month' in jd)
pm_prods = set(r['StockCode'] for r in pm)
all_prods = set(df_normal['StockCode'].unique())
# prod_month should cover all products (via all months)
pct_covered = len(pm_prods & all_prods) / len(all_prods) * 100
chk('FIX4','prod_month covers >= 99% of all products', True, pct_covered >= 99,
    f'Coverage: {pct_covered:.1f}% ({len(pm_prods)} of {len(all_prods)} products)')
# Check top-10 by revenue for a country is now possible (Germany)
de_pm = [r for r in pm for _ in [1] if True]  # all months
de_pc = [r for r in jd['prod_country'] if r['Country']=='Germany']
de_total_rev_xlsx = round(float(df_normal[df_normal['Country']=='Germany']['Revenue'].sum()), 2)
de_top_prods = sorted(de_pc, key=lambda r: r['Revenue'], reverse=True)[:10]
chk('FIX4','prod_country Germany top product exists', True, len(de_top_prods)>0,
    f'Top product: {de_top_prods[0]["Description"] if de_top_prods else "None"}')

print("\n--- FIX 5: RFM segmentation filter aware ---")
# Filter by Champions segment — invoice_index should have Segment field
champ_inv = [r for r in inv if r.get('Segment')=='Champions']
champ_rev_inv = round(sum(r['Revenue'] for r in champ_inv), 2)
champ_rev_seg = next((s['Total_Revenue'] for s in jd['rfm_segments'] if s['Segment']=='Champions'), 0)
chk('FIX5','Champions Revenue: invoice_index vs rfm_segments', champ_rev_seg, champ_rev_inv,
    f'Inv=£{champ_rev_inv:,.2f} Seg=£{champ_rev_seg:,.2f}')
champ_cust_inv = len(set(r['CustomerID'] for r in champ_inv if r['CustomerID']))
champ_count_seg = next((s['Count'] for s in jd['rfm_segments'] if s['Segment']=='Champions'), 0)
chk('FIX5','Champions Customer Count: invoice_index-derived vs rfm_segments', champ_count_seg, champ_cust_inv)
# Check rfm_customers have required fields for filter note
req_fields = {'CustomerID','Recency','Frequency','Monetary','Segment','Country','FirstDate','LastDate'}
missing = req_fields - set(jd['rfm_customers'][0].keys())
chk('FIX5','rfm_customers has all required fields', 0, len(missing), f'Missing: {missing}')

print("\n--- FIX 6: renderEmpty preserves canvas (code check) ---")
js_path = r'c:\Users\ACER\OneDrive\Desktop\IBM DATA\LATIHAN_1\script.js'
js_code = open(js_path, encoding='utf-8').read()
# renderEmpty should NOT use innerHTML = '...' anymore
old_method_gone = 'parent.innerHTML = \'<div class="empty-state">' not in js_code
chk('FIX6','Old renderEmpty (innerHTML overwrite) removed', True, old_method_gone)
# New methods should be present
has_restore = 'restoreCanvas' in js_code and 'restoreAndRenderEmpty' in js_code
chk('FIX6','New restoreCanvas() + restoreAndRenderEmpty() present', True, has_restore)
canvas_hidden = 'canvas.style.display = \'none\'' in js_code
chk('FIX6','Canvas hidden (not removed) in empty state', True, canvas_hidden)

print("\n--- FIX 7: Data Quality shows raw + dedup separately ---")
qr = jd['quality_report']
chk('FIX7','quality_report.raw_rows matches actual', raw_rows, qr['raw_rows'])
chk('FIX7','quality_report.rows_after_dedup matches actual', rows_after_dedup, qr['rows_after_dedup'])
chk('FIX7','quality_report.duplicates_removed matches actual', dup_count, qr['duplicates_removed'])
chk('FIX7','raw_rows != rows_after_dedup (they are distinct)', True, qr['raw_rows'] != qr['rows_after_dedup'],
    'Confirm they are displayed as separate items')
js_shows_raw   = 'raw_rows' in js_code and 'rows_after_dedup' in js_code
chk('FIX7','script.js references both raw_rows and rows_after_dedup', True, js_shows_raw)

print("\n--- FIX 8: Cancellation filter-aware ---")
cancel_dc = jd['cancellation'].get('by_date_country', [])
chk('FIX8','cancellation.by_date_country exists in JSON', True, len(cancel_dc)>0,
    f'{len(cancel_dc)} slices')
# UK cancel for Jan 2011
uk_jan_cancel_json = sum(r['ReturnValue'] for r in cancel_dc
    if r['DateStr'].startswith('2011-01') and r['Country']=='United Kingdom')
df_cancel['InvoiceDate'] = pd.to_datetime(df_cancel['InvoiceDate'])
df_cancel['DateStr2'] = df_cancel['InvoiceDate'].dt.strftime('%Y-%m-%d')
df_cancel['Quantity2'] = pd.to_numeric(df_cancel['Quantity'], errors='coerce').fillna(0)
df_cancel['UnitPrice2'] = pd.to_numeric(df_cancel['UnitPrice'], errors='coerce').fillna(0)
df_cancel['ReturnValue2'] = (df_cancel['Quantity2'].abs() * df_cancel['UnitPrice2']).round(2)
uk_jan_cancel_xlsx = round(float(df_cancel[
    df_cancel['DateStr2'].str.startswith('2011-01') &
    (df_cancel['Country']=='United Kingdom')
]['ReturnValue2'].sum()), 2)
chk('FIX8','UK Jan-2011 Cancel Return Value: by_date_country vs XLSX',
    uk_jan_cancel_xlsx, round(uk_jan_cancel_json,2),
    f'XLSX=£{uk_jan_cancel_xlsx:,.2f} JSON=£{round(uk_jan_cancel_json,2):,.2f}')
# Check cancelScopeBadge in HTML
html_code = open(r'c:\Users\ACER\OneDrive\Desktop\IBM DATA\LATIHAN_1\index.html', encoding='utf-8').read()
has_badge = 'cancelScopeBadge' in html_code
chk('FIX8','cancelScopeBadge element in index.html', True, has_badge)
js_updates_badge = 'cancelScopeBadge' in js_code
chk('FIX8','script.js updates cancelScopeBadge text', True, js_updates_badge)

print("\n--- GLOBAL INTEGRITY ---")
# Global KPIs unchanged
total_rev = round(float(df_normal['Revenue'].sum()), 2)
total_tx  = int(df_normal['InvoiceNo'].nunique())
total_qty = int(df_normal['Quantity'].sum())
aov       = round(total_rev/total_tx, 2)
uniq_cust = int(df_normal['CustomerID'].dropna().nunique())
chk('GLOBAL','Total Revenue unchanged', 10642110.80, total_rev)
chk('GLOBAL','Total Transactions unchanged', 19960, total_tx)
chk('GLOBAL','Total Qty Sold unchanged', 5572420, total_qty)
chk('GLOBAL','AOV unchanged', 533.17, aov)
chk('GLOBAL','Unique Customers unchanged', 4338, uniq_cust)
json_size_mb = os.path.getsize(JSON)/(1024*1024)
chk('GLOBAL','JSON file size < 15 MB', True, json_size_mb < 15, f'{json_size_mb:.1f} MB')

# ─────────────────────────────────────
print("\n" + "="*60)
print("POST-FIX AUDIT RESULTS")
print("="*60)
groups = {}
for r in results:
    groups.setdefault(r['group'], []).append(r)
total_pass = sum(1 for r in results if r['status']=='PASS')
total_fail = sum(1 for r in results if r['status']=='FAIL')
for grp, items in groups.items():
    p = sum(1 for i in items if i['status']=='PASS')
    f = sum(1 for i in items if i['status']=='FAIL')
    print(f"\n--- {grp} ({p} PASS / {f} FAIL) ---")
    for i in items:
        icon = 'PASS' if i['status']=='PASS' else 'FAIL'
        print(f"  [{icon}] {i['name']}")
        if i['status']=='FAIL' or i['note']:
            print(f"         REF={i['ref']} | ACT={i['actual']} | {i['note']}")
print(f"\nTOTAL: {total_pass} PASS | {total_fail} FAIL out of {len(results)} checks")
