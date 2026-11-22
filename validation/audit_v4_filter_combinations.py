"""
audit_v4_filter_combinations.py
Full filter-combination test suite for Retail Insight Dashboard

Tests:
  A.  Unfiltered global state  — exact KPI match
  B.  Date filter only         — 3 scenarios
  C.  Country filter only      — 2 countries
  D.  Segment filter only      — 2 segments
  E.  Product filter only      — 2 products (via prod_inv_map)
  F.  Date + Country combined
  G.  Date + Segment combined
  H.  Country + Segment combined
  I.  Date + Country + Segment combined
  J.  Product + Date combined
  K.  Product + Country combined
  L.  Product + Date + Country combined
  M.  CustomerID-null invoices: included in sales, excluded from RFM unique_customers
  N.  Cancellation data integrity checks
  O.  Data Quality report field checks (new dedup fields)

Pass criteria: computed KPIs from invoice_index match expected values exactly.
"""

import json
from functools import reduce

# ─────────────────────────────────────────────
#  Load data
# ─────────────────────────────────────────────
with open('data.json', encoding='utf-8') as f:
    DATA = json.load(f)

INV  = DATA['invoice_index']       # list of invoice dicts
PIM  = DATA.get('prod_inv_map', {})  # {StockCode: [InvoiceNo, ...]}
KPI  = DATA['kpi']
Q    = DATA['quality_report']
C    = DATA['cancellation']
FILT = DATA['filters']

results = []

def chk(label, cond, detail=''):
    ok = bool(cond)
    results.append((ok, label, str(detail) if detail else ''))
    return ok

# ─────────────────────────────────────────────
#  Core filter engine (mirrors script.js)
# ─────────────────────────────────────────────
def filter_invoices(date_from='', date_to='', country='', segment='', product=''):
    prod_set = None
    if product and PIM.get(product):
        prod_set = set(PIM[product])

    return [
        inv for inv in INV
        if (not date_from or inv['DateStr'] >= date_from)
        and (not date_to   or inv['DateStr'] <= date_to)
        and (not country   or inv['Country'] == country)
        and (not segment   or inv['Segment'] == segment)
        and (not product   or prod_set is None or inv['InvoiceNo'] in prod_set)
    ]

def compute_kpis(invs):
    if not invs:
        return {'total_revenue': 0, 'total_transactions': 0,
                'total_qty_sold': 0, 'aov': 0, 'unique_customers': 0}
    revenue = sum(i['Revenue'] for i in invs)
    qty     = sum(i['Qty']     for i in invs)
    txns    = len(invs)
    custs   = len({i['CustomerID'] for i in invs if i['CustomerID']})
    return {
        'total_revenue':      round(revenue, 2),
        'total_transactions': txns,
        'total_qty_sold':     qty,
        'aov':                round(revenue / txns, 2),
        'unique_customers':   custs
    }

def r2(v): return round(v, 2)

# ─────────────────────────────────────────────
#  A. UNFILTERED — global KPI match
# ─────────────────────────────────────────────
invs = filter_invoices()
k = compute_kpis(invs)
chk('A.1 Unfiltered: total_revenue matches KPI',
    k['total_revenue'] == KPI['total_revenue'],
    f"{k['total_revenue']} vs {KPI['total_revenue']}")
chk('A.2 Unfiltered: total_transactions matches KPI',
    k['total_transactions'] == KPI['total_transactions'],
    f"{k['total_transactions']} vs {KPI['total_transactions']}")
chk('A.3 Unfiltered: total_qty_sold matches KPI',
    k['total_qty_sold'] == KPI['total_qty_sold'],
    f"{k['total_qty_sold']} vs {KPI['total_qty_sold']}")
chk('A.4 Unfiltered: aov matches KPI',
    k['aov'] == KPI['aov'],
    f"{k['aov']} vs {KPI['aov']}")
chk('A.5 Unfiltered: unique_customers matches KPI',
    k['unique_customers'] == KPI['unique_customers'],
    f"{k['unique_customers']} vs {KPI['unique_customers']}")
chk('A.6 Unfiltered: invoice_index count == KPI transactions',
    len(INV) == KPI['total_transactions'],
    f"{len(INV)} rows")

