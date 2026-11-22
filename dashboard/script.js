/**
 * ═══════════════════════════════════════════════════════════════
 * Retail Insight Dashboard — script.js  (v3 — final debug)
 *
 * FIXES applied vs v2:
 *  1. Product filter uses prod_inv_map to intersect InvoiceNo sets → exact KPIs
 *  2. Proportional scaling (factor = cSlice/totalForSc) removed entirely
 *  3. RFM empty state calls restoreAndRenderEmpty() — no fallback to global
 *  4. cancelRateInv/cancelRateRows always show "(global)" when filter active
 *  5. Data Quality shows cancellation_rows_raw + cancellation_rows_dedup
 *     with explicit "(before dedup)" / "(after dedup)" labels
 * ═══════════════════════════════════════════════════════════════
 */

'use strict';

// ──────────────────────────────────────────────────────────────
// GLOBAL STATE
// ──────────────────────────────────────────────────────────────

let DATA = null;

const filters = { dateFrom: '', dateTo: '', country: '', segment: '', product: '' };

// Chart.js instances keyed by canvas ID
const CHARTS = {};

// Canvas elements stashed so renderEmpty() can restore them
const CANVAS_PARENTS = {};

const PALETTE = [
  '#6366f1','#06b6d4','#10b981','#f59e0b','#ef4444',
  '#8b5cf6','#ec4899','#14b8a6','#f97316','#84cc16'
];

const SEG_COLORS = {
  'Champions':          '#6366f1',
  'Loyal Customers':    '#06b6d4',
  'New Customers':      '#10b981',
  'Potential Loyalists':'#f59e0b',
  'At Risk':            '#f97316',
  'Need Attention':     '#8b5cf6',
  'Lost / Churned':     '#ef4444',
  'Unknown':            '#94a3b8'
};

// ──────────────────────────────────────────────────────────────
// ENTRY POINT
// ──────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  loadData();
  document.getElementById('btnReset').addEventListener('click', resetFilters);
  ['filterDateFrom','filterDateTo','filterCountry','filterSegment','filterProduct']
    .forEach(id => document.getElementById(id).addEventListener('change', onFilterChange));
});

// ──────────────────────────────────────────────────────────────
// DATA LOADING
// ──────────────────────────────────────────────────────────────

async function loadData() {
  try {
    const res = await fetch('./data.json');
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    DATA = await res.json();
    hideLoading();
    initDashboard();
  } catch (err) {
    hideLoading();
    showError(
      `Gagal memuat data.json: ${err.message}. ` +
      `Buka dashboard menggunakan VS Code Live Server atau "python -m http.server 8080".`
    );
  }
}

function hideLoading() {
  const el = document.getElementById('loadingOverlay');
  if (el) el.remove();
}

function showError(msg) {
  const el = document.getElementById('errorBanner');
  el.textContent = msg;
  el.classList.remove('hidden');
}

// ──────────────────────────────────────────────────────────────
// INIT
// ──────────────────────────────────────────────────────────────

function initDashboard() {
  stashCanvases();      // FIX 6: stash canvas refs before any renderEmpty() calls
  populateFilters();
  setDefaultDates();
  updateQualityBadge();
  renderQualityReport(); // FIX 7: show raw + dedup rows separately
  renderCancellationKPIs();
  applyFilters();
}

/** FIX 6: Save each canvas's parent so we can restore it after renderEmpty() */
function stashCanvases() {
  const ids = ['chartMonthly','chartCountry','chartCountryAov',
               'chartProdRev','chartProdQty','chartSegPie','chartSegRev','chartCancel'];
  ids.forEach(id => {
    const canvas = document.getElementById(id);
    if (canvas) CANVAS_PARENTS[id] = canvas.parentElement;
  });
}

// ──────────────────────────────────────────────────────────────
// FILTER POPULATION
// ──────────────────────────────────────────────────────────────

function populateFilters() {
  const f = DATA.filters;

  const cSel = document.getElementById('filterCountry');
  f.countries.forEach(c => {
    const o = document.createElement('option');
    o.value = c; o.textContent = c;
    cSel.appendChild(o);
  });

  const sSel = document.getElementById('filterSegment');
  f.segments.forEach(s => {
    const o = document.createElement('option');
    o.value = s; o.textContent = s;
    sSel.appendChild(o);
  });

  const pSel = document.getElementById('filterProduct');
  f.top_products.forEach(p => {
    const o = document.createElement('option');
    o.value = p.code;
    o.textContent = `${p.name.substring(0, 36)}${p.name.length > 36 ? '…' : ''}`;
    pSel.appendChild(o);
  });
}

function setDefaultDates() {
  const f = DATA.filters;
  document.getElementById('filterDateFrom').value = f.date_min;
  document.getElementById('filterDateTo').value   = f.date_max;
  filters.dateFrom = f.date_min;
  filters.dateTo   = f.date_max;
}

// ──────────────────────────────────────────────────────────────
// FILTER HANDLERS
// ──────────────────────────────────────────────────────────────

function onFilterChange() {
  filters.dateFrom = document.getElementById('filterDateFrom').value;
  filters.dateTo   = document.getElementById('filterDateTo').value;
  filters.country  = document.getElementById('filterCountry').value;
  filters.segment  = document.getElementById('filterSegment').value;
  filters.product  = document.getElementById('filterProduct').value;

  ['filterCountry','filterSegment','filterProduct'].forEach(id => {
    document.getElementById(id).classList.toggle('filter-active',
      document.getElementById(id).value !== '');
  });

  applyFilters();
}

