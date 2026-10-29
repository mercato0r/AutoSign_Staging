# CHANGELOG - AutoSign Pro

Format pencatatan mengikuti panduan [Keep a Changelog](https://keepachangelog.com/id/1.0.0/) dan [Semantic Versioning](https://semver.org/).

---

## [v3.2.0] - 2026-10-29

### Dioptimalkan (Changed / Optimized)
- **Asynchronous Background PDF Rasterization**:
  - Memindahkan operasi rendering bitmap `page.get_pixmap()` dari Main UI Thread ke *background worker thread* di `autosign/ui/layout_designer.py`.
  - Menerapkan pelacak generasi (`_render_generation`) untuk mencegah *race condition* atau penimpaan oleh hasil render yang sudah usang (*stale frames*).
  - Mengeliminasi UI *freeze* dan status *"Not Responding"* saat memuat dokumen, mengganti halaman, maupun mengubah skala zoom.
- **Debounced Zooming & Scrolling**:
  - Menerapkan mekanisme penundaan cerdas (100ms) pada event `Ctrl + MouseWheel` di Layout Designer menggunakan timer non-blocking `after()` dan `after_cancel()`.
  - Mencegah penumpukan puluhan siklus re-render piksel saat roda mouse diputar cepat; hanya 1 render tajam dieksekusi saat mouse berhenti berputar.
- **Non-Destructive Canvas Image Swapping**:
  - Menggantikan pola destruktif `canvas.delete("all")` dengan pembaharuan *in-place* `canvas.itemconfig(self.bg_image_id, image=...)` dan penyesuaian koordinat visual via `box.update_coords()`.
  - Menghilangkan kedipan putih/abu-abu (*flickering*) pada kanvas saat zoom dan navigasi lembar kerja.
- **Throttled Concurrency Progress & Batched Logging**:
  - `BatchOrchestrator`: Membatasi frekuensi sinyal update progres maksimal ~12.5 FPS (interval 80ms) sembari menjamin progres tugas akhir (`100%`) selalu dikirim seketika.
  - `MainWindow`: Menerapkan *buffer lock* dan *batched flush* (tiap 80ms) pada widget teks log untuk menghentikan pemborosan CPU akibat *text re-flow* Tkinter saat memproses ratusan/ribuan file PDF secara paralel.

### Ditambahkan (Added)
- Test suite pengujian otomatis baru `tests/test_optimizations.py` untuk menguji pembatasan frekuensi progres `BatchOrchestrator` dan jaminan konsistensi status akhir.

---

## [v3.1.0] - 2026-10-10

### Ditambahkan (Added)
- **UI Symbol-Based dengan Tooltip Informatif**:
  - Transformasi tombol pada sidebar Layout Designer dari *heavy text* menjadi berbasis simbol/ikon yang rapi dan ringkas (`🔍⁺`, `🔍⁻`, `↩`, `↪`, `➕ Kotak Baru`, `✏️ Label`, `🗑️ Hapus`, `💾 Simpan Profil`).
  - Komponen helper `ToolTip` mandiri (`autosign/ui/tooltip.py`) berbasis Tkinter standar tanpa pustaka pihak ketiga.
  - Penjelasan fungsi dengan kalimat lugas yang otomatis muncul saat kursor diarahkan (*hover*) ke tombol.
- **Mode Panning PDF Bebas (Metode 1)**:
  - Dukungan geser/pan kanvas PDF menggunakan **Klik Kanan Mouse (Drag Button-3)** di samping klik tengah mouse (Button-2) yang sudah ada. Memudahkan navigasi PDF berukuran besar atau saat dalam tingkat perbesaran tinggi.
- **Fitur Undo / Redo Lengkap**:
  - Tombol aksi **`↩`** dan **`↪`** di sidebar Layout Designer.
  - Shortcut keyboard **`Ctrl + Z`** untuk Undo dan **`Ctrl + Y`** / **`Ctrl + Shift + Z`** untuk Redo.
  - Snapshot otomatis untuk setiap aksi mutasi kotak tanda tangan (tambah kotak, edit label, hapus kotak, pergeseran posisi, dan pengubahan ukuran/resize).

### Dipertahankan (Preserved)
- Kontrol Zoom in/out tetap konsisten dengan tombol `[🔍⁺]`, `[🔍⁻]`, serta kombinasi `Ctrl + Scroll Mouse`.

### Catatan Rilis
- Perubahan dilakukan secara modular dan hemat resource tanpa menambah dependensi baru.
- Tidak dilakukan kompilasi / build `.exe` pada rilis ini sesuai instruksi.
