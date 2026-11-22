"""
reconcile.py — Final TODO reconciliation evidence check
"""
import json, os, subprocess

BASE = r'c:\Users\ACER\OneDrive\Desktop\IBM DATA\LATIHAN_1'
files = {}
for fn, path in [
    ('script',  BASE + r'\script.js'),
    ('html',    BASE + r'\index.html'),
    ('css',     BASE + r'\style.css'),
    ('data',    BASE + r'\data.json'),
    ('prep',    BASE + r'\prepare_data.py'),
    ('readme',  BASE + r'\README.md'),
]:
    with open(path, encoding='utf-8') as f:
        files[fn] = f.read()

d = json.loads(files['data'])

print('=' * 60)
print('  FINAL TODO RECONCILIATION — Evidence Check')
print('=' * 60)

# ─────────────────────────────────────────────
# TODO: Final Debug 2 — script.js v3 rewrite
# ─────────────────────────────────────────────
print('\n[1] Final Debug 2: script.js v3 rewrite')
code_lines = [l for l in files['script'].splitlines() if not l.strip().startswith('*')]
code_body = '\n'.join(code_lines)
e = {
    'Version header v3':              'v3 — final debug' in files['script'],
    'prod_inv_map intersection':       'prod_inv_map' in code_body and 'prodInvSet' in code_body,
    'prodInvSet.has(inv.InvoiceNo)':   'prodInvSet.has(inv.InvoiceNo)' in code_body,
    'renderProductChartsFromInvoices': 'function renderProductChartsFromInvoices' in code_body,
    'No proportional scaling':         'totalForSc' not in code_body and 'const factor =' not in code_body,
    'RFM empty restoreAndRenderEmpty': "restoreAndRenderEmpty('chartSegPie')" in code_body,
    'Cancel rate (global) suffix':     'rateSuffix' in code_body and '(global)' in code_body,
    'QR cancel dedup fields':          'cancellation_rows_raw' in code_body and 'cancellation_rows_dedup' in code_body,
    'QR before/after dedup labels':    'before dedup' in code_body and 'after dedup' in code_body,
}
all_pass = all(e.values())
for label, ok in e.items():
    print(f'  {"OK" if ok else "--"}  {label}')
print(f'  => VERDICT: {"COMPLETE" if all_pass else "INCOMPLETE"}')

# ─────────────────────────────────────────────
# TODO: Final Debug 3 — index.html update
# ─────────────────────────────────────────────
print('\n[2] Final Debug 3: index.html update')
h = {
    'cancelScopeBadge element':          'id="cancelScopeBadge"' in files['html'],
    'cancelRateInv element':             'id="cancelRateInv"' in files['html'],
    'cancelRateRows element':            'id="cancelRateRows"' in files['html'],
    'Global rate note on cards':         'Rate selalu dihitung secara global' in files['html'],
    'rfmFilterNote injection comment':   'rfmFilterNote' in files['html'],
    'Customer Segmentation aria-label':  'aria-label="Customer Segmentation"' in files['html'],
    'qualityReport container':           'id="qualityReport"' in files['html'],
    'rfmTableBody element':              'id="rfmTableBody"' in files['html'],
}
all_pass_h = all(h.values())
for label, ok in h.items():
    print(f'  {"OK" if ok else "--"}  {label}')
print(f'  => VERDICT: {"COMPLETE" if all_pass_h else "INCOMPLETE"}')

# ─────────────────────────────────────────────
# TODO: Final Debug 4 — post-fix validation suite
# ─────────────────────────────────────────────
print('\n[3] Final Debug 4: post-fix validation')
v = {
    'audit_v3.py file exists':                  os.path.exists(BASE + r'\audit_v3.py'),
    'audit_v4_filter_combinations.py exists':   os.path.exists(BASE + r'\audit_v4_filter_combinations.py'),
}

