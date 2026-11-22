"""
Portable final reconciliation for Retail Insight AI Dashboard.

Run from repository root:
    python validation/reconcile.py

The audit scripts read files using relative paths, so this script executes
them with dashboard/ as their working directory.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD = ROOT / "dashboard"
VALIDATION = ROOT / "validation"
REPORTS = ROOT / "reports"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def check_group(title: str, checks: dict[str, bool]) -> bool:
    print(f"\n[{title}]")
    for label, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    passed = sum(bool(v) for v in checks.values())
    print(f"  Result: {passed}/{len(checks)} PASS, {len(checks)-passed} FAIL")
    return all(checks.values())


def run_audit(name: str, pattern: str) -> tuple[bool, str]:
    path = VALIDATION / name
    if not path.is_file():
        return False, f"Audit script not found: {path}"
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=DASHBOARD,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (result.stdout or "") + (result.stderr or "")
    passed = result.returncode == 0 and re.search(pattern, output) is not None
    return passed, output.strip()


print("=" * 68)
print("RETAIL INSIGHT AI DASHBOARD — PORTABLE FINAL RECONCILIATION")
print(f"Repository: {ROOT}")
print("=" * 68)

js = read_text(DASHBOARD / "script.js")
html = read_text(DASHBOARD / "index.html")
readme = read_text(ROOT / "README.md")

required = [
    ROOT / "README.md", ROOT / ".gitignore",
    DASHBOARD / "index.html", DASHBOARD / "style.css",
    DASHBOARD / "script.js", DASHBOARD / "data.json",
    ROOT / "data_processing" / "prepare_data.py",
    ROOT / "data_processing" / "analyze_retail.py",
    ROOT / "data_processing" / "_check_data.py",
    VALIDATION / "audit_v3.py",
    VALIDATION / "audit_v4_filter_combinations.py",
    VALIDATION / "reconcile.py",
    REPORTS / "Laporan_Validasi_Retail_Insight_AI.txt",
]
inventory = {str(p.relative_to(ROOT)): p.is_file() for p in required}
inventory_ok = check_group("1. REQUIRED FILE INVENTORY", inventory)

js_checks = {
    "Product invoice map integration":
        "prod_inv_map" in js and "prodInvSet.has(inv.InvoiceNo)" in js,
    "Invoice-based product chart renderer":
        "function renderProductChartsFromInvoices" in js,
    "Proportional factor calculation absent":
        "const factor =" not in js
        and "cSlice.Revenue * factor" not in js
        and "sSlice.Revenue * factor" not in js,
    "RFM empty-state restoration":
        "restoreAndRenderEmpty('chartSegPie')" in js
        and "restoreAndRenderEmpty('chartSegRev')" in js,
    "Cancellation global-scope indicator":
        "rateSuffix" in js and "(global)" in js,
    "Cancellation raw/dedup fields":
        "cancellation_rows_raw" in js
        and "cancellation_rows_dedup" in js,
}
implementation_ok = check_group("2. DASHBOARD IMPLEMENTATION", js_checks)

html_checks = {
    "cancelScopeBadge": 'id="cancelScopeBadge"' in html,
    "cancelRateInv": 'id="cancelRateInv"' in html,
    "cancelRateRows": 'id="cancelRateRows"' in html,
    "qualityReport": 'id="qualityReport"' in html,
    "rfmTableBody": 'id="rfmTableBody"' in html,
    "Customer Segmentation aria-label":
        'aria-label="Customer Segmentation"' in html,
}
html_ok = check_group("3. HTML STRUCTURE", html_checks)

data = {}
data_error = ""
try:
    with (DASHBOARD / "data.json").open(encoding="utf-8") as f:
        data = json.load(f)
except Exception as exc:
    data_error = str(exc)

if data:
    q = data.get("quality_report", {})
    k = data.get("kpi", {})
    inv = data.get("invoice_index", [])
    pim = data.get("prod_inv_map", {})
    json_checks = {
        "quality_report exists": isinstance(q, dict),
        "kpi exists": isinstance(k, dict),
        "invoice_index is a list": isinstance(inv, list),
        "prod_inv_map is an object": isinstance(pim, dict),
        "Raw rows = 541,909": q.get("raw_rows") == 541909,
        "Valid sales rows = 524,878": q.get("valid_sales_rows") == 524878,
        "Transactions = 19,960": k.get("total_transactions") == 19960,
        "Revenue = GBP 10,642,110.80":
            abs(float(k.get("total_revenue", 0)) - 10642110.80) < 0.005,
        "Quantity sold = 5,572,420": k.get("total_qty_sold") == 5572420,
        "AOV = GBP 533.17": abs(float(k.get("aov", 0)) - 533.17) < 0.005,
        "Unique customers = 4,338": k.get("unique_customers") == 4338,
        "Invoice index count matches KPI":
            len(inv) == k.get("total_transactions"),
        "Product invoice map has 50 products": len(pim) == 50,
        "Cancellation raw rows = 9,288":
            q.get("cancellation_rows_raw") == 9288,
        "Cancellation dedup rows = 9,251":
            q.get("cancellation_rows_dedup") == 9251,
    }
else:
    json_checks = {"data.json loads as valid JSON": False}
    print(f"JSON load error: {data_error}")
json_ok = check_group("4. DATA.JSON AND KPI INTEGRITY", json_checks)

readme_checks = {
    "README documents dashboard/data.json": "dashboard/data.json" in readme,
    "README documents data/raw/Online Retail.xlsx":
        "data/raw/Online Retail.xlsx" in readme,
    "README does not ask for manual Windows path edits":
        "Sesuaikan variabel `FILE_IN`" not in readme
        and "path file lokal dari lingkungan pengembangan sebelumnya" not in readme,
    "README documents both audit scripts":
        "audit_v3.py" in readme and "audit_v4_filter_combinations.py" in readme,
}
readme_ok = check_group("5. README DOCUMENTATION", readme_checks)

v3_ok, v3_output = run_audit("audit_v3.py", r"PASSED:\s*48\s+FAILED:\s*0")
v4_ok, v4_output = run_audit(
    "audit_v4_filter_combinations.py",
    r"TOTAL:\s*79 PASS\s*/\s*0 FAIL out of 79 checks",
)

print("\n[6. AUTOMATED AUDIT EXECUTION]")
print("\n--- audit_v3.py ---")
print(v3_output or "(no output)")
print(f"Reconciliation verdict: {'PASS' if v3_ok else 'FAIL'}")
print("\n--- audit_v4_filter_combinations.py ---")
print(v4_output or "(no output)")
print(f"Reconciliation verdict: {'PASS' if v4_ok else 'FAIL'}")

summary = {
    "Required file inventory": inventory_ok,
    "Dashboard implementation": implementation_ok,
    "HTML structure": html_ok,
    "JSON and KPI integrity": json_ok,
    "README documentation": readme_ok,
    "Audit v3 (48/48)": v3_ok,
    "Audit v4 (79/79)": v4_ok,
}
print("\n" + "=" * 68)
print("FINAL SUMMARY")
print("=" * 68)
for label, ok in summary.items():
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
all_ok = all(summary.values())
print("-" * 68)
print(f"OVERALL: {'FINAL CHECKS PASS' if all_ok else 'ACTION REQUIRED'}")
print("=" * 68)
sys.exit(0 if all_ok else 1)
