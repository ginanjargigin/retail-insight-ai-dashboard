# Retail Insight Dashboard

**Retail Insight Dashboard: Dashboard Interaktif Analisis Penjualan dan Perilaku Pelanggan**

Dashboard berbasis HTML/CSS/JavaScript yang menganalisis data transaksi retail (541.909 baris) dari `Online Retail.xlsx` dan menampilkan KPI, grafik interaktif, segmentasi pelanggan RFM, dan analisis pembatalan.

---

## Struktur File

```
LATIHAN_1/
├── index.html          ← Dashboard utama (HTML semantik + Tailwind CSS)
├── style.css           ← Custom styles (komplemen Tailwind)
├── script.js           ← Vanilla JS: data loading, charts, filter engine
├── data.json           ← Data hasil preprocessing (12.4 MB, pre-aggregated)
├── prepare_data.py     ← Script Python untuk generate ulang data.json
├── Online Retail.xlsx  ← Dataset sumber (tidak dimodifikasi)
└── README.md           ← Panduan ini
```

---

## Cara Menjalankan Dashboard

> **Penting:** Dashboard membaca `data.json` via `fetch()`. Browser modern memblokir `fetch` dari file `file://`. Anda harus menggunakan local server.

### Opsi 1 — VS Code Live Server (paling mudah)

1. Install ekstensi **Live Server** di VS Code (ritwickdey.liveserver).
2. Buka folder `LATIHAN_1/` di VS Code.
3. Klik kanan pada `index.html` → **"Open with Live Server"**.
4. Browser akan membuka `http://127.0.0.1:5500/index.html`.

### Opsi 2 — Python HTTP Server

```bash
# Masuk ke direktori LATIHAN_1
cd "c:\Users\ACER\OneDrive\Desktop\IBM DATA\LATIHAN_1"

# Python 3
python -m http.server 8080

# Buka browser: http://localhost:8080
```

### Opsi 3 — Node.js (npx serve)

```bash
npx serve "c:\Users\ACER\OneDrive\Desktop\IBM DATA\LATIHAN_1" -l 8080
# Buka browser: http://localhost:8080
```

---

## Regenerasi data.json dari Excel

Jika dataset berubah, jalankan ulang script Python:

```bash
# Pastikan pandas dan openpyxl sudah terinstall
pip install pandas openpyxl

# Jalankan
python prepare_data.py
```

Script akan membaca `Online Retail.xlsx`, melakukan pembersihan data, dan menulis ulang `data.json` (~12.4 MB).

**Spesifikasi Python:** Python 3.10+ dengan pandas 1.5+ dan openpyxl 3.0+.

---

## Fitur Dashboard

### KPI Cards
| KPI | Sumber Kalkulasi |
|-----|-----------------|
| Total Revenue | `SUM(Quantity × UnitPrice)` untuk transaksi valid |
| Total Transactions | Jumlah `InvoiceNo` unik (tidak berawalan 'C') |
| Total Quantity Sold | `SUM(Quantity)` transaksi valid |
| Average Order Value (AOV) | Total Revenue ÷ Total Transactions |
| Unique Customers | Jumlah `CustomerID` unik (non-null) |

### Grafik
1. **Monthly Sales Trend** — Revenue bulanan (bar) + Transactions (line), dual-axis
2. **Revenue by Country (Top 10)** — Bar chart horizontal
3. **Avg Order Value by Country (Top 10)** — Bar chart horizontal
4. **Top 10 Products by Revenue** — Bar chart horizontal
5. **Top 10 Products by Quantity** — Bar chart horizontal
6. **Customer Segmentation (RFM)** — Donut chart (count) + Bar chart (revenue) + tabel summary
7. **Monthly Cancellations vs Sales** — Grouped bar + line untuk cancel invoices

### Filters (semua komponen berubah saat filter aktif)
- **Date Range** (From / To): filter berdasarkan tanggal transaksi
- **Country**: filter berdasarkan negara pelanggan
- **Customer Segment**: filter RFM segment (Champions, At Risk, dll.)
- **Product (Top 50)**: filter berdasarkan StockCode produk tertentu

---

## Data Cleaning Summary

| Langkah | Jumlah | Keterangan |
|---------|--------|-----------|
| Raw rows | 541.909 | Sebelum cleaning |
| Duplikat dihapus | 5.268 | Baris identik |
| Missing Description | 1.454 | Diisi dengan StockCode |
| Missing CustomerID | 135.080 | Tetap dalam sales, dikecualikan dari RFM |
| Invoice Pembatalan (prefix 'C') | 9.288 baris / 3.836 invoice | Dipisahkan ke analisis return |
| Quantity ≤ 0 (non-cancel) | 1.336 | Difilter dari penjualan |
| UnitPrice ≤ 0 | 2.517 | Difilter dari penjualan |
| **Baris valid untuk analisis** | **524.878** | Digunakan semua KPI & grafik |

---

## RFM Segmentation

Metode quintile scoring (skor 1–5 tiap dimensi):
- **R (Recency)**: skor 5 = paling baru beli
- **F (Frequency)**: skor 5 = paling sering beli
- **M (Monetary)**: skor 5 = paling besar spending

| Segment | Kriteria |
|---------|----------|
| Champions | R≥4, F≥4, M≥4 |
| Loyal Customers | R≥3, F≥3 |
| New Customers | R≥4, F≤2 |
| Potential Loyalists | R≥3, M≥3 |
| At Risk | R≤2, F≥3, M≥3 |
| Lost / Churned | R≤2, F≤2, M≤2 |
| Need Attention | Lainnya |

---

## Keterbatasan

- **Filter Product (Top 50)**: Hanya 50 produk teratas (berdasarkan revenue) tersedia di filter produk. Saat filter produk aktif, dashboard menampilkan grafik single-product menggunakan data dari `prod_inv_map` (invoice-level exact). Produk di luar top-50 tidak tersedia sebagai pilihan filter.
- **Granularitas tanggal pada grafik produk**: Filter tanggal bekerja pada granularitas bulan (`YearMonth`) untuk grafik produk — bukan harian. KPI (Revenue, Transactions, Qty) tetap dihitung secara akurat day-level melalui `invoice_index`.
- **Cancel Rate selalu global**: Cancel Rate (Invoices) dan Cancel Rate (Rows) selalu ditampilkan berdasarkan keseluruhan dataset, bukan filter aktif — karena pembagi dan pembilang tidak dapat dipisahkan secara per-filter dari data yang tersedia. Label `(global)` ditampilkan otomatis saat filter aktif.
- **Kolom tidak tersedia**: Dataset tidak memiliki Discount, Region, Product Category, Sales Representative, Customer Type, Payment Method, atau Sales Channel — kolom-kolom tersebut tidak ada di dataset dan tidak ditampilkan.

---

## Dependensi Eksternal (CDN)

- [Tailwind CSS v3](https://cdn.tailwindcss.com) — styling
- [Chart.js v4.4.3](https://cdn.jsdelivr.net/npm/chart.js) — grafik
- [Google Fonts — Inter](https://fonts.googleapis.com) — tipografi

Dashboard dapat digunakan offline jika CDN diganti dengan file lokal.
