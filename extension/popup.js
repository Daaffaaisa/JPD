// Popup script for IDM Clone
document.addEventListener("DOMContentLoaded", () => {
  const statusDiv = document.getElementById("status");
  const urlInput = document.getElementById("urlInput");
  const downloadBtn = document.getElementById("downloadBtn");

  // Check connection status via local loopback server or native messaging
  fetch("http://127.0.0.1:19900/api/ping")
    .then((r) => r.json())
    .then((data) => {
      if (data && data.status === "ok") {
        statusDiv.textContent = "● IDM Clone Desktop App Connected";
        statusDiv.classList.add("online");
      }
    })
    .catch(() => {
      chrome.runtime.sendNativeMessage("com.idmclone.host", { action: "ping" }, (response) => {
        if (!chrome.runtime.lastError && response && response.status === "ok") {
          statusDiv.textContent = "● IDM Host Connected (Native)";
          statusDiv.classList.add("online");
        } else {
          statusDiv.textContent = "App Disconnected (Buka run_gui.bat)";
          statusDiv.classList.remove("online");
        }
      });
    });

  downloadBtn.addEventListener("click", () => {
    const url = urlInput.value.trim();
    if (!url) {
      alert("Please enter a valid URL");
      return;
    }

    downloadBtn.textContent = "Sending...";
    downloadBtn.disabled = true;

    chrome.runtime.sendNativeMessage(
      "com.idmclone.host",
      { action: "download", url: url },
      (response) => {
        downloadBtn.disabled = false;
        downloadBtn.textContent = "Send to IDM Clone";
        if (chrome.runtime.lastError || (response && response.status === "error")) {
          alert("Error: " + (chrome.runtime.lastError ? chrome.runtime.lastError.message : response.error));
        } else {
          urlInput.value = "";
          alert("Download task successfully sent to IDM Clone!");
        }
      }
    );
  });
});
