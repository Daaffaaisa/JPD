# UI/UX & Usability Audit Report — IDM Clone

Audit komprehensif ini dilakukan menggunakan metodologi **`ui-craft`** (Discovery, Token Inventory, Heuristic Review, Technical Accessibility/Performance/Responsiveness Analysis, dan Design Law Evaluation) pada aplikasi **IDM Clone** (Desktop GUI Tkinter Win32 & Browser WebExtension).

---

## 1. Struktur UI Sekarang

### Layar & Permukaan Utama
1. **Layar Utama Desktop (`IDMGUIApp` - `src/idm_gui/app.py`):**
   - **Menu Bar Atas:** Hierarki 5 menu Win32 native cascading (`Tugas`, `Berkas`, `Unduh`, `Lihat`, `Bantuan`) dengan penataan shortcut keyboard (`Ctrl+N`, `Del`, `Alt+F4`).
   - **Toolbar Aksi Cepat:** Flat horizontal bar berlatar permukaan gelap (`#27272a`) dengan 8 tombol aksi (`➕ Tambah URL`, `▶ Lanjutkan`, `⏸ Jeda`, `⏹ Hentikan Semua`, `🗑 Hapus`, `🧹 Hapus Selesai`, `📁 Buka Folder`, `⚙ Opsi`).
   - **Paned Split Layout:**
     - *Sidebar Kiri (180px):* Treeview kategori bernavigasi hierarkis dengan indikator emoji (`📁 Kategori`, `📥 Semua Unduhan`, `🎬 Video`, `🎵 Musik`, `🖼️ Gambar`, `📦 Program`, `📄 Dokumen`, `🗜️ Zip`, `✅ Selesai`, `⏳ Belum Selesai`).
     - *Area Tabel Kanan:* Treeview daftar unduhan 6 kolom (`Nama Berkas`, `Ukuran`, `Status`, `Progres`, `Kecepatan`, `URL Unduhan`) bertema `clam` gelap dengan baris 26px dan scrollbar vertikal.
   - **Status Bar Bawah:** Indikator koneksi server IPC loopback (Port 19900) dan penghitung ringkasan tugas aktif serta total bandwidth.

2. **Layar & Dialog Modal Sekunder (`src/idm_gui/dialogs.py`):**
   - **`DownloadInfoDialog` (Info Unduh Berkas - 540x340 px):**
     - Form input URL, dropdown kategori berkas, input jalur penyimpanan lokal dengan penjelajah folder `[...]`.
     - Checkbox *"Ingat jalur ini untuk kategori"*.
     - File Information Card: Visualisasi ikon aplikasi default Windows resolusi tinggi (ekstraksi Win32 `SHGetFileInfoW`), estimasi ukuran berkas, input deskripsi opsional, dan teks akselerasi koneksi.
     - Banner peringatan keamanan merah jika terdeteksi ekstensi ganda berisiko (`.pdf.exe`).
     - Baris tombol aksi: `Unduh Nanti`, `Mulai Unduh` (Primary default Enter), dan `Batal`.
   - **`DownloadProgressDialog` (Progres Pengunduhan - 560x440 px):**
     - Header tab status (`Status unduhan`, `Pembatas Kecepatan`, `Opsi saat selesai`).
     - Kotak informasi transfer (URL, Status, Ukuran, Jumlah Terunduh %, Kecepatan saat ini, Estimasi waktu sisa/ETA, Kemampuan resume).
     - Progress bar linear utama (Canvas Tkinter).
     - Tombol kontrol: `<< Sembunyikan detail`, `Jeda`/`Lanjutkan`, dan `Batal`.
     - Collapsible Detail Panel: Kanvas visual multi-koneksi paralel dan Treeview tabel koneksi per jalur.
   - **`DownloadCompleteDialog` (Unduhan Selesai - 460x200 px):**
     - Kanvas ikon centang hijau emerald, kotak informasi berkas terunduh, dan tombol aksi (`Buka`, `Buka Folder`, `Selesai`).
   - **`OptionsDialog` (Opsi Konfigurasi - 560x430 px):**
     - Notebook 4 tab: Tab 1 `Umum` (integrasi browser & startup), Tab 2 `Jenis Berkas` (ekstensi unduh otomatis & domain pengecualian), Tab 3 `Simpan ke` (folder per kategori & direktori sementara), Tab 4 `Koneksi` (tipe koneksi & dropdown 1-32 jalur paralel).
   - **`open_add_url_dialog` (Dialog Tambah URL Cepat - 460x140 px):**
     - Dialog popup input teks URL sederhana saat clipboard kosong.

