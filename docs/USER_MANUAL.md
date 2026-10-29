# Panduan Pengguna AutoSign Pro

AutoSign Pro adalah perangkat lunak otomasi untuk penandatanganan dan pembubuhan stempel secara massal (batch processing) pada dokumen berformat PDF. Aplikasi ini dilengkapi dengan perancang tata letak visual (Visual Layout Designer), pengenalan kata kunci profil, eksekusi paralel multi-core, dan penempatan tanda tangan multi-halaman.

---

## 1. Persyaratan Sistem dan Persiapan Berkas

### 1.1 Persyaratan Sistem
- Sistem Operasi: Windows 10 atau Windows 11 (64-bit).
- Prosesor: Intel / AMD multi-core (disarankan minimal 4 core untuk pemrosesan paralel optimal).
- Memori RAM: Minimal 4 GB (disarankan 8 GB atau lebih untuk dokumen beresolusi tinggi).
- Ruang Penyimpanan: Minimal 500 MB untuk aplikasi dan berkas temporer, di luar kebutuhan kapasitas penyimpanan dokumen PDF.

### 1.2 Struktur Folder yang Diperlukan
Sebelum menjalankan aplikasi, persiapkan tiga direktori utama pada komputer:

1. **Folder PDF Master (Dokumen Sumber)**
   Folder tempat menyimpan seluruh berkas PDF asli yang akan dibubuhi tanda tangan atau stempel. Folder ini dapat memiliki struktur subfolder bertingkat (misalnya berdasarkan divisi, tahun, atau nomor proyek).

2. **Folder Master Tanda Tangan (Signature Root)**
   Folder tempat menyimpan seluruh berkas gambar tanda tangan, paraf, atau stempel. Berkas harus berformat PNG dengan latar belakang transparan. Nama berkas (tanpa ekstensi .png) harus sama persis dengan nama label yang ditentukan pada profil tata letak.

3. **Folder Output (Hasil Pemrosesan)**
   Folder tujuan untuk menampung berkas PDF yang telah selesai diproses. Struktur subfolder dari Folder PDF Master akan diduplikasi secara otomatis ke dalam Folder Output.

---

## 2. Mekanisme Pencarian Berkas Tanda Tangan (3-Tier Resolver)

AutoSign Pro menggunakan algoritma hierarkis 3 tingkat untuk menemukan berkas gambar tanda tangan (.png) yang sesuai untuk setiap dokumen:

1. **Tingkat 1 - Subfolder Identik**
   Sistem mencari berkas gambar pada subfolder di Master Tanda Tangan yang jalurnya identik dengan jalur subfolder dokumen PDF terhadap PDF Master.
   *Contoh:* Jika dokumen berada di `PDF_Master/Divisi_A/Laporan.pdf` dan label kotak adalah `TTD_Manager`, sistem mencari `Master_TTD/Divisi_A/TTD_Manager.png`.

2. **Tingkat 2 - Segmen Parent Terdekat (Reverse Walk)**
   Jika berkas tidak ditemukan di tingkat 1, sistem akan memeriksa folder induk secara bertingkat dari subfolder terdalam hingga ke atas.
   *Contoh:* Jika dokumen berada di `PDF_Master/Divisi_A/Proyek_X/Laporan.pdf`, sistem akan memeriksa `Master_TTD/Proyek_X/TTD_Manager.png`, lalu `Master_TTD/Divisi_A/TTD_Manager.png`.

3. **Tingkat 3 - Root Master Fallback**
   Jika berkas tetap belum ditemukan pada subfolder, sistem mengambil berkas tanda tangan umum yang berada langsung di direktori utama Master Tanda Tangan (`Master_TTD/TTD_Manager.png`).

Jika setelah ketiga tingkat tersebut berkas gambar tidak ditemukan, sistem mencatat peringatan status pada log dan dokumen terkait akan dilewati demi menjaga keutuhan data.

---

## 3. Panduan Penggunaan Visual Layout Designer

Visual Layout Designer digunakan untuk menentukan posisi, ukuran, dan target halaman bagi setiap tanda tangan atau stempel pada dokumen PDF.

### 3.1 Membuka Layout Designer
1. Pada jendela utama aplikasi, klik tombol **Create New Profile** untuk membuat profil baru, atau klik tombol **Edit** pada salah satu baris profil yang sudah ada.
2. Jendela Layout Designer akan terbuka secara maksimal (maximized) untuk kenyamanan penyuntingan.

### 3.2 Memuat Berkas PDF Contoh
1. Klik tombol **Buka PDF Contoh** pada panel bilah sisi kiri.
2. Pilih salah satu berkas PDF yang mewakili jenis dokumen yang akan diproses secara massal.
3. Halaman dokumen akan dirender pada kanvas kerja di sebelah kanan.

