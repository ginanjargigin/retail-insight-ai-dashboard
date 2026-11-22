# Retail Insight AI Dashboard

**Dashboard Interaktif Analisis Penjualan dan Perilaku Pelanggan**

Retail Insight AI Dashboard mengolah dataset **Online Retail** menjadi dashboard interaktif untuk memahami performa penjualan, kontribusi negara dan produk, perilaku pelanggan melalui segmentasi **RFM (Recency, Frequency, Monetary)**, serta pembatalan transaksi dan kualitas data. Proyek dikembangkan dengan bantuan IBM Bob, menggunakan Python untuk preprocessing dan HTML/CSS/JavaScript untuk dashboard.

## 1. Tujuan Proyek

Dashboard membantu pengguna untuk:
- Memantau indikator utama penjualan.
- Menganalisis tren pendapatan dari waktu ke waktu.
- Mengidentifikasi negara dan produk dengan kontribusi pendapatan terbesar.
- Memahami karakteristik pelanggan melalui segmentasi RFM.
- Memantau pembatalan transaksi dan kualitas data.

## 2. Dataset

Sumber data adalah **Online Retail.xlsx**, dengan 541.909 baris pada dataset awal. Periode transaksi yang tercatat dalam hasil preprocessing adalah 1 Desember 2010 sampai 9 Desember 2011.

Kolom utama:
- `InvoiceNo`: nomor transaksi.
- `StockCode`: kode produk.
- `Description`: deskripsi produk.
- `Quantity`: jumlah barang.
- `InvoiceDate`: tanggal transaksi.
- `UnitPrice`: harga satuan.
- `CustomerID`: identitas pelanggan.
- `Country`: negara pelanggan.

Dataset sumber tidak disertakan dalam repository. Untuk menjalankan dashboard, file `dashboard/data.json` yang sudah diproses tersedia di repository. Untuk mengulang preprocessing, pengguna perlu memperoleh dataset sumber dan meletakkannya secara lokal pada `data/raw/Online Retail.xlsx`.

Dataset tidak menyediakan atribut Discount, Region, Product Category, Sales Representative, Customer Type, Payment Method, atau Sales Channel. Dashboard tidak membuat kesimpulan berdasarkan atribut yang tidak tersedia tersebut.

## 3. Fitur Dashboard

### KPI utama

| KPI | Definisi |
|---|---|
| Total Revenue | Jumlah pendapatan dari transaksi penjualan yang memenuhi kriteria |
| Total Transactions | Jumlah `InvoiceNo` unik |
| Total Quantity Sold | Jumlah unit produk terjual |
| Average Order Value (AOV) | Total Revenue dibagi Total Transactions |
| Unique Customers | Jumlah `CustomerID` unik yang tersedia |

### Visualisasi
1. **Monthly Sales Trend** – tren pendapatan penjualan bulanan.
2. **Revenue by Country** – kontribusi pendapatan berdasarkan negara.
3. **Average Order Value by Country** – rata-rata nilai transaksi per negara.
4. **Top Products by Revenue** – produk dengan pendapatan tertinggi.
5. **Top Products by Quantity** – produk dengan jumlah penjualan tertinggi.
6. **Customer Segmentation (RFM)** – distribusi dan ringkasan segmen pelanggan.
7. **Cancellation Analysis** – analisis transaksi pembatalan.

### Filter interaktif
- Rentang tanggal.
- Negara.
- Segmen pelanggan.
- Produk (pilihan produk Top 50).

Filter memperbarui komponen dashboard sesuai granularitas data yang tersedia pada JSON hasil preprocessing.

## 4. Metode RFM

RFM mengelompokkan pelanggan berdasarkan tiga dimensi perilaku transaksi:

- **Recency (R):** jarak waktu sejak pembelian terakhir. Pembelian yang lebih baru memperoleh skor lebih baik.
- **Frequency (F):** frekuensi transaksi pelanggan. Frekuensi yang lebih tinggi memperoleh skor lebih baik.
- **Monetary (M):** total nilai pembelian pelanggan. Nilai yang lebih tinggi memperoleh skor lebih baik.