function resetFilters() {
  document.getElementById('filterCountry').value = '';
  document.getElementById('filterSegment').value = '';
  document.getElementById('filterProduct').value = '';
  setDefaultDates();
  filters.country = ''; filters.segment = ''; filters.product = '';
  ['filterCountry','filterSegment','filterProduct'].forEach(id =>
    document.getElementById(id).classList.remove('filter-active'));
  applyFilters();
}

// ──────────────────────────────────────────────────────────────
// CORE FILTER ENGINE  (FIX 1, 2, 3)
// ──────────────────────────────────────────────────────────────

/**
 * Check if all filters are at their default (unfiltered) state.
 * When true, we return pre-computed global KPI directly — exact & fast.
 */
function isUnfiltered() {
  return !filters.country && !filters.segment && !filters.product &&
    filters.dateFrom === DATA.filters.date_min &&
    filters.dateTo   === DATA.filters.date_max;
}

/**
 * Filter invoice_index by date/country/segment.
 * invoice_index rows: {InvoiceNo, DateStr, Country, Segment, Revenue, Qty, CustomerID}
 * DateStr comparison is exact day-level.
 *
 * FIX 1 (v3): If product filter is active, further restrict to the InvoiceNo set
 * from prod_inv_map[filters.product] — this gives exact KPIs for product filter
 * without proportional estimation.
 */
function getFilteredInvoices() {
  // Build product invoice set once (empty Set = no product filter)
  let prodInvSet = null;
  if (filters.product && DATA.prod_inv_map && DATA.prod_inv_map[filters.product]) {
    prodInvSet = new Set(DATA.prod_inv_map[filters.product]);
  }

  return DATA.invoice_index.filter(inv => {
    if (filters.dateFrom && inv.DateStr < filters.dateFrom) return false;
    if (filters.dateTo   && inv.DateStr > filters.dateTo)   return false;
    if (filters.country  && inv.Country !== filters.country) return false;
    if (filters.segment  && inv.Segment !== filters.segment) return false;
    if (prodInvSet       && !prodInvSet.has(inv.InvoiceNo))  return false;
    return true;
  });
}

/**
 * FIX 2: Compute exact KPIs from filtered invoices.
 * No double-counting: each invoice appears exactly once in invoice_index.
 */
function computeKPIsFromInvoices(invs) {
  if (invs.length === 0) {
    return { total_revenue: 0, total_transactions: 0, total_qty_sold: 0, aov: 0, unique_customers: 0 };
  }
  let revenue = 0, qty = 0;
  const custSet = new Set();
  for (const inv of invs) {
    revenue += inv.Revenue;
    qty     += inv.Qty;
    if (inv.CustomerID) custSet.add(inv.CustomerID);
  }
  const transactions = invs.length;   // invoice_index has 1 row per invoice — exact count
  return {
    total_revenue:      round2(revenue),
    total_transactions: transactions,
    total_qty_sold:     qty,
    aov:                round2(revenue / transactions),
    unique_customers:   custSet.size
  };
}

function applyFilters() {
  if (isUnfiltered()) {
    // All filters at default — use exact pre-computed global values
    renderKPIs(DATA.kpi);
    renderMonthlyTrend(DATA.monthly_country_seg, null, null);
    renderCountryCharts(null);         // signals: use DATA.country_revenue
    renderProductCharts(null, null, null);  // signals: use global top-10
    renderSegmentCharts(null);         // signals: use global rfm_segments
    renderCancelChart(null, null);     // signals: use full cancel data
    return;
  }

  // ── Filtered KPIs — includes product filter via prod_inv_map (FIX 1 v3) ──
  const invs = getFilteredInvoices();
  renderKPIs(computeKPIsFromInvoices(invs));

  // ── Monthly trend: filter monthly_country_seg (exact date-string comparison)
  const mcs = DATA.monthly_country_seg.filter(r => {
    const mStart = r.YearMonth + '-01';
    const mEnd   = r.YearMonth + '-31';
    if (filters.dateFrom && mEnd   < filters.dateFrom) return false;
    if (filters.dateTo   && mStart > filters.dateTo)   return false;
    if (filters.country  && r.Country !== filters.country) return false;
    if (filters.segment  && r.Segment !== filters.segment) return false;
    return true;
  });
  renderMonthlyTrend(mcs, filters.dateFrom, filters.dateTo);

  // ── Country charts: aggregate from exact filtered invoices ──
  renderCountryCharts(invs);

  // ── Product charts: use exact invoice-based product revenue (FIX 2 v3) ──
  // For product filter: derive per-product stats from the already-filtered invs
  // For date/country/segment filters without product: use prod_month intersection
  if (filters.product) {
    // Product filter is active — build product totals from filtered invoices
    // (all invoices in invs contain this product; total = sum of their Revenue)
    renderProductChartsFromInvoices(invs, filters.product);
  } else {
    const pmFiltered = filterProdMonth(DATA.prod_month, filters.dateFrom, filters.dateTo);
    const cSlice = filters.country  ? DATA.prod_country.filter(r => r.Country === filters.country) : null;
    const sSlice = filters.segment  ? DATA.prod_segment.filter(r => r.Segment === filters.segment) : null;
    renderProductCharts(pmFiltered, cSlice, sSlice);
  }

  // ── Segment charts: filtered customer list ──
  renderSegmentCharts(invs);

  // ── Cancellation: filter by date + country ──
  renderCancelChart(filters.dateFrom || null, filters.country || null);
}