3. **Permukaan Ekstensi Browser (`extension/`):**
   - **Floating Video Grabber Panel (`content.js` + `overlay.css`):** Tombol mengambang modern bergradien Sky Blue (`#0284c7` $\to$ `#0369a1`), dropdown resolusi video berlatar dark blur (`backdrop-filter: blur(8px)`), dan animasi mikro hover.
   - **Extension Browser Action Popup (`popup.html` + `popup.js`):** Dialog popup toolbar browser untuk mengecek kesehatan loopback daemon.

### Komponen yang Diulang (Reusable Components)
- `create_modern_button`: Helper tombol interaktif dengan event binding hover `<Enter>` / `<Leave>`, transisi kursor `hand2`, dan peran semantik (`primary`, `secondary`, `danger`, `toolbar`).
- `apply_theme_to_toplevel`: Helper standar penataan geometri, background dark, dan penempatan modal di tengah monitor.
- `setup_global_ttk_theme`: Pengaturan tema terpusat untuk widget `ttk.Treeview`, `ttk.Notebook`, dan `ttk.Combobox`.
- `format_size_id` & `format_time_left`: Formatter metrik ramah pengguna (lokalisasi desimal koma dan satuan waktu Bahasa Indonesia).

### Token & Variabel Desain yang Sudah Ada (`src/idm_gui/theme.py`)
- **Surfaces:** `bg_dark` (`#18181b`), `surface` (`#27272a`), `surface_alt` (`#202023`), `input_bg` (`#141416`).
- **Borders & Dividers:** `border` (`#3f3f46`), `border_light` (`#52525b`), `focus_ring` (`#38bdf8`).
- **Typography Colors:** `text_primary` (`#fafafa`), `text_secondary` (`#a1a1aa`), `text_disabled` (`#71717a`).
- **Semantic Accents:** `accent_primary` (`#0284c7`), `accent_hover` (`#0369a1`), `accent_active` (`#075985`), `secondary_bg` (`#3f3f46`), `secondary_hover` (`#52525b`), `success` (`#10b981`), `warning` (`#f59e0b`), `danger` (`#ef4444`), `danger_hover` (`#dc2626`).
- **Typography Scale:** `Segoe UI` (Title: 10pt bold, Heading: 9pt bold, Body: 9pt regular, Small: 8pt regular, Code: Consolas 9pt).

---

## 2. Temuan Teknis (Aksesibilitas, Performa, Responsif)

### Prioritas 0 — Kritis (Performa & Pengalaman Blokir)
1. **Synchronous Network Probing Membekukan Main Thread GUI (Performa):**
   - *Lokasi:* `src/idm_gui/app.py:511` pada fungsi `_show_download_info_for_url`.
   - *Detail:* Panggilan `self.engine.probe(url)` dijalankan secara synchronous di main thread Tkinter sebelum jendela dialog informasi unduhan ditampilkan. Pada server web yang lambat, berlatensi tinggi, atau CDN dengan rate limiting, antarmuka Tkinter membeku total (*Not Responding*) selama 2–5+ detik.
   - *Dampak:* Melanggar Doherty Threshold (<400ms feedback).
2. **Penghapusan Berkas Instan Tanpa Konfirmasi & Multi-Select Patah (Kontrol Pengguna):**
   - *Lokasi:* `src/idm_gui/app.py:805` (`delete_selected`) dan baris 791 (`_get_selected_task_id`).
   - *Detail:* Menekan tombol `Hapus` pada toolbar atau tombol keyboard `<Delete>` langsung menghapus tugas unduhan seketika tanpa peringatan dialog konfirmasi ("Apakah Anda yakin ingin menghapus tugas ini?"). Selain itu, meskipun tabel mendukung multi-seleksi (`selectmode="extended"`), handler hanya membaca `sel[0]`, sehingga tombol Hapus/Jeda hanya berdampak pada baris pertama dan mengabaikan baris lain yang dipilih.

### Prioritas 1 — Tinggi (Integritas State & Aksesibilitas)
3. **Tab Opsi Umum Mengabaikan Nilai Simpan (Integritas State):**
   - *Lokasi:* `src/idm_gui/dialogs.py:1020` pada `OptionsDialog._on_save`.
   - *Detail:* Checkbox integrasi browser (Chrome, Edge, Firefox, Opera) dan pengaturan autorun startup di Tab 1 (`Umum`) tidak disimpan ke objek persistensi `self.sm.data`. Setiap kali dialog ditutup dan dibuka kembali, pilihan pengguna kembali ke nilai awal.