### 3.3 Konfigurasi Identitas Profil
- **Profile Name**: Masukkan nama profil yang unik dan deskriptif (misalnya `Profil_Surat_Keputusan` atau `Profil_Kuitansi`).
- **Keywords (Dipisahkan koma)**: Masukkan satu atau beberapa kata kunci pencocokan (misalnya `SK, KEPUTUSAN, SURAT`). Setiap berkas PDF di folder sumber yang memuat kata kunci tersebut pada nama berkasnya akan otomatis diproses menggunakan profil ini.

### 3.4 Navigasi Halaman Dokumen
Dokumen PDF dapat terdiri dari satu atau banyak halaman:
- Gunakan tombol panah kiri `[ < ]` untuk berpindah ke halaman sebelumnya.
- Gunakan tombol panah kanan `[ > ]` untuk berpindah ke halaman berikutnya.
- Indikator halaman menampilkan informasi posisi halaman saat ini (misalnya `Hal: 1 / 5`).
- Setiap kotak tanda tangan yang dibuat akan terikat pada nomor halaman aktif saat kotak tersebut ditambahkan.

### 3.5 Manajemen Kotak Tanda Tangan (Bounding Box)
1. **Menambah Kotak Baru**
   Klik tombol **Kotak Baru**. Kotak berwarna akan muncul di area tengah halaman dokumen.

2. **Menggeser Posisi Kotak**
   Arahkan kursor ke dalam area kotak (kursor berubah menjadi ikon panah empat arah), tekan dan tahan klik kiri mouse, lalu geser kotak ke posisi yang diinginkan.

3. **Mengubah Ukuran Kotak (Resize)**
   Klik pada kotak untuk mengaktifkannya. Pegangan sudut (resize handle) berupa persegi kecil akan muncul di sudut kanan bawah kotak. Tarik pegangan tersebut dengan klik kiri mouse untuk memperbesar atau memperkecil area kotak.

4. **Mengubah Label Kotak**
   Pilih kotak yang akan diubah, kemudian klik tombol **Label**. Dialog input akan muncul. Masukkan nama label tanda tangan tanpa ekstensi .png (misalnya `TTD_Direktur` atau `STEMPEL_BASAH`).

5. **Menghapus Kotak**
   Pilih kotak yang ingin dihapus, kemudian klik tombol **Hapus**. Kotak akan terhapus dari lembar kerja.

### 3.6 Navigasi Kanvas dan Kontrol Tampilan
- **Perbesaran Tampilan (Zoom In / Zoom Out)**:
  - Klik tombol `[ + ]` untuk memperbesar atau tombol `[ - ]` untuk memperkecil skala tampilan.
  - Alternatif pintasan cepat: Tahan tombol `Ctrl` pada keyboard sambil memutar roda mouse (Mouse Wheel). Sistem menerapkan debouncing otomatis sehingga perbesaran berjalan mulus tanpa lag.
- **Menggeser Kanvas (Panning)**:
  - Tekan dan tahan tombol **Klik Kanan Mouse (Drag Button-3)** di atas kanvas, lalu geser mouse ke arah yang diinginkan.
  - Kanvas juga mendukung pergeseran menggunakan klik tengah mouse (Button-2).
- **Pembatalan dan Pengulangan Aksi (Undo / Redo)**:
  - Batalkan aksi terakhir dengan menekan tombol **Undo** pada sidebar atau menggunakan kombinasi tombol `Ctrl + Z`.
  - Ulangi aksi yang dibatalkan dengan menekan tombol **Redo** pada sidebar atau menggunakan kombinasi tombol `Ctrl + Y` (atau `Ctrl + Shift + Z`).
  - Riwayat mencakup penambahan kotak, penggeseran posisi, pengubahan ukuran, pengeditan label, dan penghapusan kotak.
- **Tooltip Informatif**:
  - Arahkan kursor mouse ke tombol apa pun pada sidebar untuk melihat penjelasan singkat mengenai fungsi tombol tersebut.

### 3.7 Menyimpan Profil
Setelah penataan selesai, klik tombol **Simpan Profil** di bagian bawah panel sidebar. Konfigurasi akan disimpan ke dalam direktori `profiles/<Nama_Profil>.json`. Jendela Layout Designer dapat ditutup setelah pesan konfirmasi berhasil muncul.

---

## 4. Panduan Eksekusi Pemrosesan Massal (Batch Processing)

Setelah profil konfigurasi dibuat, pemrosesan massal dapat dijalankan langsung melalui Jendela Utama (Main Window).

### 4.1 Pemilihan Profil Aktif
1. Pada bagian **Profile Management**, centang kotak centang (checkbox) pada profil-profil yang ingin diaktifkan.
2. Gunakan tombol **Toggle All** untuk memilih atau membatalkan pilihan seluruh profil sekaligus.
3. Label penghitung menampilkan jumlah profil aktif terhadap total profil yang tersedia (misalnya `(2/3 Selected)`).