Dalam proyek ini, skor setiap dimensi menggunakan skala 1–5 berbasis quintile. Pelanggan dikelompokkan ke dalam segmen seperti Champions, Loyal Customers, New Customers, Potential Loyalists, At Risk, Lost / Churned, dan Need Attention.

RFM hanya dihitung untuk transaksi dengan `CustomerID`. Transaksi tanpa `CustomerID` tetap masuk dalam metrik penjualan, tetapi tidak dihitung sebagai pelanggan unik dan tidak dimasukkan ke segmentasi RFM.

## 5. Pengolahan dan Kualitas Data

Preprocessing dilakukan melalui `data_processing/prepare_data.py`, meliputi:
- Pemeriksaan data kosong dan duplikasi.
- Penghapusan baris duplikat.
- Penanganan deskripsi produk kosong.
- Pemisahan transaksi pembatalan.
- Penyaringan transaksi penjualan berdasarkan Quantity dan UnitPrice.
- Perhitungan pendapatan.
- Penyusunan agregasi KPI, grafik, filter, dan RFM.

Ringkasan kualitas data yang tercatat:
- Data awal: 541.909 baris.
- Baris duplikat yang dihapus: 5.268.
- Missing CustomerID: 135.080 baris.
- Baris pembatalan sebelum deduplikasi: 9.288.
- Baris pembatalan setelah deduplikasi: 9.251.

## 6. Teknologi

| Teknologi | Penggunaan |
|---|---|
| IBM Bob | Asisten AI dalam pengembangan, analisis, dan debugging |
| Python dan pandas | Pemeriksaan, preprocessing, dan analisis data |
| JSON | Penyimpanan data hasil preprocessing |
| HTML | Struktur halaman dashboard |
| Tailwind CSS dan CSS | Tampilan dan responsivitas |
| Vanilla JavaScript | Logika dashboard dan filter interaktif |
| Chart.js | Visualisasi data |

## 7. Struktur Repository

```text
retail-insight-ai-dashboard/
├── .gitignore
├── README.md
├── archive/
│   ├── audit.py
│   └── audit_v2.py
├── dashboard/
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── data.json
├── data/
│   └── raw/                 # dataset sumber lokal; tidak diunggah
├── data_processing/
│   ├── _check_data.py
│   ├── analyze_retail.py
│   └── prepare_data.py
├── prompts/
│   ├── prompt_iterasi_1_rekonstruksi.md
│   ├── prompt_architecture.md
│   └── prompt_iterations.md
├── reports/
│   └── Laporan_Validasi_Retail_Insight_AI.txt
├── screenshots/
└── validation/
    ├── audit_v3.py
    ├── audit_v4_filter_combinations.py
    └── reconcile.py
```

## 8. Menjalankan Dashboard

Dashboard membaca `data.json` menggunakan `fetch()`. Jalankan melalui HTTP server, bukan dengan membuka file HTML langsung menggunakan `file://`.

Dari root repository, jalankan:

```bash
python -m http.server 8000
```

Kemudian buka alamat:

```text
http://localhost:8000/dashboard/
```

File `dashboard/data.json` sudah disediakan sehingga dataset Excel sumber tidak diperlukan hanya untuk melihat dashboard. Pastikan komputer terhubung ke internet karena Tailwind CSS dan Chart.js dimuat melalui CDN.

## 9. Mengulang Preprocessing Data

Dataset sumber tidak disertakan dalam repository. Jika ingin membangun ulang `data.json`:

1. Siapkan dataset sumber `Online Retail.xlsx`.
2. Letakkan file pada `data/raw/Online Retail.xlsx` di root repository.
3. Instal dependensi:

```bash
python -m pip install pandas openpyxl
```

4. Jalankan dari root repository:

```bash
python data_processing/prepare_data.py
```