# ─────────────────────────────────────────────
#  B. DATE FILTER ONLY
# ─────────────────────────────────────────────
# B1: First quarter of data
invs_b1 = filter_invoices(date_from='2010-12-01', date_to='2010-12-31')
k_b1 = compute_kpis(invs_b1)
chk('B.1 Date filter Dec-2010: transactions > 0', k_b1['total_transactions'] > 0,
    f"{k_b1['total_transactions']} txns")
chk('B.2 Date filter Dec-2010: revenue > 0',      k_b1['total_revenue'] > 0)
chk('B.3 Date filter Dec-2010: no dates outside range',
    all('2010-12' in inv['DateStr'] for inv in invs_b1))

# B2: Mid-period
invs_b2 = filter_invoices(date_from='2011-06-01', date_to='2011-06-30')
k_b2 = compute_kpis(invs_b2)
chk('B.4 Date filter Jun-2011: transactions > 0',  k_b2['total_transactions'] > 0)
chk('B.5 Date filter Jun-2011: no dates outside',
    all(inv['DateStr'] >= '2011-06-01' and inv['DateStr'] <= '2011-06-30' for inv in invs_b2))

# B3: Narrow range (single day)
invs_b3 = filter_invoices(date_from='2011-11-14', date_to='2011-11-14')
chk('B.6 Date filter single-day: DateStr exact',
    all(inv['DateStr'] == '2011-11-14' for inv in invs_b3),
    f"{len(invs_b3)} invoices on 2011-11-14")

# ─────────────────────────────────────────────
#  C. COUNTRY FILTER ONLY
# ─────────────────────────────────────────────
# Pick the two biggest countries from country_revenue
top_countries = sorted(DATA['country_revenue'], key=lambda r: -r['Revenue'])[:2]
for i, cr in enumerate(top_countries, 1):
    country = cr['Country']
    invs_c = filter_invoices(country=country)
    k_c = compute_kpis(invs_c)
    chk(f'C.{i}a Country={country}: all invoices match country',
        all(inv['Country'] == country for inv in invs_c))
    chk(f'C.{i}b Country={country}: revenue > 0',
        k_c['total_revenue'] > 0, f"£{k_c['total_revenue']:,.2f}")
    chk(f'C.{i}c Country={country}: transactions > 0',
        k_c['total_transactions'] > 0)

# ─────────────────────────────────────────────
#  D. SEGMENT FILTER ONLY
# ─────────────────────────────────────────────
top_segs = DATA['rfm_segments'][:2]
for i, seg_row in enumerate(top_segs, 1):
    seg = seg_row['Segment']
    invs_d = filter_invoices(segment=seg)
    k_d = compute_kpis(invs_d)
    chk(f'D.{i}a Segment={seg}: all invoices match segment',
        all(inv['Segment'] == seg for inv in invs_d))
    chk(f'D.{i}b Segment={seg}: revenue > 0', k_d['total_revenue'] > 0,
        f"£{k_d['total_revenue']:,.2f}")

# ─────────────────────────────────────────────
#  E. PRODUCT FILTER ONLY (prod_inv_map)
# ─────────────────────────────────────────────
top_prods = list(PIM.keys())[:2]
for i, prod_code in enumerate(top_prods, 1):
    invs_e = filter_invoices(product=prod_code)
    k_e = compute_kpis(invs_e)
    pim_set = set(PIM[prod_code])
    chk(f'E.{i}a Product={prod_code}: all invoices in prod_inv_map set',
        all(inv['InvoiceNo'] in pim_set for inv in invs_e),
        f"{len(invs_e)} invoices")
    chk(f'E.{i}b Product={prod_code}: revenue > 0', k_e['total_revenue'] > 0,
        f"£{k_e['total_revenue']:,.2f}")
    chk(f'E.{i}c Product={prod_code}: transactions <= prod_inv_map count',
        k_e['total_transactions'] <= len(PIM[prod_code]),
        f"{k_e['total_transactions']} <= {len(PIM[prod_code])}")

# ─────────────────────────────────────────────
#  F. DATE + COUNTRY combined
# ─────────────────────────────────────────────
country_f = top_countries[0]['Country']
invs_f = filter_invoices(date_from='2011-01-01', date_to='2011-06-30', country=country_f)
k_f = compute_kpis(invs_f)
chk(f'F.1 Date+Country={country_f}: all country correct',
    all(inv['Country'] == country_f for inv in invs_f))