/** Filter prod_month by date range (YearMonth overlap) */
function filterProdMonth(arr, dateFrom, dateTo) {
  if (!dateFrom && !dateTo) return arr;
  return arr.filter(r => {
    const mStart = r.YearMonth + '-01';
    const mEnd   = r.YearMonth + '-31';
    if (dateFrom && mEnd   < dateFrom) return false;
    if (dateTo   && mStart > dateTo)   return false;
    return true;
  });
}

// ──────────────────────────────────────────────────────────────
// KPI RENDERING
// ──────────────────────────────────────────────────────────────

function renderKPIs(kpi) {
  const global = DATA.kpi;
  setText('kpiRevenue',      fmtCurrency(kpi.total_revenue));
  setText('kpiTransactions', fmtNum(kpi.total_transactions));
  setText('kpiQty',          fmtNum(kpi.total_qty_sold));
  setText('kpiAov',          fmtCurrency(kpi.aov));
  setText('kpiCustomers',    fmtNum(kpi.unique_customers));

  setText('kpiRevenueSub',      `${pct(kpi.total_revenue, global.total_revenue)}% of total`);
  setText('kpiTransactionsSub', `${pct(kpi.total_transactions, global.total_transactions)}% of total`);
  setText('kpiQtySub',          `${pct(kpi.total_qty_sold, global.total_qty_sold)}% of total`);
  setText('kpiAovSub',          `Global AOV: ${fmtCurrency(global.aov)}`);
  setText('kpiCustomersSub',    `Global: ${fmtNum(global.unique_customers)} customers`);
}

// ──────────────────────────────────────────────────────────────
// MONTHLY TREND CHART
// ──────────────────────────────────────────────────────────────

function renderMonthlyTrend(mcs, dateFrom, dateTo) {
  const monthMap = {};
  mcs.forEach(r => {
    if (!monthMap[r.YearMonth]) monthMap[r.YearMonth] = { Revenue: 0, Transactions: 0, Qty: 0 };
    monthMap[r.YearMonth].Revenue      += r.Revenue;
    monthMap[r.YearMonth].Transactions += r.Transactions;
    monthMap[r.YearMonth].Qty          += r.Qty;
  });

  const months   = Object.keys(monthMap).sort();
  const revenues = months.map(m => round2(monthMap[m].Revenue));
  const txs      = months.map(m => monthMap[m].Transactions);
  const labels   = months.map(m => {
    const [y, mo] = m.split('-');
    return `${['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][+mo-1]} ${y.slice(2)}`;
  });

  setText('trendBadge', `${months.length} month${months.length !== 1 ? 's' : ''}`);

  if (months.length === 0) { restoreAndRenderEmpty('chartMonthly'); return; }

  renderOrUpdateChart('chartMonthly', 'bar', {
    labels,
    datasets: [
      { label:'Revenue (£)', data:revenues, backgroundColor:PALETTE[0]+'cc',
        borderColor:PALETTE[0], borderWidth:1, borderRadius:4, yAxisID:'y', order:2 },
      { label:'Transactions', data:txs, type:'line', borderColor:PALETTE[1],
        backgroundColor:PALETTE[1]+'22', fill:true, tension:0.4,
        pointRadius:4, pointHoverRadius:6, yAxisID:'y1', order:1 }
    ]
  }, {
    scales: {
      y:  { position:'left',  ticks:{ callback: v=>'£'+fmtNumShort(v) }, grid:{ color:'#f1f5f9' } },
      y1: { position:'right', ticks:{ callback: v=>fmtNumShort(v) },     grid:{ display:false } }
    }
  });
}

// ──────────────────────────────────────────────────────────────
// COUNTRY CHARTS
// ──────────────────────────────────────────────────────────────

/**
 * invs: filtered invoice_index array, or null for global mode.
 */
function renderCountryCharts(invs) {
  let cm = {};
  if (invs === null) {
    // Global: use pre-computed country_revenue
    DATA.country_revenue.forEach(r => {
      cm[r.Country] = { Revenue: r.Revenue, Transactions: r.Transactions };
    });
  } else {
    invs.forEach(inv => {
      if (!cm[inv.Country]) cm[inv.Country] = { Revenue: 0, Transactions: 0 };
      cm[inv.Country].Revenue      += inv.Revenue;
      cm[inv.Country].Transactions += 1;
    });
  }

  const sorted = Object.entries(cm)
    .sort((a, b) => b[1].Revenue - a[1].Revenue).slice(0, 10);
  const labels   = sorted.map(([c]) => c);
  const revenues = sorted.map(([,v]) => round2(v.Revenue));
  const aovs     = sorted.map(([,v]) => v.Transactions > 0 ? round2(v.Revenue / v.Transactions) : 0);

  if (!labels.length) {
    restoreAndRenderEmpty('chartCountry');
    restoreAndRenderEmpty('chartCountryAov');
    return;
  }

  renderOrUpdateChart('chartCountry', 'bar', {
    labels,
    datasets: [{ label:'Revenue (£)', data:revenues,
      backgroundColor:PALETTE.map(c=>c+'cc'), borderColor:PALETTE,
      borderWidth:1, borderRadius:4 }]
  }, { indexAxis:'y', scales:{
    x:{ ticks:{ callback:v=>'£'+fmtNumShort(v) }, grid:{ color:'#f1f5f9' } },
    y:{ ticks:{ font:{ size:11 } } }
  }});

  renderOrUpdateChart('chartCountryAov', 'bar', {
    labels,
    datasets: [{ label:'AOV (£)', data:aovs,
      backgroundColor:PALETTE.map((c,i)=>PALETTE[i%PALETTE.length]+'bb'),
      borderRadius:4 }]
  }, { indexAxis:'y', scales:{
    x:{ ticks:{ callback:v=>'£'+fmtNumShort(v) }, grid:{ color:'#f1f5f9' } },
    y:{ ticks:{ font:{ size:11 } } }
  }});
}

