# Retail Insight AI Dashboard

**Dashboard Interaktif Analisis Penjualan dan Perilaku Pelanggan**

Retail Insight AI Dashboard adalah proyek analisis data retail yang mengolah dataset **Online Retail** untuk menyajikan performa penjualan, kontribusi negara dan produk, segmentasi pelanggan menggunakan metode **RFM (Recency, Frequency, Monetary)**, serta informasi pembatalan transaksi. Proyek ini dikembangkan dengan bantuan **IBM Bob** dan menggabungkan pengolahan data Python dengan dashboard berbasis web.

> **Catatan penting sebelum menjalankan:** Pada repository yang diperiksa, `dashboard/data.json` masih berupa file kosong (2 byte). Dashboard membutuhkan JSON hasil preprocessing yang valid agar KPI, grafik, dan filter dapat ditampilkan. Ganti file tersebut dengan hasil `prepare_data.py` sebelum menjalankan dashboard atau mengirimkan repository sebagai hasil final.

---

## 1. Tujuan Proyek

Proyek ini bertujuan membantu pengguna memahami kondisi bisnis retail melalui:
- Pemantauan indikator utama penjualan.
- Analisis tren penjualan dari waktu ke waktu.
- Identifikasi negara dan produk dengan kontribusi penjualan terbesar.
- Pemahaman karakteristik dan kelompok pelanggan melalui segmentasi RFM.
- Pemantauan transaksi pembatalan dan kualitas data.

## 2. Dataset

Sumber data yang digunakan adalah **Online Retail.xlsx**, dengan data transaksi retail yang terdiri dari 541.909 baris pada dataset awal.

Kolom utama yang digunakan:
- `InvoiceNo`: nomor transaksi.
- `StockCode`: kode produk.
- `Description`: deskripsi produk.
- `Quantity`: jumlah barang.
- `InvoiceDate`: tanggal transaksi.
- `UnitPrice`: harga satuan.
- `CustomerID`: identitas pelanggan.
- `Country`: negara pelanggan.

Dataset sumber tidak disertakan di repository ini. Pastikan penggunaan dan distribusi ulang dataset mengikuti ketentuan sumber dataset.

**Batasan dataset:** dataset tidak menyediakan kolom Discount, Region, Product Category, Sales Representative, Customer Type, Payment Method, atau Sales Channel. Karena itu, proyek tidak membuat visualisasi atau kesimpulan berdasarkan atribut tersebut.

## 3. Fitur Dashboard

### KPI utama

| KPI | Definisi |
|---|---|
| Total Revenue | Jumlah nilai penjualan dari transaksi yang memenuhi kriteria |
| Total Transactions | Jumlah `InvoiceNo` unik pada transaksi penjualan |
| Total Quantity Sold | Jumlah unit produk terjual |
| Average Order Value (AOV) | Total Revenue dibagi Total Transactions |
| Unique Customers | Jumlah `CustomerID` unik yang tersedia |

### Visualisasi
1. **Monthly Sales Trend** – tren pendapatan penjualan bulanan.
2. **Revenue by Country** – kontribusi pendapatan berdasarkan negara.
3. **Average Order Value by Country** – nilai rata-rata transaksi per negara.
4. **Top 10 Products by Revenue** – sepuluh produk dengan pendapatan tertinggi.
5. **Top 10 Products by Quantity** – sepuluh produk dengan jumlah penjualan tertinggi.
6. **Customer Segmentation (RFM)** – distribusi dan ringkasan segmen pelanggan.
7. **Cancellation Analysis** – analisis pembatalan transaksi.

### Filter interaktif
- Rentang tanggal.
- Negara.
- Segmen pelanggan.
- Produk (pilihan produk Top 50).

Filter dirancang untuk memperbarui komponen dashboard tanpa memuat ulang halaman. Cakupan hasil filter mengikuti granularitas data yang disediakan dalam JSON.

## 4. Metode RFM

RFM digunakan untuk mengelompokkan pelanggan berdasarkan tiga dimensi perilaku transaksi:

