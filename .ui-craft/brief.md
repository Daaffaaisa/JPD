# Design Brief — IDM Clone

Durable design context for IDM Clone desktop GUI (Tkinter Win32) and browser WebExtension.

---

### 1. Product Purpose
Pengelola unduhan berkecepatan tinggi multi-jalur untuk Windows desktop yang mengintegrasikan penangkapan unduhan peramban, akselerasi transfer paralel zero-copy, dan streaming parser tanpa iklan maupun bloatware.

---

### 2. Primary User
Pengguna Windows desktop yang rutin mengunduh media dan berkas besar (video, film, game, dokumen) serta membutuhkan akselerasi transfer yang andal, visualisasi koneksi nyata, dan antarmuka yang tenang, rapi, serta hemat daya.

---

### 3. Core Operating Principles (Conflict-Resolution Order)
1. **Data & Speed Over Decoration:** Kecepatan transfer dan integritas data adalah prioritas tertinggi. Visualisasi antarmuka wajib mencerminkan transmisi fisik byte yang sebenarnya (bukan animasi fiktif).
2. **Calm Precision (Terinspirasi Apple Dark Mode):** Antarmuka berkesan tenang dan lega. Menggunakan satu aksen fungsional, latar belakang gelap berlapis (*elevated surfaces*), tipografi berkontras tinggi tanpa silau, dan menghindari dekorasi berlebih.
3. **Unobtrusive Autonomy:** Bekerja di latar belakang secara hening via loopback IPC port 19900 tanpa mencuri fokus jendela pengguna (*no focus-stealing*) saat unduhan dimulai dari peramban.
4. **Safety by Default:** Proaktif melindungi pengguna dari malware/adware berkedok ekstensi ganda (`.pdf.exe`) dan mewajibkan konfirmasi sebelum penghapusan data permanen.

---

### 4. Success Metric
Pengguna dapat membaca status unduhan, alokasi jalur koneksi, dan progres transfer secara sekilas dalam waktu $\le 2\text{ detik}$ tanpa distraksi visual.

---

### 5. Out of Scope
- Tidak menyematkan banner promosi, popup komersial, atau elemen berkedip.
- Tidak menggunakan rendering grafis berat yang membebani CPU (tanpa efek blur tiruan atau animasi loop berkecepatan tinggi).
- Tidak mengubah kompatibilitas alur unduh atau integrasi IPC loopback yang telah stabil.

---

### 6. Learned Constraints
- Tkinter tidak mendukung CSS asli maupun efek *backdrop-filter: blur()*.
- Sudut bulat murni hanya dapat dibentuk melalui widget `Canvas`; gunakan secara hemat untuk kartu atau tombol khusus agar tidak memperlambat event loop.
- Animasi transisi dibatasi pada durasi singkat ($120\text{–}180\text{ ms}$) menggunakan `after()`.
- Wajib mempertahankan: shortcut keyboard (`Ctrl+N`, `Del`, `Alt+F4`), dialog peringatan ekstensi ganda, ekstraksi ikon native Windows (`SHGetFileInfoW`), dan lokalisasi Bahasa Indonesia.
- Prosedur perombakan UI multi-layar wajib mengikuti siklus per-layar: (1) Screenshot baseline (before), (2) Terse audit & proposal (refresh/reskin/rebuild) lalu STOP & tunggu persetujuan, (3) Ubah hanya lapisan tampilan (1 commit per layar), (4) Verifikasi dengan bukti tes & screenshot sesudahnya, (5) Tampilkan perbandingan sebelum/sesudah lalu STOP & tunggu konfirmasi 'lanjut' sebelum ke layar berikutnya.