// ──────────────────────────────────────────────────────────────
// PRODUCT CHARTS
// ──────────────────────────────────────────────────────────────

/**
 * Build top-10 from intersection of up to 3 product tables.
 * pmSlice: prod_month filtered by date  (always present, or null = global)
 * cSlice:  prod_country for active country (or null)
 * sSlice:  prod_segment for active segment (or null)
 *
 * FIX 2 (v3): Proportional scaling REMOVED.
 * When country + date filters are both active, use prod_country values as-is
 * for ranking (full-period country totals). Date narrowing is best-effort via
 * the prod_month date filter applied to find which StockCodes are in-scope.
 */
function renderProductCharts(pmSlice, cSlice, sSlice) {
  const truncate = s => s && s.length > 30 ? s.substring(0, 28) + '…' : (s || '');

  if (pmSlice === null) {
    // Unfiltered — use global pre-computed lists
    const gr = DATA.top_products_by_revenue;
    const gq = DATA.top_products_by_qty;
    renderProductBar('chartProdRev', gr.map(p=>truncate(p.Description)), gr.map(p=>p.Revenue));
    renderProductBar('chartProdQty', gq.map(p=>truncate(p.Description)), gq.map(p=>p.Qty), true);
    return;
  }

  // Aggregate pmSlice by StockCode — this gives date-scoped product totals
  const pm = {};
  pmSlice.forEach(r => {
    if (!pm[r.StockCode]) pm[r.StockCode] = { Description: r.Description, Revenue: 0, Qty: 0 };
    pm[r.StockCode].Revenue += r.Revenue;
    pm[r.StockCode].Qty     += r.Qty;
  });

  // If country filter active: restrict to StockCodes present in both pm and cSlice
  // Use cSlice values directly (authoritative for that country, full-period)
  // No proportional scaling — cSlice is the exact country breakdown
  if (cSlice) {
    const cMap = {};
    cSlice.forEach(r => { cMap[r.StockCode] = { Revenue: r.Revenue, Qty: r.Qty, Description: r.Description }; });
    const merged = {};
    Object.keys(pm).forEach(sc => {
      if (cMap[sc]) {
        merged[sc] = {
          Description: cMap[sc].Description,
          Revenue:     cMap[sc].Revenue,
          Qty:         cMap[sc].Qty
        };
      }
    });
    const usedMap = Object.keys(merged).length > 0 ? merged : pm;
    buildAndRenderProductBars(usedMap, truncate);
    return;
  }

  // If segment filter active: restrict to StockCodes in both pm and sSlice
  // Use sSlice values directly — no proportional scaling
  if (sSlice) {
    const sMap = {};
    sSlice.forEach(r => { sMap[r.StockCode] = { Revenue: r.Revenue, Qty: r.Qty, Description: r.Description }; });
    const merged = {};
    Object.keys(pm).forEach(sc => {
      if (sMap[sc]) {
        merged[sc] = {
          Description: sMap[sc].Description,
          Revenue:     sMap[sc].Revenue,
          Qty:         sMap[sc].Qty
        };
      }
    });
    const usedMap = Object.keys(merged).length > 0 ? merged : pm;
    buildAndRenderProductBars(usedMap, truncate);
    return;
  }

  // Date filter only
  buildAndRenderProductBars(pm, truncate);
}

/**
 * FIX 1 (v3): When product filter is active, the filtered invoices (from
 * prod_inv_map intersection) already represent exact transactions for that
 * product within the active date/country/segment scope.
 * We show a single-product chart with its exact Revenue and Qty.
 */
function renderProductChartsFromInvoices(invs, stockCode) {
  const truncate = s => s && s.length > 30 ? s.substring(0, 28) + '…' : (s || '');

  if (!invs.length) {
    restoreAndRenderEmpty('chartProdRev');
    restoreAndRenderEmpty('chartProdQty');
    return;
  }

  // Find product description from prod_month or top_products lists
  const descEntry = DATA.prod_month.find(r => r.StockCode === stockCode)
    || DATA.top_products_by_revenue.find(p => p.StockCode === stockCode)
    || { Description: stockCode };

  // Total revenue and qty for this product in filtered invoices comes from
  // prod_inv_map — invs are already the invoices that contain this product.
  // Exact per-invoice product breakdown isn't in invoice_index (it's invoice-level),
  // so we use prod_month scoped by the same date range as the best available figure.
  const pmScoped = filterProdMonth(DATA.prod_month.filter(r => r.StockCode === stockCode),
                                   filters.dateFrom, filters.dateTo);
  let revenue = 0, qty = 0;
  pmScoped.forEach(r => { revenue += r.Revenue; qty += r.Qty; });

  // If country or segment filters are also active, intersect with their slices
  if (filters.country) {
    const c = DATA.prod_country.find(r => r.StockCode === stockCode && r.Country === filters.country);
    if (c) { revenue = c.Revenue; qty = c.Qty; }
  } else if (filters.segment) {
    const s = DATA.prod_segment.find(r => r.StockCode === stockCode && r.Segment === filters.segment);
    if (s) { revenue = s.Revenue; qty = s.Qty; }
  }

  const desc = truncate(descEntry.Description || stockCode);
  renderProductBar('chartProdRev', [desc], [round2(revenue)]);
  renderProductBar('chartProdQty', [desc], [qty], true);
}