- **Recency (R):** berapa lama sejak pelanggan terakhir melakukan pembelian. Semakin baru transaksi, semakin baik skornya.
- **Frequency (F):** seberapa sering pelanggan melakukan transaksi. Semakin sering, semakin baik skornya.
- **Monetary (M):** total nilai pembelian pelanggan. Semakin besar nilainya, semakin baik skornya.

Dalam proyek ini, skor setiap dimensi menggunakan skala 1–5 berbasis quintile. Pelanggan kemudian dikelompokkan ke dalam segmen seperti Champions, Loyal Customers, New Customers, Potential Loyalists, At Risk, Lost / Churned, dan Need Attention.

RFM hanya dihitung untuk transaksi yang memiliki `CustomerID`. Transaksi tanpa `CustomerID` tetap dapat masuk dalam metrik penjualan, tetapi tidak dihitung sebagai pelanggan unik dan tidak dimasukkan ke segmentasi RFM.

## 5. Pengolahan dan Kualitas Data

Tahap preprocessing pada `data_processing/prepare_data.py` mencakup:
- Pemeriksaan data kosong dan duplikasi.
- Penghapusan baris duplikat.
- Penanganan deskripsi produk yang kosong.
- Pemisahan transaksi pembatalan.
- Penyaringan transaksi penjualan dengan Quantity dan UnitPrice yang tidak memenuhi kriteria.
- Perhitungan pendapatan transaksi.
- Penyusunan agregasi untuk KPI, grafik, filter, dan RFM.

Angka kualitas data yang tercatat dalam dokumentasi proyek:
- Data awal: 541.909 baris.
- Baris duplikat yang dihapus: 5.268.
- Missing CustomerID: 135.080 baris.
- Baris pembatalan sebelum deduplikasi: 9.288.
- Baris pembatalan setelah deduplikasi: 9.251.

## 6. Teknologi

| Teknologi | Penggunaan |
|---|---|
| IBM Bob | Asisten AI untuk pengembangan, analisis, dan debugging |
| Python dan pandas | Pemeriksaan, preprocessing, dan analisis data |
| JSON | Penyimpanan data hasil preprocessing untuk dashboard |
| HTML | Struktur halaman dashboard |
| Tailwind CSS dan CSS | Tampilan dan responsivitas |
| Vanilla JavaScript | Logika dashboard, pemrosesan filter, dan interaksi |
| Chart.js | Visualisasi data |

## 7. Struktur Repository

```text
retail-insight-ai-dashboard/
├── .gitignore
├── README.md
├── dashboard/
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── data.json
├── data_processing/
│   ├── _check_data.py
│   ├── analyze_retail.py
│   └── prepare_data.py
├── validation/
│   ├── audit_v3.py
│   ├── audit_v4_filter_combinations.py
│   └── reconcile.py
├── prompts/
│   ├── prompt_iterasi_1_rekonstruksi.md
│   ├── prompt_architecture.md
│   └── prompt_iterations.md
├── reports/
│   └── Laporan_Validasi_Retail_Insight_AI.txt
├── screenshots/
│   ├── 1.1.png
│   └── 1.2.png
└── archive/
    ├── audit.py
    └── audit_v2.py
```

## 8. Cara Menjalankan Dashboard

Dashboard menggunakan `fetch()` untuk membaca `data.json`. Karena itu, jalankan melalui local web server, bukan dengan membuka file HTML langsung menggunakan protokol `file://`.

### Menggunakan Visual Studio Code Live Server

1. Clone atau unduh repository.
2. Buka folder repository di Visual Studio Code.
3. Pastikan `dashboard/data.json` telah berisi JSON hasil preprocessing yang valid.
4. Buka folder `dashboard/`.
5. Klik kanan `index.html`, lalu pilih **Open with Live Server**.
6. Dashboard akan terbuka di browser melalui alamat local server.

### Menggunakan Python HTTP Server

Jalankan perintah dari root repository:

```bash
python -m http.server 8000
```

Kemudian buka:

```text
http://localhost:8000/dashboard/
```