Script menggunakan path relatif terhadap lokasi file Python:
- Input: `data/raw/Online Retail.xlsx`.
- Output: `dashboard/data.json`.

Tidak perlu mengubah path Windows secara manual. File dataset sumber tetap lokal dan diabaikan oleh `.gitignore`.

Script analisis tambahan dapat dijalankan dari root repository:

```bash
python data_processing/analyze_retail.py
python data_processing/_check_data.py
```

## 10. Validasi dan Pengujian

Folder `validation/` berisi:
- `audit_v3.py`: pemeriksaan struktur data dan komponen kode.
- `audit_v4_filter_combinations.py`: pengujian perhitungan KPI pada kombinasi filter.
- `reconcile.py`: pemeriksaan inventaris file, implementasi dashboard, JSON, dokumentasi, serta eksekusi kedua audit.

Kedua audit menggunakan path file relatif terhadap direktori `dashboard/`. Karena itu, jalankan perintah berikut dari root repository:

```bash
python -m compileall -q data_processing validation
```

Kemudian jalankan audit dari direktori dashboard:

```bash
cd dashboard
python ../validation/audit_v3.py
python ../validation/audit_v4_filter_combinations.py
cd ..
```

Untuk menjalankan rekonsiliasi final dari root repository:

```bash
python validation/reconcile.py
```

Hasil audit yang dilaporkan:
- Audit Suite v3: 48/48 PASS.
- Audit Suite v4: 79/79 PASS.
- Total pengujian otomatis: 127/127 PASS, 0 FAIL.

Pengujian manual dashboard yang dilaporkan:
- 12/12 pemeriksaan PASS, mencakup KPI, visualisasi, filter, kombinasi filter, dan browser console.

Total rekap pengujian yang dilaporkan: 139/139 pemeriksaan otomatis dan manual, tanpa kegagalan. Pengujian manual merupakan hasil pemeriksaan langsung yang dilaporkan pengembang, bukan output dari script audit otomatis.

## 11. KPI Global Hasil Preprocessing

| Indikator | Nilai |
|---|---:|
| Total Revenue | £10,642,110.80 |
| Total Transactions | 19,960 |
| Total Quantity Sold | 5,572,420 |
| Average Order Value | £533.17 |
| Unique Customers | 4,338 |

Nilai ini merupakan KPI global pada hasil preprocessing yang digunakan dalam pengujian proyek.

Sebanyak 1.428 invoice tidak memiliki `CustomerID`, dengan revenue £1,754,901.91. Nilai revenue tersebut tetap masuk ke KPI penjualan, tetapi invoice tanpa `CustomerID` tidak berkontribusi pada jumlah pelanggan unik maupun segmentasi RFM.

## 12. Keterbatasan

- Filter produk menyediakan 50 produk teratas berdasarkan revenue.
- Transaksi tanpa `CustomerID` tidak dapat diidentifikasi sebagai pelanggan dan tidak dapat dimasukkan ke RFM.
- Cancellation rate tertentu ditampilkan dalam cakupan global ketika kombinasi filter tidak mendukung perhitungan yang lebih terperinci.
- Dashboard membutuhkan `data.json` yang valid dan koneksi internet untuk library CDN.
- Dataset Excel sumber tidak disertakan dalam repository.
- Hasil analisis hanya mencakup atribut yang tersedia pada dataset.

## 13. Dokumentasi Prompt dan Bukti Proyek

Folder `prompts/` berisi dokumentasi prompt awal (rekonstruksi), arsitektur prompt, dan iterasi pengembangan IBM Bob.

Folder `screenshots/` berisi tangkapan layar proses dan hasil proyek. Folder `reports/` berisi laporan validasi proyek.

## 14. Lisensi

Repository ini belum menetapkan lisensi. Hak penggunaan, penyalinan, dan distribusi kode belum diberikan melalui lisensi open-source tertentu.

---

**Retail Insight AI Dashboard**  
*Data-driven insights for retail sales and customer behavior.*