4. **Tab Palsu Non-Interaktif pada Dialog Progres (Aksesibilitas & Ekspektasi):**
   - *Lokasi:* `src/idm_gui/dialogs.py:506-512` pada `DownloadProgressDialog`.
   - *Detail:* Elemen visual tab `"Pembatas Kecepatan"` dan `"Opsi saat selesai"` dibuat menggunakan `tk.Label` statis tanpa event listener. Elemen ini tampak seperti tab yang bisa diklik, namun tidak merespons klik mouse pengguna.
5. **Pelanggaran Rasio Kontras WCAG AA (Aksesibilitas Visual):**
   - *Lokasi:* `OptionsDialog` (keterangan domain pengecualian) dan `DownloadProgressDialog` (label tab tidak aktif).
   - *Detail:* Warna teks `#888888` di atas background `#2b2b2b` dan `#1e1e1e` menghasilkan rasio kontras 3.2:1–3.5:1. Angka ini gagal memenuhi standar WCAG 2.1 Level AA (minimal 4.5:1 untuk teks biasa).

### Prioritas 2 — Sedang (Responsif & Konsistensi Rendering)
6. **Dimensi Statis Menyebabkan Text Clipping pada Windows High-DPI Scaling (Responsif):**
   - *Lokasi:* Seluruh dialog di `dialogs.py` (`resizable(False, False)` dengan piksel tetap seperti `540x340`, `560x430`).
   - *Detail:* Pada laptop Windows 11 modern dengan skala layar 125% atau 150%, elemen form di bagian bawah terpotong atau mepet ke tepi bingkai jendela karena layout tidak dapat diperluas.
7. **Toolbar Meluap (Overflow) Tanpa Bungkus Responsif (Responsif):**
   - *Lokasi:* `src/idm_gui/app.py:298` (`_build_toolbar`).
   - *Detail:* Toolbar ditata secara horizontal datar dengan `pack(side=tk.LEFT)`. Ketika jendela utama dikecilkan di bawah 760px lebar, tombol `⚙ Opsi` dan `📁 Buka Folder` terpotong ke luar layar tanpa menu luapan (overflow dropdown).
8. **Canvas Redraw Thrashing pada Visualisasi Segmen (Performa Render):**
   - *Lokasi:* `src/idm_gui/dialogs.py:667` (`self.seg_canvas.delete("all")`).
   - *Detail:* Menghapus dan membuat ulang puluhan objek Canvas 4 kali per detik alih-alih menggunakan `self.seg_canvas.coords()`, meningkatkan konsumsi CPU saat mengunduh di 32 koneksi.

---

## 3. Scorecard Heuristic (Nielsen + Hukum Desain)

### Heuristic Scorecard (Nielsen's 10)

| Heuristic | Score | Finding | Impact |
|---|:---:|---|---|
| **Visibility of system status** | 3 | Progres unduhan dan kecepatan transfer terpantau jelas di tabel dan dialog; namun pada Tab 1 Opsi perubahan pengaturan diabaikan tanpa peringatan, dan label akselerasi di info dialog tertulis statis "4 Koneksi" | `reduces-trust` |
| **Match system and real world** | 3 | Ekstraksi ikon aplikasi native Windows (VLC, WinRAR, PDF) dan lokalisasi istilah IDM sangat baik; namun tab "Pembatas Kecepatan" & "Opsi saat selesai" di progress dialog adalah label tiruan non-interaktif | `adds-friction` |
| **User control and freedom** | 2 | Tombol Hapus (Delete) menghapus unduhan seketika tanpa dialog konfirmasi atau undo; aksi multi-select pada tabel terpotong hanya mengeksekusi 1 baris | `blocks-conversion` |
| **Consistency and standards** | 3 | Desain desktop telah menggunakan token Zinc gelap; namun jendela mini Add URL masih menggunakan raw hardcoded widgets, dan popup ekstensi browser masih memakai tema light usang | `reduces-trust` |
| **Error prevention** | 3 | Pemindai adware ekstensi ganda (.pdf.exe) sangat efektif; namun input URL manual dan input folder tidak memiliki validasi format inline sebelum tombol ditekan | `adds-friction` |
| **Recognition over recall** | 3 | Ikon kategori dan berkas sangat membantu ingatan visual; namun tombol toolbar tidak memiliki tooltip pintasan keyboard, dan tabel kosong tidak memiliki pesan sambutan/panduan | `adds-friction` |
| **Flexibility and efficiency** | 3 | Dukungan shortcut keyboard (`Ctrl+N`, `Del`) dan intersepsi loopback browser otomatis sangat cepat; namun ketiadaan bar pencarian/filter unduhan menyulitkan pencarian daftar panjang | `adds-friction` |
| **Aesthetic and minimalist** | 4 | Palet Zinc Dark Presisi terpadu, rasio kontras warna aksen Sky Blue tepat sasaran; terdapat tumpang tindih indeks row=5 di layout grid Info Dialog dan tombol dead "+" | `minor-polish` |
| **Error recovery** | 2 | Unduhan yang gagal hanya berstatus "Gagal" tanpa kode kesalahan, rincian penyebab (misal HTTP 403 / Timeout), maupun tombol satu klik untuk mencoba ulang (Retry) | `blocks-conversion` |
| **Help and documentation** | 3 | Kotak dialog "Tentang" dan "Tip Hari Ini" tersedia; namun tidak ada dokumentasi inline terkait cara memasang ekstensi peramban atau pengaturan jalur koneksi | `minor-polish` |