Pastikan komputer terhubung ke internet karena halaman menggunakan Tailwind CSS dan Chart.js melalui CDN.

## 9. Membuat Ulang data.json

Dataset sumber perlu tersedia secara lokal terlebih dahulu. Script `data_processing/prepare_data.py` pada repository ini masih memiliki konfigurasi path file lokal dari lingkungan pengembangan sebelumnya.

Sebelum menjalankannya:

1. Buka `data_processing/prepare_data.py`.
2. Sesuaikan variabel `FILE_IN` dengan lokasi file `Online Retail.xlsx` di komputer.
3. Sesuaikan variabel `FILE_OUT` agar menunjuk ke `dashboard/data.json` di dalam repository.
4. Pastikan Python dan dependensi tersedia.
5. Jalankan script dari terminal.

Instalasi dependensi:

```bash
pip install pandas openpyxl
```

Jalankan preprocessing:

```bash
python data_processing/prepare_data.py
```

Setelah selesai, periksa bahwa `dashboard/data.json` bukan file kosong dan memiliki struktur JSON yang valid sebelum membuka dashboard.

## 10. Validasi dan Pengujian

Folder `validation/` berisi script audit dan rekonsiliasi:
- `audit_v3.py`: pemeriksaan struktur dan komponen kode.
- `audit_v4_filter_combinations.py`: pengujian kombinasi filter.
- `reconcile.py`: rekonsiliasi status dan bukti pekerjaan.

Laporan proyek mencatat hasil:
- Audit Suite v3: 48/48 pemeriksaan PASS.
- Audit Suite v4: 79/79 pemeriksaan PASS.
- Total: 127/127 pemeriksaan PASS, 0 FAIL.

Hasil tersebut merupakan hasil yang dilaporkan dari proses pengujian proyek. Untuk mereproduksi pengujian, pastikan file data dan path yang dibutuhkan oleh masing-masing script sudah sesuai dengan struktur repository.

### KPI global yang tercatat dalam laporan validasi

| Indikator | Nilai |
|---|---:|
| Total Revenue | £10,642,110.80 |
| Total Transactions | 19,960 |
| Total Quantity Sold | 5,572,420 |
| Average Order Value | £533.17 |
| Unique Customers | 4,338 |

Nilai di atas adalah angka yang tercatat dalam laporan validasi proyek. Hasil aktual saat dashboard dijalankan bergantung pada file JSON hasil preprocessing yang digunakan.

## 11. Keterbatasan yang Diketahui

- Filter produk hanya menyediakan 50 produk teratas berdasarkan revenue.
- Grafik produk menggunakan granularitas data yang disediakan dalam hasil preprocessing; KPI transaksi dihitung melalui invoice-level index.
- Cancellation rate tertentu ditampilkan dalam cakupan global, bukan berdasarkan seluruh kombinasi filter.
- Transaksi tanpa CustomerID tidak dapat digunakan untuk identifikasi pelanggan dan segmentasi RFM.
- Dashboard bergantung pada file `data.json` yang valid dan library CDN.
- Dataset Excel sumber tidak disertakan dalam repository.
- Script preprocessing masih memerlukan penyesuaian path lokal sebelum dapat dijalankan di komputer lain.

## 12. Dokumentasi Prompt dan Bukti Proyek

Folder `prompts/` berisi dokumentasi prompt awal, arsitektur prompt, dan ringkasan iterasi pengembangan IBM Bob. File prompt awal diberi label **rekonstruksi** karena bukan salinan verbatim percakapan asli.

Folder `screenshots/` berisi tangkapan layar hasil pengerjaan. Dokumentasi hasil pengujian lebih lanjut tersedia di folder `reports/`.

## 13. Lisensi

Repository ini belum menetapkan lisensi. Hak penggunaan, penyalinan, dan distribusi kode tetap mengikuti ketentuan hak cipta yang berlaku sampai lisensi ditambahkan.

---

**Retail Insight AI Dashboard**  
*Data-driven insights for retail sales and customer behavior.*
