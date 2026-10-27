import os
import sys
import winreg


def register_host(browser: str, manifest_path: str):
    abs_manifest = os.path.abspath(manifest_path)
    if not os.path.exists(abs_manifest):
        print(f"Error: Manifest not found at {abs_manifest}")
        return

    key_paths = {
        "chrome": r"Software\Google\Chrome\NativeMessagingHosts\com.idmclone.host",
        "edge": r"Software\Microsoft\Edge\NativeMessagingHosts\com.idmclone.host",
        "firefox": r"Software\Mozilla\NativeMessagingHosts\com.idmclone.host",
    }

    sub_key = key_paths.get(browser.lower())
    if not sub_key:
        print(f"Unknown browser: {browser}. Supported: chrome, edge, firefox")
        return

    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, abs_manifest)
        print(f"[+] Successfully registered Native Messaging host for {browser.capitalize()} at:")
        print(f"    HKCU\\{sub_key} -> {abs_manifest}")
    except Exception as e:
        print(f"[-] Registry registration failed: {e}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    chrome_manifest = os.path.join(base_dir, "manifests", "com.idmclone.host.json")
    firefox_manifest = os.path.join(base_dir, "manifests", "com.idmclone.host.moz.json")

    print("[*] Registering IDM Clone Native Messaging Host for browsers...")
    register_host("chrome", chrome_manifest)
    register_host("edge", chrome_manifest)
    register_host("firefox", firefox_manifest)
