// Popup script for JPD Integration Module (Dual Language ID & EN)
document.addEventListener("DOMContentLoaded", () => {
  const statusDiv = document.getElementById("status");
  const statusText = document.getElementById("status-text") || statusDiv;
  const urlInput = document.getElementById("urlInput");
  const downloadBtn = document.getElementById("downloadBtn");
  const downloadBtnText = document.getElementById("downloadBtnText") || downloadBtn;
  const lblUrl = document.getElementById("lblUrl");
  const hintText = document.getElementById("hintText");
  const langToggleBtn = document.getElementById("langToggleBtn");

  let currentLang = "id";
  try {
    const cached = localStorage.getItem("jpd_language");
    if (cached) currentLang = cached;
  } catch (e) {}

  const STRINGS = {
    id: {
      status_checking: "Memeriksa koneksi host...",
      status_connected_http: "Just Press Download (JPD) Terhubung (Port 19900)",
      status_connected_native: "Just Press Download (JPD) Host Terhubung (Native IPC)",
      status_disconnected: "Aplikasi Belum Aktif (Buka Just Press Download)",
      label_url: "Unduh Tautan Langsung:",
      btn_send: "+ Kirim ke Just Press Download",
      btn_sending: "Mengirim...",
      hint: "Otomatis mencegat unduhan dari Chromium & Firefox",
      alert_empty: "Masukkan tautan URL unduhan terlebih dahulu",
      alert_success: "Tugas unduhan berhasil dikirim ke Just Press Download (JPD)!",
      alert_fail: "Gagal mengirim tugas: Pastikan Just Press Download (JPD) aktif.",
      lang_btn: "ID 🇮🇩",
    },
    en: {
      status_checking: "Checking host connection...",
      status_connected_http: "Just Press Download (JPD) Connected (Port 19900)",
      status_connected_native: "Just Press Download (JPD) Host Connected (Native IPC)",
      status_disconnected: "Application Offline (Launch Just Press Download)",
      label_url: "Direct Download URL:",
      btn_send: "+ Send to Just Press Download",
      btn_sending: "Sending...",
      hint: "Automatically intercepts downloads from Chromium & Firefox",
      alert_empty: "Please enter a download URL first",
      alert_success: "Download task dispatched to Just Press Download (JPD) successfully!",
      alert_fail: "Failed to dispatch: Ensure Just Press Download (JPD) is running.",
      lang_btn: "EN 🇬🇧",
    }
  };

  function tr(key) {
    const tbl = STRINGS[currentLang] || STRINGS.id;
    return tbl[key] || STRINGS.id[key] || key;
  }

  function applyLanguage() {
    if (lblUrl) lblUrl.textContent = tr("label_url");
    if (downloadBtnText) downloadBtnText.textContent = tr("btn_send");
    if (hintText) hintText.textContent = tr("hint");
    if (langToggleBtn) langToggleBtn.textContent = tr("lang_btn");
    checkStatus();
  }

  if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
    chrome.storage.local.get({ jpd_language: currentLang }, (items) => {
      if (items && items.jpd_language) {
        currentLang = items.jpd_language;
        try { localStorage.setItem("jpd_language", currentLang); } catch (e) {}
        applyLanguage();
      }
    });
  }

  if (langToggleBtn) {
    langToggleBtn.addEventListener("click", () => {
      currentLang = (currentLang === "id") ? "en" : "id";
      try { localStorage.setItem("jpd_language", currentLang); } catch (e) {}
      if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
        chrome.storage.local.set({ jpd_language: currentLang });
      }
      applyLanguage();
    });
  }

  function setStatus(online, text) {
    if (online) {
      statusDiv.classList.add("online");
      statusDiv.classList.remove("offline");
      statusText.textContent = text || tr("status_connected_http");
    } else {
      statusDiv.classList.remove("online");
      statusDiv.classList.add("offline");
      statusText.textContent = text || tr("status_disconnected");
    }
  }

  function checkStatus() {
    fetch("http://127.0.0.1:19900/api/ping")
      .then((r) => r.json())
      .then((data) => {
        if (data && data.status === "ok") {
          setStatus(true, tr("status_connected_http"));
          if (data.language && data.language !== currentLang) {
            currentLang = data.language;
            try { localStorage.setItem("jpd_language", currentLang); } catch (e) {}
            if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
              chrome.storage.local.set({ jpd_language: currentLang });
            }
            applyLanguage();
          }
        } else {
          throw new Error("Invalid ping response");
        }
      })
      .catch(() => {
        if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.sendNativeMessage) {
          chrome.runtime.sendNativeMessage("com.justpressdownload.host", { action: "ping" }, (response) => {
            if (!chrome.runtime.lastError && response && response.status === "ok") {
              setStatus(true, tr("status_connected_native"));
            } else {
              chrome.runtime.sendNativeMessage("com.idmclone.host", { action: "ping" }, (resp2) => {
                if (!chrome.runtime.lastError && resp2 && resp2.status === "ok") {
                  setStatus(true, tr("status_connected_native"));
                } else {
                  setStatus(false, tr("status_disconnected"));
                }
              });
            }
          });
        } else {
          setStatus(false, tr("status_disconnected"));
        }
      });
  }

  downloadBtn.addEventListener("click", () => {
    const url = urlInput.value.trim();
    if (!url) {
      alert(tr("alert_empty"));
      urlInput.focus();
      return;
    }

    downloadBtnText.textContent = tr("btn_sending");
    downloadBtn.disabled = true;

    // Send task via native messaging or loopback server
    if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.sendNativeMessage) {
      chrome.runtime.sendNativeMessage(
        "com.justpressdownload.host",
        { action: "download", url: url },
        (response) => {
          downloadBtn.disabled = false;
          downloadBtnText.textContent = tr("btn_send");
          if (chrome.runtime.lastError || (response && response.status === "error")) {
            // Fallback to local HTTP loopback server
            fetch("http://127.0.0.1:19900/api/download", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ url: url }),
            })
              .then((r) => r.json())
              .then((data) => {
                urlInput.value = "";
                alert(tr("alert_success"));
              })
              .catch((err) => {
                alert(tr("alert_fail"));
              });
          } else {
            urlInput.value = "";
            alert(tr("alert_success"));
          }
        }
      );
    } else {
      fetch("http://127.0.0.1:19900/api/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url }),
      })
        .then((r) => r.json())
        .then((data) => {
          downloadBtn.disabled = false;
          downloadBtnText.textContent = tr("btn_send");
          urlInput.value = "";
          alert(tr("alert_success"));
        })
        .catch((err) => {
          downloadBtn.disabled = false;
          downloadBtnText.textContent = tr("btn_send");
          alert(tr("alert_fail"));
        });
    }
  });

  applyLanguage();
});
