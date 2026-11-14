"""
Just Press Download (JPD) - Internationalization & Dual-Language Engine (ID & EN)
"""

from typing import Optional
from idm_gui.settings import settings


STRINGS = {
    "id": {
        "app_name": "Just Press Download",
        "nav_title": "NAVIGASI",
        "sec_library": "PUSTAKA",
        "sec_categories": "KATEGORI BERKAS",
        "sec_storage": "PENYIMPANAN",
        "nav_all": "Semua Unduhan",
        "nav_downloading": "Sedang Mengunduh",
        "nav_finished": "Selesai",
        "cat_video": "Video",
        "cat_music": "Musik",
        "cat_pictures": "Gambar",
        "cat_programs": "Program",
        "cat_documents": "Dokumen",
        "cat_compressed": "Terkompresi",
        "cat_general": "Umum",
        # Toolbar
        "tb_add_url": "Tambah URL",
        "tb_resume": "Lanjutkan",
        "tb_pause": "Jeda",
        "tb_delete": "Hapus",
        "tb_stop": "Hentikan",
        "tb_clear": "Bersihkan",
        "tb_open_folder": "Buka Folder",
        "tb_settings": "Pengaturan",
        "tb_more": "Lainnya",
        "tb_search_placeholder": "Cari unduhan...",
        "tip_add": "Tambah URL Baru (Ctrl+N)",
        "tip_resume": "Lanjutkan Unduhan Terpilih",
        "tip_pause": "Jeda Unduhan Terpilih",
        "tip_delete": "Hapus Unduhan Terpilih (Del)",
        "tip_stop": "Hentikan Semua Unduhan",
        "tip_clear": "Bersihkan Seluruh Unduhan Selesai",
        "tip_folder": "Buka Folder Berkas Terpilih",
        "tip_settings": "Opsi Konfigurasi Just Press Download",
        # Metrics
        "stat_speed": "⚡ KECEPATAN AKTIF",
        "stat_active": "⏳ TUGAS BERJALAN",
        "stat_files": "💾 TOTAL BERKAS",
        "stat_running_queued": "{running} Berjalan • {queued} Mengantri",
        "stat_files_summary": "{count} Berkas ({size})",
        # Table
        "col_name": "Nama Berkas",
        "col_size": "Ukuran",
        "col_status": "Status",
        "col_progress": "Progres",
        "col_speed": "Kecepatan",
        "col_url": "URL Unduhan",
        # Context Menu
        "ctx_resume": "▶ Lanjutkan Unduh",
        "ctx_pause": "⏸ Jeda Unduh",
        "ctx_open_file": "📂 Buka Berkas",
        "ctx_open_folder": "📁 Buka Folder Penyimpanan",
        "ctx_copy_url": "📋 Salin URL Unduhan",
        "ctx_delete_list": "🗑 Hapus dari Daftar",
        "ctx_delete_file": "❌ Hapus Berkas dari Komputer",
        # Statuses
        "status_downloading": "⚡ Mengunduh",
        "status_completed": "✓ Selesai",
        "status_paused": "⏸ Dijeda",
        "status_failed": "✕ Gagal",
        "status_queued": "⏳ Mengantri",
        "status_merging": "⚙ Menggabungkan",
        # Empty state
        "empty_title": "Belum Ada Unduhan",
        "empty_desc": "Salin tautan dari peramban atau klik tombol di bawah untuk memulai unduhan baru.",
        "empty_btn": "+ Tambah Unduhan Baru",
        # Menus
        "menu_tasks": "Tugas",
        "menu_add_url": "Tambah URL Baru...",
        "menu_export": "Ekspor ke berkas teks...",
        "menu_import": "Impor dari berkas teks...",
        "menu_exit": "Keluar",
        "menu_file": "Berkas",
        "menu_pause": "Jeda Unduh",
        "menu_resume": "Lanjutkan Unduh",
        "menu_delete": "Hapus Unduhan",
        "menu_open_file": "Buka Berkas",
        "menu_open_folder": "Buka Folder Penyimpanan",
        "menu_downloads": "Unduhan",
        "menu_resume_all": "Lanjutkan Semua",
        "menu_pause_all": "Jeda Semua",
        "menu_stop_all": "Hentikan Semua",
        "menu_delete_completed": "Hapus Semua Yang Selesai",
        "menu_options": "⚙ Opsi / Pengaturan...",
        "menu_view": "Lihat",
        "menu_toggle_sidebar": "Sembunyikan/Tampilkan Kategori",
        "menu_arrange": "Atur Berkas",
        "sort_name": "Berdasarkan Nama Berkas",
        "sort_size": "Berdasarkan Ukuran",
        "sort_status": "Berdasarkan Status",
        "sort_speed": "Berdasarkan Kecepatan",
        "menu_language": "Bahasa (Language)",
        "menu_help": "Bantuan",
        "menu_tip": "Tip Hari Ini...",
        "menu_updates": "Periksa Pembaruan...",
        "menu_about": "Tentang Just Press Download",
        "statusbar_ready": "⚡ Siap (IPC Server Port 19900 Aktif)",
        "statusbar_summary": "Total: {total} unduhan | Aktif: {active} | Total Kecepatan: {speed}",
        # Dialogs
        "dlg_info_title": "Info Unduh Berkas",
        "dlg_info_url": "URL:",
        "dlg_info_category": "Kategori:",
        "dlg_info_save_as": "Simpan Sebagai:",
        "dlg_info_remember": "Ingat jalur ini untuk kategori '{cat}'",
        "dlg_info_desc": "Deskripsi:",
        "dlg_info_accel_stream": "⚡ Akselerasi: Mode Ekstraksi Stream Video Cepat (yt-dlp High Speed)",
        "dlg_info_accel_parallel": "⚡ Akselerasi: {conns} Koneksi Paralel HTTP Range",
        "dlg_info_probing": "Memeriksa ukuran...",
        "dlg_info_download_later": "Unduh Nanti",
        "dlg_info_start_download": "Mulai Unduh",
        "dlg_info_cancel": "Batal",
        # Options Dialog
        "dlg_opts_title": "Opsi Konfigurasi Just Press Download",
        "tab_general": "Umum",
        "tab_file_types": "Jenis Berkas",
        "tab_save_to": "Simpan ke",
        "tab_connection": "Koneksi",
        "lbl_language": "Bahasa / Language:",
        "lbl_browser_integration": "Integrasi Peramban Lanjutan (Browser Integration):",
        "chk_autorun": "Jalankan Just Press Download saat Windows dinyalakan",
        "chk_close_tray": "Tutup jendela ke System Tray (Close with minimize)",
        "chk_start_minimized": "Mulai aplikasi dalam keadaan terminimalisasi di Tray",
        "chk_sound": "Mainkan suara notifikasi saat unduhan selesai",
        "chk_confirm_delete": "Tampilkan konfirmasi sebelum menghapus tugas unduhan",
        "chk_autoclose_progress": "Tutup otomatis jendela progres saat unduhan 100% selesai",
        "chk_clipboard": "Pantau clipboard untuk tautan unduhan otomatis",
        "btn_save": "Simpan",
        "btn_cancel": "Batal",
        "complete_title": "Unduhan Selesai",
        "complete_header": "Unduhan Berhasil Selesai!",
        "complete_open_file": "Buka Berkas",
        "complete_open_folder": "Buka Folder",
        "complete_done": "Selesai",
        # Add URL Dialog
        "dlg_add_title": "Masukkan URL untuk Mengunduh",
        "dlg_add_url_lbl": "Alamat Tautan (URL):",
        "dlg_add_err_format": "* Format URL harus diawali dengan http:// atau https://",
        "dlg_add_err_empty": "* Masukkan tautan unduhan terlebih dahulu",
        "dlg_add_btn_download": "+ Unduh",
        "dlg_add_btn_cancel": "Batal",
        # Confirmation & Messages
        "confirm_delete_title": "Konfirmasi Hapus Unduhan",
        "confirm_delete_msg": "Apakah Anda yakin ingin menghapus {count} unduhan yang dipilih?",
        "confirm_delete_single": "Apakah Anda yakin ingin menghapus unduhan yang dipilih?",
        "confirm_delete_file_title": "Konfirmasi Hapus Berkas",
        "confirm_delete_file_msg": "Apakah Anda yakin ingin menghapus berkas '{fname}' secara permanen dari komputer Anda?",
        "delete_error_title": "Gagal Menghapus",
        "delete_error_msg": "Tidak dapat menghapus berkas: {err}",
        "export_dialog_title": "Ekspor Daftar Tautan Unduhan",
        "import_dialog_title": "Impor Daftar Tautan Unduhan",
        # Options Dialog extra
        "opt_ipc_port": "⚡ Port IPC Loopback: 127.0.0.1:19900 (Aktif & Siap)",
        "opt_exts_lbl": "Otomatis mulai unduh berkas dengan ekstensi berikut:",
        "opt_exceptions_lbl": "Jangan mulai unduh otomatis dari situs berikut (Pengecualian):",
        "opt_exceptions_hint": "Ketik domain dipisahkan spasi (contoh: *.speedtest.net *.fast.com)",
        "opt_cat_folders_lbl": "Folder Penyimpanan per Kategori:",
        "opt_select_cat": "Pilih Kategori:",
        "opt_save_folder": "Folder Simpan:",
        "opt_temp_dir_lbl": "Direktori Berkas Sementara (Temporary Directory):",
        "opt_conn_type_lbl": "Tipe / Kecepatan Sambungan:",
        "opt_conn_max_lbl": "Maks. Jumlah Koneksi (Parallel Connections):",
        "opt_conn_channels": "jalur (32 = Kecepatan Maksimum IDM)",
        "opt_conn_note": "* Just Press Download menggunakan akselerasi multi-koneksi paralel bertahap (kelipatan 8)",
        # Progress Dialog extra
        "prog_tab_status": "Status unduhan",
        "prog_tab_limiter": "Pembatas Kecepatan",
        "prog_tab_options": "Opsi saat selesai",
        "prog_url": "URL Unduhan:",
        "prog_status": "Status:",
        "prog_receiving": "Menerima data...",
        "prog_file_size": "Ukuran berkas:",
        "prog_downloaded": "Diunduh:",
        "prog_transfer_rate": "Tingkat transfer:",
        "prog_time_left": "Waktu tersisa:",
        "prog_calculating": "Menghitung...",
        "prog_resume_cap": "Kemampuan resume:",
        "prog_yes": "Ya",
        "prog_no": "Tidak",
        "prog_hide_details": "<< Sembunyikan detail",
        "prog_show_details": ">> Tampilkan detail",
        "prog_seg_progress": "Progres posisi mulai dan unduh berdasarkan koneksi:",
        "prog_col_conn": "Koneksi",
        "prog_col_dl": "Diunduh",
        "prog_col_status": "Status",
        "prog_limiter_enable": "Aktifkan Pembatas Kecepatan untuk Unduhan Ini",
        "prog_limiter_max": "Batas Kecepatan Maksimum:",
        "prog_limiter_presets": "Pilih Preset Cepat:",
        "prog_limiter_status_on": "Status: Pembatas Kecepatan Aktif ({rate} KB/s)",
        "prog_limiter_status_off": "Status: Pembatas Kecepatan Dinonaktifkan (Kecepatan Penuh)",
        "prog_auto_actions": "Tindakan Otomatis Pasca-Unduh:",
        "prog_auto_close": "Tutup jendela dialog progres ini saat pengunduhan selesai",
        "prog_disconnect": "Gantung saluran / Putuskan koneksi internet saat selesai",
        "prog_shutdown": "Matikan komputer secara otomatis setelah unduhan selesai",
        "prog_force_shutdown": "Paksa proses sistem untuk segera mati",
        # Dialog info extra
        "dlg_info_tip_add_cat": "Tambah Kategori Baru...",
        "dlg_info_add_cat_title": "Tambah Kategori Baru",
        "dlg_info_add_cat_prompt": "Masukkan nama kategori baru:",
        "dlg_info_tip_browse": "Pilih Folder Penyimpanan...",
        "dlg_info_browse_title": "Pilih Folder Penyimpanan untuk Kategori",
        # Progress extra
        "prog_unit_kbs": "KB/detik",
        "prog_sec_unit": "detik",
        "prog_note_safe_shutdown": "* Catatan: Aksi penutupan atau shutdown aman hanya akan dieksekusi setelah seluruh bagian berkas diverifikasi utuh.",
        # Options extra
        "opt_browse_cat_title": "Pilih Folder untuk Kategori",
        "opt_browse_temp_title": "Pilih Folder Sementara",
        "opt_conn_types": [
            "Kecepatan Tinggi: Sambungan Langsung (Ethernet/Kabel) / Wi-Fi / 4G",
            "Kecepatan Sedang: 3G / ADSL",
            "Kecepatan Rendah: Dial Up / VPN",
        ],
        # System Tray & Popups
        "tray_open": "Buka Just Press Download",
        "tray_add_url": "Tambah URL Baru...",
        "tray_resume_all": "Lanjutkan Semua Unduhan",
        "tray_pause_all": "Jeda Semua Unduhan",
        "tray_options": "Pengaturan (Opsi)...",
        "tray_exit": "Keluar (Exit)",
        "tray_notify_complete": "Unduhan Selesai: {fname}",
        "tray_notify_minimized": "Aplikasi diminimalkan ke System Tray",
        # Menu Dialogs
        "tip_dialog_title": "Tip Hari Ini - Just Press Download",
        "tip_dialog_body": "💡 Tip Cepat:\n\n1. Anda dapat menyalin tautan berkas di browser, dan Just Press Download otomatis menangkapnya.\n2. Gunakan tombol '⚙ Opsi' di menu atas untuk mengubah jumlah koneksi paralel hingga 32 jalur.\n3. Klik dua kali baris unduhan untuk langsung membuka berkas yang telah selesai diunduh.",
        "update_dialog_title": "Periksa Pembaruan - Just Press Download",
        "update_dialog_body": "✔ Anda telah menggunakan versi terbaru Just Press Download (v1.1.0 High-Performance Release)!\n\nSemua komponen sistem mutakhir dan terintegrasi.",
        "about_dialog_title": "Tentang Just Press Download",
        "about_dialog_body": "Just Press Download\nHigh-Performance Parallel Download Accelerator\nDikembangkan dengan Python, Tkinter, dan TDD.\nFitur: Akselerasi Range Paralel, Stream Video Muxer, Integrasi Peramban Native.",
        # Security warnings
        "sec_warn_double_ext": "Peringatan: Berkas memiliki ekstensi ganda (.{penultimate_ext}.{last_ext}) yang umum digunakan adware/malware!",
        "sec_warn_risky_ext": "Peringatan: Berkas berekstensi .{ext} merupakan skrip berisiko tinggi!",
        "status_unknown": "Tidak diketahui",
    },
    "en": {
        "app_name": "Just Press Download",
        "nav_title": "NAVIGATION",
        "sec_library": "LIBRARY",
        "sec_categories": "FILE CATEGORIES",
        "sec_storage": "STORAGE",
        "nav_all": "All Downloads",
        "nav_downloading": "Downloading",
        "nav_finished": "Finished",
        "cat_video": "Video",
        "cat_music": "Music",
        "cat_pictures": "Pictures",
        "cat_programs": "Programs",
        "cat_documents": "Documents",
        "cat_compressed": "Compressed",
        "cat_general": "General",
        # Toolbar
        "tb_add_url": "Add URL",
        "tb_resume": "Resume",
        "tb_pause": "Pause",
        "tb_delete": "Delete",
        "tb_stop": "Stop",
        "tb_clear": "Clear",
        "tb_open_folder": "Open Folder",
        "tb_settings": "Settings",
        "tb_more": "More",
        "tb_search_placeholder": "Search downloads...",
        "tip_add": "Add New URL (Ctrl+N)",
        "tip_resume": "Resume Selected Download",
        "tip_pause": "Pause Selected Download",
        "tip_delete": "Delete Selected Download (Del)",
        "tip_stop": "Stop All Downloads",
        "tip_clear": "Clear All Completed Downloads",
        "tip_folder": "Open Selected File Folder",
        "tip_settings": "Just Press Download Configuration Options",
        # Metrics
        "stat_speed": "⚡ ACTIVE SPEED",
        "stat_active": "⏳ ACTIVE TASKS",
        "stat_files": "💾 TOTAL FILES",
        "stat_running_queued": "{running} Running • {queued} Queued",
        "stat_files_summary": "{count} Files ({size})",
        # Table
        "col_name": "File Name",
        "col_size": "Size",
        "col_status": "Status",
        "col_progress": "Progress",
        "col_speed": "Speed",
        "col_url": "Download URL",
        # Context Menu
        "ctx_resume": "▶ Resume Download",
        "ctx_pause": "⏸ Pause Download",
        "ctx_open_file": "📂 Open File",
        "ctx_open_folder": "📁 Open Destination Folder",
        "ctx_copy_url": "📋 Copy Download URL",
        "ctx_delete_list": "🗑 Remove from List",
        "ctx_delete_file": "❌ Delete File from Disk",
        # Statuses
        "status_downloading": "⚡ Downloading",
        "status_completed": "✓ Completed",
        "status_paused": "⏸ Paused",
        "status_failed": "✕ Failed",
        "status_queued": "⏳ Queued",
        "status_merging": "⚙ Merging",
        # Empty state
        "empty_title": "No Downloads Yet",
        "empty_desc": "Copy a link from your browser or click the button below to start a new download.",
        "empty_btn": "+ Add New Download",
        # Menus
        "menu_tasks": "Tasks",
        "menu_add_url": "Add New URL...",
        "menu_export": "Export to text file...",
        "menu_import": "Import from text file...",
        "menu_exit": "Exit",
        "menu_file": "File",
        "menu_pause": "Pause Download",
        "menu_resume": "Resume Download",
        "menu_delete": "Delete Download",
        "menu_open_file": "Open File",
        "menu_open_folder": "Open Destination Folder",
        "menu_downloads": "Downloads",
        "menu_resume_all": "Resume All",
        "menu_pause_all": "Pause All",
        "menu_stop_all": "Stop All",
        "menu_delete_completed": "Clear All Completed",
        "menu_options": "⚙ Options / Settings...",
        "menu_view": "View",
        "menu_toggle_sidebar": "Show/Hide Categories",
        "menu_arrange": "Sort Files",
        "sort_name": "By File Name",
        "sort_size": "By Size",
        "sort_status": "By Status",
        "sort_speed": "By Speed",
        "menu_language": "Language (Bahasa)",
        "menu_help": "Help",
        "menu_tip": "Tip of the Day...",
        "menu_updates": "Check for Updates...",
        "menu_about": "About Just Press Download",
        "statusbar_ready": "⚡ Ready (IPC Server Port 19900 Active)",
        "statusbar_summary": "Total: {total} downloads | Active: {active} | Total Speed: {speed}",
        # Dialogs
        "dlg_info_title": "Download File Info",
        "dlg_info_url": "URL:",
        "dlg_info_category": "Category:",
        "dlg_info_save_as": "Save As:",
        "dlg_info_remember": "Remember this path for category '{cat}'",
        "dlg_info_desc": "Description:",
        "dlg_info_accel_stream": "⚡ Acceleration: Fast Video Stream Extraction (yt-dlp High Speed)",
        "dlg_info_accel_parallel": "⚡ Acceleration: {conns} Parallel HTTP Range Connections",
        "dlg_info_probing": "Checking file size...",
        "dlg_info_download_later": "Download Later",
        "dlg_info_start_download": "Start Download",
        "dlg_info_cancel": "Cancel",
        # Options Dialog
        "dlg_opts_title": "Just Press Download Configuration Options",
        "tab_general": "General",
        "tab_file_types": "File Types",
        "tab_save_to": "Save To",
        "tab_connection": "Connection",
        "lbl_language": "Language / Bahasa:",
        "lbl_browser_integration": "Advanced Browser Integration:",
        "chk_autorun": "Launch Just Press Download on Windows startup",
        "chk_close_tray": "Close window to System Tray (Close with minimize)",
        "chk_start_minimized": "Start application minimized to System Tray",
        "chk_sound": "Play notification sound when download completes",
        "chk_confirm_delete": "Show confirmation before deleting download tasks",
        "chk_autoclose_progress": "Automatically close progress window on 100% completion",
        "chk_clipboard": "Monitor clipboard for automatic download links",
        "btn_save": "Save",
        "btn_cancel": "Cancel",
        "complete_title": "Download Completed",
        "complete_header": "Download Successfully Completed!",
        "complete_open_file": "Open File",
        "complete_open_folder": "Open Folder",
        "complete_done": "Done",
        # Add URL Dialog
        "dlg_add_title": "Enter URL to Download",
        "dlg_add_url_lbl": "URL Address:",
        "dlg_add_err_format": "* URL must begin with http:// or https://",
        "dlg_add_err_empty": "* Please enter a download link first",
        "dlg_add_btn_download": "+ Download",
        "dlg_add_btn_cancel": "Cancel",
        # Confirmation & Messages
        "confirm_delete_title": "Confirm Delete Download",
        "confirm_delete_msg": "Are you sure you want to delete {count} selected downloads?",
        "confirm_delete_single": "Are you sure you want to delete the selected download?",
        "confirm_delete_file_title": "Confirm Delete File",
        "confirm_delete_file_msg": "Are you sure you want to permanently delete '{fname}' from your computer?",
        "delete_error_title": "Deletion Failed",
        "delete_error_msg": "Could not delete file: {err}",
        "export_dialog_title": "Export Download Links List",
        "import_dialog_title": "Import Download Links List",
        # Options Dialog extra
        "opt_ipc_port": "⚡ IPC Loopback Port: 127.0.0.1:19900 (Active & Ready)",
        "opt_exts_lbl": "Automatically start downloading files with the following extensions:",
        "opt_exceptions_lbl": "Do not start downloading automatically from the following sites (Exceptions):",
        "opt_exceptions_hint": "Type domains separated by space (example: *.speedtest.net *.fast.com)",
        "opt_cat_folders_lbl": "Save Folders per Category:",
        "opt_select_cat": "Select Category:",
        "opt_save_folder": "Save Folder:",
        "opt_temp_dir_lbl": "Temporary Directory:",
        "opt_conn_type_lbl": "Connection Type / Speed:",
        "opt_conn_max_lbl": "Max. Parallel Connections:",
        "opt_conn_channels": "lines (32 = IDM Maximum Speed)",
        "opt_conn_note": "* Just Press Download utilizes staged parallel multi-connections (multiples of 8)",
        # Progress Dialog extra
        "prog_tab_status": "Download status",
        "prog_tab_limiter": "Speed Limiter",
        "prog_tab_options": "Completion Options",
        "prog_url": "Download URL:",
        "prog_status": "Status:",
        "prog_receiving": "Receiving data...",
        "prog_file_size": "File size:",
        "prog_downloaded": "Downloaded:",
        "prog_transfer_rate": "Transfer rate:",
        "prog_time_left": "Time left:",
        "prog_calculating": "Calculating...",
        "prog_resume_cap": "Resume capability:",
        "prog_yes": "Yes",
        "prog_no": "No",
        "prog_hide_details": "<< Hide details",
        "prog_show_details": ">> Show details",
        "prog_seg_progress": "Download progress by connection:",
        "prog_col_conn": "Connection",
        "prog_col_dl": "Downloaded",
        "prog_col_status": "Status",
        "prog_limiter_enable": "Enable Speed Limiter for This Download",
        "prog_limiter_max": "Maximum Speed Limit:",
        "prog_limiter_presets": "Quick Presets:",
        "prog_limiter_status_on": "Status: Speed limiter active ({rate} KB/s)",
        "prog_limiter_status_off": "Status: Speed limiter disabled (Full speed)",
        "prog_auto_actions": "Automatic Post-Download Actions:",
        "prog_auto_close": "Close this dialog when download finishes",
        "prog_disconnect": "Disconnect internet connection when done",
        "prog_shutdown": "Shut down computer when done",
        "prog_force_shutdown": "Force processes to close",
        # Dialog info extra
        "dlg_info_tip_add_cat": "Add New Category...",
        "dlg_info_add_cat_title": "Add New Category",
        "dlg_info_add_cat_prompt": "Enter new category name:",
        "dlg_info_tip_browse": "Select Save Folder...",
        "dlg_info_browse_title": "Select Save Folder for Category",
        # Progress extra
        "prog_unit_kbs": "KB/s",
        "prog_sec_unit": "sec",
        "prog_note_safe_shutdown": "* Note: Safe close or shutdown will only be executed after all file parts are verified intact.",
        # Options extra
        "opt_browse_cat_title": "Select Folder for Category",
        "opt_browse_temp_title": "Select Temporary Folder",
        "opt_conn_types": [
            "High Speed: Direct Connection (Ethernet/Cable) / Wi-Fi / 4G",
            "Medium Speed: 3G / ADSL",
            "Low Speed: Dial Up / VPN",
        ],
        # System Tray & Popups
        "tray_open": "Open Just Press Download",
        "tray_add_url": "Add New URL...",
        "tray_resume_all": "Resume All Downloads",
        "tray_pause_all": "Pause All Downloads",
        "tray_options": "Options / Settings...",
        "tray_exit": "Exit",
        "tray_notify_complete": "Download Completed: {fname}",
        "tray_notify_minimized": "Application minimized to System Tray",
        # Menu Dialogs
        "tip_dialog_title": "Tip of the Day - Just Press Download",
        "tip_dialog_body": "💡 Quick Tips:\n\n1. You can copy a download link in your browser, and Just Press Download will automatically capture it.\n2. Use the '⚙ Options' button to configure up to 32 parallel connections.\n3. Double-click any completed download row to immediately open the file.",
        "update_dialog_title": "Check for Updates - Just Press Download",
        "update_dialog_body": "✔ You are using the latest version of Just Press Download (v1.1.0 High-Performance Release)!\n\nAll system components are up to date.",
        "about_dialog_title": "About Just Press Download",
        "about_dialog_body": "Just Press Download\nHigh-Performance Parallel Download Accelerator\nDeveloped with Python, Tkinter, and TDD.\nFeatures: Parallel Range Download, Streaming Muxer, Browser Native Host.",
        # Security warnings
        "sec_warn_double_ext": "Warning: File has a double extension (.{penultimate_ext}.{last_ext}) commonly used by adware/malware!",
        "sec_warn_risky_ext": "Warning: File with .{ext} extension is a high-risk executable/script!",
        "status_unknown": "Unknown",
    }
}


