"""
Just Press Download (JPD) - Internationalization & Dual-Language Engine (ID & EN)
"""

from typing import Optional
from idm_gui.settings import settings


STRINGS = {
    "id": {
        "app_name": "Just Press Download (JPD)",
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
        "tb_add_url": "+ Tambah URL",
        "tb_resume": "▷ Lanjutkan",
        "tb_pause": "❚❚ Jeda",
        "tb_delete": "✕ Hapus",
        "tb_stop": "■ Hentikan",
        "tb_clear": "✓ Bersihkan",
        "tb_open_folder": "↗ Buka Folder",
        "tb_settings": "⋯ Pengaturan",
        "tb_search_placeholder": "Cari unduhan...",
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
        "menu_file": "Berkas",
        "menu_add_url": "Tambah URL Baru...",
        "menu_exit": "Keluar",
        "menu_downloads": "Unduhan",
        "menu_resume_all": "Lanjutkan Semua",
        "menu_pause_all": "Jeda Semua",
        "menu_stop_all": "Hentikan Semua",
        "menu_view": "Tampilan",
        "menu_toggle_sidebar": "Sembunyikan/Tampilkan Kategori",
        "menu_language": "Bahasa (Language)",
        "menu_help": "Bantuan",
        "menu_about": "Tentang Just Press Download",
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
        "dlg_opts_title": "Opsi Konfigurasi Just Press Download (JPD)",
        "tab_general": "Umum",
        "tab_file_types": "Jenis Berkas",
        "tab_save_to": "Simpan ke",
        "tab_connection": "Koneksi",
        "lbl_language": "Bahasa / Language:",
        "lbl_browser_integration": "Integrasi Peramban Lanjutan (Browser Integration):",
        "chk_autorun": "Jalankan Just Press Download (JPD) saat Windows dinyalakan",
        "chk_close_tray": "Tutup jendela ke System Tray (Close with minimize)",
        "chk_start_minimized": "Mulai aplikasi dalam keadaan terminimalisasi di Tray",
        "chk_sound": "Mainkan suara notifikasi saat unduhan selesai",
        "chk_confirm_delete": "Tampilkan konfirmasi sebelum menghapus tugas unduhan",
        "chk_autoclose_progress": "Tutup otomatis jendela progres saat unduhan 100% selesai",
        "chk_clipboard": "Pantau clipboard untuk tautan unduhan otomatis",
        "btn_save": "Simpan",
        "btn_cancel": "Batal",
    },
    "en": {
        "app_name": "Just Press Download (JPD)",
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
        "tb_add_url": "+ Add URL",
        "tb_resume": "▷ Resume",
        "tb_pause": "❚❚ Pause",
        "tb_delete": "✕ Delete",
        "tb_stop": "■ Stop",
        "tb_clear": "✓ Clear",
        "tb_open_folder": "↗ Open Folder",
        "tb_settings": "⋯ Settings",
        "tb_search_placeholder": "Search downloads...",
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
        "menu_file": "File",
        "menu_add_url": "Add New URL...",
        "menu_exit": "Exit",
        "menu_downloads": "Downloads",
        "menu_resume_all": "Resume All",
        "menu_pause_all": "Pause All",
        "menu_stop_all": "Stop All",
        "menu_view": "View",
        "menu_toggle_sidebar": "Show/Hide Categories",
        "menu_language": "Language (Bahasa)",
        "menu_help": "Help",
        "menu_about": "About Just Press Download",
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
        "dlg_opts_title": "Just Press Download (JPD) Configuration Options",
        "tab_general": "General",
        "tab_file_types": "File Types",
        "tab_save_to": "Save To",
        "tab_connection": "Connection",
        "lbl_language": "Language / Bahasa:",
        "lbl_browser_integration": "Advanced Browser Integration:",
        "chk_autorun": "Launch Just Press Download (JPD) on Windows startup",
        "chk_close_tray": "Close window to System Tray (Close with minimize)",
        "chk_start_minimized": "Start application minimized to System Tray",
        "chk_sound": "Play notification sound when download completes",
        "chk_confirm_delete": "Show confirmation before deleting download tasks",
        "chk_autoclose_progress": "Automatically close progress window on 100% completion",
        "chk_clipboard": "Monitor clipboard for automatic download links",
        "btn_save": "Save",
        "btn_cancel": "Cancel",
    }
}


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
