"""
audit_v3.py  —  Post-fix validation suite for script.js v3 + data.json v3
"""
import json

with open('data.json', encoding='utf-8') as f:
    d = json.load(f)
with open('script.js', encoding='utf-8') as f:
    js = f.read()
with open('index.html', encoding='utf-8') as f:
    html = f.read()

results = []

def chk(label, cond, detail=''):
    ok = bool(cond)
    results.append((ok, label, str(detail) if detail else ''))
    return ok

# ══ DATA.JSON — quality_report new fields ══
q = d['quality_report']
chk('QR: cancellation_rows_raw exists',   'cancellation_rows_raw'  in q,  q.get('cancellation_rows_raw'))
chk('QR: cancellation_rows_dedup exists', 'cancellation_rows_dedup' in q, q.get('cancellation_rows_dedup'))
chk('QR: cancellation_rows_raw > 0',      q.get('cancellation_rows_raw', 0) > 0)
chk('QR: cancellation_rows_dedup > 0',    q.get('cancellation_rows_dedup', 0) > 0)
chk('QR: raw >= dedup (dedup removes some cancel rows)',
    q.get('cancellation_rows_raw', 0) >= q.get('cancellation_rows_dedup', 0))

# ══ DATA.JSON — prod_inv_map ══
chk('prod_inv_map exists in data.json', 'prod_inv_map' in d)
pim = d.get('prod_inv_map', {})
chk('prod_inv_map non-empty', len(pim) > 0, f'{len(pim)} products')
sample_key = list(pim.keys())[0] if pim else None
chk('prod_inv_map values are lists',
    sample_key and isinstance(pim[sample_key], list),
    f'key={sample_key}, len={len(pim[sample_key]) if sample_key else 0}')
# prod_inv_map should cover the top-50 products from filters
top50_codes = {p['code'] for p in d['filters']['top_products']}
covered = top50_codes & set(pim.keys())
chk('prod_inv_map covers all top-50 filter products',
    len(covered) == len(top50_codes),
    f'{len(covered)}/{len(top50_codes)} covered')

# ══ DATA.JSON — invoice_index structure ══
inv0 = d['invoice_index'][0]
for field in ['InvoiceNo', 'DateStr', 'Revenue', 'Qty', 'CustomerID', 'Segment']:
    chk(f'invoice_index has {field}', field in inv0)
chk('invoice_index count == KPI transactions',
    len(d['invoice_index']) == d['kpi']['total_transactions'],
    f'{len(d["invoice_index"])} vs {d["kpi"]["total_transactions"]}')

# ══ SCRIPT.JS — Fix 1: prod_inv_map in getFilteredInvoices ══
chk('script.js: prod_inv_map used in getFilteredInvoices',
    'prod_inv_map' in js and 'prodInvSet' in js)
chk('script.js: prodInvSet.has(inv.InvoiceNo)',
    'prodInvSet.has(inv.InvoiceNo)' in js)
chk('script.js: renderProductChartsFromInvoices defined',
    'function renderProductChartsFromInvoices' in js)
chk('script.js: filters.product branch routes to renderProductChartsFromInvoices',
    'if (filters.product)' in js and 'renderProductChartsFromInvoices' in js)

# ══ SCRIPT.JS — Fix 2: No proportional scaling ══
# 'totalForSc' may appear in a comment — check it's not in actual code lines
js_code_lines = [l for l in js.splitlines() if not l.strip().startswith('*') and not l.strip().startswith('//')]
js_code = '\n'.join(js_code_lines)
chk('script.js: NO totalForSc proportional lookup (code only)',  'totalForSc' not in js_code)
chk('script.js: NO const factor = proportional calc', 'const factor = ' not in js)
chk('script.js: NO cSlice.Revenue * factor',          'cSlice.Revenue * factor' not in js)
chk('script.js: NO sSlice.Revenue * factor',          'sSlice.Revenue * factor' not in js)
# cSlice direct assignment instead
chk('script.js: cSlice used directly (Revenue: cMap[sc].Revenue)',
    'Revenue:     cMap[sc].Revenue' in js)
chk('script.js: sSlice used directly (Revenue: sMap[sc].Revenue)',
    'Revenue:     sMap[sc].Revenue' in js)

# ══ SCRIPT.JS — Fix 3: RFM empty → restoreAndRenderEmpty ══
chk('script.js: RFM empty uses restoreAndRenderEmpty for chartSegPie',
    "restoreAndRenderEmpty('chartSegPie')" in js)
chk('script.js: RFM empty uses restoreAndRenderEmpty for chartSegRev',
    "restoreAndRenderEmpty('chartSegRev')" in js)
# Should NOT fallback to global inside the !labels.length block anymore
# (the old pattern had renderSegPie(DATA.rfm_segments... right after !labels.length check)
# Count how many times restoreAndRenderEmpty('chartSegPie') appears — should be >= 1
chk('script.js: restoreAndRenderEmpty chartSegPie used at least once',
    js.count("restoreAndRenderEmpty('chartSegPie')") >= 1)

# ══ SCRIPT.JS — Fix 4: cancel rates labelled (global) ══
chk('script.js: cancelRateInv shows (global) when filtered',
    "cancelRateInv" in js and "% (global)" in js)
chk('script.js: cancelRateRows shows (global) when filtered',
    "cancelRateRows" in js and "% (global)" in js)
chk('script.js: rateSuffix = isFiltered guard in renderCancellationKPIs',
    'rateSuffix' in js)
chk('script.js: renderCancelChart sets cancelRateInv global explicitly',
    "setText('cancelRateInv'" in js and "(global)" in js)

# ══ SCRIPT.JS — Fix 5: quality report dedup cancel labels ══
chk('script.js: uses cancellation_rows_raw field',   'cancellation_rows_raw'  in js)
chk('script.js: uses cancellation_rows_dedup field', 'cancellation_rows_dedup' in js)
chk('script.js: before dedup label present',         'before dedup' in js)
chk('script.js: after dedup label present',          'after dedup'  in js)
chk('script.js: fallback to old cancellation_rows if new fields missing',
    'cancellation_rows_raw  != null' in js or 'cancellation_rows_raw != null' in js)

# ══ HTML — element IDs ══
for eid in ['cancelScopeBadge', 'cancelRateInv', 'cancelRateRows',
            'rfmTableBody', 'qualityReport', 'cancelInvoices', 'cancelValue']:
    chk(f'index.html: id="{eid}" exists', f'id="{eid}"' in html)
chk('index.html: Customer Segmentation aria-label',
    'aria-label="Customer Segmentation"' in html)
chk('index.html: global note on cancel rate cards',
    'Rate selalu dihitung secara global' in html)
chk('index.html: rfmFilterNote comment present',
    'rfmFilterNote' in html)

# ══ Summary ══
passed = sum(1 for ok, _, _ in results if ok)
failed = sum(1 for ok, _, _ in results if not ok)
print()
print('=' * 65)
print(f'  VALIDATION SUITE v3  —  {passed}/{len(results)} PASS')
print('=' * 65)
for ok, label, detail in results:
    icon = 'PASS' if ok else 'FAIL'
    det = f'  [{detail}]' if detail else ''
    print(f'  [{icon}]  {label}{det}')
print('=' * 65)
print(f'  PASSED: {passed}   FAILED: {failed}')
print('=' * 65)
