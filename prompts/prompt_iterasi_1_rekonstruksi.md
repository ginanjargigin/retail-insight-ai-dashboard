# Prompt Iterasi 1 – Initial Prompt (Rekonstruksi)

> **Catatan keaslian:** Dokumen ini merupakan rekonstruksi prompt awal berdasarkan kebutuhan proyek yang telah dibahas. Dokumen ini bukan salinan verbatim dari riwayat percakapan asli IBM Bob. Gunakan label rekonstruksi ini jika prompt asli tidak tersedia.

Anda adalah seorang **Senior Data Analyst dan Frontend Engineer** yang berpengalaman dalam mengolah data retail dan membangun dashboard analitik modern menggunakan HTML, Tailwind CSS, Vanilla JavaScript, dan Chart.js.

**Buat sebuah Retail Insight Dashboard** menggunakan dataset **Online Retail.xlsx** sebagai sumber data utama. Dashboard bertujuan menyajikan informasi penjualan dan perilaku pelanggan secara interaktif agar mudah dipahami dan dapat membantu pengambilan keputusan bisnis.

Dashboard harus menampilkan KPI:
- Total Revenue
- Total Transactions
- Total Quantity Sold
- Average Order Value (AOV)
- Unique Customers

Tambahkan visualisasi berupa **Monthly Sales Trend, Revenue per Country, Top 10 Products by Revenue, Top 10 Products by Quantity Sold, Customer Segmentation menggunakan metode RFM (Recency, Frequency, Monetary), dan Cancellation & Return Analysis**.

Tambahkan filter berdasarkan **Date Range, Country, Product, dan Customer Segment** yang dapat memperbarui komponen dashboard secara dinamis tanpa melakukan refresh halaman.

Lakukan pemeriksaan dan pengolahan data sebelum digunakan dalam dashboard, termasuk pemeriksaan missing values, duplikasi, transaksi pembatalan, dan data transaksi yang tidak valid. Pastikan perhitungan revenue dan indikator penjualan menggunakan data transaksi yang sesuai dengan struktur dataset.

Gunakan **JSON sebagai sumber data dashboard** dan pisahkan kode ke dalam empat file utama, yaitu **index.html, style.css, script.js, dan data.json**.

Buat tampilan yang modern, profesional, dan responsif (mobile-first). Gunakan KPI cards, rounded corners, soft shadows, hover effects, smooth transitions, serta kombinasi warna yang konsisten. Gunakan HTML semantik, Tailwind CSS sebagai styling utama, Vanilla JavaScript tanpa framework tambahan, serta Chart.js untuk visualisasi.

Pastikan kode tersusun rapi, modular, mudah dipahami, memiliki komentar pada bagian penting, dan seluruh grafik mengambil data dari hasil pengolahan dataset asli, bukan data dummy.

**Hasil akhir yang diminta:** dashboard interaktif, informatif, responsif, dan dapat dijalankan melalui Visual Studio Code Live Server. Sertakan README singkat yang menjelaskan struktur file dan cara menjalankan dashboard.