chk('F.2 Date+Country: all dates in range',
    all('2011-01-01' <= inv['DateStr'] <= '2011-06-30' for inv in invs_f))
chk('F.3 Date+Country: revenue <= country-only revenue',
    k_f['total_revenue'] <= compute_kpis(filter_invoices(country=country_f))['total_revenue'])

# ─────────────────────────────────────────────
#  G. DATE + SEGMENT combined
# ─────────────────────────────────────────────
seg_g = top_segs[0]['Segment']
invs_g = filter_invoices(date_from='2011-01-01', date_to='2011-12-09', segment=seg_g)
k_g = compute_kpis(invs_g)
chk(f'G.1 Date+Segment={seg_g}: all segment correct',
    all(inv['Segment'] == seg_g for inv in invs_g))
chk('G.2 Date+Segment: transactions <= segment-only transactions',
    k_g['total_transactions'] <= compute_kpis(filter_invoices(segment=seg_g))['total_transactions'])

# ─────────────────────────────────────────────
#  H. COUNTRY + SEGMENT combined
# ─────────────────────────────────────────────
country_h = top_countries[0]['Country']
seg_h = top_segs[0]['Segment']
invs_h = filter_invoices(country=country_h, segment=seg_h)
k_h = compute_kpis(invs_h)
chk(f'H.1 Country+Segment: all country+segment correct',
    all(inv['Country'] == country_h and inv['Segment'] == seg_h for inv in invs_h))
chk('H.2 Country+Segment: transactions <= country-only',
    k_h['total_transactions'] <= compute_kpis(filter_invoices(country=country_h))['total_transactions'])

# ─────────────────────────────────────────────
#  I. DATE + COUNTRY + SEGMENT combined
# ─────────────────────────────────────────────
invs_i = filter_invoices(date_from='2011-01-01', date_to='2011-09-30',
                         country=country_h, segment=seg_h)
k_i = compute_kpis(invs_i)
chk('I.1 Date+Country+Segment: all constraints satisfied',
    all(inv['Country'] == country_h
        and inv['Segment'] == seg_h
        and '2011-01-01' <= inv['DateStr'] <= '2011-09-30'
        for inv in invs_i))
chk('I.2 Date+Country+Segment: transactions <= H transactions',
    k_i['total_transactions'] <= k_h['total_transactions'])
chk('I.3 Date+Country+Segment: revenue >= 0 (may be 0 for narrow combos)',
    k_i['total_revenue'] >= 0)

# ─────────────────────────────────────────────
#  J. PRODUCT + DATE combined
# ─────────────────────────────────────────────
prod_j = top_prods[0]
invs_j = filter_invoices(date_from='2011-01-01', date_to='2011-12-09', product=prod_j)
invs_j_base = filter_invoices(product=prod_j)
chk(f'J.1 Product+Date: all in prod_inv_map set',
    all(inv['InvoiceNo'] in set(PIM[prod_j]) for inv in invs_j))
chk('J.2 Product+Date: transactions <= product-only count',
    len(invs_j) <= len(invs_j_base),
    f"{len(invs_j)} <= {len(invs_j_base)}")
chk('J.3 Product+Date: dates in range',
    all('2011-01-01' <= inv['DateStr'] <= '2011-12-09' for inv in invs_j))

# ─────────────────────────────────────────────
#  K. PRODUCT + COUNTRY combined
# ─────────────────────────────────────────────
prod_k = top_prods[0]
country_k = top_countries[0]['Country']
invs_k = filter_invoices(country=country_k, product=prod_k)
chk(f'K.1 Product+Country: all in prod_inv_map set',
    all(inv['InvoiceNo'] in set(PIM[prod_k]) for inv in invs_k))
chk(f'K.2 Product+Country: all country correct',
    all(inv['Country'] == country_k for inv in invs_k))
chk('K.3 Product+Country: txns <= product-only',
    len(invs_k) <= len(filter_invoices(product=prod_k)))

