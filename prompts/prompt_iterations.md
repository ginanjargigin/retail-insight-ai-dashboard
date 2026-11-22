# Dokumentasi Iterasi Prompt – Retail Insight AI Dashboard

Dokumen ini merangkum tahapan penyempurnaan instruksi selama pengembangan. Ringkasan disusun berdasarkan catatan proyek dan laporan hasil yang tersedia; bukan transkrip verbatim dari seluruh pesan IBM Bob.

## Iterasi 1 – Prompt awal pembuatan dashboard

**Fokus:** menetapkan peran IBM Bob, konteks dataset Online Retail.xlsx, KPI, visualisasi, filter, teknologi, dan format file dashboard.

**Alasan:** memberikan gambaran awal mengenai tujuan dan ruang lingkup proyek.

**Dampak yang diharapkan:** menghasilkan rancangan awal dashboard dan struktur implementasi.

Rujuk `prompt_iterasi_1_rekonstruksi.md`. Dokumen tersebut adalah rekonstruksi, bukan salinan asli percakapan.

## Iterasi 2 – Penyesuaian terhadap struktur dataset

**Fokus:** memastikan analisis hanya menggunakan variabel yang tersedia dalam Online Retail.xlsx. Contoh variabel seperti Discount, Product Category, Sales Representative, Payment Method, dan Sales Channel tidak digunakan karena tidak tersedia dalam dataset. Analisis geografis menggunakan Country; AOV digunakan sebagai indikator nilai rata-rata transaksi.

**Alasan:** mencegah pembuatan analisis berdasarkan kolom yang tidak ada.

**Dampak:** ruang lingkup analisis menjadi sesuai dengan data sumber.

## Iterasi 3 – Data cleaning dan aturan perhitungan

**Fokus:** memperjelas pemeriksaan missing values, duplikasi, transaksi pembatalan, quantity dan UnitPrice yang tidak valid, serta penanganan CustomerID kosong.

**Aturan penting yang dilaporkan:** transaksi tanpa CustomerID tetap dihitung dalam metrik penjualan, tetapi tidak dimasukkan ke unique customers dan segmentasi RFM.

**Alasan:** menjaga konsistensi pengolahan dan interpretasi data.

**Dampak:** aturan pengolahan data menjadi lebih eksplisit dan dapat diuji.

## Iterasi 4 – Debugging dan penyempurnaan dashboard

**Fokus:** memperbaiki perhitungan KPI, pemetaan produk, perilaku filter tunggal dan kombinasi, tampilan kondisi tanpa hasil pada RFM, serta keterangan cakupan cancellation rate.

**Alasan:** hasil pengujian menemukan bagian yang perlu diperbaiki agar data dan tampilan tetap konsisten.

**Dampak:** perilaku dashboard diperbaiki berdasarkan temuan pengujian.

## Iterasi 5 – Audit akhir dan dokumentasi

**Fokus:** menjalankan audit struktur dan kode, pengujian kombinasi filter, verifikasi penanganan CustomerID kosong, rekonsiliasi status pekerjaan, serta pembaruan README.

**Hasil yang dilaporkan dalam proyek:**
- Audit Suite v3: 48/48 PASS.
- Audit Suite v4: 79/79 PASS.
- Total: 127/127 PASS, 0 FAIL yang dilaporkan.

**Alasan:** memastikan hasil akhir dan dokumentasi sesuai dengan implementasi yang dilaporkan.

**Dampak:** tersedia catatan pengujian dan dokumentasi untuk ditinjau.

## Ringkasan iterasi

| Iterasi | Fokus | Dampak |
|---|---|---|
| 1 | Prompt awal | Rancangan awal dashboard |
| 2 | Penyesuaian dataset | Analisis sesuai kolom sumber |
| 3 | Data cleaning | Aturan pengolahan lebih jelas |
| 4 | Debugging | Perbaikan fungsi dan tampilan |
| 5 | Audit akhir | Hasil pengujian terdokumentasi |

**Catatan integritas dokumentasi:** gunakan screenshot percakapan asli IBM Bob jika tersedia. Jangan menyajikan ringkasan atau rekonstruksi ini sebagai teks persis dari percakapan historis.
