import json

with open('data.json', encoding='utf-8') as f:
    d = json.load(f)

q = d['quality_report']
print('=== quality_report keys ===')
for k, v in q.items():
    print(f'  {k}: {v}')

print('\n=== KPI ===')
for k, v in d['kpi'].items():
    print(f'  {k}: {v}')

print('\n=== meta ===')
for k, v in d['meta'].items():
    print(f'  {k}: {v}')

inv = d['invoice_index']
print(f'\n=== invoice_index ===')
print(f'  keys: {list(inv[0].keys())}')
print(f'  total rows: {len(inv)}')

no_cust  = [x for x in inv if not x.get('CustomerID')]
has_cust = [x for x in inv if x.get('CustomerID')]
rev_all  = sum(x['Revenue'] for x in inv)
rev_cust = sum(x['Revenue'] for x in has_cust)
rev_no   = sum(x['Revenue'] for x in no_cust)
print(f'  with CustomerID:    {len(has_cust):>6} invoices  revenue={rev_cust:>14,.2f}')
print(f'  without CustomerID: {len(no_cust):>6} invoices  revenue={rev_no:>14,.2f}')
print(f'  total:              {len(inv):>6} invoices  revenue={rev_all:>14,.2f}')
print(f'  KPI total_revenue:  {d["kpi"]["total_revenue"]:>24,.2f}')
print(f'  match: {abs(rev_all - d["kpi"]["total_revenue"]) < 1}')

pim = d.get('prod_inv_map', {})
print(f'\n=== prod_inv_map ===')
print(f'  products covered: {len(pim)}')

top50 = {p["code"] for p in d["filters"]["top_products"]}
covered = top50 & set(pim.keys())
print(f'  top-50 filter products covered: {len(covered)}/50')

print('\n=== filters.top_products sample ===')
for p in d['filters']['top_products'][:3]:
    print(f'  {p}')

print('\n=== cancellation keys ===')
for k, v in d['cancellation'].items():
    if not isinstance(v, list):
        print(f'  {k}: {v}')
print(f'  monthly: {len(d["cancellation"].get("monthly",[]))} rows')
print(f'  by_date_country: {len(d["cancellation"].get("by_date_country",[]))} rows')