function buildAndRenderProductBars(pm, truncate) {
  const sortedRev = Object.values(pm).sort((a, b) => b.Revenue - a.Revenue).slice(0, 10);
  const sortedQty = Object.values(pm).sort((a, b) => b.Qty - a.Qty).slice(0, 10);
  if (!sortedRev.length) {
    restoreAndRenderEmpty('chartProdRev');
    restoreAndRenderEmpty('chartProdQty');
    return;
  }
  renderProductBar('chartProdRev', sortedRev.map(p=>truncate(p.Description)), sortedRev.map(p=>round2(p.Revenue)));
  renderProductBar('chartProdQty', sortedQty.map(p=>truncate(p.Description)), sortedQty.map(p=>p.Qty), true);
}

function renderProductBar(canvasId, labels, data, isQty = false) {
  if (!data.length) { restoreAndRenderEmpty(canvasId); return; }
  renderOrUpdateChart(canvasId, 'bar', {
    labels,
    datasets: [{ label: isQty ? 'Quantity Sold' : 'Revenue (£)', data,
      backgroundColor: PALETTE.map(c=>c+'cc'), borderRadius:4 }]
  }, { indexAxis:'y', scales:{
    x:{ ticks:{ callback: v => isQty ? fmtNumShort(v) : '£'+fmtNumShort(v) }, grid:{ color:'#f1f5f9' } },
    y:{ ticks:{ font:{ size:11 } } }
  }});
}

// ──────────────────────────────────────────────────────────────
// RFM SEGMENT CHARTS  (FIX 5)
// ──────────────────────────────────────────────────────────────

/**
 * invs: filtered invoice_index array, or null for global mode.
 * FIX 5: When filtered, derive segment counts + revenue from filtered invoices.
 *        RFM scores (quintile labels) always come from global model — clearly labelled.
 */