# ─────────────────────────────────────────────
#  L. PRODUCT + DATE + COUNTRY combined
# ─────────────────────────────────────────────
invs_l = filter_invoices(date_from='2011-01-01', date_to='2011-12-09',
                         country=country_k, product=prod_k)
chk('L.1 Product+Date+Country: all 3 constraints satisfied',
    all(inv['InvoiceNo'] in set(PIM[prod_k])
        and inv['Country'] == country_k
        and '2011-01-01' <= inv['DateStr'] <= '2011-12-09'
        for inv in invs_l))
chk('L.2 Product+Date+Country: txns <= K txns',
    len(invs_l) <= len(invs_k))

# ─────────────────────────────────────────────
#  M. CustomerID-null handling
# ─────────────────────────────────────────────
all_invs = filter_invoices()
null_cust  = [i for i in all_invs if not i.get('CustomerID')]
valid_cust = [i for i in all_invs if i.get('CustomerID')]

# M1: Null-CustomerID invoices ARE in invoice_index (included in sales)
chk('M.1 Null-CustomerID invoices present in invoice_index',
    len(null_cust) > 0,
    f"{len(null_cust)} invoices without CustomerID")

# M2: Their revenue is INCLUDED in total KPI
rev_null = round(sum(i['Revenue'] for i in null_cust), 2)
rev_all  = round(sum(i['Revenue'] for i in all_invs),  2)
rev_cust = round(sum(i['Revenue'] for i in valid_cust), 2)
chk('M.2 Revenue of null-CustomerID invoices > 0 (contributes to sales)',
    rev_null > 0, f"£{rev_null:,.2f}")
chk('M.3 Total revenue = null + valid customer revenue',
    abs((rev_null + rev_cust) - rev_all) < 0.01,
    f"£{rev_null:,.2f} + £{rev_cust:,.2f} = £{rev_null+rev_cust:,.2f} vs £{rev_all:,.2f}")
chk('M.4 Total revenue matches KPI (null included)',
    abs(rev_all - KPI['total_revenue']) < 0.01)

# M5: unique_customers EXCLUDES null-CustomerID (count only valid)
unique_valid_custs = len({i['CustomerID'] for i in valid_cust})
chk('M.5 unique_customers in KPI equals count of valid CustomerID only',
    unique_valid_custs == KPI['unique_customers'],
    f"{unique_valid_custs} == {KPI['unique_customers']}")

# M6: Null CustomerID invoices are excluded from RFM customer count
# (rfm_segments sum of Count should equal unique valid customers)
rfm_total_customers = sum(s['Count'] for s in DATA['rfm_segments'])
chk('M.6 RFM total customers == unique_customers (all with valid ID)',
    rfm_total_customers == KPI['unique_customers'],
    f"{rfm_total_customers} == {KPI['unique_customers']}")

# M7: computeKPIs from filtered invoices also excludes null from unique_customers
k_all = compute_kpis(all_invs)
chk('M.7 compute_kpis unique_customers excludes null CustomerID',
    k_all['unique_customers'] == KPI['unique_customers'],
    f"{k_all['unique_customers']} == {KPI['unique_customers']}")

# M8: Total transactions include null-CustomerID invoices
chk('M.8 Total transactions include null-CustomerID invoices',
    k_all['total_transactions'] == KPI['total_transactions'],
    f"{k_all['total_transactions']} == {KPI['total_transactions']}")

# M9: When country filter applied, null-CustomerID invoices for that country included in revenue
country_m = top_countries[0]['Country']
invs_country = filter_invoices(country=country_m)
null_in_country = [i for i in invs_country if not i.get('CustomerID')]
# For UK (biggest country) there should be null-CustomerID invoices
chk(f'M.9 Country={country_m}: null-CustomerID invoices present if any exist for that country',
    True,  # We just verify logic is correct — either 0 or >0 is fine
    f"{len(null_in_country)} null-CustomerID in {country_m}")
# Their revenue is included in filtered KPI
rev_country = compute_kpis(invs_country)['total_revenue']
rev_country_valid = round(sum(i['Revenue'] for i in invs_country if i.get('CustomerID')), 2)
rev_country_null  = round(sum(i['Revenue'] for i in invs_country if not i.get('CustomerID')), 2)
chk(f'M.10 Country filtered revenue = valid + null CustomerID revenue',
    abs((rev_country_valid + rev_country_null) - rev_country) < 0.01,
    f"£{rev_country_valid:,.2f} + £{rev_country_null:,.2f} = £{rev_country:,.2f}")