### Design Law Audit (6 Laws)

| Law | Status | Detail |
|---|:---:|---|
| **Fitts's Law** | **PASS** | Target klik tombol desktop memenuhi standar $\ge 24\text{ px}$ (tinggi rata-rata 28–34 px dengan padding nyaman); tombol CTA utama (*Mulai Unduh*, *Simpan*) dikelompokkan konsisten di sudut kanan bawah. |
| **Hick's Law** | **PASS** | Menu Bar utama terbagi rapi ke dalam 5 grup menu ($\le 7$ item); toolbar dibatasi 8 tombol inti; dialog opsi dipecah menjadi 4 tab tematik mandiri. |
| **Doherty Threshold** | **FAIL** | Operasi probing ukuran file HTTP HEAD dijalankan langsung di thread antarmuka pada saat membuka dialog unduhan URL, menyebabkan GUI membeku $\ge 1-3\text{ detik}$ pada link berlatensi lambat tanpa loading skeleton. |
| **Cleveland-McGill Hierarchy** | **PASS** | Progres kuantitatif dikodekan menggunakan panjang dan posisi horizontal (Linear Progress Bar & Segment Strips), menempati puncak akurasi persepsi visual manusia. Tidak ada pie chart/grafik 3D yang mendistorsi data. |
| **Miller's Law** | **PASS** | Informasi pada setiap dialog dikelompokkan ke dalam 3–4 segmen kognitif terpisah (Metadata, Direktori, Info File, Kontrol Aksi). |
| **Tesler's Law** | **PASS** | Kompleksitas sistem diserap oleh heuristik perangkat lunak: inferensi otomatis kategori berkas dari MIME/ekstensi, ekstraksi otomatis nama berkas dari header, dan auto-fallback jalur koneksi. |

### Top Findings (Ranked by Impact)

1. **User control and freedom (`blocks-conversion`) — Score 2:**
   Pemberian perintah Hapus tugas unduhan (`Del`) mengeksekusi penghapusan permanen instan tanpa dialog konfirmasi atau aksi pembatalan (Undo). Pada tabel dengan banyak item terpilih, operasi hanya menghapus baris pertama.
2. **Error recovery (`blocks-conversion`) — Score 2:**
   Kegagalan pengunduhan jaringan (HTTP 403, 404, atau putus koneksi) hanya mengubah status teks menjadi "Gagal" tanpa pesan diagnostik yang jelas atau tombol coba ulang (*Retry*).
3. **Doherty Threshold (`adds-friction`) — FAIL:**
   Panggilan probe HTTP HEAD synchronous membekukan antarmuka saat input tautan unduhan baru. Harus dipindahkan ke asynchronous background worker dengan indikator animasi memuat (*skeleton loader*).
4. **Visibility of system status (`reduces-trust`) — Score 3:**
   Pengaturan integrasi browser pada Tab Opsi Umum tidak tersimpan ke disk saat tombol Simpan ditekan, dan label akselerasi pada DownloadInfoDialog menampilkan teks statis "4 Koneksi" meskipun engine berjalan di 32 koneksi.
5. **Consistency and standards (`reduces-trust`) — Score 3:**
   Popup ekstensi browser (`popup.html`) masih menggunakan tema putih/light usang dengan warna tombol lawas (`#2b78e4`), sangat tidak selaras dengan tema Zinc Dark pada aplikasi desktop IDM Clone.

---

## 4. UsabilityScore

**43 / F** *(judged)* · Heuristic Base 48 − Law Penalty 5

| Komponen Perhitungan | Nilai Evaluasi |
|---|---|
| Rata-rata Skor Nielsen (1–5) | **2.9** |
| Heuristic Base (Skala 0–100) | **48** $\Big(\text{round}\big(\frac{2.9 - 1}{4} \times 100\big)\Big)$ |
| Hukum Desain Gagal | **1** (*Doherty Threshold: UI Freeze on sync probe*) |
| Penalti Hukum Desain | **−5** ($1 \times 5$) |
| **UsabilityScore Final** | **43 / F** |

