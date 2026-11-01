"""JustPressDownload (JPD) - Browser Integration & Native Messaging Registrant."""

import os
import json
import winreg


def update_manifest_target_path(manifest_path: str, target_binary: str):
    """Updates the binary path inside the manifest to an absolute verified path."""
    abs_manifest = os.path.abspath(manifest_path)
    if not os.path.exists(abs_manifest):
        return
    try:
        with open(abs_manifest, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["path"] = os.path.abspath(target_binary)
        with open(abs_manifest, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"[-] Gagal memperbarui target path di {abs_manifest}: {e}")


def register_host(browser: str, host_name: str, manifest_path: str):
    """Registers the native messaging host manifest in Windows Registry."""
    abs_manifest = os.path.abspath(manifest_path)
    if not os.path.exists(abs_manifest):
        print(f"[-] Error: Berkas manifest tidak ditemukan di {abs_manifest}")
        return False

    key_templates = {
        "chrome": rf"Software\Google\Chrome\NativeMessagingHosts\{host_name}",
        "edge": rf"Software\Microsoft\Edge\NativeMessagingHosts\{host_name}",
        "brave": rf"Software\BraveSoftware\Brave-Browser\NativeMessagingHosts\{host_name}",
        "firefox": rf"Software\Mozilla\NativeMessagingHosts\{host_name}",
    }

    sub_key = key_templates.get(browser.lower())
    if not sub_key:
        print(f"[-] Browser tidak dikenali: {browser}")
        return False

    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, abs_manifest)
        print(f"[✔] Berhasil mendaftarkan host untuk {browser.capitalize()}:")
        print(f"    HKCU\\{sub_key} -> {abs_manifest}")
        return True
    except Exception as e:
        print(f"[-] Gagal mendaftarkan registry untuk {browser}: {e}")
        return False


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exe_path = os.path.join(base_dir, "JustPressDownload.exe")
    if not os.path.exists(exe_path):
        exe_path = os.path.join(base_dir, "run_gui.bat")

    manifests = [
        os.path.join(base_dir, "manifests", "com.justpressdownload.host.json"),
        os.path.join(base_dir, "manifests", "com.justpressdownload.host.moz.json"),
        os.path.join(base_dir, "manifests", "com.idmclone.host.json"),
        os.path.join(base_dir, "manifests", "com.idmclone.host.moz.json"),
    ]

    print("==================================================================")
    print("  JustPressDownload (JPD) - Registrasi Integrasi Browser Otomatis")
    print("==================================================================")
    print(f"Target Binary: {exe_path}")

    for m in manifests:
        if os.path.exists(m):
            update_manifest_target_path(m, exe_path)

    # Register hosts
    for browser in ["chrome", "edge", "brave"]:
        register_host(browser, "com.justpressdownload.host", os.path.join(base_dir, "manifests", "com.justpressdownload.host.json"))
        register_host(browser, "com.idmclone.host", os.path.join(base_dir, "manifests", "com.idmclone.host.json"))

    register_host("firefox", "com.justpressdownload.host", os.path.join(base_dir, "manifests", "com.justpressdownload.host.moz.json"))
    register_host("firefox", "com.idmclone.host", os.path.join(base_dir, "manifests", "com.idmclone.host.moz.json"))

    ext_dir = os.path.join(base_dir, "extension")
    print("\n==================================================================")
    print("  CARA MEMASANG EKSTENSI KE CHROME / EDGE / BRAVE:")
    print("==================================================================")
    print("1. Buka browser Anda dan kunjungi halaman ekstensi:")
    print("   - Chrome : chrome://extensions")
    print("   - Edge   : edge://extensions")
    print("   - Brave  : brave://extensions")
    print("2. Aktifkan toggle 'Developer mode' (Mode Pengembang) di kanan atas.")
    print("3. Klik tombol 'Load unpacked' (Muat yang belum dibongkar).")
    print("4. Pilih folder ekstensi berikut:")
    print(f"   --> {ext_dir}")
    print("\n[✔] Selesai! Ekstensi JustPressDownload (JPD) langsung aktif & siap!")
    print("==================================================================")


if __name__ == "__main__":
    main()
