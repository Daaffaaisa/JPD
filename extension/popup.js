// Popup script for JustPressDownload (JPD)
document.addEventListener("DOMContentLoaded", () => {
  const statusDiv = document.getElementById("status");
  const statusText = document.getElementById("status-text") || statusDiv;
  const urlInput = document.getElementById("urlInput");
  const downloadBtn = document.getElementById("downloadBtn");

  function setStatus(online, text) {
    if (online) {
      statusDiv.classList.add("online");
      statusDiv.classList.remove("offline");
      statusText.textContent = text || "JustPressDownload Desktop Terhubung";
    } else {
      statusDiv.classList.remove("online");
      statusDiv.classList.add("offline");
      statusText.textContent = text || "Aplikasi Belum Aktif (Buka run_gui.bat)";
    }
  }

  // Check connection status via local loopback server or native messaging
  fetch("http://127.0.0.1:19900/api/ping")
    .then((r) => r.json())
    .then((data) => {
      if (data && data.status === "ok") {
        setStatus(true, "JustPressDownload (JPD) Terhubung (Port 19900)");
      } else {
        throw new Error("Invalid ping response");
      }
    })
    .catch(() => {
      if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.sendNativeMessage) {
        chrome.runtime.sendNativeMessage("com.idmclone.host", { action: "ping" }, (response) => {
          if (!chrome.runtime.lastError && response && response.status === "ok") {
            setStatus(true, "JustPressDownload (JPD) Host Terhubung (Native IPC)");
          } else {
            setStatus(false, "Aplikasi Belum Aktif (Buka run_gui.bat)");
          }
        });
      } else {
        setStatus(false, "Aplikasi Belum Aktif (Buka run_gui.bat)");
      }
    });

  downloadBtn.addEventListener("click", () => {
    const url = urlInput.value.trim();
    if (!url) {
      alert("Masukkan tautan URL unduhan terlebih dahulu");
      urlInput.focus();
      return;
    }

    downloadBtn.textContent = "Mengirim...";
    downloadBtn.disabled = true;

    // Send task via native messaging or loopback server
    if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.sendNativeMessage) {
      chrome.runtime.sendNativeMessage(
        "com.idmclone.host",
        { action: "download", url: url },
        (response) => {
          downloadBtn.disabled = false;
          downloadBtn.innerHTML = "<span>+ Kirim ke JustPressDownload</span>";
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
                alert("Tugas unduhan berhasil dikirim ke JustPressDownload (JPD)!");
              })
              .catch((err) => {
                alert("Gagal mengirim tugas: Pastikan JustPressDownload (JPD) aktif.");
              });
          } else {
            urlInput.value = "";
            alert("Tugas unduhan berhasil dikirim ke JustPressDownload (JPD)!");
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
          downloadBtn.innerHTML = "<span>+ Kirim ke JustPressDownload</span>";
          urlInput.value = "";
          alert("Tugas unduhan berhasil dikirim ke JustPressDownload (JPD)!");
        })
        .catch((err) => {
          downloadBtn.disabled = false;
          downloadBtn.innerHTML = "<span>+ Kirim ke JustPressDownload</span>";
          alert("Gagal mengirim tugas: Pastikan JustPressDownload (JPD) aktif.");
        });
    }
  });
});