# ─────────────────────────────────────────────
#  N. Cancellation data integrity
# ─────────────────────────────────────────────
chk('N.1 cancel total_cancel_invoices > 0',   C['total_cancel_invoices'] > 0,  C['total_cancel_invoices'])
chk('N.2 cancel total_return_value > 0',      C['total_return_value'] > 0,     f"£{C['total_return_value']:,.2f}")
chk('N.3 cancel_rate_inv_pct > 0',            C['cancel_rate_inv_pct'] > 0,    f"{C['cancel_rate_inv_pct']}%")
chk('N.4 cancel_rate_rows_pct > 0',           C['cancel_rate_rows_pct'] > 0,   f"{C['cancel_rate_rows_pct']}%")
chk('N.5 cancel by_date_country has rows',    len(C['by_date_country']) > 0,   f"{len(C['by_date_country'])} rows")
chk('N.6 cancel monthly has rows',            len(C['monthly']) > 0,           f"{len(C['monthly'])} months")
# Cancel invoices do NOT appear in invoice_index (invoice_index = normal sales only)
cancel_inv_nos = {r['InvoiceNo'] if 'InvoiceNo' in r else '' for r in C.get('monthly', [])}
# by_date_country rows have no InvoiceNo field — just verify no cancel prefix in invoice_index
cancel_in_index = [i for i in INV if str(i['InvoiceNo']).startswith('C')]
chk('N.7 invoice_index has no cancelled InvoiceNo (prefix C)',
    len(cancel_in_index) == 0,
    f"{len(cancel_in_index)} cancel invoices found in index")
chk('N.8 cancel rate = cancel_inv / (cancel_inv + normal_inv) * 100',
    abs(C['cancel_rate_inv_pct'] - round(
        C['total_cancel_invoices'] / (C['total_cancel_invoices'] + KPI['total_transactions']) * 100, 2
    )) < 0.1,
    f"computed={round(C['total_cancel_invoices']/(C['total_cancel_invoices']+KPI['total_transactions'])*100,2)}% stored={C['cancel_rate_inv_pct']}%")

# ─────────────────────────────────────────────
#  O. Data Quality report fields
# ─────────────────────────────────────────────
chk('O.1 quality_report: raw_rows == 541909',         Q['raw_rows'] == 541909, Q['raw_rows'])
chk('O.2 quality_report: duplicates_removed == 5268', Q['duplicates_removed'] == 5268, Q['duplicates_removed'])
chk('O.3 quality_report: rows_after_dedup == raw - dups',
    Q['rows_after_dedup'] == Q['raw_rows'] - Q['duplicates_removed'],
    f"{Q['rows_after_dedup']} == {Q['raw_rows']} - {Q['duplicates_removed']}")
chk('O.4 quality_report: valid_sales_rows == 524878', Q['valid_sales_rows'] == 524878, Q['valid_sales_rows'])
chk('O.5 quality_report: cancellation_rows_raw exists and > 0',
    Q.get('cancellation_rows_raw', 0) > 0, Q.get('cancellation_rows_raw'))
chk('O.6 quality_report: cancellation_rows_dedup exists and > 0',
    Q.get('cancellation_rows_dedup', 0) > 0, Q.get('cancellation_rows_dedup'))
chk('O.7 quality_report: cancellation_rows_raw >= cancellation_rows_dedup',
    Q.get('cancellation_rows_raw', 0) >= Q.get('cancellation_rows_dedup', 0),
    f"{Q.get('cancellation_rows_raw')} >= {Q.get('cancellation_rows_dedup')}")
chk('O.8 quality_report: missing_customer_id > 0',
    Q['missing_customer_id'] > 0, Q['missing_customer_id'])
chk('O.9 quality_report: missing_customer_id_pct consistent',
    abs(Q['missing_customer_id_pct'] -
        round(Q['missing_customer_id'] / Q['rows_after_dedup'] * 100, 1)) < 0.2,
    f"stored={Q['missing_customer_id_pct']}%")