CATEGORY_KEYS = [
    "Video",
    "Musik",
    "Gambar",
    "Program",
    "Dokumen",
    "Berkas Terkompresi",
    "Umum",
]

CATEGORY_TR_KEYS = {
    "Video": "cat_video",
    "Musik": "cat_music",
    "Gambar": "cat_pictures",
    "Program": "cat_programs",
    "Dokumen": "cat_documents",
    "Berkas Terkompresi": "cat_compressed",
    "Umum": "cat_general",
}


def get_category_display_name(cat_key: str, lang: Optional[str] = None) -> str:
    """Returns the localized display name for a given canonical category key."""
    l = lang or get_current_lang()
    tr_k = CATEGORY_TR_KEYS.get(cat_key)
    if tr_k:
        return tr(tr_k, lang=l)
    return cat_key


def get_canonical_category_key(name: str) -> str:
    """Normalizes an English or Indonesian category name back to the internal canonical key."""
    n = name.strip().lower()
    if n in ("video",):
        return "Video"
    elif n in ("musik", "music", "audio"):
        return "Musik"
    elif n in ("gambar", "pictures", "picture", "images", "image", "foto", "photo"):
        return "Gambar"
    elif n in ("program", "programs"):
        return "Program"
    elif n in ("dokumen", "documents", "document"):
        return "Dokumen"
    elif n in ("berkas terkompresi", "terkompresi", "compressed", "archive", "zip"):
        return "Berkas Terkompresi"
    elif n in ("umum", "general"):
        return "Umum"
    return name