---

## 5. Pola yang Terlihat Generik atau Tidak Konsisten

1. **Inkonsistensi Ekstensi vs Desktop Application:**
   Aplikasi desktop telah dipercantik dengan tema gelap Zinc (`#18181b` / `#27272a`), namun popup browser (`extension/popup.html`) masih tertinggal dengan tema putih abu-abu dasar (`#f8f9fa`, teks `#333`, tombol `#2b78e4`). Pengguna yang berpindah dari browser ke desktop merasakan patahan identitas visual.
2. **Widget Mentah pada Dialog Tambah URL Cepat (`open_add_url_dialog`):**
   Dialog penambahan URL manual di `app.py` masih memakai tombol mentah `tk.Button` dan warna hardcoded `#2b2b2b` / `#0066cc` alih-alih memanfaatkan sistem helper terpadu `create_modern_button` dan token `THEME`.
3. **Tab Palsu / Non-Fungsional pada Dialog Progres Unduhan:**
   Label `"Pembatas Kecepatan"` dan `"Opsi saat selesai"` digambar berdampingan dengan tab aktif seolah-olah tab fungsional, namun sebenarnya label pasif. Hal ini melanggar ekspektasi antarmuka standar.
4. **Visualisasi Segmen Multi-Koneksi yang Disimulasikan:**
   Garis-garis progress koneksi paralel pada kanvas segmen dihitung dengan rumus statis `part_pct = min(1.0, (pct / 100.0))` sehingga semua koneksi maju bersamaan secara kaku, bukan memperlihatkan byte chunk sebenarnya dari masing-masing thread.
5. **Elemen Mati (Dead Control):**
   Tombol `+` di samping dropdown kategori pada `DownloadInfoDialog` tidak memiliki fungsi callback (`command=None`), memberikan ilusi fitur tambah kategori yang rusak.
6. **Campuran Bahasa Tampilan (Language Drift):**
   Header kolom tabel utama masih berbahasa Inggris (`File Name`, `Size`, `Transfer Rate`), sedangkan menubar, toolbar, sidebar kategori, dan semua dialog modal berbahasa Indonesia (`Nama Berkas`, `Ukuran`, `Kecepatan`).

---

## 6. Rekomendasi & Rencana Perombakan

| Komponen / Layar | Tingkat Intervensi | Rekomendasi Tindakan |
|---|:---:|---|
| **Layar 1: `DownloadProgressDialog`** | **REBUILD** *(Prioritas 1)* | • Ubah kanvas segmen multi-koneksi agar membaca offset byte riil per thread (bukan simulasi statis).<br>• Ganti tab palsu dengan sub-panel fungsional nyata (Speed Limiter slider) atau hilangkan tab tiruan tersebut agar tidak membingungkan.<br>• Gunakan koordinat dinamis (`coords`) daripada `delete("all")` pada setiap tick untuk performa render 60fps. |
| **Layar 2: Input URL & `DownloadInfoDialog`** | **REFRESH** *(Prioritas 2)* | • Pindahkan HTTP HEAD probing ke background thread dan tampilkan indikator skeleton "Memeriksa ukuran..." non-blocking.<br>• Hubungkan teks koneksi dengan pengaturan aktif (`settings.get_max_connections()`).<br>• Perbaiki overlap grid layout pada `row=5` dan berikan fungsionalitas popup pada tombol `+` kategori. |
| **Layar 3: Main Window Table & Selection** | **REFRESH** *(Prioritas 3)* | • Tambahkan dialog konfirmasi sebelum aksi `Hapus` unduhan dijalankan.<br>• Perbaiki penanganan multi-select agar operasi batch berjalan pada seluruh item yang dipilih.<br>• Tambahkan kartu ilustrasi kosong (*empty-state onboarding*) jika antrian unduhan masih kosong.<br>• Samakan seluruh teks header tabel menjadi Bahasa Indonesia resmi. |
| **Layar 4: Browser Extension Popup** | **RESKIN** *(Prioritas 4)* | • Selaraskan styling CSS `popup.html` dengan Dark Zinc Design Tokens (`#18181b`, `#27272a`, `#0284c7`).<br>• Tambahkan indikator status koneksi yang responsif dan animasi pulsa saat terhubung ke port 19900. |

---
*Laporan ini disimpan secara otomatis sebagai `AUDIT.md` untuk dijadikan acuan sprint penyempurnaan UI/UX berikutnya.*