### 4.2 Pengaturan Jalur Direktori (Path Configuration)
Pastikan ketiga jalur direktori terisi dengan benar:
1. **PDF Root Folder**: Klik tombol `Browse` dan pilih folder sumber dokumen PDF.
2. **Signature Root**: Klik tombol `Browse` dan pilih folder master gambar tanda tangan/stempel.
3. **Output Folder**: Klik tombol `Browse` dan pilih folder tujuan penyimpanan hasil.
*Catatan:* Pengaturan jalur direktori akan disimpan secara otomatis ke dalam berkas konfigurasi lokal (`settings.json`) sehingga Anda tidak perlu memilih ulang setiap kali membuka aplikasi.

### 4.3 Opsi Tambahan: Lewati Berkas yang Sudah Diproses (Skip Existing)
Centang opsi **Skip Existing Files** untuk efisiensi waktu. Apabila opsi ini aktif, dokumen PDF yang nama dan jalurnya sudah terdapat di folder output tidak akan diproses ulang.

### 4.4 Menjalankan Proses
1. Klik tombol **RUN PROCESS**.
2. Sistem akan memindai folder PDF Master secara rekursif, mencocokkan kata kunci setiap dokumen dengan profil yang aktif, dan membagi tugas ke dalam antrean multi-threading.
3. Indikator kemajuan (Progress Bar) dan persentase akan bergerak secara teratur hingga mencapai 100%.
4. Panel log pemrosesan akan menampilkan status setiap berkas (berhasil diproses, dilewati, atau berkas tanda tangan tidak ditemukan).

### 4.5 Menghentikan Proses (Stop)
Jika ingin membatalkan pemrosesan yang sedang berjalan, klik tombol **STOP**. Sistem akan segera menghentikan antrean tugas berikutnya dengan aman tanpa merusak berkas PDF yang sedang ditulis.

### 4.6 Membuka Folder Output
Setelah seluruh dokumen selesai diproses, tombol **OPEN OUTPUT** akan aktif. Klik tombol tersebut untuk membuka Folder Output secara langsung di Windows File Explorer.

---

## 5. Ringkasan Pintasan Papan Ketik (Keyboard Shortcuts)

| Tombol / Kombinasi | Area | Fungsi |
|---|---|---|
| `Ctrl + Z` | Layout Designer | Membatalkan aksi terakhir (Undo) |
| `Ctrl + Y` | Layout Designer | Mengulang aksi yang dibatalkan (Redo) |
| `Ctrl + Shift + Z` | Layout Designer | Alternatif mengulang aksi yang dibatalkan (Redo) |
| `Ctrl + Scroll Mouse Up` | Layout Designer | Memperbesar tampilan dokumen (Zoom In) |
| `Ctrl + Scroll Mouse Down` | Layout Designer | Memperkecil tampilan dokumen (Zoom Out) |
| `Klik Kanan + Geser (Drag)` | Layout Designer | Menggeser lembar kerja kanvas (Panning) |
| `Klik Tengah + Geser (Drag)` | Layout Designer | Alternatif menggeser lembar kerja kanvas (Panning) |

---

## 6. Pemecahan Masalah (Troubleshooting)

### Berkas Tanda Tangan Tidak Ditemukan (Missing Signature)
- **Gejala**: Log menampilkan pesan `MISSING: <label>.png untuk <nama_dokumen>.pdf`.
- **Penyebab**: Berkas gambar PNG untuk label tersebut tidak ada pada struktur folder Master Tanda Tangan.
- **Solusi**:
  1. Periksa ejaan label pada profil di Layout Designer.
  2. Pastikan file gambar berformat `.png` (huruf kecil) dan diletakkan pada subfolder yang sesuai atau langsung pada folder utama Master Tanda Tangan.

### Dokumen PDF Kosong atau Gagal Diproses
- **Gejala**: Log menampilkan pesan galat mengenai berkas PDF kosong (0 halaman) atau berkas rusak.
- **Penyebab**: Berkas PDF di folder sumber berukuran 0 byte atau mengalami kerusakan struktur berkas.
- **Solusi**: Periksa kembali berkas PDF asli menggunakan aplikasi pembaca PDF standar untuk memastikan dokumen tidak rusak atau terkunci kata sandi.

### Orientasi Dokumen atau Rotasi Halaman
- **Keterangan**: AutoSign Pro secara otomatis menghitung matriks derotasi halaman PDF (`page.derotation_matrix`). Tanda tangan dan stempel akan menempel tegak sesuai orientasi pembacaan halaman meskipun halaman PDF asli memiliki rotasi internal 90, 180, atau 270 derajat.

### Tata Letak Tanda Tangan Mengalami Pergeseran
- **Penyebab**: Berkas PDF contoh yang digunakan pada Layout Designer memiliki dimensi atau perbandingan aspek yang berbeda dengan dokumen PDF aktual yang diproses.
- **Solusi**: Pastikan berkas contoh yang dibuka saat perancangan tata letak memiliki ukuran kertas dan tata letak yang identik dengan kelompok dokumen yang diproses.