def format_size_id(num_bytes: int, lang: Optional[str] = None) -> str:
    """Formats bytes in localized style (ID: 337,84 MB, Tidak diketahui; EN: 337.84 MB, Unknown)."""
    l = lang or get_current_lang()
    if num_bytes <= 0:
        return "Tidak diketahui" if l == "id" else "Unknown"
    elif num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 * 1024:
        val = num_bytes / 1024
        s = f"{val:.2f} KB"
        return s.replace(".", ",") if l == "id" else s
    elif num_bytes < 1024 * 1024 * 1024:
        val = num_bytes / (1024 * 1024)
        s = f"{val:.2f} MB"
        return s.replace(".", ",") if l == "id" else s
    else:
        val = num_bytes / (1024 * 1024 * 1024)
        s = f"{val:.2f} GB"
        return s.replace(".", ",") if l == "id" else s


def format_time_left(seconds: float, lang: Optional[str] = None) -> str:
    """Formats remaining time in localized style (ID: 13 menit 58 detik; EN: 13 min 58 sec)."""
    l = lang or get_current_lang()
    if seconds <= 0:
        return "Selesai" if l == "id" else "Complete"
    s = int(seconds)
    if l == "en":
        if s < 60:
            return f"{s} sec"
        elif s < 3600:
            m = s // 60
            rem_s = s % 60
            return f"{m} min {rem_s} sec" if rem_s > 0 else f"{m} min"
        else:
            h = s // 3600
            rem_m = (s % 3600) // 60
            return f"{h} hr {rem_m} min" if rem_m > 0 else f"{h} hr"
    else:
        if s < 60:
            return f"{s} detik"
        elif s < 3600:
            m = s // 60
            rem_s = s % 60
            return f"{m} menit {rem_s} detik" if rem_s > 0 else f"{m} menit"
        else:
            h = s // 3600
            rem_m = (s % 3600) // 60
            return f"{h} jam {rem_m} menit" if rem_m > 0 else f"{h} jam"


def get_current_lang() -> str:
    try:
        return settings.get_language()
    except Exception:
        return "id"


def tr(key: str, lang: Optional[str] = None, **kwargs) -> str:
    """Translates a key into the active language, with optional format string kwargs."""
    l = lang or get_current_lang()
    table = STRINGS.get(l, STRINGS["id"])
    val = table.get(key, STRINGS["id"].get(key, key))
    if kwargs:
        try:
            return val.format(**kwargs)
        except Exception:
            return val
    return val