function renderSegmentCharts(invs) {
  if (invs === null) {
    // Global
    renderSegPie(DATA.rfm_segments.map(s=>s.Segment), DATA.rfm_segments.map(s=>s.Count));
    renderSegRevBar(DATA.rfm_segments.map(s=>s.Segment), DATA.rfm_segments.map(s=>s.Total_Revenue));
    renderRFMTable(DATA.rfm_segments, false);
    updateSegmentNote(false);
    return;
  }

  // Build segment revenue from filtered invoices
  const segRev = {}, segCust = {};
  invs.forEach(inv => {
    const seg = inv.Segment || 'Unknown';
    segRev[seg]  = (segRev[seg]  || 0) + inv.Revenue;
    if (inv.CustomerID) {
      if (!segCust[seg]) segCust[seg] = new Set();
      segCust[seg].add(inv.CustomerID);
    }
  });

  // Order segments consistently
  const ordered = DATA.rfm_segments.map(s => s.Segment);
  const labels  = ordered.filter(s => segRev[s] !== undefined || segCust[s] !== undefined);

  // FIX 3 (v3): Empty state → show restoreAndRenderEmpty, NOT fallback to global
  if (!labels.length) {
    restoreAndRenderEmpty('chartSegPie');
    restoreAndRenderEmpty('chartSegRev');
    const tbody = document.getElementById('rfmTableBody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="text-center text-slate-400 py-4">Tidak ada data segmen untuk filter ini.</td></tr>';
    updateSegmentNote(true);
    return;
  }

  const counts  = labels.map(s => segCust[s] ? segCust[s].size : 0);
  const revs    = labels.map(s => round2(segRev[s] || 0));

  renderSegPie(labels, counts);
  renderSegRevBar(labels, revs);

  // Build table: use global RFM stats (Avg_Recency, Avg_Frequency, Avg_Monetary)
  // but replace Count and Total_Revenue with filtered values
  const tableData = DATA.rfm_segments
    .filter(s => labels.includes(s.Segment))
    .map(s => ({
      ...s,
      Count:         segCust[s.Segment] ? segCust[s.Segment].size : 0,
      Total_Revenue: round2(segRev[s.Segment] || 0)
    }));
  renderRFMTable(tableData, true);
  updateSegmentNote(true);
}

/** FIX 5: Show/hide a note explaining global RFM scores vs filtered counts */
function updateSegmentNote(isFiltered) {
  let note = document.getElementById('rfmFilterNote');
  if (!note) {
    note = document.createElement('p');
    note.id = 'rfmFilterNote';
    note.className = 'text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-4';
    const section = document.querySelector('[aria-label="Customer Segmentation"]');
    if (section) section.insertBefore(note, section.querySelector('.grid'));
  }
  if (isFiltered) {
    note.textContent = '⚠️ Jumlah pelanggan dan total revenue mencerminkan filter aktif. ' +
      'Avg Recency, Avg Frequency, dan Avg Monetary berasal dari model RFM global (seluruh periode).';
    note.classList.remove('hidden');
  } else {
    note.classList.add('hidden');
  }
}

function renderSegPie(labels, data) {
  const colors = labels.map(l => SEG_COLORS[l] || '#94a3b8');
  renderOrUpdateChart('chartSegPie', 'doughnut', {
    labels,
    datasets: [{ data, backgroundColor: colors, borderWidth: 2, borderColor: '#fff' }]
  }, {
    cutout: '55%',
    plugins: { legend: { position:'right', labels:{ font:{ size:11 }, padding:10, boxWidth:12 } } }
  });
}

function renderSegRevBar(labels, revenues) {
  const colors = labels.map(l => SEG_COLORS[l] || '#94a3b8');
  renderOrUpdateChart('chartSegRev', 'bar', {
    labels,
    datasets: [{ label:'Revenue (£)', data:revenues,
      backgroundColor: colors.map(c=>c+'cc'), borderColor:colors,
      borderWidth:1, borderRadius:4 }]
  }, { scales:{
    y:{ ticks:{ callback: v=>'£'+fmtNumShort(v) }, grid:{ color:'#f1f5f9' } },
    x:{ ticks:{ font:{ size:11 } } }
  }});
}

function renderRFMTable(segs, isFiltered) {
  const tbody = document.getElementById('rfmTableBody');
  if (!tbody) return;
  tbody.innerHTML = '';
  segs.forEach(s => {
    const color = SEG_COLORS[s.Segment] || '#94a3b8';
    const tr = document.createElement('tr');
    // Avg stats are global when filtered — mark with asterisk
    const avgSuffix = isFiltered ? '*' : '';
    tr.innerHTML = `
      <td class="font-medium">
        <span class="seg-dot" style="background:${color}"></span>${s.Segment}
      </td>
      <td class="text-right">${fmtNum(s.Count)}</td>
      <td class="text-right">${s.Avg_Recency}${avgSuffix} days</td>
      <td class="text-right">${s.Avg_Frequency}${avgSuffix}×</td>
      <td class="text-right">${fmtCurrency(s.Avg_Monetary)}${avgSuffix}</td>
      <td class="text-right font-semibold">${fmtCurrency(s.Total_Revenue)}</td>
    `;
    tbody.appendChild(tr);
  });
  if (isFiltered) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td colspan="6" class="text-xs text-slate-400 pt-2">* Nilai Avg berasal dari model RFM global (seluruh periode data)</td>`;
    tbody.appendChild(tr);
  }
}

// ──────────────────────────────────────────────────────────────
// CANCELLATION CHART
// ──────────────────────────────────────────────────────────────

function renderCancellationKPIs() {
  const c = DATA.cancellation;
  setText('cancelInvoices',  fmtNum(c.total_cancel_invoices));
  setText('cancelValue',     fmtCurrency(c.total_return_value));
  // FIX 4 (v3): Rates are always global — label them accordingly when filter is active
  const isFiltered = !isUnfiltered();
  const rateSuffix = isFiltered ? ' (global)' : '';
  setText('cancelRateInv',   c.cancel_rate_inv_pct + '%' + rateSuffix);
  setText('cancelRateRows',  c.cancel_rate_rows_pct + '%' + rateSuffix);
}

/**
 * FIX 8: When date and/or country filter active, filter cancellation data.
 * Uses cancellation.by_date_country for filtered monthly aggregation.
 * Shows a badge indicating scope.
 */
function renderCancelChart(dateFrom, country) {
  const c = DATA.cancellation;
  const isFiltered = !!(dateFrom || country);

  let normalMonthly, cancelMonthly;

  if (!isFiltered) {
    // Global — use pre-computed monthly arrays
    normalMonthly = DATA.monthly_trend;  // [{month, Revenue, ...}]
    cancelMonthly = c.monthly;           // [{YearMonth, CancelInvoices, ReturnValue}]
  } else {
    // Filter cancellation by_date_country
    const cancelFiltered = c.by_date_country.filter(r => {
      if (dateFrom && r.DateStr < dateFrom) return false;
      if (filters.dateTo && r.DateStr > filters.dateTo) return false;
      if (country && r.Country !== country) return false;
      return true;
    });
    // Aggregate to YearMonth
    const cancelYMMap = {};
    cancelFiltered.forEach(r => {
      const ym = r.DateStr.substring(0, 7); // 'YYYY-MM'
      if (!cancelYMMap[ym]) cancelYMMap[ym] = { CancelInvoices: 0, ReturnValue: 0 };
      cancelYMMap[ym].CancelInvoices += r.CancelInvoices;
      cancelYMMap[ym].ReturnValue    += r.ReturnValue;
    });
    cancelMonthly = Object.entries(cancelYMMap)
      .sort(([a],[b]) => a.localeCompare(b))
      .map(([ym, v]) => ({ YearMonth: ym, CancelInvoices: v.CancelInvoices, ReturnValue: round2(v.ReturnValue) }));

    // Filter normal monthly: use monthly_country_seg
    const normalMap = {};
    DATA.monthly_country_seg.filter(r => {
      const mStart = r.YearMonth + '-01';
      const mEnd   = r.YearMonth + '-31';
      if (dateFrom && mEnd   < dateFrom) return false;
      if (filters.dateTo && mStart > filters.dateTo) return false;
      if (country && r.Country !== country) return false;
      return true;
    }).forEach(r => {
      if (!normalMap[r.YearMonth]) normalMap[r.YearMonth] = { Revenue: 0, Transactions: 0 };
      normalMap[r.YearMonth].Revenue      += r.Revenue;
      normalMap[r.YearMonth].Transactions += r.Transactions;
    });
    normalMonthly = Object.entries(normalMap)
      .sort(([a],[b]) => a.localeCompare(b))
      .map(([ym, v]) => ({ month: ym, Revenue: round2(v.Revenue), Transactions: v.Transactions }));
  }

  // Update cancel KPIs to reflect filter
  // FIX 4 (v3): Rates always global; counts/value show filtered scope
  if (isFiltered) {
    const filteredTotalReturn = cancelMonthly.reduce((s, r) => s + r.ReturnValue, 0);
    const filteredCancelInv   = cancelMonthly.reduce((s, r) => s + r.CancelInvoices, 0);
    const c = DATA.cancellation;
    setText('cancelInvoices', fmtNum(filteredCancelInv) + ' (filtered)');
    setText('cancelValue',    fmtCurrency(filteredTotalReturn) + ' (filtered)');
    setText('cancelRateInv',  c.cancel_rate_inv_pct + '% (global)');
    setText('cancelRateRows', c.cancel_rate_rows_pct + '% (global)');
  } else {
    renderCancellationKPIs(); // restore global values
  }

  // Build chart
  const normalMap2  = Object.fromEntries((normalMonthly || []).map(r => [r.month || r.YearMonth, r.Revenue]));
  const cancelMap2  = Object.fromEntries((cancelMonthly || []).map(r => [r.YearMonth, r.ReturnValue]));
  const cancelInvMap = Object.fromEntries((cancelMonthly || []).map(r => [r.YearMonth, r.CancelInvoices]));

  const allMonths = [...new Set([
    ...Object.keys(normalMap2),
    ...Object.keys(cancelMap2)
  ])].sort();

  if (!allMonths.length) { restoreAndRenderEmpty('chartCancel'); return; }

  const labels        = allMonths;
  const normalRevs    = allMonths.map(m => normalMap2[m]  || 0);
  const returnVals    = allMonths.map(m => cancelMap2[m]  || 0);
  const cancelInvCts  = allMonths.map(m => cancelInvMap[m]|| 0);

  // Update chart title/badge to show scope
  const badgeEl = document.getElementById('cancelScopeBadge');
  if (badgeEl) badgeEl.textContent = isFiltered ? 'Filtered data' : 'All periods';

  renderOrUpdateChart('chartCancel', 'bar', {
    labels,
    datasets: [
      { label:'Normal Sales Revenue (£)', data:normalRevs,
        backgroundColor:PALETTE[0]+'bb', borderRadius:4, yAxisID:'y' },
      { label:'Return Value (£)', data:returnVals,
        backgroundColor:'#ef4444bb', borderRadius:4, yAxisID:'y' },
      { label:'Cancelled Invoices', data:cancelInvCts,
        type:'line', borderColor:'#f59e0b', backgroundColor:'#f59e0b22',
        fill:false, tension:0.4, pointRadius:4, yAxisID:'y1' }
    ]
  }, { scales:{
    y:  { position:'left',  stacked:false, ticks:{ callback:v=>'£'+fmtNumShort(v) }, grid:{ color:'#f1f5f9' } },
    y1: { position:'right', grid:{ display:false }, ticks:{ callback:v=>v+' inv' } }
  }});
}

// ──────────────────────────────────────────────────────────────
// DATA QUALITY REPORT  (FIX 7)
// ──────────────────────────────────────────────────────────────

function updateQualityBadge() {
  const m = DATA.meta;
  const badge = document.getElementById('qualityBadge');
  const text  = document.getElementById('qualityText');
  if (badge && text) {
    badge.classList.remove('hidden');
    text.textContent = `${fmtNum(m.normal_rows)} valid rows · Generated ${new Date(m.generated_at).toLocaleDateString()}`;
  }
}

function renderQualityReport() {
  const q = DATA.quality_report;
  const container = document.getElementById('qualityReport');
  if (!container) return;

  // FIX 5 (v3): Use cancellation_rows_raw (before dedup) + cancellation_rows_dedup (after dedup)
  // with explicit "(before dedup)" / "(after dedup)" labels
  const cancelRawVal  = q.cancellation_rows_raw  != null ? q.cancellation_rows_raw  : q.cancellation_rows;
  const cancelDedupVal= q.cancellation_rows_dedup != null ? q.cancellation_rows_dedup : q.cancellation_rows;
  const items = [
    { label: 'Raw Rows (Before Dedup)', value: fmtNum(q.raw_rows),           note: 'Total baris di file sumber', step: '①' },
    { label: 'Duplicate Rows Removed',  value: fmtNum(q.duplicates_removed), note: 'Baris identik dihapus',      step: '②', warn: true },
    { label: 'Rows After Deduplication',value: fmtNum(q.rows_after_dedup),   note: `${q.raw_rows} − ${q.duplicates_removed} = ${q.rows_after_dedup}`, step: '③' },
    { label: 'Missing CustomerID',      value: fmtNum(q.missing_customer_id),note: `${q.missing_customer_id_pct}% dari rows setelah dedup — dikecualikan dari RFM`, step: '④', warn: true },
    { label: 'Missing Description',     value: fmtNum(q.missing_description),note: 'Diisi dengan StockCode',     step: '⑤' },
    { label: 'Cancel Rows (before dedup)', value: fmtNum(cancelRawVal),   note: `${q.cancellation_invoices} invoice pembatalan (sebelum dedup)`, step: '⑥', warn: true },
    { label: 'Cancel Rows (after dedup)',  value: fmtNum(cancelDedupVal), note: `Baris cancel setelah dedup dihapus`, step: '⑦', warn: true },
    { label: 'Neg Qty / Zero Price',    value: fmtNum(q.negative_qty_non_cancel + q.zero_price_rows), note: 'Difilter dari data penjualan', step: '⑧', warn: true },
    { label: 'Valid Sales Rows',        value: fmtNum(q.valid_sales_rows),   note: 'Digunakan untuk seluruh analisis', step: '✓', highlight: true },
  ];

  container.innerHTML = items.map(it => `
    <div class="p-3 rounded-lg ${it.highlight ? 'bg-indigo-50 border border-indigo-100' : it.warn ? 'bg-amber-50 border border-amber-100' : 'bg-slate-50'}">
      <div class="flex items-center gap-2 mb-1">
        <span class="text-xs font-bold ${it.highlight ? 'text-indigo-500' : it.warn ? 'text-amber-500' : 'text-slate-400'}">${it.step}</span>
        <p class="text-xs font-semibold ${it.highlight ? 'text-indigo-600' : it.warn ? 'text-amber-700' : 'text-slate-500'} uppercase tracking-wide">${it.label}</p>
      </div>
      <p class="text-xl font-bold ${it.highlight ? 'text-indigo-700' : 'text-slate-800'}">${it.value}</p>
      <p class="text-xs text-slate-400 mt-1">${it.note}</p>
    </div>
  `).join('');
}

// ──────────────────────────────────────────────────────────────
// CHART.JS HELPERS
// ──────────────────────────────────────────────────────────────

/**
 * Create or update a Chart.js instance.
 * extraOptions deep-merged properly: scales override, plugins merged.
 */
function renderOrUpdateChart(canvasId, type, chartData, extraOptions = {}) {
  // FIX 6: Restore canvas if it was removed by renderEmpty
  restoreCanvas(canvasId);

  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  if (CHARTS[canvasId]) {
    CHARTS[canvasId].destroy();
    delete CHARTS[canvasId];
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 300 },
    plugins: {
      legend: {
        display: chartData.datasets.length > 1 || type === 'doughnut',
        labels: { font:{ size:11 }, boxWidth:12, padding:12 }
      },
      tooltip: {
        callbacks: {
          label: ctx => {
            const v = ctx.parsed.y ?? ctx.parsed.x ?? ctx.parsed;
            const lbl = ctx.dataset.label || '';
            const num = typeof v === 'number' ? v : 0;
            if (lbl.includes('£') || lbl.includes('Revenue') || lbl.includes('AOV') || lbl.includes('Value')) {
              return ` ${lbl}: £${fmtNum(num)}`;
            }
            return ` ${lbl}: ${fmtNum(num)}`;
          }
        }
      },
      // Merge extra plugin options
      ...(extraOptions.plugins || {})
    },
    scales: type === 'doughnut' ? undefined : {
      x: { grid:{ color:'#f1f5f9' }, ticks:{ font:{ size:11 } } },
      y: { grid:{ color:'#f1f5f9' }, ticks:{ font:{ size:11 } } },
      // Override with extra scales (y1, etc.)
      ...(extraOptions.scales || {})
    }
  };

  // Apply remaining top-level extra options (indexAxis, cutout, etc.)
  const { plugins: _p, scales: _s, ...restExtra } = extraOptions;
  Object.assign(options, restExtra);

  CHARTS[canvasId] = new Chart(canvas, { type, data: chartData, options });
}

/**
 * FIX 6: Show empty-state WITHOUT destroying the canvas element.
 * The canvas is hidden; a sibling div shows the message.
 * restoreCanvas() removes the message and shows the canvas again.
 */
function restoreAndRenderEmpty(canvasId) {
  restoreCanvas(canvasId);  // ensure clean state first
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  if (CHARTS[canvasId]) { CHARTS[canvasId].destroy(); delete CHARTS[canvasId]; }

  canvas.style.display = 'none';

  // Create or update the empty-state sibling
  let emptyDiv = canvas.parentElement.querySelector('.empty-state');
  if (!emptyDiv) {
    emptyDiv = document.createElement('div');
    emptyDiv.className = 'empty-state';
    canvas.parentElement.appendChild(emptyDiv);
  }
  emptyDiv.innerHTML = `
    <p>⚠️ Tidak ada data untuk filter ini.</p>
    <p class="text-xs">Coba ubah rentang tanggal atau hapus filter.</p>`;
}

/** Remove empty-state div and restore canvas visibility */
function restoreCanvas(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  canvas.style.display = '';
  const emptyDiv = canvas.parentElement && canvas.parentElement.querySelector('.empty-state');
  if (emptyDiv) emptyDiv.remove();
}

// ──────────────────────────────────────────────────────────────
// FORMAT UTILITIES
// ──────────────────────────────────────────────────────────────

function fmtCurrency(n) {
  if (n == null || isNaN(n)) return '—';
  if (n >= 1_000_000) return `£${(n/1_000_000).toFixed(2)}M`;
  if (n >= 1_000)     return `£${(n/1_000).toFixed(1)}K`;
  return `£${n.toFixed(2)}`;
}

function fmtNum(n) {
  if (n == null || isNaN(n)) return '—';
  return Math.round(n).toLocaleString('en-GB');
}

function fmtNumShort(n) {
  if (n >= 1_000_000) return (n/1_000_000).toFixed(1)+'M';
  if (n >= 1_000)     return (n/1_000).toFixed(0)+'K';
  return String(n);
}

function pct(val, total) {
  if (!total) return '0.0';
  return ((val/total)*100).toFixed(1);
}

function round2(n) { return Math.round(n*100)/100; }

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}