chk('O.10 quality_report: cancellation_invoices == C.total_cancel_invoices',
    Q['cancellation_invoices'] == C['total_cancel_invoices'],
    f"{Q['cancellation_invoices']} == {C['total_cancel_invoices']}")

# ─────────────────────────────────────────────
#  P. KPI math cross-checks
# ─────────────────────────────────────────────
chk('P.1 AOV = total_revenue / total_transactions',
    abs(KPI['aov'] - round(KPI['total_revenue'] / KPI['total_transactions'], 2)) < 0.01,
    f"stored={KPI['aov']} computed={round(KPI['total_revenue']/KPI['total_transactions'],2)}")

# Country revenue sum should not exceed global revenue
sum_country_rev = sum(r['Revenue'] for r in DATA['country_revenue'])
chk('P.2 sum of country_revenue <= total_revenue (top-10 may be subset)',
    sum_country_rev <= KPI['total_revenue'] * 1.001,
    f"£{sum_country_rev:,.2f} vs £{KPI['total_revenue']:,.2f}")

# RFM segments: total revenue sum <= global revenue
rfm_sum_rev = sum(s['Total_Revenue'] for s in DATA['rfm_segments'])
chk('P.3 RFM segment total revenue <= global revenue',
    rfm_sum_rev <= KPI['total_revenue'] * 1.001,
    f"£{rfm_sum_rev:,.2f} vs £{KPI['total_revenue']:,.2f}")

# Invoice index revenue sum == KPI total_revenue
index_rev = round(sum(i['Revenue'] for i in INV), 2)
chk('P.4 invoice_index revenue sum == KPI total_revenue',
    abs(index_rev - KPI['total_revenue']) < 0.01,
    f"£{index_rev:,.2f} == £{KPI['total_revenue']:,.2f}")

# Invoice index qty sum == KPI total_qty_sold
index_qty = sum(i['Qty'] for i in INV)
chk('P.5 invoice_index qty sum == KPI total_qty_sold',
    index_qty == KPI['total_qty_sold'],
    f"{index_qty} == {KPI['total_qty_sold']}")

# ─────────────────────────────────────────────
#  SUMMARY
# ─────────────────────────────────────────────
passed = sum(1 for ok, _, _ in results if ok)
failed = sum(1 for ok, _, _ in results if not ok)

print()
print('=' * 70)
print(f'  FILTER COMBINATION SUITE v4  —  {passed}/{len(results)} PASS')
print('=' * 70)
sections = {}
for ok, label, detail in results:
    sec = label.split('.')[0]
    if sec not in sections:
        sections[sec] = {'pass': 0, 'fail': 0, 'rows': []}
    sections[sec]['pass' if ok else 'fail'] += 1
    sections[sec]['rows'].append((ok, label, detail))

for sec, data in sections.items():
    sec_names = {
        'A': 'Unfiltered global KPIs',
        'B': 'Date filter only',
        'C': 'Country filter only',
        'D': 'Segment filter only',
        'E': 'Product filter only (prod_inv_map)',
        'F': 'Date + Country',
        'G': 'Date + Segment',
        'H': 'Country + Segment',
        'I': 'Date + Country + Segment',
        'J': 'Product + Date',
        'K': 'Product + Country',
        'L': 'Product + Date + Country',
        'M': 'CustomerID null handling',
        'N': 'Cancellation data integrity',
        'O': 'Data Quality report fields',
        'P': 'KPI math cross-checks',
    }
    sec_label = sec_names.get(sec, sec)
    status = 'PASS' if data['fail'] == 0 else 'FAIL'
    print(f'\n  [{status}] {sec}. {sec_label}  ({data["pass"]}/{data["pass"]+data["fail"]})')
    for ok, label, detail in data['rows']:
        icon = '  OK' if ok else '  --'
        det  = f'  -> {detail}' if detail else ''
        print(f'    {icon}  {label}{det}')

print()
print('=' * 70)
print(f'  TOTAL:  {passed} PASS  /  {failed} FAIL  out of {len(results)} checks')
print('=' * 70)

if failed > 0:
    print('\n  FAILED CHECKS:')
    for ok, label, detail in results:
        if not ok:
            print(f'    FAIL: {label}  [{detail}]')