r3 = subprocess.run(
    ['D:/PHYTON DATA/python.exe', 'audit_v3.py'],
    capture_output=True, text=True, cwd=BASE
)
r4 = subprocess.run(
    ['D:/PHYTON DATA/python.exe', 'audit_v4_filter_combinations.py'],
    capture_output=True, text=True, cwd=BASE
)
v3_pass = 'PASSED: 48   FAILED: 0' in r3.stdout
v4_pass = '79 PASS  /  0 FAIL' in r4.stdout
v['audit_v3 48/48 PASS'] = v3_pass
v['audit_v4 79/79 PASS'] = v4_pass

for label, ok in v.items():
    print(f'  {"OK" if ok else "--"}  {label}')
print(f'  => VERDICT: {"COMPLETE" if all(v.values()) else "INCOMPLETE"}')

# ─────────────────────────────────────────────
# README outdated content check
# ─────────────────────────────────────────────
print('\n[4] README accuracy check')
readme_issues = {
    'Mentions old top-200 limitation':    'top-200' in files['readme'],
    'Mentions N/A for unique customers':  'N/A' in files['readme'] and 'Unique Customers' in files['readme'],
    'Shows old 2.6 MB size':             '2.6 MB' in files['readme'],
}
has_issues = any(readme_issues.values())
for label, found in readme_issues.items():
    print(f'  {"STALE" if found else "OK  "}  {label}')
print(f'  => README needs update: {has_issues}')

# ─────────────────────────────────────────────
# data.json freshness
# ─────────────────────────────────────────────
print('\n[5] data.json freshness check')
q = d['quality_report']
kpi = d['kpi']
pim = d.get('prod_inv_map', {})
df = {
    'raw_rows == 541909':              q['raw_rows'] == 541909,
    'valid_sales_rows == 524878':      q['valid_sales_rows'] == 524878,
    'total_transactions == 19960':     kpi['total_transactions'] == 19960,
    'total_revenue == 10642110.80':    kpi['total_revenue'] == 10642110.80,
    'prod_inv_map 50 products':        len(pim) == 50,
    'missing_cid_pct vs rows_after_dedup': abs(q['missing_customer_id_pct'] -
        round(q['missing_customer_id'] / q['rows_after_dedup'] * 100, 1)) < 0.2,
    'cancellation_rows_raw in QR':     'cancellation_rows_raw' in q,
    'cancellation_rows_dedup in QR':   'cancellation_rows_dedup' in q,
}
all_data_ok = all(df.values())
for label, ok in df.items():
    print(f'  {"OK" if ok else "--"}  {label}')
print(f'  => data.json valid: {all_data_ok}')

# ─────────────────────────────────────────────
# File inventory
# ─────────────────────────────────────────────
print('\n[6] File inventory')
import os
for fn, path in [
    ('index.html',                     BASE + r'\index.html'),
    ('style.css',                      BASE + r'\style.css'),
    ('script.js',                      BASE + r'\script.js'),
    ('data.json',                      BASE + r'\data.json'),
    ('prepare_data.py',                BASE + r'\prepare_data.py'),
    ('audit_v3.py',                    BASE + r'\audit_v3.py'),
    ('audit_v4_filter_combinations.py',BASE + r'\audit_v4_filter_combinations.py'),
    ('README.md',                      BASE + r'\README.md'),
]:
    exists = os.path.exists(path)
    size = round(os.path.getsize(path)/1024, 1) if exists else 0
    print(f'  {"OK" if exists else "--"}  {fn:<42} {size:>8} KB')

print()
print('=' * 60)
print('  SUMMARY')
print('=' * 60)
print(f'  Final Debug 2 (script.js v3): {"COMPLETE" if all_pass else "INCOMPLETE"}')
print(f'  Final Debug 3 (index.html):   {"COMPLETE" if all_pass_h else "INCOMPLETE"}')
print(f'  Final Debug 4 (validation):   {"COMPLETE" if all(v.values()) else "INCOMPLETE"}')
print(f'  README:                        {"NEEDS UPDATE" if has_issues else "UP TO DATE"}')
print(f'  data.json:                     {"VALID" if all_data_ok else "STALE"}')
print()
print(f'  audit_v3:  48/48 PASS = {v3_pass}')
print(f'  audit_v4:  79/79 PASS = {v4_pass}')
print(f'  TOTAL:     127/127 PASS = {v3_pass and v4_pass}')
